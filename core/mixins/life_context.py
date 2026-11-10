"""Life-state context for LLM requests and chat recall.

Mixin for ProactiveVirtualDailyPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.agent.message import TextPart
from astrbot.core.provider.entities import ProviderRequest

from .. import (
    camera_photo,
    furniture_state,
    health_journal,
    item_effects,
    life_state,
    mood_history,
)
from ..context_injection import build_state_snapshot
from ..proactive import session_kind


class LifeContextMixin:
    def _furniture_activity_context(self, now) -> tuple[dict, str]:
        """Read live furniture state for normal chat and proactive context."""
        try:
            plans_path = self.data_dir / "plans.json"
            states = furniture_state.live_states(plans_path, now=now)
            context = furniture_state.furniture_context(plans_path, "", now=now)
        except (OSError, ValueError, TypeError):
            return {}, ""
        return states, context

    def _life_needs(self, plan, now, *, update_journal: bool = True) -> dict:
        """Current physiological snapshot including recent furniture effects."""
        furniture_states, _context = self._furniture_activity_context(now)
        try:
            journal_state = health_journal.persona_state(
                self.data_dir,
                str(getattr(plan, "persona_id", "") or "角色"),
                today=now.date(),
            )
            needs = life_state.compute(
                plan,
                now,
                furniture_states=furniture_states,
                history_plans=self._life_history_plans(plan),
                weak_constitution=bool(journal_state.get("weak_constitution")),
                recent_illness_days=int(journal_state.get("recent_illness_days") or 0),
            )
            if not update_journal:
                status = str(journal_state.get("status") or "healthy")
                needs["health_status"] = status
                needs["sick"] = status == "sick" or bool(needs.get("sick"))
                needs["recovering"] = status == "recovering" or bool(
                    needs.get("recovering")
                )
                if status == "sick":
                    needs["illness_label"] = "正在生病"
                elif status == "recovering":
                    needs["illness_label"] = "病后恢复中"
                return needs
            needs = health_journal.update(
                self.data_dir,
                str(getattr(plan, "persona_id", "") or "角色"),
                needs,
                now,
            )
            adjusted = item_effects.apply(
                self.data_dir,
                str(getattr(plan, "persona_id", "") or "角色"),
                needs,
                now,
            )
            try:
                mood_history.record(
                    self.data_dir,
                    str(getattr(plan, "persona_id", "") or "角色"),
                    adjusted,
                    now=now,
                )
            except Exception:
                pass
            return adjusted
        except (OSError, TypeError, ValueError):
            return {}

    def _life_history_plans(self, plan) -> list:
        """Recent plans used for sleep-debt continuity."""
        try:
            return sorted(
                (
                    value
                    for value in self.storage.plans.values()
                    if getattr(value, "persona_id", "")
                    == getattr(plan, "persona_id", "")
                    and getattr(value, "date", "") < getattr(plan, "date", "")
                ),
                key=lambda value: value.date,
            )[-3:]
        except (AttributeError, TypeError, ValueError):
            return []

    def _chat_recall_settings(self) -> dict:
        return self.config.get("chat_recall_settings", {}) or {}

    async def _inject_recent_chat(
        self, event: AstrMessageEvent, req: ProviderRequest
    ) -> None:
        """普通聊天回复前，把最近一段时间的对话塞回上下文。

        AstrBot 自己会带历史，但长对话里早期消息会被截断；这里补一段
        时间窗内的短回顾，避免「聊到一半像失忆」。
        """
        if session_kind(event.unified_msg_origin) == "group":
            return
        settings = self._chat_recall_settings()
        if not bool(settings.get("enable", True)):
            return
        try:
            minutes = int(settings.get("minutes", 60))
            messages = int(settings.get("messages", 6))
            chars = int(settings.get("chars", 400))
        except (TypeError, ValueError):
            return
        if minutes <= 0 or messages <= 0:
            return
        recap = await self._recent_chat_lines(
            event.unified_msg_origin, minutes, messages, chars
        )
        interaction_recap = self._recent_interaction_lines(3)
        if session_kind(event.unified_msg_origin) == "group":
            recap = self._filter_group_recap(recap)
        if not recap and not interaction_recap:
            return
        hint = "接着上面的话题说，不要重复已经说过的话，也不要主动提更早的事；"
        if interaction_recap:
            hint += (
                "刚才互动里说过的菜、动作和事都还是同一段对话；"
                "主人现在说“给你加个菜/给你煮了吃的”，指的就是刚才那道菜，"
                "先认出并回应那道菜，不要当成新话题或装作没发生；"
            )
        if "主动发起" in recap:
            hint += (
                "标着「你（主动发起）」的是你自己主动找对方说的话，"
                "对方现在多半就是在接那条：先接住它的内容（认下、反驳、追问都行），"
                "别当没说过，也别重新介绍一遍自己的处境；"
            )
        hint += (
            "如果上面已经说过自己在做什么，就别再复述同一个动作或细节，"
            "换个角度说或者聊对方的事。"
        )
        text = f"【你们最近聊的（大约 {minutes} 分钟内）】\n{recap}\n{hint}"
        if interaction_recap:
            text += f"\n\n【刚才的互动】\n{interaction_recap}"
        req.extra_user_content_parts.append(TextPart(text=text).mark_as_temp())
        logger.info(
            "[虚拟人生] 对话回顾注入 umo=%s 行数=%s 字数=%s 互动=%s",
            event.unified_msg_origin,
            recap.count("\n") + 1,
            len(text),
            bool(interaction_recap),
        )

    def _recent_interaction_lines(self, limit: int = 3) -> str:
        """把最近几次观察窗互动带给普通聊天，接住刚才的菜/动作。"""
        try:
            items = self.interactions.recent(limit)
            now = self._now()
        except Exception:
            return ""
        cutoff = now - timedelta(minutes=45)
        lines = []
        for item in items:
            if not isinstance(item, dict):
                continue
            speech = str(item.get("speech") or "").strip()
            if not speech:
                continue
            at = str(item.get("at") or "").strip()
            try:
                at_time = datetime.fromisoformat(at)
            except (TypeError, ValueError):
                at_time = None
            if at_time is not None:
                if at_time.tzinfo is None and now.tzinfo is not None:
                    at_time = at_time.replace(tzinfo=now.tzinfo)
                if at_time < cutoff:
                    continue
            clock = at[11:16] if len(at) >= 16 else at
            item_name = str(item.get("item_name") or "").strip()
            action = str(item.get("action") or "").strip()
            where = "·".join(part for part in (item_name, action) if part)
            prefix = f"{clock} " if clock else ""
            lines.append(f"{prefix}{where + '，' if where else ''}你回：{speech}")
        return "\n".join(lines)

    async def _recent_chat_lines(
        self, umo: str, minutes: int, messages: int, chars: int
    ) -> str:
        if not umo:
            return ""
        try:
            manager = self.context.conversation_manager
            conversation_id = await manager.get_curr_conversation_id(umo)
            if not conversation_id:
                return ""
            conversation = await manager.get_conversation(umo, conversation_id)
            raw = getattr(conversation, "history", "[]")
            history = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(history, list):
                return ""
            return self.interactions.format_history(
                history,
                now=self._now(),
                settings={
                    "history_minutes": minutes,
                    "history_messages": messages,
                    "history_chars": chars,
                },
            )
        except Exception as exc:
            logger.debug("[虚拟人生] 读取对话回顾失败 umo=%s: %s", umo, exc)
            return ""

    async def get_virtual_life_snapshot(self, umo: str) -> dict[str, Any]:
        """供其他插件读取当前虚拟生活状态（只读，不触发日程生成）。

        This is a stable, read-only interface for other plugins (for example the
        image plugin that renders chat selfies). It only reads the in-memory
        plan cache: it never calls ``_ensure_plan_for_umo`` and therefore never
        triggers an LLM schedule generation or a plan file write.

        Args:
            umo: Unified message origin of the conversation to inspect.

        Returns:
            A JSON-serializable snapshot. ``ok`` is False with a ``reason`` when
            the persona cannot be resolved or today's plan is missing/failed.
        """
        now = self._now()
        time_text = now.strftime("%Y-%m-%d %H:%M")
        date_text = now.date().isoformat()
        try:
            persona = await self.personas.resolve(umo)
        except Exception as exc:
            logger.warning("[虚拟人生] 状态快照人格解析失败 umo=%s: %s", umo, exc)
            return {
                "ok": False,
                "reason": "persona_unavailable",
                "persona_id": "",
                "persona_name": "",
                "date": date_text,
                "time": time_text,
            }
        persona_name = str(getattr(persona, "name", "") or persona.id)
        plan = self.storage.get_plan(date_text, persona.id)
        if plan is None or plan.status != "ok":
            return {
                "ok": False,
                "reason": "no_plan",
                "persona_id": persona.id,
                "persona_name": persona_name,
                "date": date_text,
                "time": time_text,
                "timeline_count": len(plan.timeline) if plan is not None else 0,
            }
        snapshot = build_state_snapshot(plan, now)
        try:
            pose_hint = camera_photo.pose_hint_for_snapshot(snapshot)
            if pose_hint:
                snapshot["pose_hint"] = pose_hint
        except Exception:
            pass
        snapshot.update(
            {
                "ok": True,
                "persona_id": persona.id,
                "persona_name": persona_name,
                "time": time_text,
            }
        )
        return snapshot
