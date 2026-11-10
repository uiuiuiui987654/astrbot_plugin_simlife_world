import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from astrbot_plugin_simlife_world.core import garage

NOW = datetime(2026, 11, 10, 10, 0)


class GarageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_default_fleet_and_parked_context(self):
        snap = garage.snapshot(self.data_dir, "p", now=NOW)
        self.assertEqual([car["id"] for car in snap["vehicles"]], ["car_white", "car_jeep", "car_sports"])
        self.assertIsNone(snap["trip"])
        self.assertIn("车库停着白色小车、吉普、跑车", garage.context(self.data_dir, "p", now=NOW))

    def test_old_single_car_save_gains_missing_cars(self):
        path = self.data_dir / "garage.json"
        path.write_text(json.dumps({"personas": {"p": {"vehicles": [dict(garage.DEFAULT_VEHICLE, fuel=5)], "trips": []}}}), encoding="utf-8")
        snap = garage.snapshot(self.data_dir, "p", now=NOW)
        self.assertEqual(len(snap["vehicles"]), 3)
        self.assertEqual(snap["vehicles"][0]["fuel"], 5)
        self.assertEqual(len(json.loads(path.read_text(encoding="utf-8"))["personas"]["p"]["vehicles"]), 3)

    def test_trip_lifecycle_auto_return(self):
        result = garage.start(self.data_dir, "p", "海边", "master", now=NOW, minutes=60, vehicle_id="car_jeep")
        self.assertTrue(result["ok"])
        self.assertEqual(result["vehicle"]["fuel"], 82 - garage.TRIP_FUEL_COST)
        self.assertIn("吉普不在，主人开车带她去了海边，预计 11:00 回来", garage.context(self.data_dir, "p", now=NOW))
        self.assertIn("已经开出去", garage.start(self.data_dir, "p", "公园", "self", now=NOW, vehicle_id="吉普")["error"])

        later = NOW + timedelta(minutes=61)
        snap = garage.snapshot(self.data_dir, "p", now=later)
        jeep = next(car for car in snap["vehicles"] if car["id"] == "car_jeep")
        self.assertEqual(jeep["status"], "parked")
        self.assertEqual(snap["history"][0]["status"], "returned")

        returns = garage.recent_returns(self.data_dir, "p", now=later)
        self.assertEqual([trip["destination"] for trip in returns], ["海边"])
        garage.mark_noted(self.data_dir, "p", returns[0]["id"])
        self.assertEqual(garage.recent_returns(self.data_dir, "p", now=later), [])

    def test_trip_length_is_clamped(self):
        short = garage.start(self.data_dir, "p", "公园", "self", now=NOW, minutes=5)
        self.assertEqual(short["trip"]["eta"], (NOW + timedelta(minutes=30)).isoformat(timespec="seconds"))
        long = garage.start(self.data_dir, "p", "公园", "x", now=NOW, minutes=999, vehicle_id="car_sports")
        self.assertEqual(long["trip"]["eta"], (NOW + timedelta(minutes=240)).isoformat(timespec="seconds"))
        self.assertEqual(long["trip"]["driver"], "self")

    def test_manual_return_and_refuel(self):
        self.assertIn("已经在车库", garage.return_home(self.data_dir, "p", now=NOW)["error"])
        garage.start(self.data_dir, "p", "书店", "self", now=NOW)
        self.assertIn("不在车库", garage.refuel(self.data_dir, "p", now=NOW)["error"])
        back = garage.return_home(self.data_dir, "p", now=NOW + timedelta(minutes=10))
        self.assertEqual(back["trip"]["status"], "returned")
        refuel = garage.refuel(self.data_dir, "p", now=NOW)
        self.assertEqual((refuel["vehicle"]["fuel"], refuel["cost"]), (garage.REFUEL_TO, garage.REFUEL_COST))

    def test_validation(self):
        self.assertFalse(garage.start(self.data_dir, "p", "  ", "self", now=NOW)["ok"])
        self.assertEqual(garage.start(self.data_dir, "p", "海边", "self", now=NOW, vehicle_id="tank")["error"], "没有这辆车")

    def test_low_fuel_blocks_trip(self):
        garage.snapshot(self.data_dir, "p", now=NOW)
        path = self.data_dir / "garage.json"
        content = json.loads(path.read_text(encoding="utf-8"))
        content["personas"]["p"]["vehicles"][0]["fuel"] = garage.TRIP_FUEL_COST - 1
        path.write_text(json.dumps(content), encoding="utf-8")
        self.assertIn("油不够", garage.start(self.data_dir, "p", "海边", "self", now=NOW)["error"])

    def test_trip_history_is_capped(self):
        for index in range(35):
            garage.refuel(self.data_dir, "p", now=NOW)
            garage.start(self.data_dir, "p", f"地点{index}", "self", now=NOW)
            garage.return_home(self.data_dir, "p", now=NOW)
        content = json.loads((self.data_dir / "garage.json").read_text(encoding="utf-8"))
        self.assertEqual(len(content["personas"]["p"]["trips"]), 30)


if __name__ == "__main__":
    unittest.main()
