import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from astrbot_plugin_simlife_world.core import travel

CATALOG = Path(travel.__file__).resolve().parent / "travel_destinations.json"
TODAY = date(2026, 11, 10)


class TravelTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self.service = travel.TravelService(self.data_dir, CATALOG)

    def tearDown(self):
        self._tmp.cleanup()

    def fresh_service(self):
        return travel.TravelService(self.data_dir, CATALOG)


class CatalogTests(TravelTestCase):
    def test_catalog_entries_are_complete(self):
        catalog = self.service.catalog()
        self.assertGreaterEqual(len(catalog), 10)
        keys = [item["key"] for item in catalog]
        self.assertEqual(len(keys), len(set(keys)))
        for item in catalog:
            with self.subTest(item=item["key"]):
                self.assertIn(item.get("region"), {"domestic", "overseas"})
                self.assertLessEqual(item["min_days"], item["max_days"])
                self.assertTrue(item.get("highlights") and item.get("lodging"))

    def test_destination_lookup(self):
        self.assertEqual(self.service.destination("HANGZHOU")["name"], "杭州")
        self.assertEqual(self.service.destination("杭州")["key"], "hangzhou")
        self.assertIsNone(self.service.destination(""))
        self.assertIn("国内：", self.service.destination_list_text())

    def test_settings_are_clamped(self):
        config = travel.TravelService.settings({"chance_per_day": 5, "min_days": 6, "max_days": 2, "enable": "false"})
        self.assertEqual((config["chance_per_day"], config["min_days"], config["max_days"]), (1.0, 6, 6))
        self.assertFalse(config["enable"])


class ManualTripTests(TravelTestCase):
    def test_plan_persist_and_phases(self):
        depart = TODAY + timedelta(days=5)
        trip, error = self.service.plan("p", "杭州", depart=depart, days=3, today=TODAY)
        self.assertEqual(error, "")
        self.assertEqual((trip.depart, trip.back, trip.length), ("2026-11-15", "2026-11-17", 3))
        self.assertEqual(len(trip.itinerary), 3)

        reloaded = self.fresh_service()
        self.assertEqual([item.id for item in reloaded.trips_for("p")], [trip.id])
        stored = json.loads((self.data_dir / "trips.json").read_text(encoding="utf-8"))
        self.assertEqual(stored["trips"][0]["city"], "杭州")

        phases = {offset: reloaded.phase(trip, TODAY + timedelta(days=offset)) for offset in (0, 4, 5, 6, 7, 8, 9, 10)}
        self.assertEqual(
            phases,
            {0: "countdown", 4: "eve", 5: "depart", 6: "away", 7: "return", 8: "afterglow", 9: "afterglow", 10: "none"},
        )
        covering = reloaded.covering("p", TODAY + timedelta(days=6))
        self.assertEqual(covering[1], "away")
        self.assertIn("已出发第 2 天", reloaded.describe(trip, TODAY + timedelta(days=6)))

    def test_overlapping_trip_is_rejected_until_cancelled(self):
        self.service.plan("p", "杭州", depart=TODAY + timedelta(days=5), days=3, today=TODAY)
        trip, error = self.service.plan("p", "苏州", depart=TODAY + timedelta(days=6), days=2, today=TODAY)
        self.assertIsNone(trip)
        self.assertIn("杭州", error)
        # another persona is independent
        self.assertIsNotNone(self.service.plan("q", "苏州", depart=TODAY + timedelta(days=6), days=2, today=TODAY)[0])

        cancelled = self.service.cancel("p", TODAY)
        self.assertEqual(cancelled.city, "杭州")
        self.assertIsNone(self.service.covering("p", TODAY + timedelta(days=6)))
        self.assertIsNotNone(self.service.plan("p", "苏州", depart=TODAY + timedelta(days=6), days=2, today=TODAY)[0])

    def test_plan_validation(self):
        self.assertIn("没有找到目的地", self.service.plan("p", "火星", today=TODAY)[1])
        self.assertIn("不能早于今天", self.service.plan("p", "杭州", depart=TODAY - timedelta(days=1), today=TODAY)[1])
        self.assertIn("已关闭", self.service.plan("p", "杭州", today=TODAY, settings={"enable": False})[1])
        self.assertIsNone(self.service.cancel("p", TODAY))

    def test_trip_length_is_clamped_to_settings(self):
        trip, _ = self.service.plan("p", "杭州", depart=TODAY + timedelta(days=1), days=40, today=TODAY)
        self.assertEqual(trip.length, travel.TravelService.settings(None)["max_days"])

    def test_same_day_trip_ids_are_unique(self):
        first, _ = self.service.plan("p", "杭州", depart=TODAY + timedelta(days=1), days=1, today=TODAY)
        self.service.cancel("p", TODAY)
        second, _ = self.service.plan("p", "杭州", depart=TODAY + timedelta(days=1), days=1, today=TODAY)
        self.assertNotEqual(first.id, second.id)

    def test_away_day_moves_home_locations_to_lodging(self):
        from dataclasses import dataclass

        from astrbot_plugin_simlife_world.core.models import TimelineItem
        from tests.fixtures import life_timeline

        def items(**kwargs):
            return tuple(TimelineItem.from_dict(item) for item in life_timeline(**kwargs))

        @dataclass(frozen=True)
        class Plan:
            timeline: tuple

        trip, _ = self.service.plan("p", "杭州", depart=TODAY + timedelta(days=1), days=3, today=TODAY)
        fixed, changes = self.service.apply(Plan(items(location="家")), trip, "away")
        self.assertTrue(changes)
        self.assertEqual({item.location for item in fixed.timeline}, {"杭州·住处"})
        unchanged, none = self.service.apply(Plan(items()), trip, "countdown")
        self.assertEqual(none, [])

    def test_location_helpers(self):
        for location in ("家", "家里", "家·卧室", "客厅", "二楼书房"):
            self.assertTrue(travel.is_home_location(location), location)
        for location in ("杭州·西湖", "农家乐", "家具店", ""):
            self.assertFalse(travel.is_home_location(location), location)
        self.assertEqual(travel.season_of(date(2026, 1, 5)), "冬")
        self.assertEqual(travel.season_of(date(2026, 7, 5)), "夏")


if __name__ == "__main__":
    unittest.main()
