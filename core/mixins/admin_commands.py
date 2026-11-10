"""Bodies of the 日程 / 大时间表 / 主动消息 / 回复延迟 commands.

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

PRIVATE_ONLY = "日程只在私聊里用，群里不能{what}。"
DRAFT_HINT = "发 /大时间表 草稿 可以看"


class AdminCommandsMixin:
    # ------------------------------------------------------------------ 日程

    async def _cmd_show_schedule(self, event: AstrMessageEvent) -> list:
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return [event.plain_result(PRIVATE_ONLY.format(what="日程查看"))]
        persona, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if not plan.has_schedule:
            return [event.plain_result("今天还没有日程。")]
        now, day = self._now(), date.fromisoformat(plan.date)
        stage_day = self.long_term.expand_day(persona.id, day) or {
            "stage": None,
            "active_periods": [],
            "holidays": self.long_term.holidays.on(day),
        }
        return await self._image_view_results(
            event,
            f"{persona.id} 的 {plan.date}",
            format_timeline(plan, now, stage_day),
            [lambda: self.image_renderer.render_timeline(plan, now, stage_day)],
        )

    async def _cmd_show_outfit(self, event: AstrMessageEvent) -> list:
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return [event.plain_result(PRIVATE_ONLY.format(what="穿搭查看"))]
        persona, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if not plan.has_outfit:
            return [event.plain_result("今天还没有穿搭。")]
        now = self._now()
        return await self._image_view_results(
            event,
            f"{persona.id} 在 {plan.date} 的穿搭",
            format_outfit(plan),
            [lambda: self.image_renderer.render_outfit(plan, now)],
        )

    async def _cmd_rewrite_all(self, event: AstrMessageEvent, extra: str | None) -> str:
        if not any(self._daily_generation_flags()):
            return "自动排日程和自动搭穿搭都关着，没有可以重写的。"
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
            else "重排没成功，详情看日志。"
        )

    async def _cmd_rewrite_part(
        self, event: AstrMessageEvent, extra: str | None, *, part: str
    ) -> str:
        """``part`` is "schedule" or "outfit"; the other half of today's plan is kept."""
        label = "日程" if part == "schedule" else "穿搭"
        schedule_on, outfit_on = self._daily_generation_flags()
        if not (schedule_on if part == "schedule" else outfit_on):
            return f"自动生成{label}已关闭。"
        persona, current = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if current.status != "ok":
            what = "日程" if part == "schedule" else "穿搭"
            return f"今天还没有能单独重写的{what}，先用“日程 重写”整个排一遍。"
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
                "[模拟人生] %s重写失败 persona=%s: %s", label, persona.id, exc
            )
            return f"{label}没重写成功，原来的{label}保持不变；详情看日志。"
        try:
            await self._store_plan(persona, plan)
        except Exception as exc:
            logger.warning(
                "[模拟人生] %s重写后保存或调度失败 persona=%s: %s",
                label,
                persona.id,
                exc,
            )
            return f"新的{label}生成了，但保存或排程时出错，详情看日志。"
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
            f"起草失败：{failure}"
            if failure is not None
            else f"草稿写好了，{DRAFT_HINT}；没问题就发 /大时间表 批准。"
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
                "[模拟人生] 大时间表草稿生成失败 source=%s: %s",
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
            logger.warning("[模拟人生] 大时间表导入失败: %s", exc, exc_info=True)
            return f"导入失败：{exc}"
        return "已存成草稿；确认没问题就发 /大时间表 批准。"

    async def _cmd_long_term_draft(self, event: AstrMessageEvent) -> list:
        persona = await self.personas.resolve(event.unified_msg_origin)
        draft = self.long_term.get_draft(persona.id)
        if not draft:
            return [event.plain_result("现在没有待批准的草稿。")]
        stages = [self.long_term.with_holidays(stage) for stage in draft["stages"]]

        def card(stage):
            return lambda: self.image_renderer.render_stage(
                stage, persona.id, status="draft", draft_metadata=draft
            )

        return await self._image_view_results(
            event,
            f"{persona.id} 的长期安排草稿（待批准，{len(stages)} 个阶段）",
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
            logger.warning("[模拟人生] 大时间表批准失败: %s", exc, exc_info=True)
            return f"采用失败：{exc}"
        made = [
            name
            for name, present in (
                ("日程", plan.has_schedule),
                ("穿搭", plan.has_outfit),
            )
            if present
        ]
        outcome = (
            "，今天的" + "和".join(made) + "已按新安排重排"
            if made
            else "；自动排日程和穿搭都关着，今天没有重排"
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
            return "现在没有可以退回的草稿。"
        await self.long_term.reject_draft(persona.id)
        self.image_renderer.invalidate_persona(persona.id)
        if not feedback:
            return "草稿已退回并删掉。"
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
            f"草稿已退回，但按意见重写时出错：{failure}"
            if failure is not None
            else f"已按你的意见重写了草稿，{DRAFT_HINT}。"
        )

    async def _cmd_long_term_list(self, event: AstrMessageEvent) -> list:
        persona = await self.personas.resolve(event.unified_msg_origin)
        stages = self.long_term.list_for_persona(persona.id)
        if not stages:
            return [event.plain_result("她还没有确定的长期安排。")]
        text = "\n".join(
            f"{s['id']} | {s['name']} | {s['kind']} | {s['start_date']} 至 {s['end_date']} | 优先级 {s['priority']}"
            for s in stages
        )
        return await self._image_view_results(
            event,
            f"{persona.id} 的长期安排（{len(stages)} 个阶段）",
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
                lines = ["有好几个阶段都对得上，请写完整的 ID 或名称："] + [
                    f"- {c['id']} | {c['name']} | {c['start_date']} 至 {c['end_date']}"
                    for c in candidates
                ]
                return [event.plain_result("\n".join(lines))]
            if stage_id:
                return [
                    event.plain_result(
                        "没找到这个阶段，先用 /大时间表 列表 看看有哪些。"
                    )
                ]
            return [event.plain_result("她还没有确定的长期安排。")]
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
            requirements or "从今天开始把长期安排整个重新规划一遍",
            self._now().date(),
            self.long_term.latest_stage(persona.id),
            source="regenerate",
            mode="replace_all",
        )
        return (
            f"重新规划失败：{failure}"
            if failure is not None
            else f"新的整体规划已写成草稿，{DRAFT_HINT}；批准之后才会替换现有安排。"
        )

    # ------------------------------------------------------------------ 主动消息

    async def _cmd_proactive_status(self, event: AstrMessageEvent) -> str:
        umo = event.unified_msg_origin
        persona, plan = await self._ensure_plan_for_umo(umo)
        if not plan.has_schedule:
            return "今天没有日程，所以没有安排主动消息。"
        state = self.policy.ensure_state(umo, persona.id, plan, self._now())
        return f"人格：{persona.id}\n今日预算：{state.sent_count}/{state.daily_budget}\n连续未回复：{state.unanswered_count}"

    async def _cmd_proactive_now(self, event: AstrMessageEvent) -> str:
        umo = event.unified_msg_origin
        persona, plan = await self._ensure_plan_for_umo(umo)
        if not plan.has_schedule:
            return "今天没有日程，没法试发主动消息。"
        sent = await self._deliver(
            umo,
            persona,
            plan,
            "管理员要求立即测试主动消息",
            0,
            self._conversation_generation(umo),
        )
        return (
            "试发的主动消息已经发出。" if sent else "刚好有新消息进来，试发的那条取消了。"
        )

    async def _cmd_proactive_times(self, event: AstrMessageEvent) -> str:
        _, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        entries = self._scheduled_proactive_entries(event.unified_msg_origin, plan)
        if not entries:
            return "这个聊天里暂时没有排好的主动消息。"
        return "\n".join(
            ["接下来会在这些时间主动找你："]
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
        verb = "已开启" if added else "已重新开启"
        where = f"这个{'群' if session_kind(umo) == 'group' else '私聊'}里的主动消息"
        logger.info("[模拟人生] %s umo=%s", verb, umo)
        try:
            persona, plan = await self._ensure_plan_for_umo(umo)
            await self._schedule_session(umo, persona, plan)
            await self.storage.save_sessions()
        except Exception as exc:
            logger.warning("[模拟人生] 已订阅，但今天的安排没排上 umo=%s: %s", umo, exc)
            return f"{verb}{where}，不过今天的主动消息没排上，看看日志或稍后再试。"
        return f"{verb}{where}；之后她会按日程和发送规则主动找你。"

    # ------------------------------------------------------------------ 回复延迟

    async def _cmd_reply_delay(self, event: AstrMessageEvent, action: str) -> str:
        action = str(action).strip()
        umo = event.unified_msg_origin
        if action == "结算":
            batch = await self.reply_delay_coordinator.settle_now(umo)
            if batch is None:
                return "这里没有在等待中的消息。"
            logger.info(
                "[模拟人生] 手动放行等待中的消息 umo=%s 条数=%s",
                umo,
                len(batch.messages),
            )
            return f"已放行等待中的 {len(batch.messages)} 条消息，马上回复。"
        if action not in {"开启", "关闭"}:
            return "用法：/回复延迟 开启 | 关闭 | 结算"
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
            "[模拟人生] 晚点回复已%s 配置有变=%s 放行批次=%s",
            action,
            changed,
            settled,
        )
        suffix = f"，等待中的 {settled} 批消息已马上放行" if settled else ""
        return f"晚点回复{'已打开' if enabled else '已关闭'}{suffix}。"
