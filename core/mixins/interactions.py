"""Observation-window interactions and user state.

Mixin for ProactiveVirtualDailyPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.core.agent.message import TextPart
from astrbot.core.provider.entities import ProviderRequest

from .. import (
    affection,
)
from ..schedule_edit import insert_activity
from ..utils import (
    timeline_item_at,
)


class InteractionsMixin:
    def _interaction_settings(self) -> dict:
        return self.config.get("interaction_settings", {}) or {}

    async def _interaction_loop(self) -> None:
        config = self.interactions.settings(self._interaction_settings())
        interval = max(1, int(config["poll_seconds"]))
        logger.info("[模拟人生] 即时互动已启动，轮询间隔=%ss", interval)
        while True:
            try:
                await self._process_interactions()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("[模拟人生] 即时互动处理失败: %s", exc)
            await asyncio.sleep(interval)

    async def _process_interactions(self) -> None:
        config = self.interactions.settings(self._interaction_settings())
        if not config["enable"]:
            return
        async with self._interaction_lock:
            for request in self.interactions.pending(limit=3):
                if not self.interactions.claim(request):
                    logger.info(
                        "[模拟人生] 互动请求已被认领或存在重复，跳过 id=%s",
                        request.get("id"),
                    )
                    continue
                try:
                    await self._handle_interaction(request, config)
                except Exception as exc:
                    logger.warning(
                        "[模拟人生] 互动失败 id=%s: %s", request.get("id"), exc
                    )
                    self.interactions.write_response(
                        request,
                        {"speech": "刚才走神了，没听清……再说一次？"},
                        qq={
                            "sent": False,
                            "umo": "",
                            "error": f"{type(exc).__name__}",
                        },
                    )
                finally:
                    self.interactions.finish(request)

    HOME_PLACE_WORDS = (
        "家",
        "客厅",
        "卧室",
        "厨房",
        "浴室",
        "卫生间",
        "阳台",
        "书房",
        "餐厅",
        "玄关",
        "健身室",
        "健身房",
        "衣帽间",
        "画室",
        "影音室",
        "露台",
        "楼梯厅",
        "洗衣房",
        "储藏室",
        "花园",
        "车库",
        "小屋",
        "公寓",
        "宿舍",
        "出租屋",
    )

    AWAY_PLACE_WORDS = (
        "路上",
        "街",
        "超市",
        "公园",
        "公司",
        "学校",
        "地铁",
        "公交",
        "出差",
        "旅行",
        "机场",
        "车站",
        "酒店",
        "民宿",
        "商场",
        "菜市场",
    )

    def _is_home_place(self, location: str, activity: str = "") -> bool:
        place = str(location or "").strip()
        if not place:
            return True
        if any(word in place for word in self.AWAY_PLACE_WORDS):
            return False
        return any(word in place for word in self.HOME_PLACE_WORDS)

    async def _handle_interaction(self, request: dict, config: dict) -> None:
        persona = await self.personas.resolve(None)
        now = self._now()
        affection_action = str(request.get("affection_action") or "")
        action_thresholds = {
            "headpat": 100,
            "handhold": 250,
            "hug": 450,
            "kiss": 650,
        }
        if affection_action in action_thresholds:
            target_persona = str(request.get("persona") or "").strip() or persona.id
            relation = affection.snapshot(self.data_dir, target_persona, now=now)
            required = action_thresholds[affection_action]
            if int(relation.get("score") or 0) < required:
                result = {
                    "speech": "现在还不太熟呢，等我们再亲近一点吧。",
                    "detail": "",
                    "mood": "",
                    "dish": None,
                    "rejected": True,
                    "affection_action": affection_action,
                    "score": int(relation.get("score") or 0),
                    "required": required,
                }
                qq = await self._sync_interaction_qq(request, result, config)
                self.interactions.write_response(request, result, qq=qq)
                logger.info(
                    "[模拟人生] 关系动作被拒绝 action=%s score=%s required=%s",
                    affection_action,
                    relation.get("score"),
                    required,
                )
                return
        plan = self.storage.get_plan(now.date().isoformat(), persona.id)
        current = timeline_item_at(plan, now) if plan is not None else None
        active = request.get("current") or {}
        place_kind = str(active.get("kind") or "").strip()
        place = str(
            active.get("location") or getattr(current, "location", "") or ""
        ).strip()
        activity = str(active.get("activity") or getattr(current, "activity", "") or "")
        away = (
            place_kind not in ("", "home")
            if place_kind
            else not self._is_home_place(place, activity)
        )
        if away and str(request.get("item_id") or "").strip():
            where = place or "外面"
            result = {
                "speech": f"我还在外面呢（{where}），等回家再碰这些吧。",
                "detail": "",
                "mood": "",
                "dish": None,
            }
            qq = await self._sync_interaction_qq(request, result, config)
            self.interactions.write_response(request, result, qq=qq)
            logger.info(
                "[模拟人生] 互动被拒绝：她不在家 location=%s item=%s",
                where,
                request.get("item_id"),
            )
            return
        user_sleeping = self._detect_user_sleep(request, now)
        if not user_sleeping and self.user_states.is_sleeping(now):
            # 主人在观察窗里点了别的东西（或打字说话），说明已经起来活动了。
            self.user_states.clear()
            logger.info("[模拟人生] 主人在观察窗活动，清除睡眠状态")
        history_text, history_items = await self._interaction_history(config)
        avoid_lines = (
            self.interactions.recent_assistant_texts(history_items, 4)
            if config.get("repeat_guard", True)
            else []
        )
        recent_gifts = self.interactions.recent_gifts(3, hours=48)
        system, user = self.interactions.build_prompt(
            request,
            persona_prompt=persona.prompt,
            persona_name=persona.id,
            location=str(getattr(current, "location", "") or ""),
            activity=str(getattr(current, "activity", "") or ""),
            now_text=now.strftime("%H:%M"),
            ingredients=self._interaction_ingredients(),
            history=history_text,
            avoid_lines=avoid_lines,
            recent_gifts=recent_gifts,
            away=away,
            user_sleeping=user_sleeping,
            settings=config,
        )
        raw = await self.plan_generator.complete(
            user, system, f"interaction_{request.get('id', 'x')}"
        )
        result = self.interactions.parse_reply(raw, config)
        if avoid_lines and self.interactions.is_repetitive(
            result.get("speech", ""), avoid_lines
        ):
            logger.info(
                "[模拟人生] 互动回复与前文重复，重写一次 id=%s speech=%s",
                request.get("id"),
                result.get("speech"),
            )
            system, user = self.interactions.build_prompt(
                request,
                persona_prompt=persona.prompt,
                persona_name=persona.id,
                location=str(getattr(current, "location", "") or ""),
                activity=str(getattr(current, "activity", "") or ""),
                now_text=now.strftime("%H:%M"),
                ingredients=self._interaction_ingredients(),
                history=history_text,
                avoid_lines=avoid_lines + [str(result.get("speech") or "")],
                recent_gifts=recent_gifts,
                away=away,
                user_sleeping=user_sleeping,
                settings=config,
            )
            raw_retry = await self.plan_generator.complete(
                user, system, f"interaction_retry_{request.get('id', 'x')}"
            )
            retry = self.interactions.parse_reply(raw_retry, config)
            if not self.interactions.is_repetitive(
                retry.get("speech", ""), avoid_lines
            ):
                result = retry
        if str(request.get("kind") or "") == "dish":
            usage = self.interactions.consume_dish(result.get("dish"), config)
            if usage["used"] or usage["missing"]:
                result["used"] = usage["used"]
                result["missing"] = usage["missing"]
                logger.info(
                    "[模拟人生] 互动做菜扣减库存 dish=%s used=%s missing=%s",
                    (result.get("dish") or {}).get("name"),
                    [f"{item['name']}x{item['amount']}" for item in usage["used"]],
                    usage["missing"],
                )
        if str(request.get("action") or "") != "give":
            self._maybe_queue_give_request(
                str(result.get("speech") or ""), persona.id, now
            )
        await self._insert_interaction_activity(request, result, config)
        qq = await self._sync_interaction_qq(request, result, config)
        action_points = {
            "headpat": 2,
            "handhold": 3,
            "hug": 4,
            "kiss": 6,
        }
        affection_action = str(request.get("affection_action") or "")
        if affection_action in action_points:
            result["affection_points"] = action_points[affection_action]
        payload = self.interactions.write_response(request, result, qq=qq)
        await self._record_interaction_turn(request, result, config)
        try:
            kind = str(request.get("kind") or "")
            action = str(request.get("action") or "")
            affection_action = str(request.get("affection_action") or "")
            action_points = {
                "headpat": 2,
                "handhold": 3,
                "hug": 4,
                "kiss": 6,
            }
            points = (
                action_points[affection_action]
                if affection_action in action_points
                else 4
                if action == "give"
                else 2
                if kind in ("dish", "game")
                else 1
            )
            affection.add(
                self.data_dir,
                persona.id,
                points,
                f"观察窗互动：{affection_action or kind or action or '聊天'}",
                now=self._now(),
            )
        except Exception as exc:
            logger.debug("[模拟人生] 增加好感失败: %s", exc)
        logger.info(
            "[模拟人生] 互动完成 id=%s kind=%s qq=%s speech=%s",
            payload.get("id"),
            payload.get("kind"),
            qq.get("sent"),
            payload.get("speech"),
        )

    async def _record_interaction_turn(
        self, request: dict, result: dict, config: dict
    ) -> None:
        """把这次观察窗互动写回 QQ 会话，下一轮普通聊天才接得上。"""
        if not config.get("record_to_conversation", True):
            return
        umo = self._interaction_umo(config)
        speech = str(result.get("speech") or "").strip()
        if not umo or not speech:
            return
        dish = (result.get("dish") or {}).get("name") or ""
        item_name = str(request.get("item_name") or "").strip()
        action = str(request.get("action") or "").strip()
        kind = str(request.get("kind") or "").strip()
        if kind == "dish":
            user_text = f"（在观察窗里走到{item_name or '餐桌'}旁边，让你做点吃的）"
            if dish:
                user_text += f"最后做的是{dish}"
        elif kind == "game":
            game_name = str(request.get("game_name") or "小游戏").strip()
            user_text = f"（在观察窗里和你玩了一局{game_name}）"
        elif action == "give":
            gift_text = str(request.get("text") or "").strip()
            if gift_text.startswith("（") and "）" in gift_text:
                gift_text = gift_text.split("）", 1)[1].strip()
            user_text = f"（在观察窗里把{item_name or '东西'}递给你）" + (
                gift_text or "喏，给你。"
            )
        else:
            user_text = f"（在观察窗里对你说）{request.get('text') or ''}"
        try:
            manager = self.context.conversation_manager
            conversation_id = await manager.get_curr_conversation_id(umo)
            if not conversation_id:
                return
            await manager.add_message_pair(
                conversation_id,
                {"role": "user", "content": [{"type": "text", "text": user_text}]},
                {"role": "assistant", "content": [{"type": "text", "text": speech}]},
            )
            logger.debug("[模拟人生] 互动已写入对话历史 umo=%s", umo)
        except Exception as exc:
            logger.warning("[模拟人生] 写入互动历史失败 umo=%s: %s", umo, exc)

    USER_SLEEP_PATTERN = (
        "晚安",
        "睡了",
        "去睡",
        "睡觉",
        "上床",
        "困了",
        "休息",
        "闭眼",
        "躺下",
    )

    USER_WAKE_PATTERN = ("我醒了", "睡醒", "醒了", "起床", "早安", "我起了")

    def _detect_user_sleep(self, request: dict, now: datetime) -> bool:
        """观察窗里点床说「我上床睡了」时，记录主人在睡觉；说醒则清除。"""
        text = str(request.get("text") or "")
        item = str(request.get("item_name") or "")
        item_id = str(request.get("item_id") or "")
        is_bed = item_id == "bed" or "床" in item
        wants_sleep = any(word in text for word in self.USER_SLEEP_PATTERN)
        wants_wake = any(word in text for word in self.USER_WAKE_PATTERN)
        if wants_wake:
            if self.user_states.is_sleeping(now):
                self.user_states.clear()
                logger.info("[模拟人生] 主人醒了，清除睡眠状态")
            return False
        if is_bed and wants_sleep:
            self.user_states.set_sleeping(now, place="卧室的床上", source="window")
            logger.info("[模拟人生] 记录主人在床上睡觉 text=%s", text[:40])
            return True
        return False

    def _update_user_state_from_message(self, text: str, now: datetime) -> None:
        message = str(text or "")
        if not message:
            return
        if any(word in message for word in self.USER_WAKE_PATTERN):
            if self.user_states.is_sleeping(now):
                self.user_states.clear()
                logger.info("[模拟人生] 主人在聊天里说自己醒了，清除睡眠状态")
            return
        sleep_hint = re.search(
            r"(我(要|去|先|准备|该|得)?去?睡|我去睡|准备睡|睡觉了|晚安|困了)",
            message,
        )
        if sleep_hint and not any(word in message for word in ("你睡", "睡得")):
            if not self.user_states.is_sleeping(now):
                self.user_states.set_sleeping(
                    now, place="QQ 聊天里说要去睡", source="chat"
                )
                logger.info("[模拟人生] 主人在聊天里说要去睡，记录睡眠状态")

    async def _inject_user_state(
        self, event: AstrMessageEvent, req: ProviderRequest
    ) -> None:
        """普通聊天里注入主人睡眠状态，回复才会轻声。"""
        text = self.user_states.describe(self._now())
        if not text:
            return
        req.extra_user_content_parts.append(TextPart(text=text).mark_as_temp())
        logger.info("[模拟人生] 注入主人睡眠状态 umo=%s", event.unified_msg_origin)

    async def _insert_interaction_activity(
        self, request: dict, result: dict, config: dict
    ) -> None:
        """由角色自己判断这次互动要不要写进当天日程，再决定怎么写。"""
        if not bool(config.get("insert_activity_enable", True)):
            return
        if str(request.get("item_id") or "") == "bed" and any(
            word in str(request.get("text") or "") for word in self.USER_SLEEP_PATTERN
        ):
            logger.info("[模拟人生] 主人在睡觉，跳过日程插入")
            return
        persona = await self.personas.resolve(None)
        now = self._now()
        date_str = now.date().isoformat()
        plan = self.storage.get_plan(date_str, persona.id)
        if plan is None or not plan.has_schedule:
            return
        current = timeline_item_at(plan, now)
        dish = str((result.get("dish") or {}).get("name") or "").strip()
        item_name = str(request.get("item_name") or "").strip()
        room = str(request.get("room") or "").strip()
        default_minutes = int(config.get("insert_activity_minutes", 30))
        max_minutes = int(config.get("insert_activity_max_minutes", 120))
        location = room or str(getattr(current, "location", "") or "")
        action = str(request.get("action") or "").strip()
        kind = str(request.get("kind") or "").strip()
        if dish:
            default_activity = f"和主人一起吃饭（{dish}）"
        elif kind == "game":
            game_name = str(request.get("game_name") or "小游戏").strip()
            default_activity = f"和主人玩了一局{game_name}"
            default_minutes = min(default_minutes, 10)
        elif action == "give":
            default_activity = f"接过主人递来的{item_name or '东西'}"
            default_minutes = min(default_minutes, 5)
        elif item_name:
            default_activity = f"在{room or '家'}陪主人待一会儿"
        else:
            default_activity = "和主人说说话"

        insert = True
        activity = default_activity
        minutes = default_minutes
        place = location
        reason = "direct"
        if bool(config.get("insert_activity_ai_decide", True)):
            system, user = self.interactions.build_schedule_decision_prompt(
                request,
                result,
                persona_prompt=persona.prompt,
                current_activity=str(getattr(current, "activity", "") or ""),
                current_location=str(getattr(current, "location", "") or ""),
                now_text=now.strftime("%H:%M"),
            )
            try:
                raw = await self.plan_generator.complete(
                    user, system, f"schedule_decision_{request.get('id', 'x')}"
                )
                decision = self.interactions.parse_schedule_decision(
                    raw, default_minutes=default_minutes
                )
            except Exception as exc:
                logger.warning("[模拟人生] 日程插入判定失败: %s", exc)
                decision = {}
            if decision:
                insert = bool(decision["insert"])
                reason = decision["reason"] or "ai"
                if insert:
                    activity = decision["activity"] or default_activity
                    minutes = max(5, min(max_minutes, int(decision["minutes"])))
                    place = decision["location"] or location
            else:
                # 模型没给出可用判断时：吃饭这类明确事件保守插入，其余跳过。
                insert = bool(dish)
                reason = "fallback"
            logger.info(
                "[模拟人生] 日程插入判定 insert=%s reason=%s activity=%s minutes=%s",
                insert,
                reason,
                activity,
                minutes,
            )
            if not insert:
                return

        try:
            updated = insert_activity(plan, now, minutes, activity, place)
        except Exception as exc:
            logger.warning("[模拟人生] 互动活动写入日程失败: %s", exc)
            return
        try:
            key = self.storage.plan_key(date_str, persona.id)
            self.storage.plans[key] = updated
            await self.storage.save_plans()
        except Exception as exc:
            logger.warning("[模拟人生] 保存互动日程失败: %s", exc)
            return
        logger.info(
            "[模拟人生] 已把互动写入今日日程 activity=%s location=%s 时长=%s分钟 (reason=%s)",
            activity,
            place or "-",
            minutes,
            reason,
        )

    async def _interaction_history(self, config: dict) -> tuple[str, list]:
        """读取目标会话最近几轮聊天，供即时互动接着往下聊。

        返回 ``(格式化文本, 原始历史列表)``；后者用于反重复判断。
        """
        if int(config.get("history_messages", 0)) <= 0:
            return "", []
        umo = self._interaction_umo(config)
        if not umo:
            return "", []
        try:
            manager = self.context.conversation_manager
            conversation_id = await manager.get_curr_conversation_id(umo)
            if not conversation_id:
                return "", []
            conversation = await manager.get_conversation(umo, conversation_id)
            raw = getattr(conversation, "history", "[]")
            history = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(history, list):
                return "", []
            text = self.interactions.format_history(
                history, now=self._now(), settings=config
            )
            if text:
                logger.debug(
                    "[模拟人生] 互动参考历史 umo=%s 行数=%s", umo, text.count("\n") + 1
                )
            return text, history
        except Exception as exc:
            logger.warning("[模拟人生] 读取互动历史失败 umo=%s: %s", umo, exc)
            return "", []

    def _interaction_ingredients(self) -> list[str]:
        path = self.data_dir / "fridge_inventory.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        items = payload.get("ingredients", []) if isinstance(payload, dict) else []
        names: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if name:
                names.append(name)
        return names

    def _interaction_umo(self, config: dict) -> str:
        configured = str(config.get("sync_umo") or "").strip()
        if configured:
            return configured
        for key in ("friend_settings", "group_settings"):
            section = self.config.get(key, {}) or {}
            for value in section.get("session_list", []) or []:
                text = str(value).strip()
                if text:
                    return text
        return ""

    async def _sync_interaction_qq(
        self, request: dict, result: dict, config: dict
    ) -> dict:
        record: dict = {"sent": False, "umo": "", "error": ""}
        if not config["sync_to_qq"]:
            record["error"] = "disabled"
            return record
        umo = self._interaction_umo(config)
        if not umo:
            record["error"] = "no_session"
            return record
        text = self.interactions.qq_text(request, result)
        if not text:
            record["error"] = "empty"
            return record
        request_id = str(request.get("id") or "")
        if not self.interactions.claim_sent(request_id):
            logger.warning(
                "[模拟人生] 互动已发送过，跳过重复 QQ 消息 id=%s", request_id
            )
            record["error"] = "duplicate"
            return record
        record["umo"] = umo
        try:
            sent = await self.context.send_message(umo, MessageChain().message(text))
        except Exception as exc:
            self.interactions.release_sent(request_id)
            record["error"] = f"{type(exc).__name__}: {exc}"
            logger.warning("[模拟人生] 互动同步 QQ 失败 umo=%s: %s", umo, exc)
            return record
        if not sent:
            self.interactions.release_sent(request_id)
            record["error"] = "platform unavailable"
            return record
        record["sent"] = True
        return record
