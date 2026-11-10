"""Timeline lookups, text summaries and the date-range syntax used by commands."""

import unittest
from dataclasses import replace
from datetime import date, datetime
from zoneinfo import ZoneInfo

from astrbot_plugin_simlife_world.core.models import DailyPlan
from astrbot_plugin_simlife_world.core.utils import (
    format_outfit,
    format_plan,
    format_timeline,
    next_available_at,
    parse_schedule_date_range,
    timeline_item_at,
)

from tests.fixtures import outfit_payload

NINE_AM = datetime(2026, 7, 14, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
PLAN = DailyPlan.from_dict(
    {
        "date": "2026-07-14",
        "persona_id": "alice",
        "theme": "日常",
        "mood": "平静",
        "outfit": outfit_payload(),
        "timeline": [
            {"id": "sleep", "start": "00:00", "end": "08:00", "activity": "睡觉", "state": "sleep", "availability": "blocked"},
            {"id": "busy", "start": "08:00", "end": "12:00", "activity": "工作", "state": "focus", "availability": "low"},
            {"id": "free", "start": "12:00", "end": "24:00", "activity": "休息", "availability": "high"},
        ],
    }
)
STAGE_DAY = {
    "stage": {"name": "暑期阶段", "start_date": "2026-07-01", "end_date": "2026-08-31"},
    "active_periods": [{"name": "考试周", "start_date": "2026-07-13", "end_date": "2026-07-19", "constraints": ["减少娱乐"]}],
    "holidays": [{"name": "纪念日"}],
}


class TimelineLookups(unittest.TestCase):
    def test_now_and_next_free(self):
        self.assertEqual(timeline_item_at(PLAN, NINE_AM).id, "busy")
        self.assertEqual(next_available_at(PLAN, NINE_AM).hour, 12)


class TextSummaries(unittest.TestCase):
    def assert_mentions(self, text, present=(), absent=()):
        for needle in present:
            self.assertIn(needle, text)
        for needle in absent:
            self.assertNotIn(needle, text)

    def test_timeline_view(self):
        self.assert_mentions(
            format_timeline(PLAN, NINE_AM, STAGE_DAY),
            present=("当前时段：08:00-12:00", "今日主题：日常", "心情状态：平静", "所处阶段：暑期阶段", "特殊时期：考试周", "今日节日：纪念日"),
            absent=("穿搭风格",),
        )
        empty_stage = {"stage": None, "active_periods": [], "holidays": []}
        self.assertIn("所处阶段：不在任何长期阶段里", format_timeline(PLAN, NINE_AM, empty_stage))

    def test_outfit_view(self):
        self.assert_mentions(format_outfit(PLAN), present=("穿搭风格：日常休闲风", "今日主题：日常", "今日心情：平静"), absent=("今天的时间线",))

    def test_plan_view_shows_only_present_halves(self):
        self.assert_mentions(format_plan(replace(PLAN, outfit=None)), present=("日程：",), absent=("穿搭：", "当前大时间段"))
        outfit_only = replace(PLAN, theme="", mood="", timeline=(), proactive_windows=())
        self.assert_mentions(format_plan(outfit_only), present=("穿搭风格：",), absent=("今日主题", "今日日程"))


class DateRanges(unittest.TestCase):
    def test_parsing(self):
        reference = date(2026, 7, 27)
        cases = {
            "2026-08-03": (date(2026, 8, 3), date(2026, 8, 3)),
            "8-3": (date(2026, 8, 3), date(2026, 8, 3)),
            "29": (date(2026, 7, 29), date(2026, 7, 29)),
            "29..2": (date(2026, 7, 29), date(2026, 8, 2)),  # end rolls into next month
            "12-29..1-2": (date(2026, 12, 29), date(2027, 1, 2)),  # ... or next year
            "2026-12-29..2": (date(2026, 12, 29), date(2027, 1, 2)),
        }
        for text, expected in cases.items():
            with self.subTest(text):
                self.assertEqual(parse_schedule_date_range(text, reference), expected)

    def test_explicit_backwards_range_is_refused(self):
        with self.assertRaisesRegex(ValueError, "结束日期在开始日期之前"):
            parse_schedule_date_range("2026-08-03..2026-08-02", date(2026, 7, 27))


if __name__ == "__main__":
    unittest.main()
