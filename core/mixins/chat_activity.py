"""Detecting activities mentioned in chat and writing them into the schedule.

Mixin for SimLifeWorldPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

import asyncio
from typing import Any

from astrbot.api import logger

from .. import chat_schedule as chat_schedule_events
from ..schedule_edit import insert_activity
from ..utils import (
    timeline_item_at,
)


class ChatActivityMixin:
    # ------------------------------------------------ 聊天日程自动补写（内部）
    def _chat_schedule_settings(self) -> dict[str, Any]:
        return chat_schedule_events.settings(
            self.config.get("chat_schedule_settings", {}) or {}
        )

    async def _detect_chat_activity(
        self, umo: str, user_text: str, reply_text: str
    ) -> None:
        if not self._schedule_available_for_umo(umo):
            return
        settings = self._chat_schedule_settings()
        if not bool(settings.get("enable", True)):
            return
        async with self._chat_schedule_lock:
            try:
                await self._run_chat_activity_detection(
                    umo, user_text, reply_text, settings
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("[模拟人生] 聊天日程判定失败 umo=%s: %s", umo, exc)

    async def _run_chat_activity_detection(
        self,
        umo: str,
        user_text: str,
        reply_text: str,
        settings: dict[str, Any],
    ) -> None:
        now = self._now()
        date_str = now.date().isoformat()
        persona = await self.personas.resolve(umo)
        plan = self.storage.get_plan(date_str, persona.id)
        if plan is None or not plan.has_schedule:
            return
        current = timeline_item_at(plan, now)
        if (
            bool(settings.get("skip_when_sleeping", True))
            and current is not None
            and current.state == "sleep"
        ):
            return
        state = self.chat_schedule_state.load()
        if not chat_schedule_events.allow_check(state, umo, now, settings):
            return
        chat_schedule_events.mark_checked(state, umo, now)
        food = self.plan_generator.food
        menu = food.latest_menu(now.date(), persona.id)
        history_text = await self._recent_chat_lines(
            umo,
            int(settings.get("history_minutes") or 0),
            int(settings.get("history_messages") or 0),
            900,
        )
        system, prompt = chat_schedule_events.build_detection_prompt(
            persona_prompt=persona.prompt,
            now=now,
            current_activity=str(getattr(current, "activity", "") or ""),
            current_location=str(getattr(current, "location", "") or ""),
            schedule_text=chat_schedule_events.format_schedule_text(plan, now),
            menu_text=chat_schedule_events.format_menu_text(menu),
            history_text=history_text,
            user_text=user_text,
            reply_text=reply_text,
        )
        raw = await self.plan_generator.complete(
            prompt,
            system,
            f"chat_schedule_{self._umo_hash(umo)}_{int(now.timestamp())}",
        )
        decision = chat_schedule_events.parse_detection(
            raw,
            default_minutes=int(settings.get("default_minutes") or 30),
            max_minutes=int(settings.get("max_minutes") or 120),
        )
        schedule_decision = decision.get("schedule") or {}
        food_decision = decision.get("food") or {}
        plan_changed = False
        food_applied = False
        old_dish = ""
        new_dish = str(food_decision.get("dish") or "").strip()
        if (
            bool(food_decision.get("update"))
            and bool(settings.get("update_menu", True))
            and menu
            and new_dish
        ):
            food_state = food.load_state()
            old_dish, menu_changed = chat_schedule_events.update_menu_state(
                food_state,
                menu_key=f"{date_str}::{persona.id}",
                date_str=date_str,
                persona_id=persona.id,
                meal=str(food_decision.get("meal") or ""),
                dish=new_dish,
                ingredients=list(food_decision.get("ingredients") or []),
                method=str(food_decision.get("method") or ""),
                now=now,
            )
            if menu_changed:
                food.save_state(food_state)
                food_applied = True
                if (
                    bool(settings.get("update_plan_text", True))
                    and old_dish
                    and new_dish
                ):
                    plan, replaced = chat_schedule_events.replace_dish_in_timeline(
                        plan, old_dish, new_dish
                    )
                    plan_changed = plan_changed or replaced
        schedule_inserted = False
        if bool(schedule_decision.get("insert")) and bool(
            settings.get("insert_activity", True)
        ):
            activity = str(schedule_decision.get("activity") or "").strip()
            minutes = int(
                schedule_decision.get("minutes")
                or settings.get("default_minutes")
                or 30
            )
            location = str(schedule_decision.get("location") or "").strip()
            max_inserts = int(settings.get("max_inserts_per_day") or 0)
            if (
                activity
                and max_inserts > 0
                and (
                    chat_schedule_events.count_schedule_inserts_today(state, date_str)
                    >= max_inserts
                )
            ):
                logger.info(
                    "[模拟人生] 聊天日程：今日插入已达上限 %s，跳过 activity=%s",
                    max_inserts,
                    activity,
                )
            elif activity and chat_schedule_events.recently_inserted(
                state, umo, activity, now
            ):
                logger.info(
                    "[模拟人生] 聊天日程：近期已插入过相近活动，跳过 activity=%s",
                    activity,
                )
            elif activity:
                moment = chat_schedule_events.resolve_start(
                    now, schedule_decision.get("start")
                )
                if chat_schedule_events.schedule_has_similar(
                    plan, activity, moment, minutes
                ):
                    logger.info(
                        "[模拟人生] 聊天日程：当前日程已有相近活动，跳过 activity=%s",
                        activity,
                    )
                else:
                    try:
                        plan = insert_activity(
                            plan,
                            moment,
                            minutes,
                            activity,
                            location or str(getattr(current, "location", "") or ""),
                        )
                    except Exception as exc:
                        logger.warning(
                            "[模拟人生] 聊天日程写入失败 activity=%s: %s",
                            activity,
                            exc,
                        )
                    else:
                        plan_changed = True
                        schedule_inserted = True
                        chat_schedule_events.record_insert(
                            state,
                            umo=umo,
                            activity=activity,
                            kind="schedule",
                            now=now,
                        )
        if plan_changed:
            self.storage.plans[self.storage.plan_key(date_str, persona.id)] = plan
            await self.storage.save_plans()
        self.chat_schedule_state.save(state)
        logger.info(
            "[模拟人生] 聊天日程判定 umo=%s insert=%s food=%s activity=%s "
            "start=%s meal=%s dish=%s reason=%s",
            umo,
            schedule_inserted,
            food_applied,
            str(schedule_decision.get("activity") or "")[:40],
            str(schedule_decision.get("start") or ""),
            str(food_decision.get("meal") or ""),
            new_dish,
            str(schedule_decision.get("reason") or food_decision.get("reason") or "")[
                :60
            ],
        )
