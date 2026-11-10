"""Autonomous speaking opportunities and message delivery.

Mixin for ProactiveVirtualDailyPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

import asyncio
import random

from astrbot.api import logger
from astrbot.api.event import MessageChain
from astrbot.core.utils.session_lock import session_lock_manager

from .. import (
    camera_photo,
    view_state,
)
from ..models import (
    DailyPlan,
)
from ..persona import PersonaContext
from ..proactive import session_kind
from ..utils import (
    parse_datetime,
    timeline_item_at,
)
from .common import (
    _group_plan_terms,
)


class ProactiveMixin:
    def _decision_settings(self) -> dict:
        return self.config.get("delivery_settings", {}) or {}

    async def _decision_loop(self) -> None:
        """固定间隔给角色一次「要不要开口」的机会，由模型自己决定。"""
        settings = self._decision_settings()
        if not bool(settings.get("decision_loop_enable", True)):
            logger.info("[虚拟人生] 发言决策循环未启用")
            return
        interval = max(5, int(settings.get("decision_interval_minutes", 20)))
        logger.info("[虚拟人生] 发言决策循环已启动，间隔=%s 分钟", interval)
        while True:
            try:
                await self._run_decision_opportunities()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("[虚拟人生] 发言决策失败: %s", exc)
            await asyncio.sleep(interval * 60)

    async def _run_decision_opportunities(self) -> None:
        settings = self._decision_settings()
        if not bool(settings.get("decision_loop_enable", True)):
            return
        now = self._now()
        min_silence = max(0, int(settings.get("decision_min_silence_minutes", 8)))
        for umo in self.policy.enabled_sessions():
            try:
                state = self.storage.sessions.get(umo)
                if state and state.last_user_message_at:
                    last = parse_datetime(state.last_user_message_at, self.timezone)
                    if (
                        last is not None
                        and (now - last).total_seconds() / 60 < min_silence
                    ):
                        continue
                persona, plan = await self._ensure_plan_for_umo(umo)
                if plan.status != "ok":
                    continue
                current = timeline_item_at(plan, now)
                if current is not None and current.state == "sleep":
                    continue
                await self._attempt_unsolicited(
                    umo,
                    persona,
                    plan,
                    "忽然想说点什么，也可能只是想想",
                    "decision",
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("[虚拟人生] 发言决策异常 umo=%s: %s", umo, exc)

    async def _attempt_unsolicited(
        self,
        umo: str,
        persona: PersonaContext,
        plan: DailyPlan,
        intent: str,
        trigger: str,
        *,
        attempt_key: str = "",
    ) -> tuple[bool, str]:
        lock = self.delivery_locks.setdefault(umo, asyncio.Lock())
        async with lock:
            if not plan.has_schedule:
                return False, "schedule unavailable"
            if self._agent_is_active(umo):
                logger.info("[虚拟人生] 跳过 %s: 会话正在处理 Agent 任务", umo)
                return False, "agent task active"
            now = self._now()
            if self.user_states.is_sleeping(now):
                logger.info("[虚拟人生] 跳过 %s: 主人在睡觉", umo)
                return False, "user sleeping"
            if trigger == "window" and not self._window_is_idle_enough(umo, now):
                logger.info("[虚拟人生] 跳过 %s: 会话尚未达到窗口沉默时间", umo)
                return False, "conversation is not idle enough"
            state = self.policy.ensure_state(umo, persona.id, plan, now)
            current_item = timeline_item_at(plan, now)
            needs = self._life_needs(plan, now)
            decision = self.policy.evaluate(
                umo=umo,
                state=state,
                current_item=current_item,
                now=now,
                trigger=trigger,
                attempt_key=attempt_key,
                needs=needs,
            )
            if not decision.allowed:
                logger.info("[虚拟人生] 跳过 %s: %s", umo, decision.reason)
                return False, decision.reason
            generation = self._conversation_generation(umo)
            delivered = await self._deliver(
                umo,
                persona,
                plan,
                intent,
                state.unanswered_count,
                generation,
                decide=(trigger == "decision"),
            )
            if not delivered:
                if trigger == "decision":
                    return False, "model chose silence"
                reason = (
                    "agent task active"
                    if self._agent_is_active(umo)
                    else "conversation is not idle enough"
                )
                return False, reason
            self.policy.record_delivery(
                state,
                now,
                count_budget=not (session_kind(umo) == "group" and trigger == "window"),
            )
            await self.storage.save_sessions()
            return True, "sent"

    def _current_room_conflict(self, text: str, current) -> str:
        """Return a home room mentioned by text that is not the current room."""
        if current is None:
            return ""
        location = str(getattr(current, "location", "") or "")
        if not location:
            return ""
        allowed = {word for word in self.HOME_PLACE_WORDS if word in location}
        for word in self.HOME_PLACE_WORDS:
            if word == "家":
                continue
            if word in str(text or "") and word not in allowed:
                return word
        return ""

    async def _deliver(
        self,
        umo: str,
        persona: PersonaContext,
        plan: DailyPlan,
        intent: str,
        unanswered_count: int,
        generation: int,
        decide: bool = False,
    ) -> bool:
        now = self._now()
        is_group = session_kind(umo) == "group"
        current_item = timeline_item_at(plan, now)
        if is_group:
            current_state = "正在过自己的日常"
        else:
            current_state = (
                current_item.activity if current_item else "今日状态暂未明确"
            )
        await self._record_completed_personal_network_events(persona.id, now)
        relationship_context = (
            "" if is_group else await self._personal_network_context(persona.id)
        )
        timeline_context = ""
        delivery = self.config.get("delivery_settings", {}) or {}
        if is_group:
            timeline_context = self._group_life_context(plan, now)
        elif delivery.get("proactive_timeline_context", True):
            furniture_states, furniture_context = self._furniture_activity_context(now)
            health_summary = str(self._life_needs(plan, now).get("summary") or "")
            timeline_context = self.smart_context_injector.build_proactive_context(
                plan,
                now,
                self.long_term,
                furniture_context=furniture_context,
                furniture_states=furniture_states,
                history_plans=self._life_history_plans(plan),
                health_summary=health_summary,
            )
        if not is_group:
            try:
                pending_actions = view_state.load_pending_actions(
                    self.data_dir / "plans.json", persona.id
                )
                if pending_actions:
                    labels = "、".join(
                        str(action.get("label") or "递东西")
                        for action in pending_actions[:2]
                    )
                    timeline_context += (
                        "\n\n【观察窗待处理】主人之前在对话里提到要给月月东西，"
                        f"观察窗里还有「{labels}」按钮。可以在主动消息里自然提醒"
                        "主人去点一下，但不要说得像系统提示。"
                    )
                recent_gifts = self.interactions.recent_gifts(2, hours=48)
                if recent_gifts:
                    gift_names = "、".join(
                        str(item.get("item_name") or "").strip()
                        for item in recent_gifts
                    )
                    timeline_context += (
                        f"\n\n【最近收到的东西】{gift_names}。"
                        "如果和当前主动消息自然相关，可以顺口提一句；"
                        "不要每条都提，也不要像在报清单。"
                    )
            except Exception:
                pass
        group_intent = "想自然地在群里说句话，和群友互动一下"
        recent_proactive: list[str] = []
        reader = getattr(self.message_generator, "recent_proactive_texts", None)
        if (
            not is_group
            and delivery.get("proactive_repeat_guard", True)
            and callable(reader)
        ):
            recent_proactive = await reader(umo, 8)
        text = await self.message_generator.generate(
            umo=umo,
            persona=persona,
            current_time=now,
            current_state=current_state,
            intent=group_intent if is_group else intent,
            unanswered_count=unanswered_count,
            relationship_context=relationship_context,
            timeline_context=timeline_context,
            recent_sent=recent_proactive,
            decide=decide,
            include_history=not is_group,
            group_mode=is_group,
        )
        if decide and not text:
            if is_group:
                try:
                    break_probability = float(
                        delivery.get("group_break_silence_probability", 0.4)
                    )
                except (TypeError, ValueError):
                    break_probability = 0.4
                break_probability = max(0.0, min(1.0, break_probability))
                if break_probability > 0 and random.random() < break_probability:
                    logger.info(
                        "[虚拟人生] 群聊冷场，按概率 %s 改口主动发言 umo=%s",
                        break_probability,
                        umo,
                    )
                    text = await self.message_generator.generate(
                        umo=umo,
                        persona=persona,
                        current_time=now,
                        current_state=current_state,
                        intent=group_intent,
                        unanswered_count=unanswered_count,
                        relationship_context="",
                        timeline_context=timeline_context,
                        recent_sent=[],
                        decide=False,
                        include_history=False,
                        group_mode=True,
                        retry_note=(
                            "群里现在有点安静，别再沉默。自然地说一句短话打破冷场，"
                            "可以分享此刻的一件小事或一个轻吐槽；不要汇报日程、"
                            "不要像公告，也不要硬开一个空泛的话题。"
                        ),
                    )
            if not text:
                logger.info("[虚拟人生] %s 这一次决定不开口", umo)
                return False
        if is_group:
            text = self._filter_group_reply(text, extra_terms=_group_plan_terms(plan))
            if not text or text == "……":
                return False
        if not is_group:
            conflict = self._current_room_conflict(text, current_item)
            if conflict:
                logger.info(
                    "[虚拟人生] 主动消息场景不一致，重写一次 umo=%s wrong=%s text=%s",
                    umo,
                    conflict,
                    text,
                )
                retry = await self.message_generator.generate(
                    umo=umo,
                    persona=persona,
                    current_time=now,
                    current_state=current_state,
                    intent=intent,
                    unanswered_count=unanswered_count,
                    relationship_context=relationship_context,
                    timeline_context=timeline_context,
                    recent_sent=recent_proactive,
                    include_history=True,
                    retry_note=(
                        f"你刚才提到了「{conflict}」，但你此刻实际在"
                        f"{getattr(current_item, 'location', '') or '当前地点'}，"
                        f"正在{getattr(current_item, 'activity', '') or current_state}。"
                        "重写这一句，不要提到其他房间、地点或旧场景，只按当前状态说。"
                    ),
                )
                if retry:
                    text = retry
                if self._current_room_conflict(text, current_item):
                    logger.info(
                        "[虚拟人生] 重写后场景仍不一致，放弃本次主动消息 umo=%s",
                        umo,
                    )
                    return False
        if recent_proactive and self.interactions.is_repetitive(text, recent_proactive):
            logger.info(
                "[虚拟人生] 主动消息与最近内容重复，重写一次 umo=%s text=%s", umo, text
            )
            retry = await self.message_generator.generate(
                umo=umo,
                persona=persona,
                current_time=now,
                current_state=current_state,
                intent=group_intent if is_group else intent,
                unanswered_count=unanswered_count,
                relationship_context=relationship_context,
                timeline_context=timeline_context,
                recent_sent=recent_proactive + [text],
                include_history=not is_group,
                retry_note=(
                    "你刚才写的那句和最近说过的话太像了（同一场景/动作/数字）。"
                    "这次必须换一个完全不同的话题或角度，别再提刚才那件事。"
                ),
            )
            if self.interactions.is_repetitive(retry, recent_proactive):
                logger.info("[虚拟人生] 重写后仍然重复，放弃本次主动消息 umo=%s", umo)
                return False
            if is_group:
                retry = self._filter_group_reply(
                    retry, extra_terms=_group_plan_terms(plan)
                )
                if not retry or retry == "……":
                    return False
            text = retry
        if not self._proactive_context_is_current(umo, generation):
            logger.info("[虚拟人生] 丢弃 %s 的主动消息：生成期间会话已发生变化", umo)
            return False
        async with session_lock_manager.acquire_lock(umo):
            if not self._proactive_context_is_current(umo, generation):
                logger.info("[虚拟人生] 丢弃 %s 的主动消息：提交前会话已发生变化", umo)
                return False
            await self._send_text(umo, text)
            await self.message_generator.record_conversation(
                umo=umo,
                persona_id=persona.id,
                intent=intent,
                assistant_text=text,
            )
        return True

    async def _send_text(self, umo: str, text: str) -> None:
        result = self.message_segmenter.split(text)
        logger.info(
            "[虚拟人生] 主动消息分段 umo=%s mode=%s chars=%s parts=%s threshold=%s reason=%s",
            umo,
            result.mode,
            result.source_length,
            len(result.segments),
            result.threshold,
            result.skipped_reason or "segmented",
        )
        for index, segment in enumerate(result.segments):
            sent = await self.context.send_message(umo, MessageChain().message(segment))
            if not sent:
                raise RuntimeError(f"platform unavailable for {umo}")
            if index + 1 < len(result.segments):
                await asyncio.sleep(self.message_segmenter.interval_for(segment))

    async def react_to_camera(self, persona_id: str, camera_event: dict) -> bool:
        """Let the character decide whether to say something right after a photo."""
        try:
            now = self._now()
            target_umo = ""
            persona = None
            for umo in self.policy.enabled_sessions():
                if session_kind(umo) == "group":
                    continue
                candidate = await self.personas.resolve(umo)
                if candidate.id == persona_id:
                    target_umo = umo
                    persona = candidate
                    break
            if not target_umo or persona is None:
                return False
            plan = self.storage.get_plan(now.date().isoformat(), persona.id)
            if plan is None or plan.status != "ok" or not plan.has_schedule:
                return False
            target = str(camera_event.get("target") or "")
            caption = str(camera_event.get("caption") or "").strip()
            if target == camera_photo.TARGET_CHARACTER:
                what = "主人刚刚用相机拍了你本人"
            elif target == camera_photo.TARGET_ITEM:
                what = (
                    "主人刚刚用相机拍了家里的「"
                    + str(camera_event.get("item_name") or "家具")
                    + "」"
                )
            else:
                what = "主人刚刚用相机拍了你此刻所在的房间"
            detail = f"（{caption}）" if caption else ""
            intent = (
                f"{what}{detail}。你可以自然地评价这张照片、害羞、吐槽、"
                "反问一句，或者什么都不说；不要像系统提示，也不要复述拍照功能。"
            )
            generation = self._conversation_generations.get(target_umo, 0)
            sent = await self._deliver(
                target_umo,
                persona,
                plan,
                intent,
                0,
                generation,
                decide=True,
            )
            logger.info(
                "[虚拟人生] 拍照后主动反应 persona=%s sent=%s",
                persona_id,
                sent,
            )
            return bool(sent)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[虚拟人生] 拍照后主动反应失败: %s", exc)
            return False
