"""Admin "日程要求": wishes for future days, checked before they are stored."""

import asyncio
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from astrbot_plugin_simlife_world.core.mixins.planning import PlanningMixin
from astrbot_plugin_simlife_world.core.models import DailyPlan
from astrbot_plugin_simlife_world.core.storage import PluginStorage

from tests.fixtures import life_timeline

TZ = ZoneInfo("Asia/Shanghai")
NOW = datetime(2026, 7, 14, 10, 0, tzinfo=TZ)


class Personas:
    async def resolve(self, umo):
        return SimpleNamespace(id="alice", prompt="")


class Host(PlanningMixin):
    def __init__(self, data_dir: Path):
        self.storage = PluginStorage(data_dir)
        self.personas = Personas()

    def _now(self):
        return NOW


def event(admin=True):
    return SimpleNamespace(is_admin=lambda: admin, unified_msg_origin="qq:FriendMessage:1")


class ScheduleRequirementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.host = Host(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, span, text="去图书馆", *, admin=True):
        return asyncio.run(self.host._add_schedule_requirement(event(admin), span, text))

    def test_stores_a_future_range(self):
        reply = self.add("2026-07-20..2026-07-22")
        self.assertIn("2026-07-20..2026-07-22", reply)
        (stored,) = self.host.storage.schedule_requirements.values()
        self.assertEqual((stored.start_date, stored.end_date, stored.requirement), ("2026-07-20", "2026-07-22", "去图书馆"))

    def test_single_day_is_shown_once(self):
        self.assertIn("要求：2026-07-20。", self.add("07-20"))

    def test_rejections(self):
        cases = {
            "only admins": ({"span": "07-20", "admin": False}, "无权限"),
            "today": ({"span": "07-14"}, "今天之后"),
            "too long": ({"span": "2026-07-20..2027-07-21"}, "366"),
            "empty": ({"span": "07-20", "text": "  "}, "不能为空"),
            "too wordy": ({"span": "07-20", "text": "很" * 501}, "500"),
            "bad date": ({"span": "07-40"}, "无法添加"),
        }
        for name, (kwargs, expected) in cases.items():
            with self.subTest(name):
                span = kwargs.pop("span")
                self.assertIn(expected, self.add(span, **kwargs))
        self.assertEqual(self.host.storage.schedule_requirements, {})

    def test_day_with_a_plan_or_ten_wishes_is_full(self):
        planned = DailyPlan.from_dict({"date": "2026-07-21", "persona_id": "alice", "timeline": life_timeline()})
        self.host.storage.plans[self.host.storage.plan_key("2026-07-21", "alice")] = planned
        self.assertIn("已有有效日程", self.add("07-20..07-22"))
        for number in range(10):
            self.add("07-25", f"要求{number}")
        self.assertIn("已有 10 条", self.add("07-25"))
        self.assertEqual(len(self.host.storage.schedule_requirements), 10)


if __name__ == "__main__":
    unittest.main()
