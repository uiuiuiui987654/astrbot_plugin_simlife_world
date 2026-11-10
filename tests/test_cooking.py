import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from astrbot_plugin_simlife_world.core import cooking

NOW = datetime(2026, 11, 10, 18, 0)


class FakeFood:
    def __init__(self, inventory, meals):
        self._inventory = inventory
        self._meals = meals

    def load_inventory(self):
        return self._inventory

    def load_catalog(self):
        return {"meals": self._meals}


MEALS = {
    "晚餐": [
        {"name": "番茄炒蛋", "ingredients": ["番茄", "鸡蛋"], "method": "炒"},
        {"name": "青椒肉丝", "ingredients": ["青椒", "猪肉"], "method": "炒"},
        {"name": "蛋炒饭", "ingredients": ["米饭", "鸡蛋", "葱"]},
        {"name": "", "ingredients": ["番茄"]},
        "坏数据",
    ],
    "午餐": [{"name": "番茄炒蛋", "ingredients": ["番茄", "鸡蛋"]}],
}


class MakeableDishTests(unittest.TestCase):
    def test_only_dishes_with_every_ingredient_in_stock(self):
        food = FakeFood(
            {
                "番茄": {"name": "番茄", "quantity": 2},
                "土鸡蛋": {"name": "土鸡蛋", "quantity": 6},
                "米饭": {"name": "米饭", "quantity": 1},
                "葱": {"name": "葱", "quantity": 0.01},
                "青椒": {"name": "青椒", "quantity": 1},
            },
            MEALS,
        )
        dishes = cooking.makeable_dishes(food)
        self.assertEqual([dish["name"] for dish in dishes], ["番茄炒蛋"])
        self.assertEqual(dishes[0]["resolved_ingredients"], ["番茄", "土鸡蛋"])
        self.assertEqual(dishes[0]["meals"], ["晚餐", "午餐"])

    def test_sorted_by_ingredient_count(self):
        food = FakeFood({name: {"name": name, "quantity": 1} for name in ("番茄", "鸡蛋", "米饭", "葱")}, MEALS)
        self.assertEqual([dish["name"] for dish in cooking.makeable_dishes(food)], ["蛋炒饭", "番茄炒蛋"])

    def test_broken_food_service_returns_empty(self):
        class Broken:
            def load_catalog(self):
                raise RuntimeError("boom")

            def load_inventory(self):
                raise RuntimeError("boom")

        self.assertEqual(cooking.makeable_dishes(Broken()), [])
        self.assertEqual(cooking.makeable_dishes(FakeFood({}, MEALS)), [])


class TasteTests(unittest.TestCase):
    def test_grades(self):
        cases = {100: "S", 92: "S", 91.6: "S", 80: "A", 65: "B", 45: "C", 25: "D", 24: "E", -5: "E", "坏": "E", None: "E"}
        for score, grade in cases.items():
            with self.subTest(score=score):
                self.assertEqual(cooking.rate_taste(score)["grade"], grade)
        self.assertEqual(cooking.rate_taste(150)["score"], 100)

    def test_generous_ingredients_bonus_comment(self):
        self.assertIn("食材给得够实在", cooking.rate_taste(85, 5)["comment"])
        self.assertNotIn("食材给得够实在", cooking.rate_taste(70, 5)["comment"])


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.plugin = SimpleNamespace(data_dir=Path(self._tmp.name), config={})

    def tearDown(self):
        self._tmp.cleanup()

    def test_record_and_mark_served(self):
        dish = {"name": "番茄炒蛋", "ingredients": ["番茄", "鸡蛋"], "method": "炒"}
        taste = cooking.rate_taste(88)
        cooking.record_cook(self.plugin, dish, taste, {"used": ["番茄"], "missing": ["鸡蛋"]}, now=NOW)
        cooking.record_cook(self.plugin, dish, taste, {}, now=NOW)
        cooking.mark_served(self.plugin, "番茄炒蛋", now=NOW)
        history = json.loads((self.plugin.data_dir / cooking.COOK_HISTORY_FILE).read_text(encoding="utf-8"))
        self.assertEqual([item["eaten_by_ai"] for item in history], [False, True])
        self.assertEqual(history[0]["missing"], ["鸡蛋"])
        self.assertEqual(history[1]["grade"], "A")

    def test_history_is_capped(self):
        for index in range(cooking.MAX_HISTORY + 3):
            cooking.record_cook(self.plugin, {"name": f"菜{index}"}, {"score": 50}, {}, now=NOW)
        history = json.loads((self.plugin.data_dir / cooking.COOK_HISTORY_FILE).read_text(encoding="utf-8"))
        self.assertEqual(len(history), cooking.MAX_HISTORY)
        self.assertEqual(history[0]["dish"], "菜3")

    def test_without_interaction_service_nothing_is_consumed(self):
        usage = cooking.consume_ingredients(self.plugin, {"name": "x", "ingredients": ["a", "b"]})
        self.assertEqual(usage, {"used": [], "missing": ["a", "b"]})

    def test_serve_payload(self):
        payload = cooking.serve_interaction_payload("番茄炒蛋", "", persona="p")
        self.assertEqual(payload["item_id"], cooking.KITCHEN_TABLE_ID)
        self.assertEqual(payload["text"], "我下厨做了番茄炒蛋（还行），来吃饭吧。")


if __name__ == "__main__":
    unittest.main()
