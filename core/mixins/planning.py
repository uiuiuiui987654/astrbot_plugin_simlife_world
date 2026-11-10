"""Daily plan generation, schedule requirements and travel commands.

Mixin for ProactiveVirtualDailyPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from ..models import (
    DailyPlan,
    ScheduleRequirement,
)
from ..persona import PersonaContext
from ..utils import (
    parse_schedule_date_range,
    prune_date_keys,
)


class PlanningMixin:
    async def _daily_refresh(self) -> None:
        await self._refresh_all(force=True)

    async def _refresh_all(self, *, force: bool) -> None:
        async with self.refresh_lock:
            now = self._now()
            self.storage.prune_schedule_requirements(now.date())
            await self._check_long_term_renewals(now.date())
            grouped: dict[str, tuple[PersonaContext, list[str]]] = {}
            for umo in self.policy.enabled_sessions():
                persona = await self.personas.resolve(umo)
                grouped.setdefault(persona.id, (persona, []))[1].append(umo)

            for persona, sessions in grouped.values():
                await self._record_completed_personal_network_events(persona.id, now)
                await self._process_deliveries(persona, now)
                await self._ensure_world_event(persona, now.date())
                await self._record_garage_returns(persona, now)
                await self._settle_work_income(persona, now.date() - timedelta(days=1))
                await self._settle_work_income(persona, now.date(), before=now)
                await self._write_daily_diary(persona, now.date() - timedelta(days=1))
                await self._write_weekly_diary(persona, now)
                await self._write_monthly_diary(persona, now)
                await self._write_yearly_diary(persona, now)
                await self._record_anniversary(persona, now)
                plan = await self._ensure_plan(persona, now.date(), force=force)
                for umo in sessions:
                    await self._schedule_session(umo, persona, plan)

            keep_days = int(
                (self.config.get("schedule_settings", {}) or {}).get("history_days", 14)
            )
            self.storage.plans = prune_date_keys(
                self.storage.plans, keep_days, now.date()
            )
            await self.storage.save_plans()
            await self.storage.save_sessions()

    async def _ensure_plan_for_umo(
        self,
        umo: str,
        *,
        force: bool = False,
        extra: str = "",
        preserve_disabled: bool = False,
    ) -> tuple[PersonaContext, DailyPlan]:
        persona = await self.personas.resolve(umo)
        plan = await self._ensure_plan(
            persona,
            self._now().date(),
            force=force,
            extra=extra,
            preserve_disabled=preserve_disabled,
        )
        return persona, plan

    async def _ensure_plan(
        self,
        persona: PersonaContext,
        target: date,
        *,
        force: bool = False,
        extra: str = "",
        preserve_disabled: bool = False,
    ) -> DailyPlan:
        date_str = target.isoformat()
        existing = self.storage.get_plan(date_str, persona.id)
        if existing and not force:
            return existing
        settings = self.config.get("schedule_settings", {}) or {}
        include_schedule, include_outfit = self._daily_generation_flags()
        history_plans = []
        if include_schedule:
            reference_days = max(0, int(settings.get("reference_history_days", 3)))
            history_plans = self.storage.get_recent_plans(
                persona.id, target, reference_days
            )
        long_term_settings = self.config.get("long_term_settings", {}) or {}
        long_term_context = ""
        if include_schedule and long_term_settings.get("enable", True):
            long_term_context = self.long_term.format_day_context(
                persona.id,
                target,
                fallback_to_latest=True,
            )
        schedule_requirements = (
            self.storage.active_schedule_requirements(persona.id, target)
            if include_schedule
            else []
        )
        relationship_context = (
            await self._personal_network_context(persona.id) if include_schedule else ""
        )
        new_character_hint = (
            await self._generate_new_character(persona) if include_schedule else ""
        )
        requirement_sections = []
        if extra.strip():
            requirement_sections.append("本次补充要求：\n" + extra.strip())
        if schedule_requirements:
            requirement_sections.append(
                "预设日程要求：\n"
                + "\n".join(f"- {item.requirement}" for item in schedule_requirements)
            )
        if new_character_hint:
            requirement_sections.append("新人物出现要求：\n" + new_character_hint)
        plan = await self.plan_generator.generate(
            target,
            persona,
            extra="\n\n".join(requirement_sections),
            history_plans=history_plans,
            long_term_context=long_term_context,
            relationship_context=relationship_context,
            include_schedule=include_schedule,
            include_outfit=include_outfit,
            base_plan=existing if preserve_disabled else None,
        )
        plan_key = self.storage.plan_key(date_str, persona.id)
        previous_plan = self.storage.plans.get(plan_key)
        self.storage.plans[plan_key] = plan
        if include_schedule and plan.has_schedule:
            self.storage.consume_schedule_requirements(
                [item.id for item in schedule_requirements], target
            )
        try:
            await self.storage.save_plans()
        except Exception:
            if previous_plan is None:
                self.storage.plans.pop(plan_key, None)
            else:
                self.storage.plans[plan_key] = previous_plan
            for item in schedule_requirements:
                self.storage.schedule_requirements[item.id] = item
            raise
        return plan

    async def _add_schedule_requirement(
        self,
        event: AstrMessageEvent,
        date_range: str,
        requirement: str,
    ) -> str:
        if not event.is_admin():
            return "无权限：仅管理员可以添加日程要求。"
        today = self._now().date()
        requirement = str(requirement).strip()
        try:
            start, end = parse_schedule_date_range(date_range, today)
            if start <= today:
                raise ValueError("只能为今天之后的日期添加日程要求")
            range_days = (end - start).days + 1
            if range_days > 366:
                raise ValueError("日期区间不能超过 366 天")
            if not requirement:
                raise ValueError("日程要求不能为空")
            if len(requirement) > 500:
                raise ValueError("每条日程要求不能超过 500 字")
            persona = await self.personas.resolve(event.unified_msg_origin)
            for offset in range(range_days):
                target = start + timedelta(days=offset)
                existing_plan = self.storage.get_plan(target.isoformat(), persona.id)
                if existing_plan and existing_plan.has_schedule:
                    raise ValueError(
                        f"{target.isoformat()} 已有有效日程，无法添加首次生成要求"
                    )
                if (
                    len(self.storage.active_schedule_requirements(persona.id, target))
                    >= 10
                ):
                    raise ValueError(
                        f"{target.isoformat()} 已有 10 条日程要求，无法继续添加"
                    )
        except ValueError as exc:
            return f"无法添加日程要求：{exc}。"

        item = ScheduleRequirement(
            id=uuid.uuid4().hex[:12],
            persona_id=persona.id,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            requirement=requirement,
            created_at=self._now().isoformat(),
        )
        self.storage.schedule_requirements[item.id] = item
        try:
            await self.storage.save_plans()
        except Exception as exc:
            self.storage.schedule_requirements.pop(item.id, None)
            logger.warning(
                "[Virtual Life] Schedule requirement persistence failed persona=%s: %s",
                persona.id,
                exc,
            )
            return "日程要求保存失败，请检查日志后重试。"
        normalized_range = (
            item.start_date
            if item.start_date == item.end_date
            else f"{item.start_date}..{item.end_date}"
        )
        return f"已为人格 {persona.id} 添加日程要求：{normalized_range}。"

    def _parse_travel_plan_args(
        self, text: str, today: date
    ) -> tuple[str, date | None, int | None]:
        """Split "<destination> [YYYY-MM-DD|MM-DD] [days]" into its parts."""
        tokens = [token for token in str(text or "").split() if token]
        depart: date | None = None
        days: int | None = None
        name_parts: list[str] = []
        for token in tokens:
            parts = token.split("-")
            if (
                depart is None
                and len(parts) in (2, 3)
                and all(part.isdigit() for part in parts)
            ):
                try:
                    depart = parse_schedule_date_range(token, today)[0]
                    continue
                except ValueError:
                    pass
            if days is None and token.isdigit() and 1 <= int(token) <= 30:
                days = int(token)
                continue
            name_parts.append(token)
        name = "".join(name_parts).strip()
        if not name:
            raise ValueError(
                "格式：/虚拟日程 旅行 规划 <目的地> [出发日期] [天数]，"
                "例如「/虚拟日程 旅行 规划 京都 2026-11-20 5」。"
            )
        return name, depart, days

    async def _handle_travel_command(
        self, event: AstrMessageEvent, action: str, argument: str
    ) -> str:
        persona = await self.personas.resolve(event.unified_msg_origin)
        today = self._now().date()
        settings = self.config.get("travel_settings", {}) or {}
        action = str(action or "").strip()
        argument = str(argument or "").strip()
        if action in {"目的地", "列表", "清单"}:
            return self.travel.destination_list_text()
        if action in {"规划", "安排", "计划"}:
            if not event.is_admin():
                return "无权限：只有管理员可以规划旅行。"
            try:
                name, depart, days = self._parse_travel_plan_args(argument, today)
            except ValueError as exc:
                return str(exc)
            trip, error = self.travel.plan(
                persona.id,
                name,
                depart=depart,
                days=days,
                persona_prompt=persona.prompt,
                today=today,
                settings=settings,
            )
            if trip is None:
                return error
            return (
                f"已为人格 {persona.id} 安排旅行：\n"
                + self.travel.describe(trip, today)
                + "\n\n之后生成日程时会按这趟行程写；想改时间就先取消再重新规划。"
            )
        if action in {"取消", "删除"}:
            if not event.is_admin():
                return "无权限：只有管理员可以取消旅行。"
            trip = self.travel.cancel(persona.id, today)
            if trip is None:
                return "现在没有可以取消的旅行。"
            return f"已取消：{trip.city}（{trip.depart} → {trip.back}）。"
        trip = self.travel.current(persona.id, today) or self.travel.upcoming(
            persona.id, today
        )
        if trip is None:
            return (
                "现在没有安排旅行。\n"
                + self.travel.destination_list_text()
                + "\n\n用法：/虚拟日程 旅行 规划 <目的地> [出发日期] [天数]"
            )
        return self.travel.describe(trip, today)
