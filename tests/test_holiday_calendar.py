"""Chinese public + lunar festivals (needs the real holidays / lunar_python packages)."""

import unittest
from datetime import date

from astrbot_plugin_simlife_world.core.holiday_calendar import ChinaHolidayCalendar

from tests.astrbot_stub import is_stubbed

FESTIVALS_2026 = {
    date(2026, 2, 16): "除夕",
    date(2026, 2, 17): "春节",
    date(2026, 3, 3): "元宵节",
    date(2026, 6, 19): "端午节",
    date(2026, 8, 19): "七夕节",
    date(2026, 9, 25): "中秋节",
    date(2026, 10, 18): "重阳节",
    date(2027, 1, 15): "腊八节",
}


@unittest.skipIf(is_stubbed("holidays") or is_stubbed("lunar_python"), "calendar libraries not installed")
class Festivals(unittest.TestCase):
    calendar = ChinaHolidayCalendar()

    def names_on(self, day):
        return [item["name"] for item in self.calendar.on(day)]

    def test_known_festivals(self):
        for day, name in FESTIVALS_2026.items():
            with self.subTest(day=day):
                self.assertIn(name, self.names_on(day))

    def test_spring_festival_listed_once(self):
        self.assertEqual(self.names_on(date(2026, 2, 17)).count("春节"), 1)

    def test_upcoming_starts_tomorrow(self):
        upcoming = self.calendar.upcoming(date(2026, 9, 24), 2)
        self.assertIn("中秋节", [item["name"] for item in upcoming])
        self.assertNotIn("2026-09-24", [item["date"] for item in upcoming])


if __name__ == "__main__":
    unittest.main()
