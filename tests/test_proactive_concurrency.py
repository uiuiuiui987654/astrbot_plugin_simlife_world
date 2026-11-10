"""A proactive message is dropped if the conversation moved on while it was being written."""

import asyncio
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from zoneinfo import ZoneInfo

from astrbot.core.utils.session_lock import session_lock_manager

from astrbot_plugin_simlife_world.main import ProactiveVirtualDailyPlugin

from tests.fixtures import nap_day

NOW = datetime(2026, 8, 3, 16, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
FRIEND = "aiocqhttp:FriendMessage:42"
PERSONA = SimpleNamespace(id="alice", prompt="persona")
PLAN = nap_day()


def host():
    plugin = object.__new__(ProactiveVirtualDailyPlugin)
    plugin.config = {"delivery_settings": {"minimum_idle_for_window_minutes": 20, "proactive_timeline_context": False}}
    plugin._now = lambda: NOW
    plugin.delivery_locks = {}
    plugin._conversation_generations = {}
    plugin._conversation_activity_at = {}
    plugin._active_agent_counts = {}
    plugin._agent_release_tasks = set()
    plugin._schedule_idle = Mock()
    plugin.user_states = SimpleNamespace(is_sleeping=lambda _now: False)
    plugin.policy = SimpleNamespace(ensure_state=Mock(), evaluate=Mock())
    return plugin


def writer(plugin, write):
    """Wire up just enough for _deliver; ``write`` plays the LLM."""
    plugin._record_completed_personal_network_events = AsyncMock()
    plugin._personal_network_context = AsyncMock(return_value="")
    plugin.smart_context_injector = plugin.long_term = Mock()
    plugin.message_generator = SimpleNamespace(generate=write, record_conversation=AsyncMock(return_value=True))
    plugin._send_text = AsyncMock()
    return plugin


class Gate(unittest.IsolatedAsyncioTestCase):
    async def attempt(self, plugin, plan=PLAN, trigger="window"):
        plugin._deliver = AsyncMock()
        result = await plugin._attempt_unsolicited(FRIEND, PERSONA, plan, "intent", trigger)
        plugin.policy.evaluate.assert_not_called()
        plugin._deliver.assert_not_awaited()
        return result

    async def test_refused_before_the_policy_runs(self):
        busy = host()
        busy._active_agent_counts[FRIEND] = 1
        just_talked = host()
        just_talked._mark_conversation_activity(FRIEND, NOW - timedelta(minutes=5))
        no_schedule = PLAN.__class__(date=PLAN.date, persona_id=PLAN.persona_id, theme="", mood="", outfit=PLAN.outfit, timeline=())
        self.assertEqual(await self.attempt(busy), (False, "agent running"))
        self.assertEqual(await self.attempt(just_talked), (False, "chat not quiet yet"))
        self.assertEqual(await self.attempt(host(), no_schedule, "idle"), (False, "no schedule today"))


class Delivery(unittest.IsolatedAsyncioTestCase):
    async def test_unchanged_chat_gets_the_message(self):
        plugin = writer(host(), AsyncMock(return_value="current"))
        self.assertTrue(await plugin._deliver(FRIEND, PERSONA, PLAN, "intent", 0, generation=0))
        plugin._send_text.assert_awaited_once_with(FRIEND, "current")
        plugin.message_generator.record_conversation.assert_awaited_once()

    async def test_user_spoke_while_writing(self):
        plugin = host()

        async def write(**_):
            plugin._mark_conversation_activity(FRIEND, NOW)
            return "stale"

        writer(plugin, write)
        self.assertFalse(await plugin._deliver(FRIEND, PERSONA, PLAN, "intent", 0, generation=0))
        plugin._send_text.assert_not_awaited()

    async def test_user_spoke_while_waiting_for_the_session_lock(self):
        written = asyncio.Event()

        async def write(**_):
            written.set()
            return "stale before commit"

        plugin = writer(host(), write)
        async with session_lock_manager.acquire_lock(FRIEND):
            delivery = asyncio.create_task(plugin._deliver(FRIEND, PERSONA, PLAN, "intent", 0, generation=0))
            await written.wait()
            await asyncio.sleep(0)
            plugin._mark_conversation_activity(FRIEND, NOW)
        self.assertFalse(await delivery)
        plugin._send_text.assert_not_awaited()
        plugin.message_generator.record_conversation.assert_not_awaited()


class AgentRuns(unittest.IsolatedAsyncioTestCase):
    async def test_release_waits_until_the_framework_saved_history(self):
        plugin = host()
        event = SimpleNamespace(unified_msg_origin=FRIEND)
        async with session_lock_manager.acquire_lock(FRIEND):
            await plugin.mark_agent_active(event, None)
            await plugin.defer_agent_release(event, None, None)
            await asyncio.sleep(0)
            self.assertTrue(plugin._agent_is_active(FRIEND))
        await asyncio.gather(*tuple(plugin._agent_release_tasks))
        self.assertFalse(plugin._agent_is_active(FRIEND))
        self.assertEqual(plugin._conversation_generation(FRIEND), 2)
        plugin._schedule_idle.assert_called_once_with(FRIEND)


if __name__ == "__main__":
    unittest.main()
