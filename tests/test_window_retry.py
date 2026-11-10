"""Missed proactive windows: whether to try again, when, and how to phrase the late message."""

import asyncio
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from zoneinfo import ZoneInfo

from astrbot_plugin_simlife_world.core.proactive import ProactivePolicy
from astrbot_plugin_simlife_world.main import ProactiveVirtualDailyPlugin

from tests.fixtures import nap_day

TZ = ZoneInfo("Asia/Shanghai")
HALF_PAST_NOON = datetime(2026, 7, 14, 12, 30, tzinfo=TZ)
FRIEND = "aiocqhttp:FriendMessage:42"
PLAN = nap_day()
WINDOW = PLAN.proactive_windows[0]
NOT_IDLE = "conversation is not idle enough"


def host(now=HALF_PAST_NOON, **delivery):
    config = {
        "friend_settings": {"enable": True, "session_list": [FRIEND], "cooldown_minutes": 120},
        "group_settings": {"enable": False, "session_list": []},
        "delivery_settings": {"minimum_idle_for_window_minutes": 20, **delivery},
    }
    plugin = object.__new__(ProactiveVirtualDailyPlugin)
    plugin.config = config
    plugin.timezone = TZ
    plugin.storage = SimpleNamespace(sessions={})
    plugin.policy = ProactivePolicy(config, plugin.storage, TZ)
    plugin._conversation_activity_at = {}
    plugin._window_retry_counts = {}
    plugin._now = lambda: now
    return plugin


class LateIntent(unittest.TestCase):
    def test_explains_the_missed_moment_naturally(self):
        intent = host()._delayed_window_intent(WINDOW, PLAN, "sleeping")
        for needle in ("上午打个招呼", "上午日程", "休息"):
            self.assertIn(needle, intent)
        self.assertNotIn("延迟的主动消息", intent)
        self.assertIn("时机不太合适", host()._delayed_window_intent(WINDOW, PLAN, ""))

    def test_still_inside_the_activity_means_nothing_was_missed(self):
        self.assertEqual(host(HALF_PAST_NOON.replace(hour=10))._delayed_window_intent(WINDOW, PLAN, NOT_IDLE), WINDOW.intent)


class WhetherToRetry(unittest.TestCase):
    def test_policy(self):
        default, opted_in = host(), host(window_retry_when_not_idle=True, window_retry_when_cooldown=True)
        for reason in ("sleeping", "availability probability rejected"):
            self.assertTrue(default._should_retry_window(FRIEND, reason))
        for reason in (NOT_IDLE, "cooldown active", "agent task active"):
            with self.subTest(reason):
                self.assertFalse(default._should_retry_window(FRIEND, reason))
                self.assertTrue(opted_in._should_retry_window(FRIEND, reason))

    def test_waiting_for_an_agent_does_not_use_up_retries(self):
        plugin = host(window_retry_when_not_idle=True)
        plugin._attempt_unsolicited = AsyncMock(return_value=(False, "agent task active"))
        plugin._schedule_window_retry = Mock()
        asyncio.run(plugin._attempt_window(FRIEND, SimpleNamespace(id="alice"), PLAN, WINDOW, delayed=False))
        self.assertEqual(plugin._window_retry_counts, {})
        plugin._schedule_window_retry.assert_called_once()


class WhenToRetry(unittest.TestCase):
    def retry_at(self, reason, plugin=None, **session):
        plugin = plugin or host()
        if session:
            plugin.storage.sessions[FRIEND] = SimpleNamespace(**session)
        return plugin._window_retry_run_at(FRIEND, PLAN, reason)

    def ago(self, **delta):
        return (HALF_PAST_NOON - timedelta(**delta)).isoformat()

    def test_asleep_waits_for_the_next_free_slot(self):
        run_at = self.retry_at("sleeping")
        self.assertEqual(run_at.hour, 14)

    def test_busy_chat_waits_out_the_quiet_period(self):
        self.assertGreaterEqual(self.retry_at(NOT_IDLE, last_user_message_at=self.ago(minutes=10)), HALF_PAST_NOON + timedelta(minutes=10))
        plugin = host()
        plugin._conversation_activity_at[FRIEND] = HALF_PAST_NOON - timedelta(minutes=5)  # an agent just finished
        self.assertGreaterEqual(self.retry_at(NOT_IDLE, plugin, last_user_message_at=self.ago(hours=1)), HALF_PAST_NOON + timedelta(minutes=15))

    def test_cooldown_waits_until_it_ends(self):
        self.assertGreaterEqual(self.retry_at("cooldown active", last_proactive_at=self.ago(minutes=30)), HALF_PAST_NOON + timedelta(minutes=90))

    def test_no_retry(self):
        long_cooldown = host()
        long_cooldown.config["friend_settings"]["cooldown_minutes"] = 2000
        cases = {
            "unknown reason": ("budget exhausted", None, {}),
            "cooldown past midnight": ("cooldown active", long_cooldown, {"last_proactive_at": self.ago(minutes=10)}),
            "agent wait past midnight": ("agent task active", host(HALF_PAST_NOON.replace(hour=23, minute=45)), {}),
        }
        for name, (reason, plugin, session) in cases.items():
            with self.subTest(name):
                self.assertIsNone(self.retry_at(reason, plugin, **session))


if __name__ == "__main__":
    unittest.main()
