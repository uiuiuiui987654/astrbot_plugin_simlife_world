"""Loop bookkeeping, conversation activity and agent-busy tracking.

Mixin for ProactiveVirtualDailyPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import replace
from datetime import datetime

from astrbot.api import logger
from astrbot.core.utils.session_lock import session_lock_manager

from .. import (
    money,
    timeline_rules,
    wardrobe,
)
from ..utils import (
    now_in,
)


class RuntimeStateMixin:
    async def _cancel_stale_loops(self) -> None:
        """热重载可能留下旧实例的后台循环，启动时按协程归属清理。"""
        current = asyncio.current_task()
        stale: list[asyncio.Task] = []
        for task in asyncio.all_tasks():
            if task is current or task.done():
                continue
            coro = task.get_coro()
            qualname = getattr(coro, "__qualname__", "")
            if not qualname.endswith(("_interaction_loop", "_decision_loop")):
                continue
            task.cancel()
            stale.append(task)
        if stale:
            await asyncio.gather(*stale, return_exceptions=True)
            logger.info("[虚拟人生] 清理旧实例遗留循环 %s 个", len(stale))

    async def _normalize_loaded_timelines(self) -> None:
        """启动时修正历史数据：多站行程、旧版强制女仆装、旧摆位坐标。"""
        changed = 0
        if money.backfill_placements(self.data_dir):
            changed += 1
        for key, plan in list(self.storage.plans.items()):
            updated = timeline_rules.split_plan_timeline(plan.timeline)
            migrated_outfit = wardrobe.migrate_legacy_forced_outfit(plan.outfit)
            if updated == plan.timeline and migrated_outfit is plan.outfit:
                continue
            self.storage.plans[key] = replace(
                plan,
                timeline=updated,
                outfit=migrated_outfit,
            )
            changed += 1
        if changed:
            await self.storage.save_plans()
            logger.info("[虚拟人生] 启动时规范化历史日程/穿搭 %s 条", changed)

    @staticmethod
    def _umo_hash(umo: str) -> str:
        return hashlib.sha1(umo.encode("utf-8")).hexdigest()[:12]

    def _now(self) -> datetime:
        return now_in(self.timezone)

    def _daily_generation_flags(self) -> tuple[bool, bool]:
        settings = self.config.get("schedule_settings", {}) or {}
        return (
            bool(settings.get("daily_schedule_generation_enable", True)),
            bool(settings.get("daily_outfit_generation_enable", True)),
        )

    def _mark_conversation_activity(
        self, umo: str, moment: datetime | None = None
    ) -> int:
        generation = self._conversation_generations.get(umo, 0) + 1
        self._conversation_generations[umo] = generation
        self._conversation_activity_at[umo] = moment or self._now()
        return generation

    def _conversation_generation(self, umo: str) -> int:
        return self._conversation_generations.get(umo, 0)

    def _agent_is_active(self, umo: str) -> bool:
        return self._active_agent_counts.get(umo, 0) > 0

    def _proactive_context_is_current(self, umo: str, generation: int) -> bool:
        return (
            not self._agent_is_active(umo)
            and self._conversation_generation(umo) == generation
        )

    def _window_is_idle_enough(self, umo: str, now: datetime) -> bool:
        activity_at = self._conversation_activity_at.get(umo)
        if activity_at is None:
            return True
        delivery = self.config.get("delivery_settings", {}) or {}
        minimum = max(0, int(delivery.get("minimum_idle_for_window_minutes", 20)))
        return (now - activity_at).total_seconds() >= minimum * 60

    async def _release_agent_after_history_save(self, umo: str) -> None:
        history_saved = False
        try:
            async with session_lock_manager.acquire_lock(umo):
                history_saved = True
        finally:
            count = self._active_agent_counts.get(umo, 0)
            if count <= 1:
                self._active_agent_counts.pop(umo, None)
                if history_saved:
                    self._mark_conversation_activity(umo)
                    self._schedule_idle(umo)
            else:
                self._active_agent_counts[umo] = count - 1
