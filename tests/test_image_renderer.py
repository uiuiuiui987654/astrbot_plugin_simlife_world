"""The data handed to the card template, and caching of stage cards."""

import asyncio
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from astrbot_plugin_simlife_world.core.image_renderer import ScheduleImageRenderer
from astrbot_plugin_simlife_world.core.models import DailyPlan

from tests.fixtures import outfit_payload

HALF_NINE = datetime(2026, 7, 14, 9, 30)
LIBRARY_DAY = DailyPlan.from_dict(
    {
        "date": "2026-07-14",
        "persona_id": "Caranlaf",
        "theme": "学习日",
        "mood": "专注",
        "outfit": outfit_payload("夏季学院风"),
        "timeline": [
            {"id": "sleep", "start": "00:00", "end": "08:00", "activity": "睡觉", "state": "sleep", "availability": "blocked"},
            {"id": "study", "start": "08:00", "end": "24:00", "activity": "学习", "location": "图书馆", "state": "focus", "availability": "low"},
        ],
    }
)
SEMESTER = {
    "id": "semester",
    "name": "秋季学期",
    "kind": "academic",
    "start_date": "2026-09-01",
    "end_date": "2027-01-20",
    "priority": 50,
    "summary": "正常上课",
    "weekly_rules": [{"weekdays": [2], "start": "18:00", "end": "20:00", "title": "社团例会", "location": "活动室", "participants": ["社员"], "required": True}],
    "special_dates": [],
    "holidays": [{"date": "2026-09-25", "name": "中秋节", "kind": "traditional"}],
    "special_periods": [],
    "milestones": [],
    "constraints": [],
}


class Cards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    async def fake_render(self, template, data, return_url, options):
        self.calls.append((data, options))
        path = self.root / f"render-{len(self.calls)}.png"
        path.write_bytes(b"image")
        return str(path)

    def render(self, method, *args, settings=None):
        """Call a renderer method synchronously."""
        renderer = ScheduleImageRenderer(self.root, self.fake_render, settings)
        return asyncio.run(getattr(renderer, method)(*args))

    def test_timeline_card(self):
        stage_day = {
            "stage": {"name": "暑期学习阶段", "kind": "academic", "start_date": "2026-07-01", "end_date": "2026-08-31", "summary": "集中学习"},
            "active_periods": [{"name": "考试周", "start_date": "2026-07-13", "end_date": "2026-07-19", "constraints": ["减少娱乐", "保证睡眠"]}],
            "holidays": [{"date": "2026-07-14", "name": "纪念日", "kind": "public"}],
        }
        self.assertTrue(Path(self.render("render_timeline", LIBRARY_DAY, HALF_NINE, stage_day)).exists())
        data, options = self.calls[0]
        self.assertEqual([item["current"] for item in data["items"]], [False, True])
        self.assertEqual(
            (data["status_label"], data["theme_text"], data["mood"], data["current_stage"]["name"]),
            ("当前时段 08:00–24:00", "学习日", "专注", "暑期学习阶段"),
        )
        self.assertEqual(data["active_periods"][0]["constraints_text"], "减少娱乐；保证睡眠")
        self.assertEqual(data["today_holidays"][0]["name"], "纪念日")
        self.assertEqual(options["type"], "png")

    def test_timeline_card_without_stage(self):
        self.render("render_timeline", LIBRARY_DAY, HALF_NINE, {"stage": None, "active_periods": [], "holidays": []})
        data, _ = self.calls[0]
        self.assertEqual((data["current_stage"], data["active_periods"], data["today_holidays"]), (None, [], []))

    def test_outfit_card(self):
        self.render("render_outfit", LIBRARY_DAY, HALF_NINE)
        data, _ = self.calls[0]
        self.assertEqual((data["outfit_style"], data["has_schedule"], data["theme_text"], data["mood"]), ("日常休闲风", True, "学习日", "专注"))
        self.assertEqual([item["label"] for item in data["outfit_items"][1:3]], ["内衣与打底", "内裤"])

    def test_stage_card_is_cached(self):
        first = self.render("render_stage", SEMESTER, "Caranlaf")
        self.assertEqual(self.render("render_stage", SEMESTER, "Caranlaf"), first)
        self.assertEqual(len(self.calls), 1)
        stage = self.calls[0][0]["stage"]
        self.assertEqual((stage["weekly_rules"][0]["weekday_text"], stage["holidays"][0]["name"]), ("周二", "中秋节"))

    def test_stage_overview_and_look_settings(self):
        self.render("render_stage_list", [SEMESTER], "Caranlaf", settings={"image_theme": "light", "image_width": 900})
        data, _ = self.calls[0]
        self.assertEqual((data["theme"], data["width"], data["stages"][0]["left"], data["stages"][0]["width"]), ("light", 900, 0.0, 100.0))


if __name__ == "__main__":
    unittest.main()
