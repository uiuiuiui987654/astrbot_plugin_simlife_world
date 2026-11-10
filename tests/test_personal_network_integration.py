"""The personal-network link stays off unless enabled and only logs finished, shared activities."""

import asyncio
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

from astrbot_plugin_simlife_world.core.models import DailyPlan
from astrbot_plugin_simlife_world.main import SimLifeWorldPlugin

from tests.fixtures import outfit_payload

TZ = ZoneInfo("Asia/Shanghai")


def network_plugin():
    return SimpleNamespace(
        get_context_for_plugin=AsyncMock(return_value="network context"),
        record_life_event_from_plugin=AsyncMock(return_value={"created": True}),
    )


def host(enabled, network=None):
    plugin = object.__new__(SimLifeWorldPlugin)
    plugin.config = {"personal_network_integration": {"enable": enabled, "max_context_chars": 2500}}
    plugin.context = MagicMock()
    plugin.context.get_registered_star.return_value = SimpleNamespace(activated=True, star_cls=network) if network else None
    plugin._personal_network_unavailable_logged = False
    plugin.timezone = TZ
    plugin.storage = SimpleNamespace(plans={})
    return plugin


def day_with_lin():
    def meal(slot_id, start, end, what):
        return {"id": slot_id, "start": start, "end": end, "activity": what, "location": "Cafe", "state": "social", "participant_ids": ["person-1"]}

    return DailyPlan.from_dict(
        {
            "date": "2026-07-28",
            "persona_id": "alice",
            "theme": "social",
            "mood": "warm",
            "outfit": outfit_payload(),
            "timeline": [meal("lunch", "00:00", "12:00", "Lunch with Lin"), meal("dinner", "12:00", "24:00", "Dinner with Lin")],
        }
    )


class PersonalNetworkLink(unittest.TestCase):
    def test_disabled_means_never_looked_up(self):
        plugin = host(enabled=False)
        self.assertIsNone(plugin._personal_network_plugin())
        plugin.context.get_registered_star.assert_not_called()

    def test_context_uses_configured_limit(self):
        network = network_plugin()
        self.assertEqual(asyncio.run(host(True, network)._personal_network_context("alice")), "network context")
        network.get_context_for_plugin.assert_awaited_once_with("alice", max_chars=2500)

    def test_only_finished_activities_are_recorded(self):
        network = network_plugin()
        plugin = host(True, network)
        plugin.storage.plans = {"2026-07-28::alice": day_with_lin()}
        asyncio.run(plugin._record_completed_personal_network_events("alice", datetime(2026, 7, 28, 13, 0, tzinfo=TZ)))
        call = network.record_life_event_from_plugin.await_args
        network.record_life_event_from_plugin.assert_awaited_once()
        self.assertEqual(call.args, ("alice",))
        self.assertEqual(
            (call.kwargs["participant_ids"], call.kwargs["source_key"], call.kwargs["source"]),
            (["person-1"], "2026-07-28:lunch", "astrbot_plugin_simlife_world"),
        )


if __name__ == "__main__":
    unittest.main()
