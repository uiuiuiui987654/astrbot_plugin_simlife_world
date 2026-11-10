"""Reply-delay batching of incoming messages.

Mixin for ProactiveVirtualDailyPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

from datetime import datetime

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import Image, Record, Reply
from astrbot.core.agent.message import TextPart
from astrbot.core.provider.entities import ProviderRequest

from ..proactive import session_kind
from ..reply_delay import (
    QueuedMessage,
    format_delay_context,
    format_queued_messages,
)
from ..utils import (
    timeline_item_at,
)


class ReplyDelayMixin:
    async def _prepare_reply_delay(
        self,
        event: AstrMessageEvent,
    ) -> None:
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            event.set_extra("virtual_life_reply_delay_excluded", True)
            return
        excluded = event.get_extra("provider_request") is not None
        event.set_extra("virtual_life_reply_delay_excluded", excluded)
        if excluded:
            return
        if not self.reply_delay_policy.enabled:
            return
        try:
            received_at = datetime.fromtimestamp(float(event.created_at), self.timezone)
        except (AttributeError, TypeError, ValueError, OSError):
            received_at = self._now()
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
        except Exception:
            logger.exception("[虚拟人生] 回复延迟跳过：人格解析失败")
            return
        plan = self.storage.get_plan(received_at.date().isoformat(), persona.id)
        if not plan or not plan.has_schedule:
            logger.info(
                "[虚拟人生] 回复延迟跳过：内存中没有有效日程 persona=%s date=%s",
                persona.id,
                received_at.date().isoformat(),
            )
            return
        arrival_item = timeline_item_at(plan, received_at)
        if arrival_item is None:
            return

        active = self.reply_delay_coordinator.is_active(
            event.unified_msg_origin,
            received_at,
        )
        decision = self.reply_delay_policy.decide(
            arrival_item,
            received_at,
            len(event.get_message_str()),
            active_conversation=active,
            needs=self._life_needs(plan, received_at),
        )
        queued = QueuedMessage(
            received_at=received_at,
            sender_id=event.get_sender_id(),
            sender_name=event.get_sender_name(),
            prompt=str(event.get_message_str() or ""),
            image_urls=self._message_media_urls(event, Image),
            audio_urls=self._message_media_urls(event, Record),
            temporary_files=tuple(
                str(path)
                for path in getattr(event, "_temporary_local_files", ())
                if path
            ),
        )
        batch, primary = await self.reply_delay_coordinator.enqueue(
            event.unified_msg_origin,
            queued,
            decision,
            arrival_item,
            extend_seconds=(
                self.reply_delay_policy.merge_window_seconds
                if self.reply_delay_policy.merge_extend
                else 0
            ),
            max_total_seconds=self.reply_delay_policy.max_merge_seconds,
        )
        if batch is None:
            return
        if not primary:
            self._detach_temporary_files(event, queued.temporary_files)
            event.stop_event()
            logger.info(
                "[虚拟人生] 消息已加入回复延迟批次 umo=%s queued=%s deadline=%s",
                event.unified_msg_origin,
                len(batch.messages),
                batch.deadline.isoformat(),
            )
            return

        if decision.delay_seconds > 0 and self.reply_delay_policy.notify_user:
            notification = self.reply_delay_policy.notification(decision)
            if notification:
                try:
                    await self.context.send_message(
                        event.unified_msg_origin,
                        MessageChain().message(notification),
                    )
                except Exception:
                    logger.exception("[虚拟人生] 回复延迟提示发送失败")

        messages = await self.reply_delay_coordinator.settle(batch, self._now())
        settled_at = self._now()
        event.set_extra("virtual_life_reply_delay_batch", batch)
        event.set_extra("virtual_life_reply_delay_messages", messages)
        event.set_extra("virtual_life_reply_delay_persona_id", persona.id)
        event.set_extra("virtual_life_reply_delay_settled_at", settled_at)
        logger.info(
            "[虚拟人生] 回复延迟批次开始结算 umo=%s availability=%s planned=%ss actual=%ss queued=%s",
            event.unified_msg_origin,
            decision.availability,
            decision.delay_seconds,
            max(0, int((settled_at - batch.created_at).total_seconds())),
            len(messages),
        )

    @staticmethod
    def _message_media_urls(
        event: AstrMessageEvent, media_type: type
    ) -> tuple[str, ...]:
        components = []
        for component in event.get_messages():
            components.append(component)
            if isinstance(component, Reply) and component.chain:
                components.extend(component.chain)
        urls = []
        for component in components:
            if not isinstance(component, media_type):
                continue
            value = component.path or component.url or component.file
            if value and str(value) not in urls:
                urls.append(str(value))
        return tuple(urls)

    @staticmethod
    def _detach_temporary_files(
        event: AstrMessageEvent,
        temporary_files: tuple[str, ...],
    ) -> None:
        tracked = getattr(event, "_temporary_local_files", None)
        if not isinstance(tracked, list):
            return
        for path in temporary_files:
            while path in tracked:
                tracked.remove(path)

    def _apply_reply_delay_batch(
        self,
        event: AstrMessageEvent,
        req: ProviderRequest,
    ) -> None:
        batch = event.get_extra("virtual_life_reply_delay_batch")
        messages = event.get_extra("virtual_life_reply_delay_messages")
        settled_at = event.get_extra("virtual_life_reply_delay_settled_at")
        persona_id = event.get_extra("virtual_life_reply_delay_persona_id")
        if not batch or not messages or not isinstance(settled_at, datetime):
            return
        req.prompt = format_queued_messages(
            messages,
            group=session_kind(event.unified_msg_origin) == "group",
        )
        req.image_urls = [url for message in messages for url in message.image_urls]
        req.audio_urls = [url for message in messages for url in message.audio_urls]
        for message in messages:
            for path in message.temporary_files:
                event.track_temporary_local_file(path)
        current_plan = self.storage.get_plan(
            settled_at.date().isoformat(),
            str(persona_id),
        )
        current_item = (
            timeline_item_at(current_plan, settled_at)
            if current_plan and current_plan.has_schedule
            else None
        )
        delay_context = format_delay_context(batch, settled_at, current_item)
        req.extra_user_content_parts.append(TextPart(text=delay_context).mark_as_temp())
