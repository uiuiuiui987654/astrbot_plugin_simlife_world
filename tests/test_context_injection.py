"""Which pieces of her state reach the chat prompt, by keyword, and within the size limit."""

import json
import unittest
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from astrbot_plugin_simlife_world.core.context_injection import SmartContextInjector
from astrbot_plugin_simlife_world.core.long_term import LongTermTimelineStore, validate_stage
from astrbot_plugin_simlife_world.core.models import DailyPlan

from tests.fixtures import outfit_payload

NOW = datetime(2026, 7, 15, 9, 30)
SHIPPED = {
    key: value["default"]
    for key, value in json.loads(Path(__file__).resolve().parents[1].joinpath("_conf_schema.json").read_text(encoding="utf-8"))[
        "smart_context_injection"
    ]["items"].items()
    if "default" in value
}
STUDY_DAY = DailyPlan.from_dict(
    {
        "date": "2026-07-15",
        "persona_id": "alice",
        "theme": "学习日",
        "mood": "专注",
        "outfit": outfit_payload("清爽学院风"),
        "timeline": [
            {"id": "sleep", "start": "00:00", "end": "08:00", "activity": "睡觉", "state": "sleep", "availability": "blocked"},
            {"id": "study", "start": "08:00", "end": "12:00", "activity": "自习", "location": "图书馆", "state": "focus", "availability": "low"},
            {"id": "free", "start": "12:00", "end": "24:00", "activity": "午后安排"},
        ],
    }
)
SEMESTER = validate_stage(
    {
        "id": "semester",
        "name": "秋季学期",
        "kind": "academic",
        "start_date": "2026-07-01",
        "end_date": "2026-12-31",
        "priority": 50,
        "summary": "正常上课",
        "milestones": [{"date": "2026-07-18", "title": "提交作业", "lead_days": 1}],
        "constraints": ["工作日优先学习"],
    },
    "alice",
)


def store():
    long_term = LongTermTimelineStore(Path("unused"))
    long_term.stages = [SEMESTER]
    return long_term


def injector(**settings):
    return SmartContextInjector({**SHIPPED, **settings})


def ask(question, plan=STUDY_DAY, **settings):
    return injector(**settings).build(plan, NOW, store(), question)


class ChatInjection(unittest.TestCase):
    def check(self, text, present=(), absent=()):
        for needle in present:
            self.assertIn(needle, text)
        for needle in absent:
            self.assertNotIn(needle, text)

    def test_base_module(self):
        self.check(ask("你好！"), absent=("当前活动：自习",))  # off by default
        self.check(ask("你好！", base_module_enable=True), present=("当前活动：自习",), absent=("今日穿搭：", "当前大时间表阶段"))

    def test_outfit_and_underwear(self):
        self.check(ask("今天穿什么？"), present=("今日穿搭", "白色短袖衬衫"), absent=("浅色无痕内衣", "浅色无痕内裤"))
        self.check(ask("内衣怎么搭？"), present=("浅色无痕内衣", "浅色无痕内裤"))
        outfit_only = replace(STUDY_DAY, theme="", mood="", timeline=(), proactive_windows=())
        self.check(ask("今天穿什么？", outfit_only), present=("今日穿搭",), absent=("当前活动",))
        self.check(ask("今天穿什么，在干嘛？", replace(STUDY_DAY, outfit=None)), present=("当前活动：自习",), absent=("今日穿搭：",))

    def test_schedule_and_long_term(self):
        self.check(
            ask("考试前我几点有空？"),
            present=("上个时段：00:00-08:00 睡觉", "下个时段：12:00-24:00 午后安排", "所处长期阶段：秋季学期", "近期里程碑：2026-07-18 提交作业"),
        )
        self.check(ask("在干嘛？"), present=("时间：2026-07-15 09:30", "当前活动：自习", "地点：图书馆", "状态：focus，可打扰度：low"))
        self.assertEqual(ask("在干嘛？", base_module_enable=True).count("当前活动：自习"), 1)

    def test_full_queries_point_at_tools(self):
        self.check(ask("给我完整大时间表"), present=("get_long_term_timeline",))
        self.check(ask("给我完整日程"), present=("get_virtual_daily_schedule",), absent=("get_long_term_timeline",))

    def test_module_report(self):
        text, modules, limit = injector().build_details(STUDY_DAY, NOW, store(), "在干嘛，上课吗？")
        self.assertTrue(text)
        self.assertEqual(limit, 1600)
        self.assertNotIn("base", modules)
        self.assertTrue({"schedule", "long_term"} <= set(modules))
        _, modules, _ = injector(base_module_enable=True).build_details(STUDY_DAY, NOW, store(), "在干嘛？")
        self.assertEqual(modules, ("base", "schedule"))

    def test_size_limit(self):
        for text in (ask("穿搭", max_chars=400), injector(max_chars=400).build_proactive_context(STUDY_DAY, NOW, store())):
            self.assertLessEqual(len(text), 400)
            self.assertTrue(text.endswith("</character_state>"))


class ProactiveInjection(unittest.TestCase):
    def test_always_has_schedule_and_stage(self):
        text = injector().build_proactive_context(STUDY_DAY, NOW, store())
        self.assertTrue(text.startswith("<character_state>") and text.endswith("</character_state>"))
        for needle in ("当前活动：自习", "上个时段：00:00-08:00 睡觉", "下个时段：12:00-24:00 午后安排", "今日主题：学习日；心情：专注", "所处长期阶段：秋季学期"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
