import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from astrbot_plugin_simlife_world.core import furniture_state, view_state

NOW = datetime(2026, 11, 10, 20, 0)
DIFFUSER = {"id": "aroma_diffuser", "name": "香薰机", "room": "卧室", "actions": ["开香薰", "关香薰", "换精油"]}
SOFA = {"id": "sofa", "name": "沙发", "room": "客厅", "actions": ["坐下"]}


class FurnitureStateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.plans_path = Path(self._tmp.name) / "plans.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_toggle_device_and_auto_off(self):
        fresh = furniture_state.decorate_item(DIFFUSER, None, now=NOW)
        self.assertEqual(fresh["actions"], ["开香薰", "换精油"])
        self.assertFalse(fresh["power_on"])

        on = furniture_state.record_action(self.plans_path, DIFFUSER, "开香薰", "p", now=NOW)
        self.assertTrue(on["power_on"])
        self.assertEqual(on["actions"][0], "关香薰")
        self.assertEqual(on["auto_off_minutes"], 60)

        later = furniture_state.live_states(self.plans_path, now=NOW + timedelta(minutes=61))
        self.assertFalse(later["aroma_diffuser"]["on"])
        self.assertEqual(later["aroma_diffuser"]["last_action"], "自动关闭")
        stored = json.loads(furniture_state.states_path(self.plans_path).read_text(encoding="utf-8"))
        self.assertFalse(stored["items"]["aroma_diffuser"]["on"])

    def test_power_words(self):
        spec = furniture_state.DEVICE_SPECS["tv"]
        cases = {"开电视": True, "关电视": False, "打开": True, "关闭电视": False, "播放电影": True, "开关面板": None, "换台": None}
        for action, expected in cases.items():
            with self.subTest(action=action):
                self.assertEqual(furniture_state._power_delta(action, spec), expected)

    def test_plain_furniture_records_last_action(self):
        result = furniture_state.record_action(self.plans_path, SOFA, "坐下", "p", now=NOW)
        self.assertNotIn("power_on", result)
        self.assertEqual(result["state_summary"], "最近动作：坐下（刚刚）")
        later = furniture_state.decorate_item(SOFA, result["state"], now=NOW + timedelta(hours=2))
        self.assertEqual(later["state_label"], "最近动作：坐下（2 小时前）")

    def test_action_message(self):
        self.assertEqual(furniture_state.action_message(DIFFUSER, "开香薰"), "香薰机已打开")
        self.assertEqual(furniture_state.action_message(DIFFUSER, "关掉"), "香薰机已关闭")
        self.assertEqual(furniture_state.action_message(SOFA, "坐下"), "已记录：沙发 · 坐下")

    def test_item_without_id_is_not_stored(self):
        furniture_state.record_action(self.plans_path, {"name": "无名"}, "摸一下", "p", now=NOW)
        self.assertFalse(furniture_state.states_path(self.plans_path).exists())

    def test_state_file_is_capped(self):
        for index in range(furniture_state.MAX_ITEMS + 10):
            furniture_state.record_action(
                self.plans_path, {"id": f"item{index}"}, "看", "p", now=NOW + timedelta(seconds=index)
            )
        states = furniture_state.load_states(self.plans_path)
        self.assertEqual(len(states), furniture_state.MAX_ITEMS)
        self.assertNotIn("item0", states)

    def test_context_mentions_current_and_running_devices(self):
        items, _ = view_state.load_home_items(self.plans_path, "p")
        by_id = {item["id"]: item for item in items}
        furniture_state.record_action(self.plans_path, by_id["tv"], "开电视", "p", now=NOW)
        furniture_state.record_action(self.plans_path, by_id["aroma_diffuser"], "开香薰", "p", now=NOW + timedelta(minutes=1))
        text = furniture_state.furniture_context(self.plans_path, "aroma_diffuser", now=NOW + timedelta(minutes=2))
        self.assertIn("操作了", text)
        self.assertIn("香薰机开着", text)
        self.assertIn("现在开着的设备：", text)
        self.assertIn("约 118 分钟后自动关", text)
        self.assertIn("最近的家具操作", furniture_state.furniture_context(self.plans_path, "", now=NOW))


if __name__ == "__main__":
    unittest.main()
