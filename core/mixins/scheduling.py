"""Job scheduling for proactive messages: plan windows, the occasional night message, idle pings, retries.

Job ids share the prefix ``pvd:<umo-hash>:`` so a session's jobs can be dropped together
when its plan changes.
"""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta

from ..models import DailyPlan, ProactiveWindow, minute_of_day
from ..persona import PersonaContext
from ..proactive import session_kind
from ..utils import deterministic_int, deterministic_probability, next_available_at, parse_datetime
from ..window_schedule import proactive_window_offset_minutes

# Rejection reasons reported by the proactive policy.
ASLEEP = "sleeping"
UNAVAILABLE = "availability probability rejected"
NOT_IDLE = "conversation is not idle enough"
AGENT_BUSY = "agent task active"
COOLDOWN = "cooldown active"
WAIT_FOR_FREE_SLOT = {ASLEEP, UNAVAILABLE}

MISSED_REASONS = {
    NOT_IDLE: "当时你正在忙或正在聊天，没找到合适的插话时机",
    AGENT_BUSY: "当时你们正在处理一件复杂的事情，不适合突然打断",
    COOLDOWN: "当时你们刚刚才聊过，紧接着再开口会显得太突兀",
    UNAVAILABLE: "当时对方的状态不太适合被打扰",
    ASLEEP: "当时对方正在休息",
}
NIGHT_INTENT = "睡梦中醒来、起夜或失眠时忽然想起对方"
IDLE_INTENT = "会话已经沉默了一段时间，想自然地重新联系"


class SchedulingMixin:
    # ------------------------------------------------------------------ helpers

    def _job_prefix(self, umo: str) -> str:
        return f"pvd:{self._umo_hash(umo)}:"

    def _delivery(self) -> dict:
        return self.config.get("delivery_settings", {}) or {}

    def _later(self, base: datetime, low: int, high: int) -> datetime:
        return base + timedelta(minutes=random.randint(low, high))

    def _at_time(self, date_str: str, hhmm: str) -> datetime:
        hour, minute = (int(part) for part in hhmm.split(":"))
        return datetime.combine(date.fromisoformat(date_str), time(hour, minute), self.timezone)

    def _end_time(self, date_str: str, hhmm: str) -> datetime:
        if hhmm != "24:00":
            return self._at_time(date_str, hhmm)
        return datetime.combine(date.fromisoformat(date_str) + timedelta(days=1), time.min, self.timezone)

    @staticmethod
    def _duration_minutes(start: str, end: str) -> int:
        return minute_of_day(end) - minute_of_day(start)

    @staticmethod
    def _window_matches(umo: str, window: ProactiveWindow) -> bool:
        return window.audience in {"both", "group" if session_kind(umo) == "group" else "private"}

    # ------------------------------------------------------------------ (re)scheduling a session

    async def _reschedule_plan_sessions(self, persona: PersonaContext, plan: DailyPlan) -> None:
        for umo in self.policy.enabled_sessions():
            resolved = await self.personas.resolve(umo)
            if resolved.id == persona.id:
                await self._schedule_session(umo, resolved, plan)
        await self.storage.save_sessions()

    async def _schedule_session(self, umo: str, persona: PersonaContext, plan: DailyPlan) -> None:
        """Replace the session's plan jobs with ones for ``plan``."""
        plan_jobs = self._job_prefix(umo) + "plan:"
        self.runtime.remove_prefix(plan_jobs)
        self.runtime.remove(self._job_prefix(umo) + "idle")
        if not plan.has_schedule:
            self._schedule_available_umos.discard(umo)
            return
        self._schedule_available_umos.add(umo)
        now = self._now()
        state = self.policy.ensure_state(umo, persona.id, plan, now)
        jitter = self._delivery().get("proactive_window_jitter_minutes", 15)
        for window in plan.proactive_windows:
            if not self._window_matches(umo, window):
                continue
            run_at = self._at_time(plan.date, window.at) + timedelta(
                minutes=proactive_window_offset_minutes(plan, window, jitter)
            )
            if run_at > now:
                self.runtime.add_date_job(
                    f"{plan_jobs}window:{window.id}", run_at, self._run_window, umo, persona.id, plan.revision, window.id
                )
        await self._schedule_sleep_exception(umo, persona, plan, state)
        self._schedule_idle(umo)

    async def _schedule_sleep_exception(self, umo, persona, plan, state) -> None:
        """Once per day and session, maybe pick a moment inside her longest sleep to message anyway."""
        if state.sleep_drawn:
            return
        state.sleep_drawn = True
        chance = max(0.0, min(1.0, float(self._delivery().get("sleep_exception_probability", 0.08))))
        state.sleep_selected = deterministic_probability(f"sleep::{plan.date}::{umo}") < chance
        sleeps = [item for item in plan.timeline if item.state == "sleep"] if state.sleep_selected else []
        if not sleeps:
            return
        longest = max(sleeps, key=lambda item: self._duration_minutes(item.start, item.end))
        start, end = self._at_time(plan.date, longest.start), self._end_time(plan.date, longest.end)
        if end <= self._now() or (end - start).total_seconds() < 120:
            return
        earliest = max(start, self._now() + timedelta(seconds=10))
        room = max(1, int((end - earliest).total_seconds() // 60) - 1)
        run_at = earliest + timedelta(minutes=deterministic_int(f"sleep-time::{plan.date}::{umo}", 0, room))
        self.runtime.add_date_job(
            self._job_prefix(umo) + "plan:sleep", run_at, self._run_sleep, umo, persona.id, plan.revision
        )

    def _schedule_idle(self, umo: str, *, run_at: datetime | None = None) -> None:
        """(Re)arm the "it's been quiet for a while" ping, by default after a random idle span."""
        job_id = self._job_prefix(umo) + "idle"
        self.runtime.remove(job_id)
        if not self.policy.is_enabled(umo) or umo not in self._schedule_available_umos:
            return
        if run_at is None:
            settings = self.policy.settings_for(umo)
            shortest = max(1, int(settings.get("idle_min_minutes", 90)))
            longest = max(shortest, int(settings.get("idle_max_minutes", shortest)))
            run_at = self._later(self._now(), shortest, longest)
        self.runtime.add_date_job(job_id, run_at, self._run_idle, umo)

    # ------------------------------------------------------------------ job bodies

    async def _current(self, umo: str, persona_id: str, revision: str):
        """``(persona, plan)`` if the job still belongs to the live plan, else ``None``."""
        persona, plan = await self._ensure_plan_for_umo(umo)
        return (persona, plan) if persona.id == persona_id and plan.revision == revision else None

    @staticmethod
    def _find_window(plan: DailyPlan, window_id: str) -> ProactiveWindow | None:
        return next((window for window in plan.proactive_windows if window.id == window_id), None)

    async def _run_window(self, umo: str, persona_id: str, revision: str, window_id: str) -> None:
        persona, plan = await self._ensure_plan_for_umo(umo)
        if persona.id != persona_id or plan.revision != revision:
            await self._schedule_session(umo, persona, plan)
            return
        window = self._find_window(plan, window_id)
        if window:
            await self._attempt_window(umo, persona, plan, window, delayed=False)

    async def _run_delayed_window(
        self, umo: str, persona_id: str, revision: str, window_id: str, scheduled_at: str, retry_reason: str = ""
    ) -> None:
        live = await self._current(umo, persona_id, revision)
        window = self._find_window(live[1], window_id) if live else None
        if window:
            await self._attempt_window(
                umo, *live, window, delayed=True, attempt_key=scheduled_at, retry_reason=retry_reason
            )

    async def _run_sleep(self, umo: str, persona_id: str, revision: str) -> None:
        live = await self._current(umo, persona_id, revision)
        if live:
            await self._attempt_unsolicited(umo, *live, NIGHT_INTENT, "sleep")

    async def _run_idle(self, umo: str) -> None:
        persona, plan = await self._ensure_plan_for_umo(umo)
        sent, reason = await self._attempt_unsolicited(umo, persona, plan, IDLE_INTENT, "idle")
        if sent:
            self._schedule_idle(umo)
        elif reason in WAIT_FOR_FREE_SLOT:
            free_at = next_available_at(plan, self._now())
            if free_at:
                self._schedule_idle(umo, run_at=self._later(free_at, 3, 15))
        elif reason in {COOLDOWN, NOT_IDLE, AGENT_BUSY}:
            self._schedule_idle(umo, run_at=self._now() + timedelta(minutes=30))

    # ------------------------------------------------------------------ windows and their retries

    async def _attempt_window(
        self,
        umo: str,
        persona: PersonaContext,
        plan: DailyPlan,
        window: ProactiveWindow,
        *,
        delayed: bool,
        attempt_key: str = "",
        retry_reason: str = "",
    ) -> None:
        """Try a window now; when the moment was wrong, book a retry later the same day."""
        intent = self._delayed_window_intent(window, plan, retry_reason) if delayed else window.intent
        sent, reason = await self._attempt_unsolicited(
            umo, persona, plan, intent, "window", attempt_key=attempt_key or window.id
        )
        key = (umo, plan.revision, window.id)
        if sent:
            self._window_retry_counts.pop(key, None)
            return
        if not self._should_retry_window(umo, reason):
            return
        tries = self._window_retry_counts.get(key, 0)
        if tries >= max(0, int(self._delivery().get("window_retry_max", 3))):
            return
        run_at = self._window_retry_run_at(umo, plan, reason)
        if run_at is None:
            return
        self._schedule_window_retry(umo, persona, plan, window, run_at, reason)
        if reason != AGENT_BUSY:  # waiting on a running agent task doesn't use up a retry
            self._window_retry_counts[key] = tries + 1

    def _delayed_window_intent(self, window: ProactiveWindow, plan: DailyPlan, retry_reason: str = "") -> str:
        """Once the window's activity is over, tell the model it missed the moment and why."""
        source = next((item for item in plan.timeline if item.id == window.source_item_id), None)
        if not source or self._now() < self._end_time(plan.date, source.end):
            return window.intent
        why = MISSED_REASONS.get(retry_reason, "当时时机不太合适")
        return (
            f"{window.intent}。你原本打算在「{source.activity}」时段联系对方，但{why}，"
            "错过了那个时机；现在自然地向对方提起，别让对方察觉这是程序自动安排的。"
        )

    def _should_retry_window(self, umo: str, reason: str) -> bool:
        if reason in WAIT_FOR_FREE_SLOT:
            return True
        switch = {
            NOT_IDLE: "window_retry_when_not_idle",
            AGENT_BUSY: "window_retry_when_not_idle",
            COOLDOWN: "window_retry_when_cooldown",
        }.get(reason)
        return bool(switch and self._delivery().get(switch, False))

    def _window_retry_run_at(self, umo: str, plan: DailyPlan, reason: str) -> datetime | None:
        """When to retry, or ``None`` if there's no sensible time left today."""
        now = self._now()
        if reason in WAIT_FOR_FREE_SLOT:
            free_at = next_available_at(plan, now)
            if not free_at:
                return None
            run_at = self._later(free_at, 3, 15)
        elif reason == AGENT_BUSY:
            run_at = now + timedelta(minutes=30)
        elif reason == NOT_IDLE:
            state = self.storage.sessions.get(umo)
            quiet = max(0, int(self._delivery().get("minimum_idle_for_window_minutes", 20)))
            seen = [parse_datetime(state.last_user_message_at, self.timezone)] if state and state.last_user_message_at else []
            if activity_at := self._conversation_activity_at.get(umo):
                seen.append(activity_at)
            if not seen:
                return None
            run_at = self._later(max(max(seen) + timedelta(minutes=quiet), now), 1, 5)
        elif reason == COOLDOWN:
            state = self.storage.sessions.get(umo)
            if not state or not state.last_proactive_at:
                return None
            cooldown = max(0, int(self.policy.settings_for(umo).get("cooldown_minutes", 0)))
            ready = parse_datetime(state.last_proactive_at, self.timezone) + timedelta(minutes=cooldown)
            run_at = self._later(max(ready, now), 1, 5)
        else:
            return None
        return None if run_at.date() > date.fromisoformat(plan.date) else run_at

    def _schedule_window_retry(
        self,
        umo: str,
        persona: PersonaContext,
        plan: DailyPlan,
        window: ProactiveWindow,
        run_at: datetime | None = None,
        retry_reason: str = "",
    ) -> None:
        if run_at is None:
            free_at = next_available_at(plan, self._now())
            if not free_at:
                return
            run_at = self._later(free_at, 3, 15)
        self.runtime.add_date_job(
            f"{self._job_prefix(umo)}plan:window-retry:{window.id}",
            run_at,
            self._run_delayed_window,
            umo,
            persona.id,
            plan.revision,
            window.id,
            run_at.isoformat(),
            retry_reason,
        )
