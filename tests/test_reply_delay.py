"""Reply delays: the formula language, the per-message decision, batching and the prompt text."""

import asyncio
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from astrbot_plugin_simlife_world.core.models import TimelineItem
from astrbot_plugin_simlife_world.core.reply_delay import (
    DelayDecision,
    FormulaError,
    QueuedMessage,
    ReplyDelayCoordinator,
    ReplyDelayPolicy,
    SafeFormulaEvaluator,
    format_delay_context,
    format_queued_messages,
)

SCHEMA = json.loads(Path(__file__).resolve().parents[1].joinpath("_conf_schema.json").read_text(encoding="utf-8"))["reply_delay_settings"]["items"]
SHIPPED = {
    key: ({inner: spec["default"] for inner, spec in item["items"].items()} if item.get("type") == "object" else item["default"])
    for key, item in SCHEMA.items()
    if item.get("type") == "object" or "default" in item
}
STUDY = TimelineItem(id="study", start="09:00", end="10:00", activity="自习", location="图书馆", state="focus", availability="low")
TEN_TO_TEN = datetime(2026, 7, 28, 9, 59, 50)
NINE = datetime(2026, 7, 28, 9, 0)
NOON = datetime(2026, 7, 28, 12, 0)


def evaluator(*draws):
    """An evaluator whose random() returns ``draws`` in turn (or the midpoint when none are given)."""
    pending = iter(draws)
    return SafeFormulaEvaluator(random_fn=lambda low, high: next(pending) if draws else (low + high) / 2)


class Formulas(unittest.TestCase):
    def test_arithmetic_variables_and_functions(self):
        self.assertEqual(evaluator().evaluate("ceil(random(0, 4) + min(remaining, message_length) / 2)", {"remaining": 30, "message_length": 6}), 5)

    def test_probability(self):
        self.assertEqual(evaluator(0.2).evaluate("probability(0.25, 90)", {}), 90)
        self.assertEqual(evaluator(0.8).evaluate("probability(0.25, 90)", {}), 0)
        self.assertEqual(evaluator(0.8).evaluate("probability(0.25, 90, 15)", {}), 15)
        documented = "probability(0.3, random(30, 90), remaining)"
        self.assertEqual(evaluator(60.0, 0.2).evaluate(documented, {"remaining": 600}), 60)
        self.assertEqual(evaluator(60.0, 0.8).evaluate(documented, {"remaining": 600}), 600)

    def test_certain_probabilities_draw_nothing(self):
        no_draws = SafeFormulaEvaluator(random_fn=lambda low, high: self.fail("drew a random number"))
        self.assertEqual(no_draws.evaluate("probability(0, 90, 15)", {}), 15)
        self.assertEqual(no_draws.evaluate("probability(1, 90, 15)", {}), 90)

    def test_refused(self):
        for expression in (
            "probability(-0.1, 90)",
            "probability(1.1, 90)",
            "probability(0.5)",
            "probability(0.5, 90, 15, 0)",
            "remaining.__class__",
            "unknown + 1",
            "__import__('os').system('whoami')",
            "1 / 0",
        ):
            with self.subTest(expression), self.assertRaises(FormulaError):
                evaluator().evaluate(expression, {"remaining": 10})


class Decisions(unittest.TestCase):
    def decide(self, settings, now=TEN_TO_TEN, **kwargs):
        policy = ReplyDelayPolicy(settings, evaluator=evaluator())
        return policy, policy.decide(STUDY, now, 4, **kwargs)

    def test_caps(self):
        _, near_end = self.decide({"max_delay_seconds": 1800, "delay_formulas": {"low": "300"}})
        self.assertEqual((near_end.remaining_seconds, near_end.delay_seconds), (10, 10))
        _, last_half_second = self.decide({"delay_formulas": {"low": "300"}}, datetime(2026, 7, 28, 9, 59, 59, 500000))
        self.assertEqual((last_half_second.remaining_seconds, last_half_second.delay_seconds), (0, 0))
        _, capped = self.decide({"max_delay_seconds": 30, "delay_formulas": {"low": "remaining"}}, NINE)
        self.assertEqual(capped.delay_seconds, 30)

    def test_mid_conversation_skips_the_formula(self):
        _, decision = self.decide({"delay_formulas": {"low": "300"}}, active_conversation=True)
        self.assertEqual((decision.delay_seconds, decision.active_conversation), (0, True))

    def test_broken_formula_means_no_delay(self):
        _, decision = self.decide({"max_delay_seconds": 1800, "delay_formulas": {"low": "__import__('os')"}}, NINE)
        self.assertEqual((decision.formula, decision.delay_seconds), ("__import__('os')", 0))
        self.assertTrue(decision.formula_error)

    def test_nothing_configured_means_off(self):
        policy, decision = self.decide({}, NINE)
        self.assertEqual(
            (policy.enabled, policy.notify_user, policy.active_conversation_seconds, policy.max_delay_seconds, decision.delay_seconds),
            (False, False, 0, 0, 0),
        )
        self.assertTrue(decision.formula_error)
        self.assertEqual(policy.notification(decision), "")

    def test_notification_template(self):
        policy, decision = self.decide(
            {"notification_template": "{availability}: {public_reason}; {delay_seconds}s", "public_reasons": {"low": "暂时不便回复"}},
            active_conversation=True,
        )
        self.assertEqual(policy.notification(decision), "low: 暂时不便回复; 0s")

    def test_shipped_defaults(self):
        policy, decision = self.decide(SHIPPED)
        self.assertEqual(
            (policy.enabled, policy.notify_user, policy.active_conversation_seconds, policy.max_delay_seconds), (False, True, 300, 1800)
        )
        self.assertTrue(policy.notification(decision).startswith("预计"))

    def test_formula_help_lists_every_function(self):
        hint = SCHEMA["delay_formulas"]["hint"]
        for name in (
            "remaining=",
            "message_length=",
            "random(low, high)",
            "probability(p, hit_value[, miss_value])",
            "min(a, ...)",
            "max(a, ...)",
            "round(value[, digits])",
            "ceil(value)",
            "floor(value)",
            "probability(0.3, random(30, 90), remaining)",
        ):
            self.assertIn(name, hint)


def decision(seconds):
    return DelayDecision(delay_seconds=seconds, remaining_seconds=100, availability="normal", formula=str(seconds), public_reason="正在处理事情")


def message(text, after=0, sender=("42", "用户"), images=()):
    return QueuedMessage(NOON + timedelta(seconds=after), *sender, text, images, ())


def prompts(messages):
    return [item.prompt for item in messages]


class Batching(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.queue = ReplyDelayCoordinator()

    async def test_later_messages_join_without_moving_the_deadline(self):
        batch, first = await self.queue.enqueue("umo", message("第一条"), decision(10))
        joined, again = await self.queue.enqueue("umo", message("第二条", 8), decision(99))
        self.assertEqual((first, again, joined is batch, batch.deadline), (True, False, True, NOON + timedelta(seconds=10)))
        self.assertEqual(prompts(await self.queue.settle(batch, batch.deadline)), ["第一条", "第二条"])

    async def test_zero_delay(self):
        batch, first = await self.queue.enqueue("solo", message("立即回复"), decision(0))
        self.assertEqual((batch, first), (None, True))
        self.assertIsNone(await self.queue.settle_now("solo"))
        open_batch, _ = await self.queue.enqueue("umo", message("第一条"), decision(10))
        joined, first = await self.queue.enqueue("umo", message("第二条", 1), decision(0))  # still joins an open batch
        self.assertEqual((joined is open_batch, first), (True, False))
        self.assertEqual(prompts(await self.queue.settle(open_batch, open_batch.deadline)), ["第一条", "第二条"])

    async def test_message_at_the_deadline_starts_over(self):
        old, _ = await self.queue.enqueue("umo", message("旧批次"), decision(10))
        new, first = await self.queue.enqueue("umo", message("新批次", 10), decision(5))
        self.assertTrue(first)
        self.assertIsNot(new, old)
        self.assertEqual(prompts(await self.queue.settle(old, old.deadline)), ["旧批次"])
        self.assertEqual(prompts(await self.queue.settle(new, new.deadline)), ["新批次"])

    async def test_settling_by_hand_wakes_the_waiter(self):
        batch, _ = await self.queue.enqueue("umo", message("立即结算"), decision(3600))
        waiting = asyncio.create_task(self.queue.settle(batch, NOON))
        await asyncio.sleep(0)
        self.assertIs(await self.queue.settle_now("umo"), batch)
        self.assertEqual(prompts(await asyncio.wait_for(waiting, timeout=0.1)), ["立即结算"])
        self.assertIsNone(await self.queue.settle_now("umo"))

    async def test_settle_all(self):
        waiters, batches = [], []
        for umo in ("private", "group"):
            batch, _ = await self.queue.enqueue(umo, message(umo), decision(3600))
            batches.append(batch)
            waiters.append(asyncio.create_task(self.queue.settle(batch, NOON)))
        await asyncio.sleep(0)
        self.assertEqual({id(batch) for batch in await self.queue.settle_all_now()}, {id(batch) for batch in batches})
        self.assertEqual([prompts(result) for result in await asyncio.wait_for(asyncio.gather(*waiters), timeout=0.1)], [["private"], ["group"]])

    async def test_conversation_window_is_in_memory_only(self):
        self.queue.mark_replied("umo", NOON, 120)
        self.assertTrue(self.queue.is_active("umo", NOON + timedelta(seconds=119)))
        self.assertFalse(self.queue.is_active("umo", NOON + timedelta(seconds=120)))
        self.queue.mark_replied("umo", NOON, 120)
        self.queue.clear()
        self.assertFalse(self.queue.is_active("umo", NOON))

    async def test_prompt_text_for_a_group_batch(self):
        lunch = TimelineItem(id="lunch", start="12:00", end="13:00", activity="和同事吃午饭", location="餐厅", state="social", availability="normal")
        batch, _ = await self.queue.enqueue("umo", message("第一条", sender=("1", "甲"), images=("image",)), decision(10), lunch)
        await self.queue.enqueue("umo", message("第二条", 2, sender=("2", "乙")), decision(99), lunch)
        merged = format_queued_messages(await self.queue.settle(batch, batch.deadline), group=True)
        context = format_delay_context(batch, batch.deadline, lunch)
        for needle in ("甲 (1)：第一条 [附件：1 张图片]", "乙 (2)：第二条"):
            self.assertIn(needle, merged)
        for needle in ("消息到达时活动：和同事吃午饭", "消息到达时地点：餐厅", "不要主动向用户披露"):
            self.assertIn(needle, context)


if __name__ == "__main__":
    unittest.main()
