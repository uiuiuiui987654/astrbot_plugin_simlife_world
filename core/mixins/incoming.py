"""Incoming message routing and hand-over (gift) requests.

Mixin for ProactiveVirtualDailyPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

import re
from datetime import datetime

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.star.filter.command import CommandFilter
from astrbot.core.star.filter.command_group import CommandGroupFilter
from astrbot.core.star.filter.regex import RegexFilter

from .. import (
    money,
    view_state,
)
from ..proactive import session_kind
from .common import (
    GIVE_INTENT_PATTERNS,
    _requested_gift_label,
)


class IncomingMixin:
    def _is_conversation_event(self, event: AstrMessageEvent) -> bool:
        if event.get_extra("handlers_parsed_params", None):
            return False
        handlers = event.get_extra("activated_handlers", None) or []
        for handler in handlers:
            for event_filter in getattr(handler, "event_filters", None) or []:
                if isinstance(
                    event_filter, (CommandFilter, CommandGroupFilter, RegexFilter)
                ):
                    return False
        return True

    def _schedule_private_only(self) -> bool:
        settings = self.config.get("schedule_settings", {}) or {}
        return bool(settings.get("private_only", True))

    def _schedule_available_for_umo(self, umo: str) -> bool:
        """日程、日程注入、回复延迟和主动消息只对私聊会话生效。"""
        if not umo:
            return False
        return not self._schedule_private_only() or session_kind(umo) == "friend"

    @staticmethod
    def _give_action_label(text: str) -> str | None:
        raw = str(text or "").strip()
        if not raw:
            return None
        for pattern in GIVE_INTENT_PATTERNS:
            match = pattern.search(raw)
            if not match:
                continue
            item = str(match.group("item") or "").strip().lstrip("了着过点个些")
            item = re.sub(r"^(?:盒|杯|瓶|袋|份|碗|盘|罐|串|块|颗)(?=.)", "", item)
            item = item.rstrip("吧啊呀哦嘛呢啦呗")
            if not item or item in ("东西", "礼物"):
                return "把东西递给月月"
            return f"把{item}递给月月"
        return None

    def _known_gift_item_names(self, persona_id: str | None = None) -> list[str]:
        """收集家具名和持有物名，用于识别月月请求里要递的东西。"""
        names: set[str] = set()
        try:
            items, _ = view_state.load_home_items(self.data_dir / "plans.json")
            names.update(
                str(item.get("name") or "").strip()
                for item in items
                if str(item.get("name") or "").strip()
            )
        except Exception:
            logger.debug("[虚拟人生] _known_gift_item_names 出错，已忽略", exc_info=True)
        if persona_id:
            try:
                snapshot = money.snapshot(self.data_dir, persona_id)
                names.update(
                    str(item.get("name") or "").strip()
                    for item in snapshot.get("possessions") or []
                    if str(item.get("name") or "").strip()
                )
            except Exception:
                logger.debug("[虚拟人生] _known_gift_item_names 出错，已忽略", exc_info=True)
        return sorted(names, key=len, reverse=True)

    def _maybe_queue_give_request(
        self,
        text: str,
        persona_id: str,
        now: datetime,
    ) -> dict | None:
        """月月主动请主人递东西时，给观察窗补一个待处理按钮。"""
        label = _requested_gift_label(text, self._known_gift_item_names(persona_id))
        if not label:
            return None
        try:
            action = view_state.queue_pending_action(
                self.data_dir / "plans.json",
                persona=persona_id,
                label=label,
                source=f"月月请求：{text[:120]}",
                now=now,
            )
            logger.info("[虚拟人生] 月月请求递东西，已准备观察窗按钮 label=%s", label)
            return action
        except Exception as exc:
            logger.warning("[虚拟人生] 准备月月请求按钮失败: %s", exc)
            return None

    async def _maybe_queue_give_action(
        self, event: AstrMessageEvent, now: datetime
    ) -> None:
        """私聊出现「拿东西给他/她/月月」时，给观察窗准备一个按钮。"""
        if session_kind(event.unified_msg_origin) != "friend":
            return
        if not (self._interaction_settings().get("enable", True)):
            return
        text = str(event.get_message_str() or "").strip()
        label = self._give_action_label(text)
        if not label:
            return
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            view_state.queue_pending_action(
                self.data_dir / "plans.json",
                persona=persona.id,
                label=label,
                source=text,
                now=now,
            )
            logger.info(
                "[虚拟人生] 已准备观察窗递东西按钮 umo=%s label=%s",
                event.unified_msg_origin,
                label,
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 准备递东西按钮失败: %s", exc)

    async def _handle_incoming(self, event: AstrMessageEvent) -> None:
        umo = event.unified_msg_origin
        if not self.policy.is_enabled(umo):
            return
        if not self._is_conversation_event(event):
            logger.debug("[虚拟人生] 指令不算聊天，不重置安静计时 umo=%s", umo)
            return
        now = self._now()
        if session_kind(umo) == "friend":
            # 群聊消息不能改写主人的睡眠状态，否则会影响私聊和日程。
            self._update_user_state_from_message(
                str(event.get_message_str() or ""), now
            )
            await self._maybe_queue_give_action(event, now)
        self._mark_conversation_activity(umo, now)
        self.policy.record_incoming(umo, now)
        await self.storage.save_sessions()
        self._schedule_idle(umo)
