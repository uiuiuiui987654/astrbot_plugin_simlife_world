"""plans.json (daily plans + schedule requirements) and sessions.json."""

from __future__ import annotations

import asyncio
import copy
import json
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .jsonio import atomic_write_json
from .models import DailyPlan, ScheduleRequirement, SessionState

PLANS_VERSION = 3
SESSIONS_VERSION = 1


class JsonRepository:
    """One JSON object on disk; a missing or unreadable file reads as ``default``."""

    def __init__(self, path: Path, default: dict[str, Any]):
        self.path = path
        self.default = default
        self.lock = asyncio.Lock()

    def _read(self) -> dict[str, Any]:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            value = None
        return value if isinstance(value, dict) else copy.deepcopy(self.default)

    async def load(self) -> dict[str, Any]:
        async with self.lock:
            if not self.path.exists():
                return copy.deepcopy(self.default)
            return await asyncio.to_thread(self._read)

    async def save(self, value: dict[str, Any]) -> None:
        async with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(atomic_write_json, self.path, value)


def _parse_all(raw: dict[str, Any], parse, errors: tuple[type[Exception], ...]) -> dict[str, Any]:
    """Parse every value, silently skipping entries that no longer validate."""
    parsed = {}
    for key, value in raw.items():
        try:
            parsed[key] = parse(value)
        except errors:
            continue
    return parsed


class PluginStorage:
    def __init__(self, data_dir: Path):
        self.plans_repo = JsonRepository(
            data_dir / "plans.json", {"schema_version": PLANS_VERSION, "plans": {}, "schedule_requirements": {}}
        )
        self.sessions_repo = JsonRepository(data_dir / "sessions.json", {"schema_version": SESSIONS_VERSION, "sessions": {}})
        self.plans: dict[str, DailyPlan] = {}
        self.schedule_requirements: dict[str, ScheduleRequirement] = {}
        self.sessions: dict[str, SessionState] = {}

    async def load(self) -> None:
        stored_plans = await self.plans_repo.load()
        stored_sessions = await self.sessions_repo.load()
        self.plans = _parse_all(stored_plans.get("plans", {}), DailyPlan.from_dict, (KeyError, TypeError, ValueError))
        requirements = _parse_all(
            stored_plans.get("schedule_requirements", {}), ScheduleRequirement.from_dict, (TypeError, ValueError)
        )
        self.schedule_requirements = {item.id: item for item in requirements.values()}
        self.sessions = {key: SessionState.from_dict(value) for key, value in stored_sessions.get("sessions", {}).items()}

    # ------------------------------------------------------------------ plans

    @staticmethod
    def plan_key(date_str: str, persona_id: str) -> str:
        return f"{date_str}::{persona_id}"

    def get_plan(self, date_str: str, persona_id: str) -> DailyPlan | None:
        return self.plans.get(self.plan_key(date_str, persona_id))

    def get_recent_plans(self, persona_id: str, before: date, days: int) -> list[DailyPlan]:
        """Successful plans of the ``days`` days before ``before``, oldest first."""
        found = (self.get_plan((before - timedelta(days=back)).isoformat(), persona_id) for back in range(max(0, days), 0, -1))
        return [plan for plan in found if plan and plan.status == "ok"]

    # ------------------------------------------------------- schedule requirements

    @staticmethod
    def _covers(item: ScheduleRequirement, day: str) -> bool:
        return item.start_date <= day <= item.end_date and day not in item.consumed_dates

    def active_schedule_requirements(self, persona_id: str, target: date) -> list[ScheduleRequirement]:
        day = target.isoformat()
        matching = [item for item in self.schedule_requirements.values() if item.persona_id == persona_id and self._covers(item, day)]
        return sorted(matching, key=lambda item: (item.created_at, item.id))

    def consume_schedule_requirements(self, requirement_ids: list[str], target: date) -> int:
        """Mark ``target`` as used; a requirement used on every day of its range is removed."""
        day, used = target.isoformat(), 0
        for requirement_id in requirement_ids:
            item = self.schedule_requirements.get(requirement_id)
            if item is None or not self._covers(item, day):
                continue
            consumed = tuple(sorted((*item.consumed_dates, day)))
            span = (date.fromisoformat(item.end_date) - date.fromisoformat(item.start_date)).days + 1
            if len(consumed) >= span:
                del self.schedule_requirements[requirement_id]
            else:
                self.schedule_requirements[requirement_id] = replace(item, consumed_dates=consumed)
            used += 1
        return used

    def prune_schedule_requirements(self, today: date) -> int:
        expired = [key for key, item in self.schedule_requirements.items() if date.fromisoformat(item.end_date) < today]
        for key in expired:
            del self.schedule_requirements[key]
        return len(expired)

    # ------------------------------------------------------------------ saving

    async def save_plans(self) -> None:
        await self.plans_repo.save(
            {
                "schema_version": PLANS_VERSION,
                "plans": {key: plan.to_dict() for key, plan in self.plans.items()},
                "schedule_requirements": {key: item.to_dict() for key, item in self.schedule_requirements.items()},
            }
        )

    async def save_sessions(self) -> None:
        await self.sessions_repo.save(
            {"schema_version": SESSIONS_VERSION, "sessions": {key: state.to_dict() for key, state in self.sessions.items()}}
        )
