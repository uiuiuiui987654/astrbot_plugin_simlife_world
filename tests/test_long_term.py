"""Long-term stages: validation, expanding one day, picking a stage, drafts and persistence."""

import asyncio
import tempfile
import unittest
from datetime import date
from pathlib import Path

from astrbot_plugin_simlife_world.core.long_term import LongTermTimelineStore, validate_stage, validate_stage_bundle

from tests.astrbot_stub import is_stubbed


def semester(**changes):
    stage = {
        "id": "semester-fall",
        "name": "秋季学期",
        "kind": "academic",
        "start_date": "2026-09-01",
        "end_date": "2027-01-20",
        "priority": 10,
        "summary": "正常上课并准备期末考试",
        "weekly_rules": [{"weekdays": [1], "start": "08:00", "end": "10:00", "title": "高等数学", "location": "教学楼"}],
        "special_dates": [{"date": "2026-09-07", "start": "08:00", "end": "11:00", "title": "开学典礼"}],
        "special_periods": [{"name": "期末周", "start_date": "2027-01-10", "end_date": "2027-01-20", "constraints": ["减少娱乐"]}],
        "milestones": [{"date": "2026-09-10", "title": "提交选课确认", "lead_days": 3}],
        "constraints": ["工作日保持学生作息"],
    }
    stage.update(changes)
    return stage


def bare(stage_id, name, start, end, **changes):
    return semester(id=stage_id, name=name, start_date=start, end_date=end, weekly_rules=[], special_dates=[], special_periods=[], milestones=[], **changes)


def store_with(*stages, directory="unused"):
    store = LongTermTimelineStore(Path(directory))
    store.stages = list(stages)
    return store


class Validation(unittest.TestCase):
    def test_normalised_stage(self):
        stage = validate_stage(semester(priority="42"), "student")
        self.assertEqual((stage["persona_id"], stage["kind"], stage["priority"]), ("student", "academic", 42))

    def test_refusals(self):
        empty_time = semester()
        empty_time["special_dates"][0]["start"] = ""
        for name, (value, message) in {
            "empty event time": (empty_time, "requires non-empty start and end"),
            "worded priority": (semester(priority="high"), "priority must be an integer"),
        }.items():
            with self.subTest(name), self.assertRaisesRegex(ValueError, message):
                validate_stage(value, "student")

    def test_bundle_must_be_continuous(self):
        winter = {"id": "winter-break", "name": "寒假", "kind": "academic", "start_date": "2027-01-22", "end_date": "2027-02-20"}
        with self.assertRaises(ValueError):  # one-day gap after 01-20
            validate_stage_bundle({"stages": [semester(), winter]}, "student")


class Queries(unittest.TestCase):
    def test_one_off_event_replaces_the_weekly_one(self):
        day = store_with(validate_stage(semester(), "student")).expand_day("student", date(2026, 9, 7))
        self.assertEqual([event["title"] for event in day["fixed_events"]], ["开学典礼"])
        self.assertEqual([item["title"] for item in day["milestones"]], ["提交选课确认"])

    def test_personas_do_not_share_stages(self):
        release = validate_stage(bare("release", "发布工期", "2026-09-01", "2026-10-01", kind="project", priority=20), "worker")
        store = store_with(validate_stage(semester(), "student"), release)
        self.assertEqual(store.active_stage("student", date(2026, 9, 10))["id"], "semester-fall")
        self.assertEqual(store.active_stage("worker", date(2026, 9, 10))["id"], "release")

    def test_resolving_a_stage(self):
        winter = validate_stage(bare("winter-break", "寒假", "2027-01-21", "2027-02-20"), "student")
        store = store_with(validate_stage(semester(), "student"), winter)
        cases = {
            (date(2026, 10, 1), ""): "semester-fall",  # current
            (date(2026, 8, 1), ""): "semester-fall",  # next
            (date(2027, 3, 1), ""): "winter-break",  # latest past
            (date(2026, 10, 1), "寒假"): "winter-break",
            (date(2026, 10, 1), "winter"): "winter-break",
        }
        for (day, query), expected in cases.items():
            with self.subTest(day=day, query=query):
                self.assertEqual(store.resolve_stage("student", day, query)[0]["id"], expected)

    def test_ambiguous_query_lists_candidates(self):
        spring = validate_stage(bare("semester-spring", "春季学期", "2027-01-21", "2027-06-30"), "student")
        stage, candidates = store_with(validate_stage(semester(), "student"), spring).resolve_stage("student", date(2026, 10, 1), "semester")
        self.assertIsNone(stage)
        self.assertEqual([item["id"] for item in candidates], ["semester-fall", "semester-spring"])

    @unittest.skipIf(is_stubbed("holidays") or is_stubbed("lunar_python"), "calendar libraries not installed")
    def test_festivals_show_up(self):
        stage = validate_stage(semester(), "student")
        store = store_with(stage)
        self.assertIn("中秋节", [item["name"] for item in store.with_holidays(stage)["holidays"]])
        self.assertIn("今日节日：中秋节", store.format_day_context("student", date(2026, 9, 25)))


class Persistence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def reload(self):
        store = LongTermTimelineStore(self.path)
        asyncio.run(store.load())
        return store

    def test_saved_stages_come_back(self):
        asyncio.run(store_with(validate_stage(semester(), "student"), directory=self.path).save())
        self.assertEqual(self.reload().find("student", "semester-fall")["name"], "秋季学期")

    def test_approving_a_draft_remembers_who_to_notify(self):
        store = LongTermTimelineStore(self.path)
        stages = validate_stage_bundle({"stages": [semester()]}, "student")
        asyncio.run(store.set_draft("student", stages, source="natural", admin_umo="admin", created_at="t", requirements="生成校历"))
        approved = asyncio.run(store.approve_draft("student", "admin"))
        restored = self.reload()
        self.assertEqual(approved[0]["id"], "semester-fall")
        self.assertIsNone(restored.get_draft("student"))
        self.assertEqual(restored.notification_target("student"), "admin")


if __name__ == "__main__":
    unittest.main()
