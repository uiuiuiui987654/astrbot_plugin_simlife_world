"""Bodies of the 虚拟日程 / 大时间表 / 主动消息 / 回复延迟 commands.

The decorated handlers in ``main.py`` stay thin: each awaits one of these and
yields the returned results, so the command surface lives in one place and
the behaviour here.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from ..models import DailyPlan
from ..proactive import session_kind
from ..utils import format_outfit, format_plan, format_timeline

PRIVATE_ONLY = "虚拟日程系统仅在私聊生效，群聊中不提供{what}。"
DRAFT_HINT = "使用 /大时间表 草稿 查看"


class AdminCommandsMixin:
    # ------------------------------------------------------------------ 虚拟日程

    async def _cmd_show_schedule(self, event: AstrMessageEvent) -> list:
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return [event.plain_result(PRIVATE_ONLY.format(what="日程查看"))]
        persona, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if not plan.has_schedule:
            return [event.plain_result("今日没有日程。")]
        now, day = self._now(), date.fromisoformat(plan.date)
        stage_day = self.long_term.expand_day(persona.id, day) or {
            "stage": None,
            "active_periods": [],
            "holidays": self.long_term.holidays.on(day),
        }
        return await self._image_view_results(
            event,
            f"{persona.id} · {plan.date} 虚拟日程",
            format_timeline(plan, now, stage_day),
            [lambda: self.image_renderer.render_timeline(plan, now, stage_day)],
        )

    async def _cmd_show_outfit(self, event: AstrMessageEvent) -> list:
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return [event.plain_result(PRIVATE_ONLY.format(what="穿搭查看"))]
        persona, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if not plan.has_outfit:
            return [event.plain_result("今日没有穿搭。")]
        now = self._now()
        return await self._image_view_results(
            event,
            f"{persona.id} · {plan.date} 今日穿搭",
            format_outfit(plan),
            [lambda: self.image_renderer.render_outfit(plan, now)],
        )

    async def _cmd_rewrite_all(self, event: AstrMessageEvent, extra: str | None) -> str:
        if not any(self._daily_generation_flags()):
            return "日程生成和穿搭生成均已关闭。"
        persona, plan = await self._ensure_plan_for_umo(
            event.unified_msg_origin,
            force=True,
            extra=extra or "",
            preserve_disabled=True,
        )
        await self._reschedule_plan_sessions(persona, plan)
        return (
            format_plan(plan, self._now())
            if plan.status == "ok"
            else "重写失败，请检查 LLM 输出。"
        )

    async def _cmd_rewrite_part(
        self, event: AstrMessageEvent, extra: str | None, *, part: str
    ) -> str:
        """``part`` is "schedule" or "outfit"; the other half of today's plan is kept."""
        label = "日程" if part == "schedule" else "穿搭"
        schedule_on, outfit_on = self._daily_generation_flags()
        if not (schedule_on if part == "schedule" else outfit_on):
            return f"{label}生成功能已关闭。"
        persona, current = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if current.status != "ok":
            what = "日程" if part == "schedule" else "穿搭"
            return f"今日没有可局部重写的有效{what}，请先使用“虚拟日程 重写”。"
        try:
            if part == "schedule":
                plan = await self.plan_generator.rewrite_schedule(
                    current,
                    persona,
                    extra=extra or "",
                    long_term_context=self._day_long_term_context(
                        persona.id, date.fromisoformat(current.date)
                    ),
                    relationship_context=await self._personal_network_context(
                        persona.id
                    ),
                )
            else:
                plan = await self.plan_generator.rewrite_outfit(
                    current, persona, extra=extra or ""
                )
        except Exception as exc:
            logger.warning(
                "[虚拟人生] %s重写失败 persona=%s: %s", label, persona.id, exc
            )
            return f"{label}重写失败，已保留原{label}，请检查 LLM 输出或日志。"
        try:
            await self._store_plan(persona, plan)
        except Exception as exc:
            logger.warning(
                "[虚拟人生] %s重写后保存或调度失败 persona=%s: %s",
                label,
                persona.id,
                exc,
            )
            return f"{label}已生成，但保存或调度失败，请检查日志。"
        return (
            format_plan(plan, self._now())
            if part == "schedule"
            else format_outfit(plan)
        )

    def _day_long_term_context(self, persona_id: str, day: date) -> str:
        if not (self.config.get("long_term_settings", {}) or {}).get("enable", True):
            return ""
        return self.long_term.format_day_context(
            persona_id, day, fallback_to_latest=True
        )

    async def _store_plan(self, persona, plan: DailyPlan) -> None:
        self.storage.plans[self.storage.plan_key(plan.date, persona.id)] = plan
        await self.storage.save_plans()
        await self._reschedule_plan_sessions(persona, plan)

    # ------------------------------------------------------------------ 大时间表

    async def _cmd_long_term_generate(
        self, event: AstrMessageEvent, requirements: str | None
    ) -> str:
        persona = await self.personas.resolve(event.unified_msg_origin)
        latest = self.long_term.latest_stage(persona.id)
        start = (
            date.fromisoformat(latest["end_date"]) + timedelta(days=1)
            if latest
            else self._now().date()
        )
        failure = await self._draft_or_error(
            event,
            persona,
            requirements or "",
            start,
            latest,
            source="natural",
            mode="append",
        )
        return (
            f"生成草稿失败：{failure}"
            if failure is not None
            else f"已生成大时间表草稿，{DRAFT_HINT}，确认后执行 /大时间表 批准。"
        )

    async def _draft_or_error(
        self, event, persona, requirements, start, previous, *, source, mode
    ) -> str | None:
        """Create a draft; the error text on failure, ``None`` on success."""
        try:
            await self._create_long_term_draft(
                persona=persona,
                admin_umo=event.unified_msg_origin,
                requirements=requirements,
                start_date=start,
                previous_stage=previous,
                source=source,
                mode=mode,
            )
        except Exception as exc:
            logger.warning(
                "[虚拟人生] 大时间表草稿生成失败 source=%s: %s",
                source,
                exc,
                exc_info=True,
            )
            return str(exc)
        return None

    async def _cmd_long_term_import(self, event: AstrMessageEvent, content: str) -> str:
        persona = await self.personas.resolve(event.unified_msg_origin)
        try:
            await self.long_term.set_draft(
                persona.id,
                self._parse_long_term_json(content, persona.id),
                source="json",
                admin_umo=event.unified_msg_origin,
                created_at=self._now().isoformat(),
                requirements="结构化数据导入",
                mode="replace_all",
            )
            self.image_renderer.invalidate_persona(persona.id)
        except Exception as exc:
            logger.warning("[虚拟人生] 大时间表导入失败: %s", exc, exc_info=True)
            return f"导入草稿失败：{exc}"
        return "结构化数据已保存为草稿，确认后执行 /大时间表 批准。"

    async def _cmd_long_term_draft(self, event: AstrMessageEvent) -> list:
        persona = await self.personas.resolve(event.unified_msg_origin)
        draft = self.long_term.get_draft(persona.id)
        if not draft:
            return [event.plain_result("当前人格没有待批准草稿。")]
        stages = [self.long_term.with_holidays(stage) for stage in draft["stages"]]

        def card(stage):
            return lambda: self.image_renderer.render_stage(
                stage, persona.id, status="draft", draft_metadata=draft
            )

        return await self._image_view_results(
            event,
            f"{persona.id} · 大时间表草稿 · 待批准 · 共 {len(stages)} 个阶段",
            json.dumps({**draft, "stages": stages}, ensure_ascii=False, indent=2),
            [card(stage) for stage in stages],
        )

    async def _cmd_long_term_approve(self, event: AstrMessageEvent) -> str:
        persona = await self.personas.resolve(event.unified_msg_origin)
        try:
            approved = await self.long_term.approve_draft(
                persona.id, event.unified_msg_origin
            )
            self.image_renderer.invalidate_persona(persona.id)
            plan = await self._refresh_persona_daily_plan(persona)
        except Exception as exc:
            logger.warning("[虚拟人生] 大时间表批准失败: %s", exc, exc_info=True)
            return f"批准失败：{exc}"
        made = [
            name
            for name, present in (
                ("日程", plan.has_schedule),
                ("穿搭", plan.has_outfit),
            )
            if present
        ]
        outcome = (
            "，已按开关重生成今日" + "和".join(made)
            if made
            else "；日程和穿搭生成均已关闭，未生成今日内容"
        )
        return f"大时间表已生效{outcome}：" + "、".join(
            stage["name"] for stage in approved
        )

    async def _cmd_long_term_reject(
        self, event: AstrMessageEvent, feedback: str | None
    ) -> str:
        persona = await self.personas.resolve(event.unified_msg_origin)
        draft = self.long_term.get_draft(persona.id)
        if not draft:
            return "当前人格没有待拒绝草稿。"
        await self.long_term.reject_draft(persona.id)
        self.image_renderer.invalidate_persona(persona.id)
        if not feedback:
            return "草稿已拒绝并删除。"
        mode = str(draft.get("mode", "append"))
        failure = await self._draft_or_error(
            event,
            persona,
            "；".join(
                part
                for part in (draft.get("requirements", ""), f"修改意见：{feedback}")
                if part
            ),
            date.fromisoformat(draft["stages"][0]["start_date"]),
            self.long_term.latest_stage(persona.id)
            if draft.get("mode") == "append"
            else None,
            source="revision",
            mode=mode,
        )
        return (
            f"草稿已拒绝，但重新生成失败：{failure}"
            if failure is not None
            else f"已按修改意见重新生成草稿，{DRAFT_HINT}。"
        )

    async def _cmd_long_term_list(self, event: AstrMessageEvent) -> list:
        persona = await self.personas.resolve(event.unified_msg_origin)
        stages = self.long_term.list_for_persona(persona.id)
        if not stages:
            return [event.plain_result("当前人格没有已批准的大时间表。")]
        text = "\n".join(
            f"{s['id']} | {s['name']} | {s['kind']} | {s['start_date']} 至 {s['end_date']} | 优先级 {s['priority']}"
            for s in stages
        )
        return await self._image_view_results(
            event,
            f"{persona.id} · 已批准阶段，共 {len(stages)} 个",
            text,
            [lambda: self.image_renderer.render_stage_list(stages, persona.id)],
        )

    async def _cmd_long_term_view(
        self, event: AstrMessageEvent, stage_id: str | None
    ) -> list:
        persona = await self.personas.resolve(event.unified_msg_origin)
        stage, candidates = self.long_term.resolve_stage(
            persona.id, self._now().date(), stage_id or ""
        )
        if not stage:
            if candidates:
                lines = ["找到多个匹配阶段，请使用完整 ID 或名称："] + [
                    f"- {c['id']} | {c['name']} | {c['start_date']} 至 {c['end_date']}"
                    for c in candidates
                ]
                return [event.plain_result("\n".join(lines))]
            if stage_id:
                return [
                    event.plain_result(
                        "未找到匹配阶段，请先使用 /大时间表 列表 查看可用 ID。"
                    )
                ]
            return [event.plain_result("当前人格没有已批准的大时间表。")]
        stage = self.long_term.with_holidays(stage)
        return await self._image_view_results(
            event,
            f"{persona.id} · {stage['name']}",
            json.dumps(stage, ensure_ascii=False, indent=2),
            [lambda: self.image_renderer.render_stage(stage, persona.id)],
        )

    async def _cmd_long_term_regenerate(
        self, event: AstrMessageEvent, requirements: str | None
    ) -> str:
        persona = await self.personas.resolve(event.unified_msg_origin)
        failure = await self._draft_or_error(
            event,
            persona,
            requirements or "重新规划完整大时间表",
            self._now().date(),
            self.long_term.latest_stage(persona.id),
            source="regenerate",
            mode="replace_all",
        )
        return (
            f"重生成草稿失败：{failure}"
            if failure is not None
            else f"已生成替换全部阶段的草稿，{DRAFT_HINT}，批准后才会生效。"
        )

    # ------------------------------------------------------------------ 主动消息

    async def _cmd_proactive_status(self, event: AstrMessageEvent) -> str:
        umo = event.unified_msg_origin
        persona, plan = await self._ensure_plan_for_umo(umo)
        if not plan.has_schedule:
            return "今日没有日程，主动消息未安排。"
        state = self.policy.ensure_state(umo, persona.id, plan, self._now())
        return f"人格：{persona.id}\n今日预算：{state.sent_count}/{state.daily_budget}\n连续未回复：{state.unanswered_count}"

    async def _cmd_proactive_now(self, event: AstrMessageEvent) -> str:
        umo = event.unified_msg_origin
        persona, plan = await self._ensure_plan_for_umo(umo)
        if not plan.has_schedule:
            return "今日没有日程，无法发送测试主动消息。"
        sent = await self._deliver(
            umo,
            persona,
            plan,
            "管理员要求立即测试主动消息",
            0,
            self._conversation_generation(umo),
        )
        return (
            "测试主动消息已发送。" if sent else "会话状态已变化，测试主动消息未发送。"
        )

    async def _cmd_proactive_times(self, event: AstrMessageEvent) -> str:
        _, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        entries = self._scheduled_proactive_entries(event.unified_msg_origin, plan)
        if not entries:
            return "当前会话没有已安排的主动消息。"
        return "\n".join(
            ["主动消息具体执行时间："]
            + [
                f"- {at.astimezone(self.timezone).strftime('%Y-%m-%d %H:%M:%S %z')}｜{label}"
                for at, label in entries
            ]
        )

    async def _cmd_subscribe(self, event: AstrMessageEvent) -> str:
        """Turn on proactive messages for this chat and schedule today right away."""
        umo = event.unified_msg_origin
        added = self.policy.subscribe(umo)
        self.config.save_config()
        verb = "已订阅" if added else "已刷新订阅"
        where = f"当前{'群聊' if session_kind(umo) == 'group' else '私聊'}会话"
        logger.info("[虚拟人生] %s主动消息会话 umo=%s", verb, umo)
        try:
            persona, plan = await self._ensure_plan_for_umo(umo)
            await self._schedule_session(umo, persona, plan)
            await self.storage.save_sessions()
        except Exception as exc:
            logger.warning("[虚拟人生] 订阅后即时调度失败 umo=%s: %s", umo, exc)
            return f"{verb}{where}，但今日日程调度失败，请检查日志或稍后重试。"
        return f"{verb}{where}，主动消息将在符合日程与发送规则时触发。"

    # ------------------------------------------------------------------ 回复延迟

    async def _cmd_reply_delay(self, event: AstrMessageEvent, action: str) -> str:
        action = str(action).strip()
        umo = event.unified_msg_origin
        if action == "结算":
            batch = await self.reply_delay_coordinator.settle_now(umo)
            if batch is None:
                return "当前会话没有等待结算的回复批次。"
            logger.info(
                "[虚拟人生] 管理员立即结算回复延迟批次 会话=%s 消息数=%s",
                umo,
                len(batch.messages),
            )
            return f"已立即结算当前会话的回复批次，共 {len(batch.messages)} 条消息。"
        if action not in {"开启", "关闭"}:
            return "用法：/回复延迟 开启|关闭|结算"
        enabled = action == "开启"
        settings = self.config.get("reply_delay_settings", {}) or {}
        changed = bool(settings.get("enable")) != enabled
        settings["enable"] = enabled
        self.config["reply_delay_settings"] = settings
        self.reply_delay_policy.settings = settings
        if changed:
            self.config.save_config()
        # Turning delays off answers everything that is still waiting.
        settled = (
            0 if enabled else len(await self.reply_delay_coordinator.settle_all_now())
        )
        logger.info(
            "[虚拟人生] 管理员%s回复延迟 配置变更=%s 结算批次=%s",
            action,
            changed,
            settled,
        )
        suffix = f"，并立即结算 {settled} 个等待批次" if settled else ""
        return f"回复延迟{'已开启' if enabled else '已关闭'}{suffix}。"
