"""Window jitter: stable per plan, switchable off, never leaves the source activity."""

import unittest

from astrbot_plugin_simlife_world.core.models import DailyPlan
from astrbot_plugin_simlife_world.core.window_schedule import proactive_window_offset_minutes as offset

from tests.fixtures import simple_day


def plan_with_window_at(at="12:00"):
    payload = simple_day()
    payload["proactive_windows"][0]["at"] = at
    plan = DailyPlan.from_dict(payload)
    return plan, plan.proactive_windows[0]


class WindowJitter(unittest.TestCase):
    def test_same_plan_same_offset(self):
        plan, window = plan_with_window_at()
        self.assertEqual(offset(plan, window, 15), offset(plan, window, 15))
        self.assertEqual(offset(plan, window, 15), 4)

    def test_zero_jitter_means_on_time(self):
        self.assertEqual(offset(*plan_with_window_at(), 0), 0)

    def test_edges_of_the_activity_clamp_the_offset(self):
        self.assertGreaterEqual(offset(*plan_with_window_at("07:00"), 15), 0)
        self.assertLessEqual(offset(*plan_with_window_at("22:59"), 15), 0)


if __name__ == "__main__":
    unittest.main()
