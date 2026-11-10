import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from astrbot_plugin_simlife_world.core import money, transport

NOW = datetime(2026, 11, 10, 20, 0)


def plan(*items):
    return {
        "timeline": [
            {"id": f"t{index}", "start": start, "end": end, "activity": activity}
            for index, (start, end, activity) in enumerate(items)
        ]
    }


class MoneyTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def stored(self):
        return json.loads((self.data_dir / "money.json").read_text(encoding="utf-8"))


class WalletTests(MoneyTestCase):
    def test_new_wallet_is_empty_and_not_written(self):
        self.assertEqual(money.balance(self.data_dir, "p"), 0.0)
        self.assertFalse((self.data_dir / "money.json").exists())

    def test_add_and_spend_round_to_cents(self):
        money.add(self.data_dir, "p", 10.004, "红包", at=NOW)
        result = money.spend(self.data_dir, "p", 3.333, "奶茶", at=NOW)
        self.assertTrue(result["ok"])
        self.assertAlmostEqual(money.balance(self.data_dir, "p"), 6.67)
        kinds = [item["kind"] for item in money.snapshot(self.data_dir, "p")["transactions"]]
        self.assertEqual(kinds, ["income", "spend"])

    def test_zero_add_is_noop(self):
        money.add(self.data_dir, "p", 0, "无")
        self.assertFalse((self.data_dir / "money.json").exists())

    def test_spend_rejects_overdraft_and_non_positive(self):
        money.add(self.data_dir, "p", 5, "零花", at=NOW)
        self.assertEqual(money.spend(self.data_dir, "p", 6, "x")["error"], "余额不足")
        self.assertFalse(money.spend(self.data_dir, "p", 0, "x")["ok"])
        self.assertEqual(money.balance(self.data_dir, "p"), 5.0)

    def test_negative_spend_amount_is_treated_as_positive(self):
        money.add(self.data_dir, "p", 5, "零花", at=NOW)
        money.spend(self.data_dir, "p", -2, "x", at=NOW)
        self.assertEqual(money.balance(self.data_dir, "p"), 3.0)

    def test_wallets_are_per_persona(self):
        money.add(self.data_dir, "a", 7, "x", at=NOW)
        self.assertEqual(money.balance(self.data_dir, "b"), 0.0)
        self.assertEqual(money.balance(self.data_dir, "a"), 7.0)

    def test_transaction_history_is_capped(self):
        for _ in range(money.MAX_TRANSACTIONS + 15):
            money.add(self.data_dir, "p", 1, "x", at=NOW)
        wallet = self.stored()["wallets"]["p"]
        self.assertEqual(len(wallet["transactions"]), money.MAX_TRANSACTIONS)
        self.assertEqual(wallet["balance"], money.MAX_TRANSACTIONS + 15)

    def test_corrupt_file_reads_as_empty(self):
        (self.data_dir / "money.json").write_text("{oops", encoding="utf-8")
        self.assertEqual(money.balance(self.data_dir, "p"), 0.0)
        money.add(self.data_dir, "p", 2, "x", at=NOW)
        self.assertEqual(money.balance(self.data_dir, "p"), 2.0)

    def test_spent_on_counts_only_spend_kind_that_day(self):
        money.add(self.data_dir, "p", 100, "x", at=NOW)
        money.spend(self.data_dir, "p", 10, "a", at=NOW)
        money.spend(self.data_dir, "p", 5, "b", kind="gift", at=NOW)
        money.spend(self.data_dir, "p", 7, "c", at=datetime(2026, 11, 9, 9))
        self.assertEqual(money.spent_on(self.data_dir, "p", "2026-11-10"), 10.0)

    def test_format_money(self):
        self.assertEqual(money.format_money(12), "12")
        self.assertEqual(money.format_money(12.5), "12.50")
        self.assertEqual(money.format_money(None), "0")


class GoalTests(MoneyTestCase):
    def test_goal_validation(self):
        self.assertFalse(money.set_goal(self.data_dir, "p", "", 10)["ok"])
        self.assertFalse(money.set_goal(self.data_dir, "p", "相机", 0)["ok"])

    def test_goal_progress_and_fulfil(self):
        money.set_goal(self.data_dir, "p", "相机", 50, wish="拍星空", at=NOW)
        money.add(self.data_dir, "p", 30, "x", at=NOW)
        goal = money.snapshot(self.data_dir, "p")["goal"]
        self.assertEqual((goal["remaining"], goal["achieved"]), (20.0, False))
        self.assertFalse(money.fulfill_goal(self.data_dir, "p", at=NOW)["ok"])

        money.add(self.data_dir, "p", 25, "x", at=NOW)
        result = money.fulfill_goal(self.data_dir, "p", at=NOW)
        self.assertTrue(result["ok"])
        self.assertEqual(result["balance"], 5.0)
        self.assertTrue(result["goal"]["fulfilled"])
        self.assertEqual(money.possessions(self.data_dir, "p")[-1]["category"], "愿望")
        self.assertFalse(money.fulfill_goal(self.data_dir, "p", at=NOW)["ok"])

    def test_clear_and_request_goal(self):
        self.assertFalse(money.mark_goal_requested(self.data_dir, "p")["ok"])
        money.set_goal(self.data_dir, "p", "相机", 50, at=NOW)
        self.assertTrue(money.mark_goal_requested(self.data_dir, "p", at=NOW)["goal"]["requested_at"])
        self.assertEqual(money.clear_goal(self.data_dir, "p"), {"ok": True, "cleared": True})
        self.assertIsNone(money.snapshot(self.data_dir, "p")["goal"])


class WorkAndExpenseTests(MoneyTestCase):
    DAY = plan(
        ("07:00", "07:30", "吃早饭"),
        ("08:00", "08:40", "地铁通勤"),
        ("09:00", "12:00", "在公司写代码"),
        ("12:00", "12:45", "吃午饭"),
        ("13:30", "18:00", "开会和做方案"),
        ("18:30", "19:00", "骑单车回家"),
        ("19:00", "20:00", "吃晚饭"),
        ("21:00", "22:00", "看书"),
    )

    def test_work_segments_respect_cutoff(self):
        self.assertEqual(money.work_minutes(self.DAY), 180 + 270)
        self.assertEqual(money.work_minutes(self.DAY, before=datetime(2026, 11, 10, 13)), 180)

    def test_expense_segments_price_by_kind_and_mode(self):
        costs = {segment["activity"]: segment["cost"] for segment in money.expense_segments(self.DAY)}
        self.assertEqual(costs["吃早饭"], 8.0)
        self.assertEqual(costs["吃午饭"], 18.0)
        self.assertEqual(costs["吃晚饭"], 22.0)
        self.assertEqual(costs["地铁通勤"], transport.cost_for("地铁"))
        self.assertEqual(costs["骑单车回家"], 1.5)
        self.assertNotIn("看书", costs)

    def test_walking_is_free_and_skipped(self):
        segments = money.expense_segments(plan(("08:00", "08:20", "走路去公司")))
        self.assertEqual(segments, [])

    def test_work_settlement_is_idempotent_per_segment(self):
        noon = datetime(2026, 11, 10, 12, 30)
        first = money.settle_work_segments(self.data_dir, "p", "2026-11-10", self.DAY, before=noon, hourly_rate=20, at=noon)
        self.assertEqual((first["minutes"], first["amount"]), (180, 60.0))
        again = money.settle_work_segments(self.data_dir, "p", "2026-11-10", self.DAY, before=noon, hourly_rate=20)
        self.assertTrue(again["skipped"])
        evening = money.settle_work_segments(self.data_dir, "p", "2026-11-10", self.DAY, hourly_rate=20, at=NOW)
        self.assertEqual((evening["minutes"], evening["settled_count"]), (270, 1))
        self.assertEqual(money.balance(self.data_dir, "p"), 150.0)

    def test_legacy_settled_day_is_not_paid_again(self):
        money.add(self.data_dir, "p", 1, "x", at=NOW)
        content = self.stored()
        content["wallets"]["p"]["settled_work_dates"] = ["2026-11-10"]
        (self.data_dir / "money.json").write_text(json.dumps(content), encoding="utf-8")
        self.assertTrue(money.settle_work_income(self.data_dir, "p", "2026-11-10", self.DAY)["skipped"])

    def test_expenses_may_create_debt_and_settle_once(self):
        result = money.settle_expense_segments(self.data_dir, "p", "2026-11-10", self.DAY, at=NOW)
        expected = 8 + 4 + 18 + 1.5 + 22
        self.assertEqual(result["amount"], expected)
        self.assertEqual(money.balance(self.data_dir, "p"), -expected)
        self.assertTrue(money.settle_expense_segments(self.data_dir, "p", "2026-11-10", self.DAY)["skipped"])
        self.assertFalse(money.settle_expense_segments(self.data_dir, "p", "2026-11-11", self.DAY)["skipped"])

    def test_empty_day_is_skipped(self):
        self.assertTrue(money.settle_work_segments(self.data_dir, "p", "", self.DAY)["skipped"])
        self.assertTrue(money.settle_expense_segments(self.data_dir, "p", "2026-11-10", plan())["skipped"])


class PossessionTests(MoneyTestCase):
    def test_add_place_and_remove(self):
        money.add_possession(self.data_dir, "p", {"id": "plant", "name": "绿萝", "price": 30}, at=NOW)
        money.add_possession(self.data_dir, "p", {"id": "lamp", "name": "台灯", "price": 60}, at=NOW)
        first = money.place_possession(self.data_dir, "p", "绿萝", "客厅")
        second = money.place_possession(self.data_dir, "p", "lamp", "客厅")
        self.assertTrue(first["ok"] and second["ok"])
        self.assertNotEqual(first["item"]["place"], second["item"]["place"])

        explicit = money.place_possession(self.data_dir, "p", "绿萝", "客厅", x=2, y=-1, z_cm=500)
        self.assertEqual((explicit["item"]["place"]["x"], explicit["item"]["place"]["y"]), (0.95, 0.05))
        self.assertEqual(explicit["item"]["place"]["z_cm"], 200.0)

        self.assertFalse(money.place_possession(self.data_dir, "p", "沙发", "客厅")["ok"])
        self.assertFalse(money.place_possession(self.data_dir, "p", "绿萝", "")["ok"])
        self.assertEqual(money.remove_possession(self.data_dir, "p", "PLANT")["item"]["name"], "绿萝")
        self.assertFalse(money.remove_possession(self.data_dir, "p", "绿萝")["ok"])

    def test_backfill_gives_room_only_items_a_place(self):
        money.add_possession(self.data_dir, "p", {"id": "a", "name": "A"}, at=NOW)
        content = self.stored()
        content["wallets"]["p"]["possessions"][0]["room"] = "卧室"
        (self.data_dir / "money.json").write_text(json.dumps(content), encoding="utf-8")
        self.assertTrue(money.backfill_placements(self.data_dir))
        self.assertIn("place", money.possessions(self.data_dir, "p")[0])
        self.assertFalse(money.backfill_placements(self.data_dir))


if __name__ == "__main__":
    unittest.main()
