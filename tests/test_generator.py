"""Daily plan generation against a scripted LLM: prompts, validation, retries and rewrites."""

import asyncio
import json
import unittest
from dataclasses import replace
from datetime import date
from types import SimpleNamespace

from astrbot_plugin_simlife_world.core.generator import DailyPlanGenerator
from astrbot_plugin_simlife_world.core.long_term import validate_stage
from astrbot_plugin_simlife_world.core.models import DailyPlan
from astrbot_plugin_simlife_world.core.persona import PersonaContext

from tests.fixtures import life_timeline, outfit_payload

ALICE = PersonaContext("alice", "persona")
DAY = date(2026, 7, 14)
STYLES = ["复古文艺风", "可爱甜美风"]


class ScriptedLLM:
    """Answers with the given replies in order and remembers every prompt it saw."""

    def __init__(self, *replies):
        self.replies, self.prompts, self.systems = list(replies), [], []

    @property
    def calls(self):
        return len(self.prompts)

    async def text_chat(self, prompt, session_id, system_prompt=None):
        self.prompts.append(prompt)
        self.systems.append(system_prompt)
        return SimpleNamespace(completion_text=self.replies.pop(0))


class Context:
    def __init__(self, default, selected=None):
        self.default, self.selected, self.asked_for = default, selected, []

    def get_provider_by_id(self, provider_id):
        self.asked_for.append(provider_id)
        return self.selected

    def get_using_provider(self):
        return self.default


def config(retries=0, styles=None, sessions=None, **overrides):
    prompts = {
        "generation_retry_prompt_template": "RETRY {mode} attempt={attempt} error={error} previous=<previous>{previous_output}</previous>",
        "schedule_generation_system_prompt": "SCHEDULE_SYSTEM",
        "outfit_generation_system_prompt": "OUTFIT_SYSTEM",
        "complete_generation_prompt_template": "COMPLETE {mode} {date} {persona} {theme} {mood} {outfit_style} {history} {long_term_context} {requirements}",
        "schedule_prompt_template": "SCHEDULE {mode} {date} {persona} {theme} {mood} {history} {long_term_context} {outfit_context} {timeline} {requirements}",
        "outfit_prompt_template": "OUTFIT {mode} {date} {persona} {theme} {mood} {outfit_style} {timeline} {current_outfit} {requirements}",
    }
    schedule = {"generation_retries": retries}
    for key, value in overrides.items():
        (prompts if key in prompts else schedule)[key] = value
    return {
        "schedule_settings": schedule,
        "prompt_settings": prompts,
        "creative_pool": {} if styles is None else {"outfit_styles": styles},
        **(sessions or {}),
    }


def answer(**changes):
    payload = {
        "theme": "日常",
        "mood": "平静",
        "outfit": outfit_payload(),
        "timeline": life_timeline("all", "正常生活", "家", "available", "normal"),
        "proactive_windows": [],
        "budget_bonus": {"private": 1, "group": 0},
    }
    payload.update(changes)
    return json.dumps(payload, ensure_ascii=False)


def outfit_answer(summary="清爽学院造型", style="日常休闲风", wrapped=True, drop=()):
    outfit = outfit_payload(summary, style)
    outfit["items"] = [item for item in outfit["items"] if item["category"] not in drop]
    return json.dumps({"outfit": outfit} if wrapped else outfit, ensure_ascii=False)


def window(window_id, audience, at="09:00"):
    return {"id": window_id, "at": at, "intent": "主动问候", "audience": audience, "source_item_id": "all"}


def todays_plan():
    return DailyPlan.from_dict(
        {
            "date": "2026-07-14",
            "persona_id": "alice",
            "theme": "文艺日",
            "mood": "温柔",
            "outfit": outfit_payload("复古书卷气造型", "复古文艺风"),
            "timeline": life_timeline("old", "旧日程", "家", "available", "normal"),
            "revision": "old-revision",
        }
    )


def generator(llm, cfg=None, selected=None):
    context = Context(llm, selected)
    return DailyPlanGenerator(context, cfg or config()), context


def run(coro):
    return asyncio.run(coro)


class WhatGetsGenerated(unittest.TestCase):
    def test_schedule_only(self):
        llm = ScriptedLLM(answer())
        plan = run(generator(llm)[0].generate(DAY, ALICE, include_schedule=True, include_outfit=False))
        self.assertEqual((plan.has_schedule, plan.has_outfit, llm.systems), (True, False, ["SCHEDULE_SYSTEM"]))
        self.assertIn("SCHEDULE 生成日程", llm.prompts[0])

    def test_outfit_only(self):
        llm = ScriptedLLM(outfit_answer())
        plan = run(generator(llm)[0].generate(DAY, ALICE, include_schedule=False, include_outfit=True))
        self.assertEqual((plan.has_schedule, plan.has_outfit, plan.theme, plan.mood), (False, True, "", ""))
        self.assertEqual(llm.systems, ["OUTFIT_SYSTEM"])
        self.assertIn("OUTFIT 生成穿搭", llm.prompts[0])

    def test_nothing_enabled_asks_nothing(self):
        llm = ScriptedLLM()
        plan = run(generator(llm)[0].generate(DAY, ALICE, include_schedule=False, include_outfit=False))
        self.assertEqual((plan.has_schedule, plan.has_outfit, llm.calls), (False, False, 0))

    def test_switched_off_half_is_kept_from_the_old_plan(self):
        original = todays_plan()
        plan = run(generator(ScriptedLLM(answer()))[0].generate(DAY, ALICE, include_schedule=True, include_outfit=False, base_plan=original))
        self.assertTrue(plan.has_schedule)
        self.assertEqual(plan.outfit, original.outfit)
        self.assertNotEqual(plan.timeline, original.timeline)

    def test_complete_generation_combines_prompts(self):
        llm = ScriptedLLM(answer())
        cfg = config(schedule_generation_system_prompt="严格覆盖 00:00 到 24:00，并在输出前自检。", outfit_generation_system_prompt="outfit 必须是 JSON 对象并包含 underwear。")
        run(generator(llm, cfg)[0].generate(DAY, ALICE))
        for needle in ("严格覆盖 00:00 到 24:00，并在输出前自检。", "outfit 必须是 JSON 对象", "underwear"):
            self.assertIn(needle, llm.systems[0])


class ProactiveWindowBudget(unittest.TestCase):
    def test_caps_are_written_into_the_prompt(self):
        llm = ScriptedLLM(answer())
        sessions = {"friend_settings": {"enable": True, "daily_budget_max": 4}, "group_settings": {"enable": True, "daily_budget_max": 2}}
        run(generator(llm, config(sessions=sessions))[0].generate(DAY, ALICE))
        for needle in ("主动消息预算约束", "不得超过 4 个", "不得超过 2 个"):
            self.assertIn(needle, llm.prompts[0])
        llm = ScriptedLLM(answer())
        run(generator(llm)[0].generate(DAY, ALICE))
        self.assertNotIn("主动消息预算约束", llm.prompts[0])

    def test_too_many_windows_is_sent_back(self):
        cases = {
            "friends": (
                {"friend_settings": {"enable": True, "daily_budget_max": 2}, "group_settings": {"enable": True, "daily_budget_max": 1}},
                [window("w1", "both"), window("w2", "both", "12:00"), window("w3", "both", "18:00")],
                [window("w1", "both")],
                "面向好友数量 3 超过预算上限 2",
                None,
            ),
            "groups only": (
                {"friend_settings": {"enable": False}, "group_settings": {"enable": True, "daily_budget_max": 1}},
                [window("w1", "group"), window("w2", "group", "12:00")],
                [window("w1", "group")],
                "面向群聊数量 2 超过预算上限 1",
                "面向好友",
            ),
        }
        for name, (sessions, too_many, fine, complaint, unmentioned) in cases.items():
            with self.subTest(name):
                llm = ScriptedLLM(answer(proactive_windows=too_many), answer(proactive_windows=fine))
                plan = run(generator(llm, config(retries=1, sessions=sessions))[0].generate(DAY, ALICE))
                self.assertEqual((plan.status, len(plan.proactive_windows), llm.calls), ("ok", 1, 2))
                self.assertIn(complaint, llm.prompts[1])
                if unmentioned:
                    self.assertNotIn(unmentioned, llm.prompts[1])


class Retries(unittest.TestCase):
    def test_bad_answer_then_good(self):
        llm = ScriptedLLM("not json", answer())
        plan = run(generator(llm, config(retries=1))[0].generate(DAY, ALICE))
        self.assertEqual((plan.status, plan.persona_id, plan.outfit.style, llm.calls), ("ok", "alice", "日常休闲风", 2))
        self.assertEqual(llm.systems[0], "SCHEDULE_SYSTEM\n\nOUTFIT_SYSTEM")
        self.assertIn("COMPLETE 完整生成", llm.prompts[0])
        self.assertEqual(llm.prompts[0].count("persona"), 1)
        for needle in ("not json", "LLM response does not contain a JSON object", "attempt=2"):
            self.assertIn(needle, llm.prompts[1])

    def test_retry_shows_only_the_latest_bad_answer(self):
        llm = ScriptedLLM("first invalid", "second invalid", answer())
        self.assertEqual(run(generator(llm, config(retries=2))[0].generate(DAY, ALICE)).status, "ok")
        self.assertIn("first invalid", llm.prompts[1])
        self.assertNotIn("first invalid", llm.prompts[2])
        self.assertIn("second invalid", llm.prompts[2])
        self.assertIn("attempt=3", llm.prompts[2])

    def test_outfit_fields_must_be_wrapped_in_full_generation(self):
        flattened = json.loads(answer())
        flattened.update(flattened.pop("outfit"))
        llm = ScriptedLLM(json.dumps(flattened, ensure_ascii=False), answer())
        self.assertEqual(run(generator(llm, config(retries=1))[0].generate(DAY, ALICE)).status, "ok")
        self.assertIn("missing structured outfit", llm.prompts[1])

    def test_giving_up(self):
        llm = ScriptedLLM("bad", "still bad")
        self.assertEqual(run(generator(llm, config(retries=1))[0].generate(DAY, ALICE)).status, "failed")
        self.assertEqual(llm.calls, 2)
        llm = ScriptedLLM("bad", "still bad")
        with self.assertRaises(RuntimeError):  # rewrites raise instead of returning a failed plan
            run(generator(llm, config(retries=1))[0].rewrite_schedule(todays_plan(), ALICE))
        self.assertEqual(llm.calls, 2)


class Rewrites(unittest.TestCase):
    def test_schedule_rewrite_keeps_everything_else(self):
        llm = ScriptedLLM(
            answer(timeline=life_timeline("new", "新日程", "图书馆", "focus", "low"), budget_bonus={"private": 2, "group": 1}, theme="不应采用", outfit=outfit_payload("不应采用"))
        )
        original = todays_plan()
        new = run(generator(llm)[0].rewrite_schedule(original, ALICE, extra="安排阅读", long_term_context="<long_term_timeline>暑假</long_term_timeline>"))
        self.assertEqual((new.theme, new.mood, new.outfit), (original.theme, original.mood, original.outfit))
        self.assertEqual(next(item for item in new.timeline if item.id == "new").activity, "新日程")
        self.assertEqual(new.private_bonus, 2)
        self.assertNotEqual(new.revision, original.revision)
        self.assertIn("安排阅读", llm.prompts[0])
        self.assertIn("暑假", llm.prompts[0])
        self.assertEqual(llm.systems[0], "SCHEDULE_SYSTEM")

    def test_schedule_rewrite_of_an_empty_day_picks_theme_and_mood(self):
        empty = DailyPlan(date="2026-07-14", persona_id="alice", theme="", mood="", outfit=None, timeline=())
        plan = run(generator(ScriptedLLM(answer()))[0].rewrite_schedule(empty, ALICE))
        self.assertTrue(plan.has_schedule and plan.theme and plan.mood)
        self.assertFalse(plan.has_outfit)

    def test_outfit_rewrite_picks_a_new_style_and_keeps_the_schedule(self):
        llm = ScriptedLLM(outfit_answer(style="模型错误风格"))
        original = todays_plan()
        new = run(generator(llm, config(styles=STYLES))[0].rewrite_outfit(original, ALICE))
        self.assertEqual((new.outfit.style, new.outfit.summary), ("可爱甜美风", "清爽学院造型"))
        self.assertEqual(
            (new.theme, new.mood, new.timeline, new.proactive_windows, new.private_bonus),
            (original.theme, original.mood, original.timeline, original.proactive_windows, original.private_bonus),
        )
        self.assertIn("旧日程", llm.prompts[0])
        self.assertEqual(llm.systems[0], "OUTFIT_SYSTEM")

    def test_outfit_rewrite_accepts_a_bare_outfit(self):
        llm = ScriptedLLM(outfit_answer("直接返回的穿搭", wrapped=False))
        new = run(generator(llm, config(styles=STYLES))[0].rewrite_outfit(todays_plan(), ALICE))
        self.assertEqual((new.outfit.summary, new.outfit.style, llm.calls), ("直接返回的穿搭", "可爱甜美风", 1))

    def test_outfit_rewrite_retries(self):
        cases = {
            "no wrapper": ('{"result": "missing wrapper"}', ('"result": "missing wrapper"', "missing structured outfit")),
            "no underpants": (outfit_answer("缺少内裤的穿搭", drop={"underpants"}), ("missing the underpants category",)),
        }
        for name, (bad, complaints) in cases.items():
            with self.subTest(name):
                llm = ScriptedLLM(bad, outfit_answer("修正后的穿搭"))
                new = run(generator(llm, config(retries=1, styles=STYLES))[0].rewrite_outfit(todays_plan(), ALICE))
                self.assertEqual((new.outfit.summary, llm.calls), ("修正后的穿搭", 2))
                for complaint in complaints:
                    self.assertIn(complaint, llm.prompts[1])

    def test_style_named_in_the_request_wins(self):
        llm = ScriptedLLM(outfit_answer("利落通勤造型"))
        new = run(generator(llm, config(styles=["复古文艺风", "极简都市风", "可爱甜美风"]))[0].rewrite_outfit(todays_plan(), ALICE, extra="请穿极简都市风"))
        self.assertEqual(new.outfit.style, "极简都市风")
        self.assertIn("极简都市风", llm.prompts[0])


class PromptHistory(unittest.TestCase):
    def test_recent_days_reach_the_prompt(self):
        yesterday = DailyPlan.from_dict(
            {
                "date": "2026-07-13",
                "persona_id": "alice",
                "theme": "宅家日",
                "mood": "慵懒",
                "outfit": outfit_payload("舒适的居家造型"),
                "timeline": [{"id": "all", "start": "00:00", "end": "24:00", "activity": "在家看书"}],
            }
        )
        llm = ScriptedLLM(answer())
        run(generator(llm)[0].generate(DAY, ALICE, history_plans=[yesterday]))
        for needle in ("2026-07-13", "在家看书", "不要照抄"):
            self.assertIn(needle, llm.prompts[0])

    def test_only_the_latest_day_is_detailed(self):
        base = todays_plan()

        def single(day, theme, activity, place):
            return replace(base, date=day, theme=theme, timeline=(replace(base.timeline[0], start="00:00", end="24:00", activity=activity, location=place),))

        text = DailyPlanGenerator._format_history([single("2026-07-12", "旧主题", "旧活动", "旧地点"), single("2026-07-13", "最近主题", "最近活动", "最近地点")])
        for needle in ("较早日程摘要", "主要活动：旧活动", "最近一天详情", "00:00-24:00 最近活动 @ 最近地点"):
            self.assertIn(needle, text)
        for needle in ("00:00-24:00 旧活动", "旧地点"):
            self.assertNotIn(needle, text)

    def test_long_term_context_reaches_the_prompt(self):
        llm = ScriptedLLM(answer())
        run(generator(llm)[0].generate(date(2026, 9, 7), PersonaContext("student", "persona"), long_term_context="<long_term_timeline>开学典礼</long_term_timeline>"))
        self.assertIn("开学典礼", llm.prompts[0])


class Providers(unittest.TestCase):
    def test_schedule_provider_setting(self):
        default, chosen = ScriptedLLM(), ScriptedLLM(answer())
        gen, context = generator(default, config(schedule_llm_provider="schedule-provider"), selected=chosen)
        self.assertEqual(run(gen.generate(DAY, ALICE)).status, "ok")
        self.assertEqual((context.asked_for, chosen.calls, default.calls), (["schedule-provider"], 1, 0))

    def test_old_llm_provider_key_is_ignored(self):
        default, chosen = ScriptedLLM(answer()), ScriptedLLM()
        gen, context = generator(default, config(llm_provider="legacy-provider"), selected=chosen)
        self.assertEqual(run(gen.generate(DAY, ALICE)).status, "ok")
        self.assertEqual((context.asked_for, default.calls, chosen.calls), ([], 1, 0))


class LongTermGeneration(unittest.TestCase):
    def test_stages_start_where_asked_and_the_rules_are_spelled_out(self):
        spring = {
            "id": "semester-spring",
            "name": "春季学期",
            "kind": "academic",
            "start_date": "2027-02-20",
            "end_date": "2027-07-10",
            "priority": 75,
            "summary": "正常上课",
            "weekly_rules": [],
            "special_dates": [],
            "special_periods": [],
            "milestones": [],
            "constraints": [],
        }
        llm = ScriptedLLM(json.dumps({"stages": [spring]}, ensure_ascii=False))
        winter = validate_stage({"id": "winter", "name": "寒假", "kind": "academic", "start_date": "2027-01-21", "end_date": "2027-02-19"}, "student")
        gen = DailyPlanGenerator(Context(llm), {"schedule_settings": {}, "creative_pool": {}})
        stages = run(gen.generate_long_term_timeline(PersonaContext("student", "persona"), start_date=date(2027, 2, 20), previous_stage=winter))
        self.assertEqual((stages[0]["start_date"], stages[0]["priority"]), ("2027-02-20", 75))
        for rule in (
            "priority",
            "text values such as high, medium, or low",
            "start and end must be non-empty",
            "unique integers from 1 to 7",
            "required must be a JSON boolean",
            "Special period rules",
            "non-negative JSON integer",
            "self-check every field",
        ):
            self.assertIn(rule, llm.systems[0])
        self.assertIn("前一阶段：寒假", llm.prompts[0])


if __name__ == "__main__":
    unittest.main()
