"""World events and the weekly / monthly report."""

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from astrbot_plugin_simlife_world.core import affection, diary, money, mood_history, weekly, world_events

NOW = datetime(2026, 11, 10, 21, 0)


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class WorldEventTests(StoreTestCase):
    def test_event_is_stable_per_day(self):
        first = world_events.get_or_create(self.data_dir, "p", "2026-11-10")
        again = world_events.get_or_create(self.data_dir, "p", "2026-11-10")
        self.assertTrue(first["created"])
        self.assertFalse(again["created"])
        self.assertEqual(first["title"], again["title"])
        self.assertEqual(world_events.recent(self.data_dir, "p", "2026-11-10")["title"], first["title"])

    def test_no_repeats_within_two_weeks(self):
        start = datetime(2026, 1, 1)
        titles = [
            world_events.get_or_create(self.data_dir, "p", (start + timedelta(days=day)).date().isoformat())["title"]
            for day in range(world_events.RECENT_AVOID_DAYS + 1)
        ]
        self.assertEqual(len(titles), len(set(titles)))

    def test_reroll_always_changes_event(self):
        day = "2026-11-10"
        seen = [world_events.get_or_create(self.data_dir, "p", day)["title"]]
        for _ in range(5):
            seen.append(world_events.reroll(self.data_dir, "p", day)["title"])
        for previous, current in zip(seen, seen[1:]):
            self.assertNotEqual(previous, current)

    def test_list_recent_sorted(self):
        for day in ("2026-11-08", "2026-11-10", "2026-11-09"):
            world_events.get_or_create(self.data_dir, "p", day)
        self.assertEqual([entry["date"] for entry in world_events.list_recent(self.data_dir, "p", 2)], ["2026-11-10", "2026-11-09"])

    def test_event_catalog_is_well_formed(self):
        titles = [event[0] for event in world_events.EVENTS]
        self.assertEqual(len(titles), len(set(titles)))
        for title, summary, mood in world_events.EVENTS:
            self.assertTrue(title and summary)
            self.assertIsInstance(mood, int)


class WeeklyReportTests(StoreTestCase):
    def test_report_aggregates_the_week(self):
        in_week = NOW - timedelta(days=2)
        too_old = NOW - timedelta(days=9)
        money.add(self.data_dir, "p", 100, "工资", kind="work", at=in_week)
        money.add(self.data_dir, "p", 50, "主人给的", kind="master", at=in_week)
        money.spend(self.data_dir, "p", 30, "零食", kind="purchase", at=in_week)
        money.add(self.data_dir, "p", 999, "旧", kind="work", at=too_old)
        money.add_possession(self.data_dir, "p", {"name": "奶茶", "price": 15}, at=in_week)
        money.add_possession(self.data_dir, "p", {"name": "奶茶", "price": 15}, at=in_week)
        diary.add_entry(self.data_dir, "p", in_week.date().isoformat(), "忙碌", "工作 120 分钟，又工作 30 分钟", now=in_week)
        diary.add_entry(self.data_dir, "p", too_old.date().isoformat(), "旧", "工作 999 分钟", now=too_old)
        affection.add(self.data_dir, "p", 10, "聊天", now=in_week)
        mood_history.record(self.data_dir, "p", {"mood": 60, "energy": 40}, now=in_week)
        mood_history.record(self.data_dir, "p", {"mood": 80, "energy": 60}, now=NOW)

        report = weekly.build(self.data_dir, "p", now=NOW)
        self.assertEqual((report["start"], report["end"]), ("2026-11-04", "2026-11-10"))
        self.assertEqual((report["income"], report["expense"], report["net"]), (150.0, 30.0, 120.0))
        self.assertEqual(report["work_minutes"], 150)
        self.assertEqual(report["diary_count"], 1)
        self.assertEqual(report["affection_gained"], 10)
        self.assertEqual((report["mood_average"], report["energy_average"]), (70.0, 50.0))
        self.assertEqual(report["top_goods"], [{"name": "奶茶", "count": 2, "amount": 30.0}])
        self.assertEqual(report["income_categories"][0], {"label": "工作", "amount": 100.0})

        text = weekly.format_report(report)
        self.assertTrue(text.startswith("生活周报 · 2026-11-04 至 2026-11-10"))
        self.assertIn("收入 150 元，支出 30 元", text)
        self.assertIn("工作：150 分钟。", text)

    def test_month_report_sees_more_than_ten_purchases(self):
        for index in range(14):
            money.add_possession(self.data_dir, "p", {"name": f"物品{index}", "price": 1}, at=NOW - timedelta(days=index))
        report = weekly.build(self.data_dir, "p", now=NOW, days=30)
        self.assertEqual(sum(item["count"] for item in report["top_goods"][:6]), 6)
        self.assertEqual(len(report["purchases"]), 12)

    def test_titles_by_span(self):
        empty = weekly.build(self.data_dir, "p", now=NOW, days=30)
        self.assertTrue(weekly.format_report(empty).startswith("生活月报"))
        self.assertTrue(weekly.format_report(weekly.build(self.data_dir, "p", now=NOW, days=365)).startswith("年度总结"))
        self.assertEqual(empty["moods"], [])


if __name__ == "__main__":
    unittest.main()
