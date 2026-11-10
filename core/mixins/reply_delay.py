"""Reply delays on incoming chat: hold the message, collect follow-ups, then answer the batch."""

from __future__ import annotations

from datetime import datetime

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import Image, Record, Reply
from astrbot.core.agent.message import TextPart
from astrbot.core.provider.entities import ProviderRequest

from ..proactive import session_kind
from ..reply_delay import QueuedMessage, format_delay_context, format_queued_messages
from ..utils import timeline_item_at

EXTRA = "virtual_life_reply_delay_"  # prefix of the event extras this mixin uses


class ReplyDelayMixin:
    def _arrival_time(self, event: AstrMessageEvent) -> datetime:
        try:
            return datetime.fromtimestamp(float(event.created_at), self.timezone)
        except (AttributeError, TypeError, ValueError, OSError):
            return self._now()

    async def _prepare_reply_delay(self, event: AstrMessageEvent) -> None:
        """Runs before the LLM request: either waits out the delay (first message) or parks the message."""
        umo = event.unified_msg_origin
        excluded = (
            not self._schedule_available_for_umo(umo)
            or event.get_extra("provider_request") is not None
        )
        event.set_extra(EXTRA + "excluded", excluded)
        policy = self.reply_delay_policy
        if excluded or not policy.enabled:
            return
        received_at = self._arrival_time(event)
        try:
            persona = await self.personas.resolve(umo)
        except Exception:
            logger.exception("[虚拟人生] 不知道是哪个人格，不做晚点回复")
            return
        day = received_at.date().isoformat()
        plan = self.storage.get_plan(day, persona.id)
        if not plan or not plan.has_schedule:
            logger.info(
                "[虚拟人生] 今天没有日程，不做晚点回复 persona=%s date=%s",
                persona.id,
                day,
            )
            return
        arrival_item = timeline_item_at(plan, received_at)
        if arrival_item is None:
            return

        text = event.get_message_str()
        decision = policy.decide(
            arrival_item,
            received_at,
            len(text),
            active_conversation=self.reply_delay_coordinator.is_active(
                umo, received_at
            ),
            needs=self._life_needs(plan, received_at),
        )
        message = QueuedMessage(
            received_at=received_at,
            sender_id=event.get_sender_id(),
            sender_name=event.get_sender_name(),
            prompt=str(text or ""),
            image_urls=self._message_media_urls(event, Image),
            audio_urls=self._message_media_urls(event, Record),
            temporary_files=tuple(
                str(path)
                for path in getattr(event, "_temporary_local_files", ())
                if path
            ),
        )
        batch, first = await self.reply_delay_coordinator.enqueue(
            umo,
            message,
            decision,
            arrival_item,
            extend_seconds=policy.merge_window_seconds if policy.merge_extend else 0,
            max_total_seconds=policy.max_merge_seconds,
        )
        if batch is None:
            return
        if not first:
            # The first message of the batch answers for this one; its files now belong to that request.
            self._detach_temporary_files(event, message.temporary_files)
            event.stop_event()
            logger.info(
                "[虚拟人生] 消息并入等待中的一批 umo=%s 条数=%s 截止=%s",
                umo,
                len(batch.messages),
                batch.deadline.isoformat(),
            )
            return

        notice = (
            policy.notification(decision)
            if decision.delay_seconds > 0 and policy.notify_user
            else ""
        )
        if notice:
            try:
                await self.context.send_message(umo, MessageChain().message(notice))
            except Exception:
                logger.exception("[虚拟人生] 等待提示没发出去")

        messages = await self.reply_delay_coordinator.settle(batch, self._now())
        settled_at = self._now()
        for key, value in (
            ("batch", batch),
            ("messages", messages),
            ("persona_id", persona.id),
            ("settled_at", settled_at),
        ):
            event.set_extra(EXTRA + key, value)
        logger.info(
            "[虚拟人生] 等待结束，开始回复 umo=%s 可打扰度=%s 计划=%ss 实际=%ss 条数=%s",
            umo,
            decision.availability,
            decision.delay_seconds,
            max(0, int((settled_at - batch.created_at).total_seconds())),
            len(messages),
        )

    @staticmethod
    def _message_media_urls(
        event: AstrMessageEvent, media_type: type
    ) -> tuple[str, ...]:
        """Unique paths/urls of ``media_type`` parts, including those inside a quoted reply."""
        parts = []
        for part in event.get_messages():
            parts.append(part)
            if isinstance(part, Reply) and part.chain:
                parts += part.chain
        found = (
            str(part.path or part.url or part.file)
            for part in parts
            if isinstance(part, media_type) and (part.path or part.url or part.file)
        )
        return tuple(dict.fromkeys(found))

    @staticmethod
    def _detach_temporary_files(
        event: AstrMessageEvent, temporary_files: tuple[str, ...]
    ) -> None:
        tracked = getattr(event, "_temporary_local_files", None)
        if isinstance(tracked, list):
            tracked[:] = [path for path in tracked if path not in temporary_files]

    def _apply_reply_delay_batch(
        self, event: AstrMessageEvent, req: ProviderRequest
    ) -> None:
        """Swap the request's prompt for the whole batch and add what happened while she waited."""
        batch = event.get_extra(EXTRA + "batch")
        messages = event.get_extra(EXTRA + "messages")
        settled_at = event.get_extra(EXTRA + "settled_at")
        if not batch or not messages or not isinstance(settled_at, datetime):
            return
        req.prompt = format_queued_messages(
            messages, group=session_kind(event.unified_msg_origin) == "group"
        )
        req.image_urls = [url for message in messages for url in message.image_urls]
        req.audio_urls = [url for message in messages for url in message.audio_urls]
        for message in messages:
            for path in message.temporary_files:
                event.track_temporary_local_file(path)
        plan = self.storage.get_plan(
            settled_at.date().isoformat(), str(event.get_extra(EXTRA + "persona_id"))
        )
        now_item = (
            timeline_item_at(plan, settled_at) if plan and plan.has_schedule else None
        )
        req.extra_user_content_parts.append(
            TextPart(
                text=format_delay_context(batch, settled_at, now_item)
            ).mark_as_temp()
        )
