"""The proactive gate: budget, unanswered streak, availability and subscriptions."""

import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from astrbot_plugin_simlife_world.core.models import DailyPlan
from astrbot_plugin_simlife_world.core.proactive import ProactivePolicy

from tests.fixtures import outfit_payload

TZ = ZoneInfo("Asia/Shanghai")
NOW = datetime(2026, 7, 14, 12, 0, tzinfo=TZ)
FRIEND = "aiocqhttp:FriendMessage:42"
GROUP = "aiocqhttp:GroupMessage:42"


def whole_day(availability="normal", private_bonus=2):
    return DailyPlan.from_dict(
        {
            "date": "2026-07-14",
            "persona_id": "alice",
            "theme": "日常",
            "mood": "平静",
            "outfit": outfit_payload(),
            "timeline": [{"id": "all", "start": "00:00", "end": "24:00", "activity": "休息", "availability": availability}],
            "budget_bonus": {"private": private_bonus, "group": 1},
        }
    )


class Gate(unittest.TestCase):
    def setUp(self):
        self.config = {
            "friend_settings": {
                "enable": True,
                "session_list": [FRIEND],
                "daily_budget_min": 1,
                "daily_budget_max": 1,
                "llm_bonus_max": 2,
                "daily_hard_max": 2,
                "cooldown_minutes": 120,
            },
            "group_settings": {"enable": False, "session_list": []},
            "delivery_settings": {
                "max_unanswered": 3,
                "minimum_idle_for_window_minutes": 20,
                "availability_probabilities": {"blocked": 0.0, "low": 0.25, "normal": 0.7, "high": 1.0},
            },
        }
        self.policy = ProactivePolicy(self.config, SimpleNamespace(sessions={}), TZ)

    def state(self, plan, **changes):
        state = self.policy.ensure_state(FRIEND, "alice", plan, NOW)
        for key, value in changes.items():
            setattr(state, key, value)
        return state

    def window_verdict(self, availability):
        plan = whole_day(availability)
        state = self.state(plan, daily_budget=10, last_user_message_at=(NOW - timedelta(hours=1)).isoformat())
        return self.policy.evaluate(umo=FRIEND, state=state, current_item=plan.timeline[0], now=NOW, trigger="window", attempt_key=availability)

    def test_budget_never_exceeds_hard_max(self):
        self.assertEqual(self.state(whole_day(private_bonus=99)).daily_budget, 2)

    def test_three_unanswered_in_a_row_stops_her(self):
        state = self.state(whole_day(), daily_budget=10, unanswered_count=3)
        verdict = self.policy.evaluate(umo=FRIEND, state=state, current_item=None, now=NOW, trigger="idle")
        self.assertFalse(verdict.allowed)
        self.assertIn("unanswered", verdict.reason)

    def test_availability(self):
        self.assertEqual(self.policy.availability_probability(whole_day("blocked").timeline[0]), 0.0)
        self.assertTrue(self.window_verdict("high").allowed)
        blocked = self.window_verdict("blocked")
        self.assertEqual((blocked.allowed, blocked.reason), (False, "availability probability rejected"))

    def test_a_reply_resets_the_streak(self):
        state = self.state(whole_day(), unanswered_count=2)
        self.policy.record_incoming(FRIEND, NOW + timedelta(minutes=1))
        self.assertEqual(state.unanswered_count, 0)

    def test_subscribing(self):
        self.config["friend_settings"].update(enable=False, session_list=[])
        self.assertTrue(self.policy.subscribe(FRIEND))
        self.assertFalse(self.policy.subscribe(FRIEND))  # already there
        self.assertEqual((self.config["friend_settings"]["enable"], self.config["friend_settings"]["session_list"]), (True, [FRIEND]))
        self.assertTrue(self.policy.is_enabled(FRIEND))
        self.assertTrue(self.policy.subscribe(GROUP))
        self.assertEqual((self.config["group_settings"]["enable"], self.config["group_settings"]["session_list"]), (True, [GROUP]))


if __name__ == "__main__":
    unittest.main()
