"""Affection, diary and mood history."""

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from astrbot_plugin_simlife_world.core import affection, diary, mood_history

DAY1 = datetime(2026, 11, 10, 12, 0)


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class AffectionTests(StoreTestCase):
    def test_fresh_snapshot(self):
        info = affection.snapshot(self.data_dir, "p", now=DAY1)
        self.assertEqual((info["score"], info["level"], info["next_score"]), (0, "陌生", 100))
        self.assertEqual((info["days_known"], info["nickname"], info["daily_remaining"]), (1, "主人", affection.DAILY_CAP))

    def test_daily_cap_resets_next_day(self):
        affection.add(self.data_dir, "p", 15, "聊天", now=DAY1)
        info = affection.add(self.data_dir, "p", 15, "送礼", now=DAY1)
        self.assertEqual((info["score"], info["daily_remaining"]), (20, 0))
        self.assertEqual(affection.add(self.data_dir, "p", 5, "x", now=DAY1)["score"], 20)
        self.assertEqual([event["points"] for event in info["events"]], [15, 5])

        info = affection.add(self.data_dir, "p", 5, "第二天", now=DAY1 + timedelta(days=1))
        self.assertEqual((info["score"], info["daily_points"]), (25, 5))

    def test_non_positive_points_are_ignored(self):
        affection.add(self.data_dir, "p", -50, "吵架", now=DAY1)
        self.assertFalse((self.data_dir / "affection.json").exists())

    def test_level_up_records_milestone(self):
        for day in range(5):
            info = affection.add(self.data_dir, "p", 20, "陪伴", now=DAY1 + timedelta(days=day))
        self.assertEqual((info["score"], info["level"]), (100, "眼熟"))
        self.assertEqual([item["level"] for item in info["milestones"]], ["眼熟"])
        self.assertEqual(info["next_score"], 250)

    def test_days_known_and_anniversaries(self):
        affection.add(self.data_dir, "p", 1, "初见", now=DAY1)
        info = affection.snapshot(self.data_dir, "p", now=DAY1 + timedelta(days=6))
        self.assertEqual((info["days_known"], info["is_anniversary"]), (7, True))
        self.assertEqual(info["next_anniversary"], 30)
        self.assertEqual(affection.next_anniversary(800), None)

    def test_nickname(self):
        self.assertFalse(affection.set_nickname(self.data_dir, "p", "  ")["ok"])
        self.assertEqual(affection.set_nickname(self.data_dir, "p", "小笨蛋小笨蛋小笨蛋！", now=DAY1)["nickname"], "小笨蛋小笨蛋小笨蛋！")
        self.assertEqual(len(affection.set_nickname(self.data_dir, "p", "一" * 30, now=DAY1)["nickname"]), 12)
        self.assertIn("称呼：" + "一" * 12, affection.format_status(self.data_dir, "p"))


class DiaryTests(StoreTestCase):
    def test_auto_entry_replaces_same_day_manual_appends(self):
        diary.add_entry(self.data_dir, "p", "2026-11-10", "初稿", "a", now=DAY1)
        diary.add_entry(self.data_dir, "p", "2026-11-10", "终稿", "b", now=DAY1)
        diary.add_entry(self.data_dir, "p", "2026-11-10", "手写", "c", source="manual", now=DAY1)
        diary.add_entry(self.data_dir, "p", "2026-11-10", "手写2", "d", source="manual", now=DAY1)
        titles = [entry["title"] for entry in diary.list_entries(self.data_dir, "p")]
        self.assertEqual(titles, ["终稿", "手写", "手写2"])
        self.assertTrue(diary.has_entry(self.data_dir, "p", "2026-11-10", "manual"))
        self.assertFalse(diary.has_entry(self.data_dir, "p", "2026-11-11", "auto"))

    def test_entries_are_capped_and_truncated(self):
        for day in range(diary.MAX_ENTRIES + 5):
            diary.add_entry(self.data_dir, "p", f"d{day:03d}", "t", "x" * 2000, now=DAY1)
        entries = diary.list_entries(self.data_dir, "p", limit=1000)
        self.assertEqual(len(entries), diary.MAX_ENTRIES)
        self.assertEqual(entries[0]["date"], "d005")
        self.assertEqual(len(entries[-1]["summary"]), 1200)

    def test_format(self):
        self.assertEqual(diary.format_entries([]), "还没有写日记。")
        entry = diary.add_entry(self.data_dir, "p", "", "", "内容", now=DAY1)
        self.assertEqual((entry["date"], entry["title"]), ("2026-11-10", "这天"))
        self.assertIn("2026-11-10  这天\n内容", diary.format_entries([entry]))


class MoodHistoryTests(StoreTestCase):
    def test_one_entry_per_day_with_write_gap(self):
        needs = {"mood": 60, "energy": 70.04, "willingness": 9, "label": "x"}
        first = mood_history.record(self.data_dir, "p", needs, now=DAY1)
        self.assertEqual(first["entry"], {"date": "2026-11-10", "at": "2026-11-10T12:00:00", "mood": 60.0, "energy": 70.0})
        self.assertTrue(mood_history.record(self.data_dir, "p", {"mood": 10}, now=DAY1 + timedelta(minutes=5))["skipped"])
        mood_history.record(self.data_dir, "p", {"mood": 10}, now=DAY1 + timedelta(minutes=15))
        mood_history.record(self.data_dir, "p", {"mood": 30}, now=DAY1 + timedelta(days=1))
        entries = mood_history.list_entries(self.data_dir, "p")
        self.assertEqual([(entry["date"], entry["mood"]) for entry in entries], [("2026-11-10", 10.0), ("2026-11-11", 30.0)])
        self.assertEqual(len(mood_history.between(self.data_dir, "p", "2026-11-11", "2026-11-30")), 1)

    def test_rejects_empty_needs(self):
        self.assertFalse(mood_history.record(self.data_dir, "p", {})["ok"])
        self.assertFalse(mood_history.record(self.data_dir, "p", {"mood": "高"})["ok"])


if __name__ == "__main__":
    unittest.main()
