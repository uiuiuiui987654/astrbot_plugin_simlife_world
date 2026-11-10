"""Every panel endpoint answers through the dispatcher, and the shared POST checks keep their order."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import panel_server  # noqa: E402

from astrbot_plugin_simlife_world.core import money  # noqa: E402

UNKNOWN = {"ok": False, "error": "未知视图操作"}
GET_ENDPOINTS = [
    "integrations", "trips", "backup", "state", "cooking/history", "recent_activity", "home_items", "decor/items",
    "fridge", "fridge/recipe", "cooking/dishes", "item_wishes", "interact", "wallet", "garage", "memory",
    "diagnostics", "shop", "furniture_slots", "weekly", "diary", "book", "ping",
]


class ViewRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.data_dir = Path(cls._tmp.name)
        cls.api = panel_server.make_api(cls.data_dir)
        money.add(cls.data_dir, panel_server.PERSONA, 500, "seed")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def get(self, endpoint, **params):
        return self.api.dispatch(endpoint, "GET", {"persona": panel_server.PERSONA, **params}, {})

    def post(self, endpoint, **payload):
        return self.api.dispatch(endpoint, "POST", {}, {"persona": panel_server.PERSONA, **payload})

    def test_every_get_endpoint_is_routed(self):
        for endpoint in GET_ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                result = self.get(endpoint)
                self.assertIsInstance(result, dict)
                self.assertNotEqual(result, UNKNOWN)
        self.assertEqual(self.get("nope"), UNKNOWN)
        self.assertEqual(self.api.dispatch("state", "PUT", {}, {}), UNKNOWN)

    def test_state_has_the_demo_day(self):
        state = self.get("state")
        self.assertTrue(state["ok"])
        self.assertEqual(state["persona"], panel_server.PERSONA)
        self.assertEqual(len(state["timeline"]), len(panel_server.DEMO_DAY))

    def test_preview_blocks_interactions_but_not_wallet_goal_clear(self):
        self.assertEqual(self.post("interact", text="hi", preview=True)["error"], "时间预览只供查看，请回到当前时间再互动")
        self.assertTrue(self.post("wallet/goal/clear", preview=True)["ok"])

    def test_furniture_checks_run_before_handlers(self):
        self.assertEqual(self.post("interact", item_id="ghost", action="x")["error"], "未知家具")
        self.assertEqual(self.post("interact", item_id="sofa", action="起飞")["error"], "未知家具动作")
        self.assertEqual(self.post("nope/nope"), UNKNOWN)

    def test_round_trips(self):
        self.assertTrue(self.post("shop/buy", id="milk_tea")["ok"])
        self.assertEqual(self.get("wallet")["wallet"]["balance"], 485.0)
        self.assertTrue(self.post("decor/place", item_id="sofa", room="书房", x=0.3, y=0.4)["ok"])
        self.assertFalse(self.post("decor/store", item_id="ghost")["ok"])
        self.assertTrue(self.post("decor/reset")["ok"])
        self.assertTrue(self.post("affection/nickname", nickname="小笨蛋")["ok"])


if __name__ == "__main__":
    unittest.main()
