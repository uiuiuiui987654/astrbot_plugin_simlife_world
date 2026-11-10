"""Speaking first: the decision loop, the policy gate, writing and sending proactive messages."""

from __future__ import annotations

import asyncio
import random

from astrbot.api import logger
from astrbot.api.event import MessageChain
from astrbot.core.utils.session_lock import session_lock_manager

from .. import camera_photo, life_memory, view_state
from ..models import DailyPlan
from ..persona import PersonaContext
from ..proactive import session_kind
from ..utils import parse_datetime, timeline_item_at
from .common import _group_plan_terms

DECISION_INTENT = "忽然想说点什么，也可能只是想想"
GROUP_INTENT = "想自然地在群里说句话，和群友互动一下"
GROUP_STATE = "正在过自己的日常"
BREAK_SILENCE_NOTE = (
    "群里现在有点安静，别再沉默。自然地说一句短话打破冷场，"
    "可以分享此刻的一件小事或一个轻吐槽；不要汇报日程、"
    "不要像公告，也不要硬开一个空泛的话题。"
)
REPEAT_NOTE = "你刚才写的那句和最近说过的话太像了（同一场景/动作/数字）。这次必须换一个完全不同的话题或角度，别再提刚才那件事。"
EMPTY_GROUP_REPLY = "……"


class ProactiveMixin:
    def _decision_settings(self) -> dict:
        return self.config.get("delivery_settings", {}) or {}

    # ------------------------------------------------------------------ the decision loop

    async def _decision_loop(self) -> None:
        """Every few minutes give her the chance to say something; the model decides whether to."""
        settings = self._decision_settings()
        if not settings.get("decision_loop_enable", True):
            logger.info("[模拟人生] 发言决策循环未启用")
            return
        minutes = max(5, int(settings.get("decision_interval_minutes", 20)))
        logger.info("[模拟人生] 发言决策循环已启动，间隔=%s 分钟", minutes)
        while True:
            try:
                await self._run_decision_opportunities()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("[模拟人生] 发言决策失败: %s", exc)
            await asyncio.sleep(minutes * 60)

    async def _run_decision_opportunities(self) -> None:
        settings = self._decision_settings()
        if not settings.get("decision_loop_enable", True):
            return
        now = self._now()
        quiet_minutes = max(0, int(settings.get("decision_min_silence_minutes", 8)))
        for umo in self.policy.enabled_sessions():
            try:
                state = self.storage.sessions.get(umo)
                last = (
                    parse_datetime(state.last_user_message_at, self.timezone)
                    if state and state.last_user_message_at
                    else None
                )
                if (
                    last is not None
                    and (now - last).total_seconds() / 60 < quiet_minutes
                ):
                    continue  # they're talking; don't butt in
                persona, plan = await self._ensure_plan_for_umo(umo)
                current = timeline_item_at(plan, now) if plan.status == "ok" else None
                if plan.status != "ok" or (
                    current is not None and current.state == "sleep"
                ):
                    continue
                await self._attempt_unsolicited(
                    umo, persona, plan, DECISION_INTENT, "decision"
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("[模拟人生] 发言决策异常 umo=%s: %s", umo, exc)

    # ------------------------------------------------------------------ gate

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
        """``(sent, reason)``; the reason feeds the retry logic in the scheduling mixin."""
        async with self.delivery_locks.setdefault(umo, asyncio.Lock()):
            if not plan.has_schedule:
                return False, "no schedule today"
            now = self._now()
            refusal = self._quick_refusal(umo, trigger, now)
            if refusal:
                return False, refusal
            state = self.policy.ensure_state(umo, persona.id, plan, now)
            verdict = self.policy.evaluate(
                umo=umo,
                state=state,
                current_item=timeline_item_at(plan, now),
                now=now,
                trigger=trigger,
                attempt_key=attempt_key,
                needs=self._life_needs(plan, now),
            )
            if not verdict.allowed:
                logger.info("[模拟人生] %s 这次不发：%s", umo, verdict.reason)
                return False, verdict.reason
            sent = await self._deliver(
                umo,
                persona,
                plan,
                intent,
                state.unanswered_count,
                self._conversation_generation(umo),
                decide=trigger == "decision",
            )
            if not sent:
                if trigger == "decision":
                    return False, "decided to stay quiet"
                return False, "agent running" if self._agent_is_active(
                    umo
                ) else "chat not quiet yet"
            # Group windows are scheduled chatter and don't spend the daily budget.
            self.policy.record_delivery(
                state,
                now,
                count_budget=not (session_kind(umo) == "group" and trigger == "window"),
            )
            await self.storage.save_sessions()
            return True, "sent"

    def _quick_refusal(self, umo: str, trigger: str, now) -> str:
        """Reasons to stay quiet that don't need the policy at all."""
        if self._agent_is_active(umo):
            logger.info("[模拟人生] %s 正在跑 Agent 任务，先不打扰", umo)
            return "agent running"
        if self.user_states.is_sleeping(now):
            logger.info("[模拟人生] 跳过 %s: 主人在睡觉", umo)
            return "user sleeping"
        if trigger == "window" and not self._window_is_idle_enough(umo, now):
            logger.info("[模拟人生] %s 刚刚还在聊，窗口先不发", umo)
            return "chat not quiet yet"
        return ""

    # ------------------------------------------------------------------ writing the message

    def _current_room_conflict(self, text: str, current) -> str:
        """A room the text mentions although she is somewhere else ("" when consistent)."""
        location = (
            str(getattr(current, "location", "") or "") if current is not None else ""
        )
        if not location:
            return ""
        here = {word for word in self.HOME_PLACE_WORDS if word in location}
        text = str(text or "")
        return next(
            (
                word
                for word in self.HOME_PLACE_WORDS
                if word != "家" and word in text and word not in here
            ),
            "",
        )

    async def _private_extras(self, persona: PersonaContext, now) -> str:
        """Little things worth mentioning in a private message: pending gifts, memories, a street encounter."""
        extras = ""
        try:
            pending = view_state.load_pending_actions(
                self.data_dir / "plans.json", persona.id
            )
            if pending:
                labels = "、".join(
                    str(action.get("label") or "递东西") for action in pending[:2]
                )
                extras += (
                    "\n\n【观察窗待处理】主人之前在对话里提到要给月月东西，"
                    f"观察窗里还有「{labels}」按钮。可以在主动消息里自然提醒"
                    "主人去点一下，但不要说得像系统提示。"
                )
            memory = self._life_memory_context(persona.id, now)
            if memory:
                extras += "\n\n" + memory
            encounter = life_memory.unshared_encounter(
                self.data_dir, persona.id, now.date()
            )
            if encounter:
                extras += f"\n\n【刚才路上遇到的小事】{encounter['text']}。如果和这条主动消息搭得上，可以像随口分享一样提一句；搭不上就别硬说。"
                life_memory.mark_shared(
                    self.data_dir, persona.id, now.date(), encounter["key"]
                )
            gifts = self.interactions.recent_gifts(2, hours=48)
            if gifts:
                names = "、".join(
                    str(item.get("item_name") or "").strip() for item in gifts
                )
                extras += f"\n\n【最近收到的东西】{names}。如果和当前主动消息自然相关，可以顺口提一句；不要每条都提，也不要像在报清单。"
        except Exception:
            logger.debug("[模拟人生] 主动消息附加信息读取失败", exc_info=True)
        return extras

    def _group_break_chance(self) -> float:
        try:
            chance = float(
                self._decision_settings().get("group_break_silence_probability", 0.4)
            )
        except (TypeError, ValueError):
            chance = 0.4
        return max(0.0, min(1.0, chance))

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
        """Write the message (with consistency / repetition rewrites) and send it if the chat hasn't moved on."""
        now = self._now()
        group = session_kind(umo) == "group"
        current = timeline_item_at(plan, now)
        doing = (
            GROUP_STATE
            if group
            else (current.activity if current else "今天的安排还没定")
        )
        settings = self._decision_settings()
        await self._record_completed_personal_network_events(persona.id, now)
        relationships = (
            "" if group else await self._personal_network_context(persona.id)
        )
        if group:
            context = self._group_life_context(plan, now)
        elif settings.get("proactive_timeline_context", True):
            furniture_states, furniture_context = self._furniture_activity_context(now)
            context = self.smart_context_injector.build_proactive_context(
                plan,
                now,
                self.long_term,
                furniture_context=furniture_context,
                furniture_states=furniture_states,
                history_plans=self._life_history_plans(plan),
                health_summary=str(self._life_needs(plan, now).get("summary") or ""),
            )
        else:
            context = ""
        if not group:
            context += await self._private_extras(persona, now)
        reader = getattr(self.message_generator, "recent_proactive_texts", None)
        said_lately: list[str] = (
            await reader(umo, 8)
            if not group
            and settings.get("proactive_repeat_guard", True)
            and callable(reader)
            else []
        )
        base = dict(
            umo=umo,
            persona=persona,
            current_time=now,
            current_state=doing,
            intent=GROUP_INTENT if group else intent,
            unanswered_count=unanswered_count,
            relationship_context=relationships,
            timeline_context=context,
            recent_sent=said_lately,
        )

        async def write(**changes) -> str:
            return await self.message_generator.generate(**{**base, **changes})

        def tidy_for_group(candidate: str) -> str:
            return self._filter_group_reply(
                candidate, extra_terms=_group_plan_terms(plan)
            )

        text = await write(decide=decide, include_history=not group, group_mode=group)
        if decide and not text:
            chance = self._group_break_chance() if group else 0.0
            if chance > 0 and random.random() < chance:
                logger.info(
                    "[模拟人生] 群聊冷场，按概率 %s 改口主动发言 umo=%s", chance, umo
                )
                text = await write(
                    relationship_context="",
                    recent_sent=[],
                    decide=False,
                    include_history=False,
                    group_mode=True,
                    retry_note=BREAK_SILENCE_NOTE,
                )
            if not text:
                logger.info("[模拟人生] %s 这一次决定不开口", umo)
                return False
        if group:
            text = tidy_for_group(text)
            if not text or text == EMPTY_GROUP_REPLY:
                return False
        else:
            wrong_room = self._current_room_conflict(text, current)
            if wrong_room:
                logger.info(
                    "[模拟人生] 主动消息场景不一致，重写一次 umo=%s wrong=%s text=%s",
                    umo,
                    wrong_room,
                    text,
                )
                where = getattr(current, "location", "") or "当前地点"
                what = getattr(current, "activity", "") or doing
                text = (
                    await write(
                        include_history=True,
                        retry_note=f"你刚才提到了「{wrong_room}」，但你此刻实际在{where}，正在{what}。"
                        "重写这一句，不要提到其他房间、地点或旧场景，只按当前状态说。",
                    )
                    or text
                )
                if self._current_room_conflict(text, current):
                    logger.info(
                        "[模拟人生] 重写后场景仍不一致，放弃本次主动消息 umo=%s", umo
                    )
                    return False
        if said_lately and self.interactions.is_repetitive(text, said_lately):
            logger.info(
                "[模拟人生] 主动消息与最近内容重复，重写一次 umo=%s text=%s", umo, text
            )
            rewrite = await write(
                recent_sent=said_lately + [text],
                include_history=not group,
                retry_note=REPEAT_NOTE,
            )
            if self.interactions.is_repetitive(rewrite, said_lately):
                logger.info("[模拟人生] 重写后仍然重复，放弃本次主动消息 umo=%s", umo)
                return False
            if group:
                rewrite = tidy_for_group(rewrite)
                if not rewrite or rewrite == EMPTY_GROUP_REPLY:
                    return False
            text = rewrite
        return await self._commit_proactive(umo, persona, intent, text, generation)

    async def _commit_proactive(
        self, umo: str, persona: PersonaContext, intent: str, text: str, generation: int
    ) -> bool:
        """Send unless the user spoke while we were writing (checked again under the session lock)."""
        if not self._proactive_context_is_current(umo, generation):
            logger.info("[模拟人生] %s 写消息时对方说话了，这条作废", umo)
            return False
        async with session_lock_manager.acquire_lock(umo):
            if not self._proactive_context_is_current(umo, generation):
                logger.info("[模拟人生] %s 发送前对方说话了，这条作废", umo)
                return False
            await self._send_text(umo, text)
            await self.message_generator.record_conversation(
                umo=umo, persona_id=persona.id, intent=intent, assistant_text=text
            )
        return True

    async def _send_text(self, umo: str, text: str) -> None:
        """Send in human-sized pieces with typing pauses; raises when the platform refuses."""
        split = self.message_segmenter.split(text)
        logger.info(
            "[模拟人生] 拆分发送 umo=%s 方式=%s 字数=%s 条数=%s 阈值=%s 说明=%s",
            umo,
            split.mode,
            split.source_length,
            len(split.segments),
            split.threshold,
            split.skipped_reason or "segmented",
        )
        for number, piece in enumerate(split.segments, start=1):
            if not await self.context.send_message(umo, MessageChain().message(piece)):
                raise RuntimeError(f"could not send to {umo}")
            if number < len(split.segments):
                await asyncio.sleep(self.message_segmenter.interval_for(piece))

    # ------------------------------------------------------------------ camera reactions

    async def react_to_camera(self, persona_id: str, camera_event: dict) -> bool:
        """Let her decide whether to comment right after the owner took a photo."""
        try:
            now = self._now()
            umo, persona = "", None
            for candidate_umo in self.policy.enabled_sessions():
                if session_kind(candidate_umo) == "group":
                    continue
                candidate = await self.personas.resolve(candidate_umo)
                if candidate.id == persona_id:
                    umo, persona = candidate_umo, candidate
                    break
            if not umo or persona is None:
                return False
            plan = self.storage.get_plan(now.date().isoformat(), persona.id)
            if plan is None or plan.status != "ok" or not plan.has_schedule:
                return False
            target = str(camera_event.get("target") or "")
            if target == camera_photo.TARGET_CHARACTER:
                subject = "主人刚刚用相机拍了你本人"
            elif target == camera_photo.TARGET_ITEM:
                subject = f"主人刚刚用相机拍了家里的「{camera_event.get('item_name') or '家具'}」"
            else:
                subject = "主人刚刚用相机拍了你此刻所在的房间"
            caption = str(camera_event.get("caption") or "").strip()
            intent = (
                f"{subject}{f'（{caption}）' if caption else ''}。你可以自然地评价这张照片、害羞、吐槽、"
                "反问一句，或者什么都不说；不要像系统提示，也不要复述拍照功能。"
            )
            sent = await self._deliver(
                umo,
                persona,
                plan,
                intent,
                0,
                self._conversation_generations.get(umo, 0),
                decide=True,
            )
            logger.info(
                "[模拟人生] 拍照后主动反应 persona=%s sent=%s", persona_id, sent
            )
            return bool(sent)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[模拟人生] 拍照后主动反应失败: %s", exc)
            return False
