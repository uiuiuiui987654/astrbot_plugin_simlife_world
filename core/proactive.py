from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import DailyPlan, SessionState, TimelineItem
from .utils import deterministic_int, deterministic_probability, parse_datetime


@dataclass(slots=True, frozen=True)
class SendDecision:
    allowed: bool
    reason: str


def session_kind(umo: str) -> str:
    return "group" if "groupmessage" in umo.lower() else "friend"


class ProactivePolicy:
    def __init__(self, config, storage, timezone):
        self.config = config
        self.storage = storage
        self.timezone = timezone

    def settings_for(self, umo: str) -> dict:
        key = "group_settings" if session_kind(umo) == "group" else "friend_settings"
        return self.config.get(key, {}) or {}

    def enabled_sessions(self) -> list[str]:
        sessions: list[str] = []
        for key in ("friend_settings", "group_settings"):
            settings = self.config.get(key, {}) or {}
            if not settings.get("enable", False):
                continue
            sessions.extend(str(value).strip() for value in settings.get("session_list", []) if str(value).strip())
        return list(dict.fromkeys(sessions))

    def is_enabled(self, umo: str) -> bool:
        settings = self.settings_for(umo)
        return bool(settings.get("enable", False) and umo in settings.get("session_list", []))

    def subscribe(self, umo: str) -> bool:
        settings = self.settings_for(umo)
        settings["enable"] = True
        sessions = settings.get("session_list")
        if not isinstance(sessions, list):
            sessions = []
            settings["session_list"] = sessions
        if umo in sessions:
            return False
        sessions.append(umo)
        return True

    def ensure_state(self, umo: str, persona_id: str, plan: DailyPlan, now: datetime) -> SessionState:
        date_str = now.date().isoformat()
        is_group = session_kind(umo) == "group"
        state = self.storage.sessions.get(umo)
        if not state or state.date != date_str:
            settings = self.settings_for(umo)
            minimum = max(0, int(settings.get("daily_budget_min", 0)))
            if is_group:
                minimum = max(1, minimum)
            maximum = max(minimum, int(settings.get("daily_budget_max", minimum)))
            base = deterministic_int(f"budget::{date_str}::{umo}", minimum, maximum)
            bonus_raw = plan.group_bonus if is_group else plan.private_bonus
            bonus = max(0, min(int(settings.get("llm_bonus_max", 0)), bonus_raw))
            hard_max = max(minimum if is_group else 0, int(settings.get("daily_hard_max", base + bonus)))
            state = SessionState(
                date=date_str,
                persona_id=persona_id,
                daily_budget=min(hard_max, base + bonus),
                last_user_message_at=now.isoformat(),
            )
            self.storage.sessions[umo] = state
        else:
            state.persona_id = persona_id
            if is_group and state.daily_budget < 1:
                state.daily_budget = 1
        return state

    def record_incoming(self, umo: str, now: datetime) -> None:
        state = self.storage.sessions.get(umo)
        if not state:
            state = SessionState(date=now.date().isoformat(), last_user_message_at=now.isoformat())
            self.storage.sessions[umo] = state
        state.last_user_message_at = now.isoformat()
        state.unanswered_count = 0

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
        if not self.is_enabled(umo):
            return SendDecision(False, "session disabled or not whitelisted")
        delivery = self.config.get("delivery_settings", {}) or {}
        max_unanswered = max(0, int(delivery.get("max_unanswered", 3)))
        if max_unanswered and state.unanswered_count >= max_unanswered:
            return SendDecision(False, "maximum unanswered count reached")
        # 决策循环的主动消息：对方还没回上一条时先别再开口，避免连续追问和复读。
        # 空闲/窗口触发仍沿用 max_unanswered，不受这里影响。
        if trigger == "decision":
            decision_max_unanswered = max(
                0, int(delivery.get("decision_max_unanswered", 1))
            )
            if decision_max_unanswered and state.unanswered_count >= decision_max_unanswered:
                return SendDecision(
                    False, "waiting for a reply before another proactive message"
                )
        if state.sent_count >= state.daily_budget and not (
            session_kind(umo) == "group" and trigger == "window"
        ):
            return SendDecision(False, "daily budget exhausted")

        settings = self.settings_for(umo)
        is_group_window = session_kind(umo) == "group" and trigger == "window"
        if state.last_proactive_at and not is_group_window:
            elapsed = (now - parse_datetime(state.last_proactive_at, self.timezone)).total_seconds() / 60
            if trigger == "decision":
                cooldown = max(0, int(delivery.get("decision_cooldown_minutes", 15)))
            else:
                cooldown = max(0, int(settings.get("cooldown_minutes", 0)))
            if elapsed < cooldown:
                return SendDecision(False, "cooldown active")

        if trigger == "window" and state.last_user_message_at:
            idle = (now - parse_datetime(state.last_user_message_at, self.timezone)).total_seconds() / 60
            if idle < max(0, int(delivery.get("minimum_idle_for_window_minutes", 20))):
                return SendDecision(False, "conversation is not idle enough")

        if trigger != "sleep":
            if current_item and current_item.state == "sleep":
                return SendDecision(False, "sleeping")
        need_energy = self._need_value(needs, "energy")
        need_satiety = self._need_value(needs, "satiety")
        need_hygiene = self._need_value(needs, "hygiene")
        need_mood = self._need_value(needs, "mood")
        need_willingness = self._need_value(needs, "willingness")
        need_health = self._need_value(needs, "health")
        need_weak = bool(needs.get("weak_constitution")) if isinstance(needs, dict) else False
        need_rainy = (
            int(needs.get("rainy_streak") or 0)
            if isinstance(needs, dict)
            else 0
        )
        need_irregular = (
            int(needs.get("sleep_regularity_minutes") or 0)
            if isinstance(needs, dict)
            else 0
        )
        need_jetlag = (
            int(needs.get("social_jetlag_minutes") or 0)
            if isinstance(needs, dict)
            else 0
        )
        need_late_night = (
            int(needs.get("late_night_streak") or 0)
            if isinstance(needs, dict)
            else 0
        )
        need_sunny = (
            int(needs.get("sunny_streak") or 0)
            if isinstance(needs, dict)
            else 0
        )
        need_lonely = bool(needs.get("lonely")) if isinstance(needs, dict) else False
        need_chronic_lonely = (
            bool(needs.get("chronic_lonely")) if isinstance(needs, dict) else False
        )
        need_social_afterglow = (
            bool(needs.get("social_afterglow")) if isinstance(needs, dict) else False
        )
        need_hydration = (
            int(needs.get("hydration") or 100)
            if isinstance(needs, dict)
            else 100
        )
        need_hangover = bool(needs.get("hangover")) if isinstance(needs, dict) else False
        need_hangover_severity = (
            str(needs.get("hangover_severity") or "")
            if isinstance(needs, dict)
            else ""
        )
        need_alcohol_today = (
            bool(needs.get("alcohol_today")) if isinstance(needs, dict) else False
        )
        need_tipsy = bool(needs.get("tipsy")) if isinstance(needs, dict) else False
        need_frequent_drinking = (
            bool(needs.get("frequent_drinking")) if isinstance(needs, dict) else False
        )
        need_drinking_recovery = (
            bool(needs.get("drinking_recovery")) if isinstance(needs, dict) else False
        )
        need_work_stress = (
            int(needs.get("work_stress") or 0)
            if isinstance(needs, dict)
            else 0
        )
        need_overwork = bool(needs.get("overwork")) if isinstance(needs, dict) else False
        need_overwork_recovery = (
            bool(needs.get("overwork_recovery")) if isinstance(needs, dict) else False
        )
        need_caffeine_crash = (
            bool(needs.get("caffeine_crash")) if isinstance(needs, dict) else False
        )
        need_fever_recovery = (
            bool(needs.get("fever_recovery")) if isinstance(needs, dict) else False
        )
        need_eye_strain = bool(needs.get("eye_strain")) if isinstance(needs, dict) else False
        need_soreness = (
            bool(needs.get("muscle_soreness")) if isinstance(needs, dict) else False
        )
        need_heavy_food = (
            bool(needs.get("frequent_heavy_food")) if isinstance(needs, dict) else False
        )
        need_discomfort = (
            int(needs.get("discomfort_count") or 0)
            if isinstance(needs, dict)
            else 0
        )
        need_fast_music = (
            bool(needs.get("energetic_music_sleep"))
            if isinstance(needs, dict)
            else False
        )
        need_calm_music = (
            bool(needs.get("audio_sleep_relief"))
            if isinstance(needs, dict)
            else False
        )
        need_odor = bool(needs.get("body_odor")) if isinstance(needs, dict) else False
        need_monday = bool(needs.get("monday_blues")) if isinstance(needs, dict) else False
        need_social_satisfied = (
            bool(needs.get("socially_satisfied")) if isinstance(needs, dict) else False
        )
        need_solitude = bool(needs.get("need_solitude")) if isinstance(needs, dict) else False
        need_afternoon_dip = (
            bool(needs.get("afternoon_dip"))
            and not bool(needs.get("afternoon_dip_relief"))
            if isinstance(needs, dict)
            else False
        )
        need_morning_grogginess = (
            bool(needs.get("morning_grogginess"))
            and not bool(needs.get("morning_grogginess_relief"))
            if isinstance(needs, dict)
            else False
        )
        need_evening_sleepiness = (
            bool(needs.get("evening_sleepiness")) if isinstance(needs, dict) else False
        )
        need_social_hangover = (
            bool(needs.get("social_hangover_yesterday"))
            if isinstance(needs, dict)
            else False
        )
        need_sick = bool(needs.get("sick")) if isinstance(needs, dict) else False
        need_recovering = (
            bool(needs.get("recovering")) if isinstance(needs, dict) else False
        )
        if needs and needs.get("sleeping") and trigger != "sleep":
            return SendDecision(False, "sleeping")
        if need_sick:
            severity = str(needs.get("illness_severity") or "moderate")
            sick_chance = 0.08 if severity == "severe" else 0.2
            if needs.get("fever"):
                sick_chance = 0.05
            if trigger == "decision" and deterministic_probability(
                f"sick::{state.date}::{umo}::{attempt_key or 'sick'}"
            ) < sick_chance:
                return SendDecision(True, "allowed: low-frequency sick message")
            return SendDecision(False, "feeling sick")
        if trigger != "decision" and need_energy is not None and need_energy < 15:
            return SendDecision(False, "too exhausted to reach out")
        if trigger == "decision" and need_energy is not None and need_energy < 10:
            return SendDecision(False, "too exhausted to initiate a conversation")
        if need_willingness is not None and need_willingness < (12 if trigger == "decision" else 16):
            return SendDecision(False, "too unmotivated to reach out")
        if need_health is not None and need_health < (20 if trigger == "decision" else 25):
            return SendDecision(False, "feeling unwell")
        if trigger not in ("sleep", "decision"):
            probability = self.availability_probability(current_item)
            factor = 1.0
            if need_energy is not None:
                factor *= 0.55 if need_energy < 25 else 0.82 if need_energy < 40 else 1.0
            if need_satiety is not None:
                factor *= 0.65 if need_satiety < 25 else 0.86 if need_satiety < 40 else 1.0
            if need_hygiene is not None and need_hygiene < 30:
                factor *= 0.9
            if need_mood is not None:
                if need_mood < 35:
                    factor *= 0.7
                elif need_mood >= 75:
                    factor *= 1.1
            if need_willingness is not None:
                if need_willingness < 30:
                    factor *= 0.65
                elif need_willingness < 45:
                    factor *= 0.85
                elif need_willingness >= 75:
                    factor *= 1.05
            if need_health is not None and need_health < 50:
                factor *= 0.7
            if need_weak:
                factor *= 0.75
            if need_rainy >= 2:
                factor *= 0.85
            if need_irregular >= 120:
                factor *= 0.9
            if need_jetlag >= 90:
                factor *= 0.9
            if need_late_night >= 3:
                factor *= 0.9
            if need_sunny >= 3:
                factor *= 1.05
            if need_lonely:
                factor *= 1.08
            if need_chronic_lonely:
                factor *= 1.05
            if need_social_afterglow:
                factor *= 1.03
            if need_hydration < 30:
                factor *= 0.85
            if need_hangover:
                factor *= 0.5 if need_hangover_severity == "severe" else 0.85
            if need_alcohol_today:
                factor *= 0.9
            if need_tipsy:
                factor *= 1.15
            if need_frequent_drinking:
                factor *= 0.9
            if need_drinking_recovery:
                factor *= 1.05
            if need_work_stress >= 4:
                factor *= 0.9
            if need_overwork:
                factor *= 0.9
            if need_overwork_recovery:
                factor *= 1.05
            if need_caffeine_crash:
                factor *= 0.9
            if need_fever_recovery:
                factor *= 0.9
            if need_eye_strain:
                factor *= 0.95
            if need_soreness:
                factor *= 0.97
            if need_heavy_food:
                factor *= 0.95
            if need_discomfort:
                factor *= max(0.85, 1.0 - need_discomfort * 0.02)
            if need_fast_music:
                factor *= 1.05
            if need_calm_music:
                factor *= 0.95
            if need_odor:
                factor *= 0.95
            if need_monday:
                factor *= 0.95
            if need_social_satisfied:
                factor *= 1.05
            if need_solitude:
                factor *= 0.9
            if need_social_hangover:
                factor *= 0.95
            if need_afternoon_dip:
                factor *= 0.97
            if need_morning_grogginess:
                factor *= 0.97
            if need_evening_sleepiness:
                factor *= 0.98
            if need_recovering:
                factor *= 0.5
            probability = max(0.0, min(1.0, probability * factor))
            probability_key = attempt_key or (current_item.id if current_item else "none")
            if deterministic_probability(f"availability::{state.date}::{umo}::{probability_key}") >= probability:
                return SendDecision(False, "availability probability rejected")
        return SendDecision(True, "allowed")

    @staticmethod
    def _need_value(needs: dict | None, key: str) -> float | None:
        if not isinstance(needs, dict):
            return None
        try:
            return max(0.0, min(100.0, float(needs.get(key))))
        except (TypeError, ValueError):
            return None

    def availability_probability(self, current_item: TimelineItem | None) -> float:
        if current_item is None:
            return 1.0
        delivery = self.config.get("delivery_settings", {}) or {}
        configured = delivery.get("availability_probabilities", {}) or {}
        raw = configured.get(current_item.availability)
        if raw is None:
            return 1.0
        try:
            return max(0.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            return 1.0

    def record_delivery(
        self, state: SessionState, now: datetime, *, count_budget: bool = True
    ) -> None:
        if count_budget:
            state.sent_count += 1
        state.unanswered_count += 1
        state.last_proactive_at = now.isoformat()
