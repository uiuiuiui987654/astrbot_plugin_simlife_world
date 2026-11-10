import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from astrbot_plugin_simlife_world.core import delivery, goods, item_effects, money

NOW = datetime(2026, 11, 10, 15, 0)


class GoodsTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        money.add(self.data_dir, "p", 500, "初始", at=NOW)

    def tearDown(self):
        self._tmp.cleanup()


class CatalogTests(unittest.TestCase):
    def test_catalog_entries_are_well_formed(self):
        items = goods.load_goods()
        self.assertGreater(len(items), 20)
        ids = [item["id"] for item in items]
        self.assertEqual(len(ids), len(set(ids)), "duplicate goods ids")
        for item in items:
            self.assertTrue(item.get("name"), item)
            self.assertGreaterEqual(float(item.get("price") or 0), 0, item)
            self.assertIn(item.get("category"), goods.DEFAULT_EFFECTS, item)

    def test_find_by_id_name_then_fuzzy(self):
        self.assertEqual(goods.find_goods("MILK_TEA")["id"], "milk_tea")
        self.assertEqual(goods.find_goods("奶茶")["id"], "milk_tea")
        self.assertIsNotNone(goods.find_goods("饮品"))
        self.assertIsNone(goods.find_goods(""))
        self.assertIsNone(goods.find_goods("不存在的东西xyz"))

    def test_list_by_category_and_format(self):
        drinks = goods.list_goods("饮品", limit=3)
        self.assertTrue(drinks and len(drinks) <= 3)
        self.assertTrue(all("饮品" in item["category"] for item in drinks))
        self.assertIn("id=", goods.format_goods(drinks))

    def test_missing_catalog_file_is_empty(self):
        self.assertEqual(goods.load_goods(Path("/nonexistent/goods.json")), [])


class PurchaseTests(GoodsTestCase):
    def test_purchase_charges_and_adds_possessions(self):
        result = goods.purchase(self.data_dir, "p", "奶茶", 2, at=NOW)
        self.assertTrue(result["ok"])
        self.assertEqual(result["amount"], 30.0)
        self.assertEqual(money.balance(self.data_dir, "p"), 470.0)
        self.assertEqual([item["id"] for item in money.possessions(self.data_dir, "p")], ["milk_tea", "milk_tea"])

    def test_quantity_is_clamped(self):
        self.assertEqual(goods.purchase(self.data_dir, "p", "chips", 99, at=NOW)["quantity"], 5)
        self.assertEqual(goods.purchase(self.data_dir, "p", "chips", 0, at=NOW)["quantity"], 1)

    def test_purchase_fails_without_money_or_item(self):
        self.assertFalse(goods.purchase(self.data_dir, "p", "不存在的东西xyz", at=NOW)["ok"])
        money.spend(self.data_dir, "p", 495, "x", at=NOW)
        result = goods.purchase(self.data_dir, "p", "ramen", at=NOW)
        self.assertEqual(result["error"], "余额不足")
        self.assertEqual(money.possessions(self.data_dir, "p"), [])

    def test_delivery_purchase_arrives_later(self):
        result = goods.purchase(self.data_dir, "p", "ramen", 2, at=NOW, delivery_minutes=30)
        self.assertTrue(result["delivery"])
        self.assertEqual(money.possessions(self.data_dir, "p"), [])
        self.assertIn("拉面 ×2", delivery.pending_summary(self.data_dir, "p"))

        self.assertEqual(delivery.deliver_due(self.data_dir, "p", NOW + timedelta(minutes=10)), [])
        arrived = delivery.deliver_due(self.data_dir, "p", NOW + timedelta(minutes=31))
        self.assertEqual(len(arrived), 1)
        self.assertEqual(len(money.possessions(self.data_dir, "p")), 2)
        self.assertEqual(delivery.list_orders(self.data_dir, "p"), [])
        self.assertEqual(delivery.pending_summary(self.data_dir, "p"), "")
        self.assertEqual(len(delivery.recent_delivered(self.data_dir, "p", now=NOW + timedelta(hours=1))), 1)
        self.assertEqual(delivery.recent_delivered(self.data_dir, "p", now=NOW + timedelta(hours=8)), [])

    def test_delivery_is_per_persona(self):
        delivery.place_order(self.data_dir, "other", {"id": "x", "name": "X"}, 1, 1, now=NOW, minutes=0)
        self.assertEqual(delivery.deliver_due(self.data_dir, "p", NOW), [])
        self.assertEqual(len(delivery.list_orders(self.data_dir, "other")), 1)


class UseItemTests(GoodsTestCase):
    def test_consumable_is_used_up_and_affects_needs(self):
        goods.purchase(self.data_dir, "p", "奶茶", at=NOW)
        result = goods.use_item(self.data_dir, "p", "奶茶", at=NOW)
        self.assertTrue(result["consumed"])
        self.assertEqual(money.possessions(self.data_dir, "p"), [])
        needs = item_effects.apply(self.data_dir, "p", {"hydration": 50, "mood": 99}, now=NOW + timedelta(minutes=5))
        self.assertEqual(needs, {"hydration": 78.0, "mood": 100})

    def test_durable_item_is_kept_with_halved_effect(self):
        goods.purchase(self.data_dir, "p", "headphones", at=NOW)
        result = goods.use_item(self.data_dir, "p", "耳机", at=NOW)
        self.assertFalse(result["consumed"])
        self.assertEqual(result["effects"], {"mood": 3.0})
        self.assertEqual(len(money.possessions(self.data_dir, "p")), 1)

    def test_effects_expire(self):
        goods.purchase(self.data_dir, "p", "chips", at=NOW)
        goods.use_item(self.data_dir, "p", "chips", at=NOW)
        later = item_effects.apply(self.data_dir, "p", {"satiety": 10, "mood": 10}, now=NOW + timedelta(hours=3))
        self.assertEqual(later, {"satiety": 10, "mood": 10})

    def test_unknown_item(self):
        self.assertFalse(goods.use_item(self.data_dir, "p", "奶茶")["ok"])
        self.assertFalse(goods.use_item(self.data_dir, "p", "")["ok"])


class ItemEffectTests(GoodsTestCase):
    def test_add_ignores_unknown_and_zero_keys(self):
        self.assertFalse(item_effects.add(self.data_dir, "p", {"luck": 5, "mood": 0})["ok"])
        result = item_effects.add(self.data_dir, "p", {"energy": -30, "luck": 5}, now=NOW, ttl_minutes=1)
        self.assertEqual(result["effects"], {"energy": -30.0})
        # minimum ttl is 5 minutes; result is clamped to 0
        self.assertEqual(item_effects.apply(self.data_dir, "p", {"energy": 10}, now=NOW + timedelta(minutes=4)), {"energy": 0})
        self.assertEqual(item_effects.apply(self.data_dir, "p", {"energy": 10}, now=NOW + timedelta(minutes=6)), {"energy": 10})


if __name__ == "__main__":
    unittest.main()
