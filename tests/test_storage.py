"""Plans, sessions and admin requirements on disk."""

import asyncio
import tempfile
import unittest
from datetime import date
from pathlib import Path

from astrbot_plugin_simlife_world.core.models import DailyPlan, ScheduleRequirement, SessionState
from astrbot_plugin_simlife_world.core.storage import PluginStorage

from tests.fixtures import outfit_payload


def one_block_day(day="2026-07-14", persona="alice", theme="日常", outfit=True):
    return DailyPlan.from_dict(
        {
            "date": day,
            "persona_id": persona,
            "theme": theme,
            "mood": "平静",
            "outfit": outfit_payload() if outfit else None,
            "timeline": [{"id": "all", "start": "00:00", "end": "24:00", "activity": theme}],
        }
    )


def requirement(req_id, start, end, text="减少外出"):
    return ScheduleRequirement(id=req_id, persona_id="alice", start_date=start, end_date=end, requirement=text, created_at="2026-07-14T12:00:00+08:00")


class Storage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.storage = PluginStorage(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, *plans):
        for plan in plans:
            self.storage.plans[self.storage.plan_key(plan.date, plan.persona_id)] = plan

    def reloaded(self):
        asyncio.run(self.storage.save_plans())
        asyncio.run(self.storage.save_sessions())
        fresh = PluginStorage(Path(self.tmp.name))
        asyncio.run(fresh.load())
        return fresh

    def test_everything_survives_a_restart(self):
        self.put(one_block_day())
        self.storage.schedule_requirements["req"] = requirement("req", "2026-07-15", "2026-07-16")
        self.storage.sessions["umo"] = SessionState(date="2026-07-14", persona_id="alice", daily_budget=2)
        fresh = self.reloaded()
        self.assertEqual(fresh.get_plan("2026-07-14", "alice").theme, "日常")
        self.assertEqual(fresh.schedule_requirements["req"].requirement, "减少外出")
        self.assertEqual(fresh.sessions["umo"].daily_budget, 2)

    def test_schedule_without_outfit_survives(self):
        self.put(one_block_day(outfit=False))
        plan = self.reloaded().get_plan("2026-07-14", "alice")
        self.assertEqual((plan.has_schedule, plan.has_outfit), (True, False))

    def test_recent_plans_are_per_persona_and_chronological(self):
        self.put(
            one_block_day("2026-07-11", theme="太早"),
            one_block_day("2026-07-12", theme="前天"),
            one_block_day("2026-07-13", theme="昨天"),
            one_block_day("2026-07-13", "bob", "其他人格"),
        )
        self.assertEqual([plan.theme for plan in self.storage.get_recent_plans("alice", date(2026, 7, 14), 2)], ["前天", "昨天"])

    def test_unreadable_old_plan_is_dropped(self):
        old = {"date": "2026-07-14", "persona_id": "alice", "theme": "旧日程", "mood": "平静", "outfit": "旧版字符串穿搭", "timeline": []}
        asyncio.run(self.storage.plans_repo.save({"schema_version": 1, "plans": {"2026-07-14::alice": old}}))
        asyncio.run(self.storage.load())
        self.assertEqual(self.storage.plans, {})


class Requirements(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.storage = PluginStorage(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def active(self, persona, day):
        return [item.id for item in self.storage.active_schedule_requirements(persona, day)]

    def test_used_up_one_day_at_a_time(self):
        self.storage.schedule_requirements["req"] = requirement("req", "2026-07-15", "2026-07-16")
        self.assertEqual((self.active("alice", date(2026, 7, 15)), self.active("bob", date(2026, 7, 15))), (["req"], []))
        self.assertEqual(self.storage.consume_schedule_requirements(["req"], date(2026, 7, 15)), 1)
        self.assertEqual((self.active("alice", date(2026, 7, 15)), self.active("alice", date(2026, 7, 16))), ([], ["req"]))
        self.storage.consume_schedule_requirements(["req"], date(2026, 7, 16))
        self.assertNotIn("req", self.storage.schedule_requirements)

    def test_expired_ones_are_pruned(self):
        self.storage.schedule_requirements.update(
            expired=requirement("expired", "2026-07-14", "2026-07-14", "旧要求"),
            current=requirement("current", "2026-07-15", "2026-07-15", "今日要求"),
        )
        self.assertEqual(self.storage.prune_schedule_requirements(date(2026, 7, 15)), 1)
        self.assertEqual(set(self.storage.schedule_requirements), {"current"})


if __name__ == "__main__":
    unittest.main()
