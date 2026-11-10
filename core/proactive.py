"""Whether a proactive message may be sent now, and the per-chat daily budget."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from .models import DailyPlan, SessionState, TimelineItem
from .utils import deterministic_int, deterministic_probability, parse_datetime


@dataclass(slots=True, frozen=True)
class SendDecision:
    allowed: bool
    reason: str


def session_kind(umo: str) -> str:
    return "group" if "groupmessage" in umo.lower() else "friend"


def _when(test: Callable[[dict], bool], factor: float) -> Callable[[dict], float]:
    return lambda needs: factor if test(needs) else 1.0


def _flag(key: str, factor: float) -> Callable[[dict], float]:
    return _when(lambda needs: bool(needs.get(key)), factor)


def _at_least(key: str, limit: int, factor: float) -> Callable[[dict], float]:
    return _when(lambda needs: int(needs.get(key) or 0) >= limit, factor)


def _unrelieved(key: str, relief: str, factor: float) -> Callable[[dict], float]:
    return _when(lambda needs: bool(needs.get(key)) and not bool(needs.get(relief)), factor)


def _hangover(needs: dict) -> float:
    if not needs.get("hangover"):
        return 1.0
    return 0.5 if str(needs.get("hangover_severity") or "") == "severe" else 0.85


def _discomfort(needs: dict) -> float:
    count = int(needs.get("discomfort_count") or 0)
    return max(0.85, 1.0 - count * 0.02) if count else 1.0


# Body / mood signals that make reaching out less (or more) likely, applied in this order.
NEED_MULTIPLIERS: tuple[Callable[[dict], float], ...] = (
    _flag("weak_constitution", 0.75),
    _at_least("rainy_streak", 2, 0.85),
    _at_least("sleep_regularity_minutes", 120, 0.9),
    _at_least("social_jetlag_minutes", 90, 0.9),
    _at_least("late_night_streak", 3, 0.9),
    _at_least("sunny_streak", 3, 1.05),
    _flag("lonely", 1.08),
    _flag("chronic_lonely", 1.05),
    _flag("social_afterglow", 1.03),
    _when(lambda needs: int(needs.get("hydration") or 100) < 30, 0.85),
    _hangover,
    _flag("alcohol_today", 0.9),
    _flag("tipsy", 1.15),
    _flag("frequent_drinking", 0.9),
    _flag("drinking_recovery", 1.05),
    _at_least("work_stress", 4, 0.9),
    _flag("overwork", 0.9),
    _flag("overwork_recovery", 1.05),
    _flag("caffeine_crash", 0.9),
    _flag("fever_recovery", 0.9),
    _flag("eye_strain", 0.95),
    _flag("muscle_soreness", 0.97),
    _flag("frequent_heavy_food", 0.95),
    _discomfort,
    _flag("energetic_music_sleep", 1.05),
    _flag("audio_sleep_relief", 0.95),
    _flag("body_odor", 0.95),
    _flag("monday_blues", 0.95),
    _flag("socially_satisfied", 1.05),
    _flag("need_solitude", 0.9),
    _flag("social_hangover_yesterday", 0.95),
    _unrelieved("afternoon_dip", "afternoon_dip_relief", 0.97),
    _unrelieved("morning_grogginess", "morning_grogginess_relief", 0.97),
    _flag("evening_sleepiness", 0.98),
    _flag("recovering", 0.5),
)


def _level(needs: dict | None, key: str) -> float | None:
    """A 0–100 need value, or ``None`` when missing / not a number."""
    if not isinstance(needs, dict):
        return None
    try:
        return max(0.0, min(100.0, float(needs.get(key))))
    except (TypeError, ValueError):
        return None


def _band(value: float | None, steps: tuple[tuple[float, float], ...], default: float = 1.0) -> float:
    """Multiplier of the first ``(upper bound, multiplier)`` step ``value`` falls under."""
    if value is None:
        return 1.0
    return next((factor for bound, factor in steps if value < bound), default)


def _need_factor(needs: dict | None) -> float:
    energy, satiety, hygiene = _level(needs, "energy"), _level(needs, "satiety"), _level(needs, "hygiene")
    mood, willingness, health = _level(needs, "mood"), _level(needs, "willingness"), _level(needs, "health")
    factor = 1.0
    factor *= _band(energy, ((25, 0.55), (40, 0.82)))
    factor *= _band(satiety, ((25, 0.65), (40, 0.86)))
    if hygiene is not None and hygiene < 30:
        factor *= 0.9
    if mood is not None:
        factor *= 0.7 if mood < 35 else 1.1 if mood >= 75 else 1.0
    if willingness is not None:
        factor *= _band(willingness, ((30, 0.65), (45, 0.85), (75, 1.0)), default=1.05)
    if health is not None and health < 50:
        factor *= 0.7
    if isinstance(needs, dict):
        for multiplier in NEED_MULTIPLIERS:
            factor *= multiplier(needs)
    return factor


class ProactivePolicy:
    def __init__(self, config, storage, timezone):
        self.config = config
        self.storage = storage
        self.timezone = timezone

    # ------------------------------------------------------------------ sessions

    def settings_for(self, umo: str) -> dict:
        return self.config.get(f"{session_kind(umo)}_settings", {}) or {}

    def enabled_sessions(self) -> list[str]:
        found: list[str] = []
        for key in ("friend_settings", "group_settings"):
            settings = self.config.get(key, {}) or {}
            if settings.get("enable", False):
                found += [str(umo).strip() for umo in settings.get("session_list", []) if str(umo).strip()]
        return list(dict.fromkeys(found))

    def is_enabled(self, umo: str) -> bool:
        settings = self.settings_for(umo)
        return bool(settings.get("enable", False) and umo in settings.get("session_list", []))

    def subscribe(self, umo: str) -> bool:
        """Enable proactive messages for this chat; ``False`` if it was already listed."""
        settings = self.settings_for(umo)
        settings["enable"] = True
        if not isinstance(settings.get("session_list"), list):
            settings["session_list"] = []
        if umo in settings["session_list"]:
            return False
        settings["session_list"].append(umo)
        return True

    def _daily_budget(self, umo: str, day: str, plan: DailyPlan) -> int:
        settings, group = self.settings_for(umo), session_kind(umo) == "group"
        low = max(0, int(settings.get("daily_budget_min", 0)))
        if group:
            low = max(1, low)  # groups always get at least one window message
        high = max(low, int(settings.get("daily_budget_max", low)))
        base = deterministic_int(f"budget::{day}::{umo}", low, high)
        extra = max(0, min(int(settings.get("llm_bonus_max", 0)), plan.group_bonus if group else plan.private_bonus))
        cap = max(low if group else 0, int(settings.get("daily_hard_max", base + extra)))
        return min(cap, base + extra)

    def ensure_state(self, umo: str, persona_id: str, plan: DailyPlan, now: datetime) -> SessionState:
        """Today's counters for ``umo``, created (with a fresh budget) on the first call of the day."""
        day = now.date().isoformat()
        state = self.storage.sessions.get(umo)
        if state and state.date == day:
            state.persona_id = persona_id
            if session_kind(umo) == "group" and state.daily_budget < 1:
                state.daily_budget = 1
            return state
        state = SessionState(
            date=day, persona_id=persona_id, daily_budget=self._daily_budget(umo, day, plan), last_user_message_at=now.isoformat()
        )
        self.storage.sessions[umo] = state
        return state

    def record_incoming(self, umo: str, now: datetime) -> None:
        state = self.storage.sessions.setdefault(umo, SessionState(date=now.date().isoformat()))
        state.last_user_message_at = now.isoformat()
        state.unanswered_count = 0

    def record_delivery(self, state: SessionState, now: datetime, *, count_budget: bool = True) -> None:
        state.sent_count += int(count_budget)
        state.unanswered_count += 1
        state.last_proactive_at = now.isoformat()

    # ------------------------------------------------------------------ decision

    def _minutes_since(self, stamp: str, now: datetime) -> float:
        return (now - parse_datetime(stamp, self.timezone)).total_seconds() / 60

    def _gate(self, umo: str, state: SessionState, current_item: TimelineItem | None, now: datetime, trigger: str) -> str:
        """Hard rules (whitelist, unanswered, budget, cooldown, idle, sleep); ``""`` when all pass."""
        if not self.is_enabled(umo):
            return "session disabled or not whitelisted"
        delivery = self.config.get("delivery_settings", {}) or {}
        unanswered_cap = max(0, int(delivery.get("max_unanswered", 3)))
        if unanswered_cap and state.unanswered_count >= unanswered_cap:
            return "maximum unanswered count reached"
        if trigger == "decision":
            # self-initiated messages wait for a reply before the next one
            reply_cap = max(0, int(delivery.get("decision_max_unanswered", 1)))
            if reply_cap and state.unanswered_count >= reply_cap:
                return "waiting for a reply before another proactive message"
        group_window = session_kind(umo) == "group" and trigger == "window"
        if state.sent_count >= state.daily_budget and not group_window:
            return "daily budget exhausted"
        if state.last_proactive_at and not group_window:
            cooldown = (
                delivery.get("decision_cooldown_minutes", 15)
                if trigger == "decision"
                else self.settings_for(umo).get("cooldown_minutes", 0)
            )
            if self._minutes_since(state.last_proactive_at, now) < max(0, int(cooldown)):
                return "cooldown active"
        if trigger == "window" and state.last_user_message_at:
            quiet_needed = max(0, int(delivery.get("minimum_idle_for_window_minutes", 20)))
            if self._minutes_since(state.last_user_message_at, now) < quiet_needed:
                return "conversation is not idle enough"
        if trigger != "sleep" and current_item and current_item.state == "sleep":
            return "sleeping"
        return ""

    def evaluate(
        self,
        *,
        umo: str,
        state: SessionState,
        current_item: TimelineItem | None,
        now: datetime,
        trigger: str,
        attempt_key: str = "",
        needs: dict | None = None,
    ) -> SendDecision:
        blocked = self._gate(umo, state, current_item, now, trigger)
        if blocked:
            return SendDecision(False, blocked)
        if needs and needs.get("sleeping") and trigger != "sleep":
            return SendDecision(False, "sleeping")
        if isinstance(needs, dict) and needs.get("sick"):
            # sick: only an occasional self-initiated message
            chance = 0.05 if needs.get("fever") else 0.08 if str(needs.get("illness_severity") or "moderate") == "severe" else 0.2
            roll = deterministic_probability(f"sick::{state.date}::{umo}::{attempt_key or 'sick'}")
            if trigger == "decision" and roll < chance:
                return SendDecision(True, "allowed: low-frequency sick message")
            return SendDecision(False, "feeling sick")
        deciding = trigger == "decision"
        energy = _level(needs, "energy")
        if energy is not None and energy < (10 if deciding else 15):
            return SendDecision(False, "too exhausted to initiate a conversation" if deciding else "too exhausted to reach out")
        willingness = _level(needs, "willingness")
        if willingness is not None and willingness < (12 if deciding else 16):
            return SendDecision(False, "too unmotivated to reach out")
        health = _level(needs, "health")
        if health is not None and health < (20 if deciding else 25):
            return SendDecision(False, "feeling unwell")
        if trigger in ("sleep", "decision"):
            return SendDecision(True, "allowed")
        chance = max(0.0, min(1.0, self.availability_probability(current_item) * _need_factor(needs)))
        key = attempt_key or (current_item.id if current_item else "none")
        if deterministic_probability(f"availability::{state.date}::{umo}::{key}") >= chance:
            return SendDecision(False, "availability probability rejected")
        return SendDecision(True, "allowed")

    @staticmethod
    def _need_value(needs: dict | None, key: str) -> float | None:
        return _level(needs, key)

    def availability_probability(self, current_item: TimelineItem | None) -> float:
        """Configured send chance for the current segment's availability (default 1)."""
        if current_item is None:
            return 1.0
        table: dict[str, Any] = (self.config.get("delivery_settings", {}) or {}).get("availability_probabilities", {}) or {}
        raw = table.get(current_item.availability)
        try:
            return 1.0 if raw is None else max(0.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            return 1.0
