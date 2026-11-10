import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from astrbot_plugin_simlife_world.core import food

CATALOG = Path(food.__file__).resolve().parent / "food_catalog.json"
DAY = date(2026, 11, 10)


class FoodTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self.system = food.FoodSystem(self.data_dir, CATALOG)
        self.catalog = self.system.load_catalog()
        self.category_of = self.system._category_map(self.catalog)

    def tearDown(self):
        self._tmp.cleanup()

    def all_dishes(self):
        for dishes in self.catalog["meals"].values():
            yield from dishes


class CatalogTests(FoodTestCase):
    def test_catalog_has_meals_and_starter_pantry(self):
        self.assertTrue({"早餐", "午餐", "晚餐"} <= set(self.catalog["meals"]))
        self.assertTrue(self.catalog.get("starter_inventory"))
        for dish in self.all_dishes():
            with self.subTest(dish=dish.get("name")):
                self.assertTrue(dish.get("name") and dish.get("ingredients"))

    def test_first_load_seeds_starter_inventory(self):
        inventory = self.system.load_inventory()
        self.assertEqual(len(inventory), len({item["name"] for item in self.catalog["starter_inventory"]}))
        self.assertTrue(self.system.inventory_path().exists())


class DietTests(FoodTestCase):
    def test_detect_diet_keywords(self):
        rules = food.detect_diet("她是素食主义者，不吃辣")
        self.assertTrue(rules.vegetarian and rules.no_spicy)
        self.assertFalse(rules.vegan)
        self.assertTrue(food.detect_diet("严格素食 vegan").vegan)
        self.assertEqual(food.detect_diet(""), food.DietRules())

    def test_rules_filter_dishes(self):
        vegetarian = food.DietRules(vegetarian=True)
        no_spicy = food.DietRules(no_spicy=True)
        for dish in self.all_dishes():
            ingredients = set(dish.get("ingredients") or [])
            if vegetarian.allows(dish, self.category_of):
                for ingredient in ingredients - food.EGG_INGREDIENTS:
                    self.assertNotIn(self.category_of.get(ingredient), food.MEAT_CATEGORIES, (dish["name"], ingredient))
            if no_spicy.allows(dish, self.category_of):
                self.assertNotIn("辣", set(dish.get("tags") or []), dish["name"])
                self.assertFalse(food.SPICY_INGREDIENTS & ingredients, dish["name"])


class MenuTests(FoodTestCase):
    def test_vegetarian_menu_contains_no_meat(self):
        for offset in range(10):
            menu = self.system.plan_day(DAY + timedelta(days=offset), "p", "她吃素")
            for meal in menu["meals"]:
                for ingredient in meal["ingredients"]:
                    if ingredient in food.EGG_INGREDIENTS:
                        continue
                    self.assertNotIn(self.category_of.get(ingredient), food.MEAT_CATEGORIES, (meal, ingredient))

    def test_menu_shape(self):
        menu = self.system.plan_day(DAY, "p", "")
        self.assertEqual((menu["date"], menu["persona_id"]), ("2026-11-10", "p"))
        self.assertEqual([meal["meal"] for meal in menu["meals"]], ["早餐", "午餐", "晚餐"])
        for meal in menu["meals"]:
            self.assertIn(meal["source"], {"home", "out", "simple", "delivery", "skip"})
        self.assertIn("早餐", self.system.format_menu_text(menu))

    def test_state_is_trimmed(self):
        state = self.system._empty_state()
        state["menus"] = {f"2026-01-{day:02d}|p": {} for day in range(1, 32)} | {f"2026-02-{day:02d}|p": {} for day in range(1, 10)}
        state["log"] = [{"i": index} for index in range(600)]
        self.system.save_state(state)
        stored = json.loads(self.system.state_path().read_text(encoding="utf-8"))
        self.assertEqual(len(stored["menus"]), 30)
        self.assertEqual(len(stored["log"]), 500)
        self.assertIn("2026-02-09|p", stored["menus"])

    def test_inventory_normalisation(self):
        self.system.inventory_path().write_text(
            json.dumps({"ingredients": [{"name": " 鸡蛋 ", "quantity": "6"}, {"name": ""}, "坏数据", {"name": "盐", "quantity": None, "category": ""}]}, ensure_ascii=False),
            encoding="utf-8",
        )
        inventory = self.system.load_inventory()
        self.assertEqual(set(inventory), {"鸡蛋", "盐"})
        self.assertEqual(inventory["鸡蛋"]["quantity"], 6)
        self.assertEqual(inventory["盐"]["category"], "其他")


if __name__ == "__main__":
    unittest.main()
