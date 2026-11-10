"""The "generate schedule / outfit" switches decide which inputs a new day is built from."""

import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from astrbot_plugin_simlife_world.core.models import DailyPlan
from astrbot_plugin_simlife_world.main import ProactiveVirtualDailyPlugin

EMPTY_DAY = DailyPlan(date="2026-08-14", persona_id="alice", theme="", mood="", outfit=None, timeline=())
PERSONA = SimpleNamespace(id="alice", prompt="persona")


def host(schedule=True, outfit=True):
    plugin = object.__new__(ProactiveVirtualDailyPlugin)
    plugin.config = {
        "schedule_settings": {"daily_schedule_generation_enable": schedule, "daily_outfit_generation_enable": outfit},
        "long_term_settings": {"enable": True},
    }
    plugin.storage = SimpleNamespace(
        plans={},
        schedule_requirements={},
        get_plan=Mock(return_value=None),
        get_recent_plans=Mock(return_value=[]),
        active_schedule_requirements=Mock(return_value=[]),
        consume_schedule_requirements=Mock(),
        plan_key=Mock(return_value="2026-08-14::alice"),
        save_plans=AsyncMock(),
    )
    plugin.long_term = SimpleNamespace(format_day_context=Mock(return_value="阶段"))
    plugin._personal_network_context = AsyncMock(return_value="关系")
    plugin._generate_new_character = AsyncMock(return_value="新人")
    plugin._recent_life_memory = Mock(return_value="")
    plugin.plan_generator = SimpleNamespace(generate=AsyncMock(return_value=EMPTY_DAY))
    return plugin


class GenerationSwitches(unittest.IsolatedAsyncioTestCase):
    def test_both_on_by_default(self):
        plugin = object.__new__(ProactiveVirtualDailyPlugin)
        plugin.config = {}
        self.assertEqual(plugin._daily_generation_flags(), (True, True))

    async def test_outfit_only_day_skips_schedule_inputs(self):
        plugin = host(schedule=False)
        await plugin._ensure_plan(PERSONA, date(2026, 8, 14))
        sent = plugin.plan_generator.generate.await_args.kwargs
        self.assertEqual((sent["include_schedule"], sent["include_outfit"]), (False, True))
        self.assertEqual((sent["history_plans"], sent["long_term_context"], sent["relationship_context"]), ([], "", ""))
        for unused in (plugin.storage.active_schedule_requirements, plugin.storage.consume_schedule_requirements):
            unused.assert_not_called()
        plugin._personal_network_context.assert_not_awaited()
        plugin._generate_new_character.assert_not_awaited()

    async def test_schedule_day_gathers_its_inputs(self):
        plugin = host(outfit=False)
        await plugin._ensure_plan(PERSONA, date(2026, 8, 14))
        sent = plugin.plan_generator.generate.await_args.kwargs
        self.assertEqual((sent["include_schedule"], sent["include_outfit"]), (True, False))
        plugin.storage.get_recent_plans.assert_called_once()
        plugin.storage.active_schedule_requirements.assert_called_once()
        plugin._personal_network_context.assert_awaited_once()
        plugin._generate_new_character.assert_awaited_once()

    async def test_day_without_schedule_clears_proactive_jobs(self):
        plugin = object.__new__(ProactiveVirtualDailyPlugin)
        plugin.runtime = SimpleNamespace(remove_prefix=Mock(), remove=Mock())
        plugin.policy = SimpleNamespace(ensure_state=Mock())
        plugin._schedule_available_umos = {"umo"}
        plugin._umo_hash = lambda umo: "h"
        await plugin._schedule_session("umo", PERSONA, EMPTY_DAY)
        self.assertNotIn("umo", plugin._schedule_available_umos)
        plugin.runtime.remove_prefix.assert_called_once_with("pvd:h:plan:")
        plugin.runtime.remove.assert_called_once_with("pvd:h:idle")
        plugin.policy.ensure_state.assert_not_called()


if __name__ == "__main__":
    unittest.main()
