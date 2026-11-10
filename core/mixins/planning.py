"""Daily plans: the nightly refresh, generating a day, admin schedule requirements, travel commands."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from .. import life_memory
from ..models import DailyPlan, ScheduleRequirement
from ..persona import PersonaContext
from ..utils import parse_schedule_date_range, prune_date_keys

MAX_REQUIREMENT_CHARS = 500
MAX_REQUIREMENTS_PER_DAY = 10
MAX_REQUIREMENT_SPAN_DAYS = 366
MEMORY_CONTINUITY_NOTE = (
    "\n以上是真实发生过的事。新日程可以自然延续（比如接着读买来的书、"
    "再去路过的那家店、继续和主人约好的事），但不要照搬同样的安排。"
)


class PlanningMixin:
    async def _daily_refresh(self) -> None:
        await self._refresh_all(force=True)

    async def _refresh_all(self, *, force: bool) -> None:
        """Settle yesterday, write diaries, (re)plan today and reschedule every enabled session."""
        async with self.refresh_lock:
            now = self._now()
            today, yesterday = now.date(), now.date() - timedelta(days=1)
            self.storage.prune_schedule_requirements(today)
            await self._check_long_term_renewals(today)
            by_persona: dict[str, tuple[PersonaContext, list[str]]] = {}
            for umo in self.policy.enabled_sessions():
                persona = await self.personas.resolve(umo)
                by_persona.setdefault(persona.id, (persona, []))[1].append(umo)

            for persona, sessions in by_persona.values():
                await self._record_completed_personal_network_events(persona.id, now)
                await self._process_deliveries(persona, now)
                await self._ensure_world_event(persona, today)
                await self._record_garage_returns(persona, now)
                await self._settle_work_income(persona, yesterday)
                await self._settle_work_income(persona, today, before=now)
                await self._write_daily_diary(persona, yesterday)
                for write in (
                    self._write_weekly_diary,
                    self._write_monthly_diary,
                    self._write_yearly_diary,
                    self._record_anniversary,
                ):
                    await write(persona, now)
                plan = await self._ensure_plan(persona, today, force=force)
                for umo in sessions:
                    await self._schedule_session(umo, persona, plan)

            history_days = int(
                (self.config.get("schedule_settings", {}) or {}).get("history_days", 14)
            )
            self.storage.plans = prune_date_keys(
                self.storage.plans, history_days, today
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
        return persona, await self._ensure_plan(
            persona,
            self._now().date(),
            force=force,
            extra=extra,
            preserve_disabled=preserve_disabled,
        )

    async def _ensure_plan(
        self,
        persona: PersonaContext,
        target: date,
        *,
        force: bool = False,
        extra: str = "",
        preserve_disabled: bool = False,
    ) -> DailyPlan:
        """The stored plan for ``target``, generating (and saving) a new one when missing or forced.

        ``preserve_disabled`` keeps the parts whose daily generation is switched off.
        """
        day = target.isoformat()
        existing = self.storage.get_plan(day, persona.id)
        if existing and not force:
            return existing
        with_schedule, with_outfit = self._daily_generation_flags()
        history, long_term_context, requirements, relationships, newcomer = (
            [],
            "",
            [],
            "",
            "",
        )
        if with_schedule:
            lookback = max(
                0,
                int(
                    (self.config.get("schedule_settings", {}) or {}).get(
                        "reference_history_days", 3
                    )
                ),
            )
            history = self.storage.get_recent_plans(persona.id, target, lookback)
            if (self.config.get("long_term_settings", {}) or {}).get("enable", True):
                long_term_context = self.long_term.format_day_context(
                    persona.id, target, fallback_to_latest=True
                )
            requirements = self.storage.active_schedule_requirements(persona.id, target)
            relationships = await self._personal_network_context(persona.id)
            newcomer = await self._generate_new_character(persona)

        sections = []
        if extra.strip():
            sections.append("这次额外的要求：\n" + extra.strip())
        if requirements:
            sections.append(
                "之前预留的要求：\n"
                + "\n".join(f"- {item.requirement}" for item in requirements)
            )
        if newcomer:
            sections.append("今天会遇到的新朋友：\n" + newcomer)
        if with_schedule:
            memory = self._recent_life_memory(persona.id, target)
            if memory:
                sections.append(memory + MEMORY_CONTINUITY_NOTE)

        plan = await self.plan_generator.generate(
            target,
            persona,
            extra="\n\n".join(sections),
            history_plans=history,
            long_term_context=long_term_context,
            relationship_context=relationships,
            include_schedule=with_schedule,
            include_outfit=with_outfit,
            base_plan=existing if preserve_disabled else None,
        )
        key = self.storage.plan_key(day, persona.id)
        before = self.storage.plans.get(key)
        self.storage.plans[key] = plan
        if with_schedule and plan.has_schedule:
            self.storage.consume_schedule_requirements(
                [item.id for item in requirements], target
            )
        try:
            await self.storage.save_plans()
        except Exception:
            # Put memory back the way it was so a later retry sees the same state.
            if before is None:
                self.storage.plans.pop(key, None)
            else:
                self.storage.plans[key] = before
            for item in requirements:
                self.storage.schedule_requirements[item.id] = item
            raise
        return plan

    def _recent_life_memory(self, persona_id: str, target: date) -> str:
        try:
            self._sync_life_memory(persona_id, self._now(), days_back=3)
            return life_memory.recent_context(self.data_dir, persona_id, target)
        except Exception:
            logger.debug("[虚拟人生] 读取生活记忆失败", exc_info=True)
            return ""

    async def _add_schedule_requirement(
        self, event: AstrMessageEvent, date_range: str, requirement: str
    ) -> str:
        """Admin command: a wish for future days, used once when those days are first planned."""
        if not event.is_admin():
            return "只有管理员能预留日程要求。"
        today = self._now().date()
        requirement = str(requirement).strip()
        try:
            start, end = parse_schedule_date_range(date_range, today)
            persona = await self._requirement_target(
                event, start, end, today, requirement
            )
        except ValueError as exc:
            return f"没加上：{exc}。"

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
                "[虚拟人生] 日程要求保存失败 persona=%s: %s", persona.id, exc
            )
            return "要求没存上，看看日志再试一次。"
        span = (
            item.start_date
            if item.start_date == item.end_date
            else f"{item.start_date}..{item.end_date}"
        )
        return f"记下了，{persona.id} 在 {span} 排日程时会照顾这条要求。"

    async def _requirement_target(
        self,
        event: AstrMessageEvent,
        start: date,
        end: date,
        today: date,
        requirement: str,
    ) -> PersonaContext:
        """Validate a new requirement; returns the persona it is for or raises ``ValueError``."""
        span = (end - start).days + 1
        if start <= today:
            raise ValueError("只能给明天及以后的日子留要求")
        if span > MAX_REQUIREMENT_SPAN_DAYS:
            raise ValueError(f"一次最多覆盖 {MAX_REQUIREMENT_SPAN_DAYS} 天")
        if not requirement:
            raise ValueError("要求是空的")
        if len(requirement) > MAX_REQUIREMENT_CHARS:
            raise ValueError(f"要求太长了，{MAX_REQUIREMENT_CHARS} 字以内")
        persona = await self.personas.resolve(event.unified_msg_origin)
        for day in (start + timedelta(days=offset) for offset in range(span)):
            planned = self.storage.get_plan(day.isoformat(), persona.id)
            if planned and planned.has_schedule:
                raise ValueError(
                    f"{day.isoformat()} 的日程已经排好了，要求来不及用上"
                )
            if (
                len(self.storage.active_schedule_requirements(persona.id, day))
                >= MAX_REQUIREMENTS_PER_DAY
            ):
                raise ValueError(
                    f"{day.isoformat()} 已经攒了 {MAX_REQUIREMENTS_PER_DAY} 条要求，满了"
                )
        return persona

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
