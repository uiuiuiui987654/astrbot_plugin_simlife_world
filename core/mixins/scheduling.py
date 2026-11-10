"""Scheduling proactive windows, sleep/idle jobs and retries.

Mixin for ProactiveVirtualDailyPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta

from ..models import (
    DailyPlan,
    ProactiveWindow,
)
from ..persona import PersonaContext
from ..proactive import session_kind
from ..utils import (
    deterministic_int,
    deterministic_probability,
    next_available_at,
    parse_datetime,
)
from ..window_schedule import proactive_window_offset_minutes


class SchedulingMixin:
    async def _reschedule_plan_sessions(
        self, persona: PersonaContext, plan: DailyPlan
    ) -> None:
        for umo in self.policy.enabled_sessions():
            resolved = await self.personas.resolve(umo)
            if resolved.id == persona.id:
                await self._schedule_session(umo, resolved, plan)
        await self.storage.save_sessions()

    async def _schedule_session(
        self, umo: str, persona: PersonaContext, plan: DailyPlan
    ) -> None:
        prefix = f"pvd:{self._umo_hash(umo)}:plan:"
        self.runtime.remove_prefix(prefix)
        self.runtime.remove(f"pvd:{self._umo_hash(umo)}:idle")
        if not plan.has_schedule:
            self._schedule_available_umos.discard(umo)
            return
        self._schedule_available_umos.add(umo)
        now = self._now()
        state = self.policy.ensure_state(umo, persona.id, plan, now)
        delivery = self.config.get("delivery_settings", {}) or {}
        jitter_minutes = delivery.get("proactive_window_jitter_minutes", 15)
        for window in plan.proactive_windows:
            if not self._window_matches(umo, window):
                continue
            run_at = self._at_time(plan.date, window.at) + timedelta(
                minutes=proactive_window_offset_minutes(plan, window, jitter_minutes),
            )
            if run_at <= now:
                continue
            self.runtime.add_date_job(
                prefix + "window:" + window.id,
                run_at,
                self._run_window,
                umo,
                persona.id,
                plan.revision,
                window.id,
            )
        await self._schedule_sleep_exception(umo, persona, plan, state)
        self._schedule_idle(umo)

    @staticmethod
    def _window_matches(umo: str, window: ProactiveWindow) -> bool:
        kind = "group" if session_kind(umo) == "group" else "private"
        return window.audience in {"both", kind}

    def _at_time(self, date_str: str, hhmm: str) -> datetime:
        hour, minute = map(int, hhmm.split(":"))
        return datetime.combine(
            date.fromisoformat(date_str), time(hour, minute), self.timezone
        )

    async def _schedule_sleep_exception(self, umo, persona, plan, state) -> None:
        if state.sleep_drawn:
            return
        state.sleep_drawn = True
        probability = float(
            (self.config.get("delivery_settings", {}) or {}).get(
                "sleep_exception_probability", 0.08
            )
        )
        state.sleep_selected = deterministic_probability(
            f"sleep::{plan.date}::{umo}"
        ) < max(0.0, min(1.0, probability))
        if not state.sleep_selected:
            return
        sleep_items = [item for item in plan.timeline if item.state == "sleep"]
        if not sleep_items:
            return
        item = max(
            sleep_items,
            key=lambda value: self._duration_minutes(value.start, value.end),
        )
        start = self._at_time(plan.date, item.start)
        end = self._end_time(plan.date, item.end)
        if end <= self._now() or (end - start).total_seconds() < 120:
            return
        earliest = max(start, self._now() + timedelta(seconds=10))
        span = max(1, int((end - earliest).total_seconds() // 60) - 1)
        offset = deterministic_int(f"sleep-time::{plan.date}::{umo}", 0, span)
        run_at = earliest + timedelta(minutes=offset)
        self.runtime.add_date_job(
            f"pvd:{self._umo_hash(umo)}:plan:sleep",
            run_at,
            self._run_sleep,
            umo,
            persona.id,
            plan.revision,
        )

    @staticmethod
    def _duration_minutes(start: str, end: str) -> int:
        def value(raw: str) -> int:
            if raw == "24:00":
                return 1440
            hour, minute = map(int, raw.split(":"))
            return hour * 60 + minute

        return value(end) - value(start)

    def _end_time(self, date_str: str, hhmm: str) -> datetime:
        if hhmm == "24:00":
            return datetime.combine(
                date.fromisoformat(date_str) + timedelta(days=1),
                time.min,
                self.timezone,
            )
        return self._at_time(date_str, hhmm)

    def _schedule_idle(self, umo: str, *, run_at: datetime | None = None) -> None:
        job_id = f"pvd:{self._umo_hash(umo)}:idle"
        self.runtime.remove(job_id)
        if not self.policy.is_enabled(umo) or umo not in self._schedule_available_umos:
            return
        if run_at is None:
            settings = self.policy.settings_for(umo)
            minimum = max(1, int(settings.get("idle_min_minutes", 90)))
            maximum = max(minimum, int(settings.get("idle_max_minutes", minimum)))
            run_at = self._now() + timedelta(minutes=random.randint(minimum, maximum))
        self.runtime.add_date_job(job_id, run_at, self._run_idle, umo)

    async def _run_window(
        self, umo: str, persona_id: str, revision: str, window_id: str
    ) -> None:
        persona, plan = await self._ensure_plan_for_umo(umo)
        if persona.id != persona_id or plan.revision != revision:
            await self._schedule_session(umo, persona, plan)
            return
        window = next(
            (value for value in plan.proactive_windows if value.id == window_id), None
        )
        if not window:
            return
        await self._attempt_window(umo, persona, plan, window, delayed=False)

    async def _run_delayed_window(
        self,
        umo: str,
        persona_id: str,
        revision: str,
        window_id: str,
        scheduled_at: str,
        retry_reason: str = "",
    ) -> None:
        persona, plan = await self._ensure_plan_for_umo(umo)
        if persona.id != persona_id or plan.revision != revision:
            return
        window = next(
            (value for value in plan.proactive_windows if value.id == window_id), None
        )
        if not window:
            return
        await self._attempt_window(
            umo,
            persona,
            plan,
            window,
            delayed=True,
            attempt_key=scheduled_at,
            retry_reason=retry_reason,
        )

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
        intent = window.intent
        if delayed:
            intent = self._delayed_window_intent(window, plan, retry_reason)
        sent, reason = await self._attempt_unsolicited(
            umo,
            persona,
            plan,
            intent,
            "window",
            attempt_key=attempt_key or window.id,
        )
        if sent:
            self._window_retry_counts.pop((umo, plan.revision, window.id), None)
            return
        if not self._should_retry_window(umo, reason):
            return
        key = (umo, plan.revision, window.id)
        count = self._window_retry_counts.get(key, 0)
        delivery = self.config.get("delivery_settings", {}) or {}
        retry_max = max(0, int(delivery.get("window_retry_max", 3)))
        if count >= retry_max:
            return
        run_at = self._window_retry_run_at(umo, plan, reason)
        if run_at is None:
            return
        self._schedule_window_retry(umo, persona, plan, window, run_at, reason)
        if reason != "agent task active":
            self._window_retry_counts[key] = count + 1

    def _delayed_window_intent(
        self,
        window: ProactiveWindow,
        plan: DailyPlan,
        retry_reason: str = "",
    ) -> str:
        source = next(
            (item for item in plan.timeline if item.id == window.source_item_id), None
        )
        base = window.intent
        if not source:
            return base
        if self._now() < self._end_time(plan.date, source.end):
            return base
        reason_hint = {
            "conversation is not idle enough": "当时你正在忙或正在聊天，没找到合适的插话时机",
            "agent task active": "当时你们正在处理一件复杂的事情，不适合突然打断",
            "cooldown active": "当时你们刚刚才聊过，紧接着再开口会显得太突兀",
            "availability probability rejected": "当时对方的状态不太适合被打扰",
            "sleeping": "当时对方正在休息",
        }.get(retry_reason, "当时时机不太合适")
        return (
            f"{base}。你原本打算在「{source.activity}」时段联系对方，但{reason_hint}，"
            "错过了那个时机；现在自然地向对方提起，别让对方察觉这是程序自动安排的。"
        )

    def _should_retry_window(self, umo: str, reason: str) -> bool:
        if reason in {"sleeping", "availability probability rejected"}:
            return True
        delivery = self.config.get("delivery_settings", {}) or {}
        if reason == "conversation is not idle enough":
            return bool(delivery.get("window_retry_when_not_idle", False))
        if reason == "agent task active":
            return bool(delivery.get("window_retry_when_not_idle", False))
        if reason == "cooldown active":
            return bool(delivery.get("window_retry_when_cooldown", False))
        return False

    def _window_retry_run_at(
        self, umo: str, plan: DailyPlan, reason: str
    ) -> datetime | None:
        now = self._now()
        if reason in {"sleeping", "availability probability rejected"}:
            next_time = next_available_at(plan, now)
            if not next_time:
                return None
            run_at = next_time + timedelta(minutes=random.randint(3, 15))
        elif reason == "agent task active":
            run_at = now + timedelta(minutes=30)
        elif reason == "conversation is not idle enough":
            state = self.storage.sessions.get(umo)
            delivery = self.config.get("delivery_settings", {}) or {}
            idle_required = max(
                0, int(delivery.get("minimum_idle_for_window_minutes", 20))
            )
            activity_times = []
            if state and state.last_user_message_at:
                activity_times.append(
                    parse_datetime(state.last_user_message_at, self.timezone)
                )
            if activity_at := self._conversation_activity_at.get(umo):
                activity_times.append(activity_at)
            if not activity_times:
                return None
            target = max(activity_times) + timedelta(minutes=idle_required)
            run_at = max(target, now) + timedelta(minutes=random.randint(1, 5))
        elif reason == "cooldown active":
            state = self.storage.sessions.get(umo)
            if not state or not state.last_proactive_at:
                return None
            settings = self.policy.settings_for(umo)
            cooldown = max(0, int(settings.get("cooldown_minutes", 0)))
            target = parse_datetime(state.last_proactive_at, self.timezone) + timedelta(
                minutes=cooldown
            )
            run_at = max(target, now) + timedelta(minutes=random.randint(1, 5))
        else:
            return None
        if run_at.date() > date.fromisoformat(plan.date):
            return None
        return run_at

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
            next_time = next_available_at(plan, self._now())
            if not next_time:
                return
            run_at = next_time + timedelta(minutes=random.randint(3, 15))
        self.runtime.add_date_job(
            f"pvd:{self._umo_hash(umo)}:plan:window-retry:{window.id}",
            run_at,
            self._run_delayed_window,
            umo,
            persona.id,
            plan.revision,
            window.id,
            run_at.isoformat(),
            retry_reason,
        )

    async def _run_sleep(self, umo: str, persona_id: str, revision: str) -> None:
        persona, plan = await self._ensure_plan_for_umo(umo)
        if persona.id != persona_id or plan.revision != revision:
            return
        await self._attempt_unsolicited(
            umo, persona, plan, "睡梦中醒来、起夜或失眠时忽然想起对方", "sleep"
        )

    async def _run_idle(self, umo: str) -> None:
        persona, plan = await self._ensure_plan_for_umo(umo)
        sent, reason = await self._attempt_unsolicited(
            umo, persona, plan, "会话已经沉默了一段时间，想自然地重新联系", "idle"
        )
        if sent:
            self._schedule_idle(umo)
            return
        if reason in {"sleeping", "availability probability rejected"}:
            next_time = next_available_at(plan, self._now())
            if next_time:
                self._schedule_idle(
                    umo, run_at=next_time + timedelta(minutes=random.randint(3, 15))
                )
        elif reason in {
            "cooldown active",
            "conversation is not idle enough",
            "agent task active",
        }:
            self._schedule_idle(umo, run_at=self._now() + timedelta(minutes=30))
