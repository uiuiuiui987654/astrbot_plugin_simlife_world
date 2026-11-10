import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from astrbot_plugin_simlife_world.core import health_journal

DAY = datetime(2026, 11, 10, 20, 0)

SICK = {"sick": True, "health": 35, "summary": "发烧了", "fever": True}
WELL = {"sick": False, "health": 80, "sleep_debt_minutes": 0, "satiety": 70, "hygiene": 70, "summary": ""}


class HealthJournalTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def update(self, needs, day_offset):
        return health_journal.update(self.data_dir, "p", dict(needs), DAY + timedelta(days=day_offset))

    def test_healthy_day_is_plain(self):
        result = self.update(WELL, 0)
        self.assertEqual((result["health_status"], result["sick_days"], result["recovery_days_left"]), ("healthy", 0, 0))
        self.assertFalse(result["weak_constitution"])

    def test_sick_days_count_from_onset(self):
        self.assertEqual(self.update(SICK, 0)["sick_days"], 1)
        third = self.update(SICK, 2)
        self.assertEqual((third["sick_days"], third["health_status"]), (3, "sick"))
        self.assertIn("病程第 3 天", third["summary"])

    def test_full_episode_sick_recovering_healthy(self):
        self.update(SICK, 0)
        self.update(SICK, 1)
        recovering = self.update(dict(WELL, fever=True), 2)
        self.assertEqual(recovering["health_status"], "recovering")
        self.assertEqual(recovering["recovery_required_days"], 3)  # fever needs 3 days
        self.assertTrue(recovering["fever_recovery"])
        self.assertIn("刚退烧", recovering["summary"])
        self.assertEqual(recovering["episodes"], [{"onset": "2026-11-10", "recovered": "2026-11-12", "days": 2}])

        # good state shortens the remaining recovery to 1 day
        healed = self.update(WELL, 3)
        self.assertEqual(healed["health_status"], "healthy")

        state = health_journal.persona_state(self.data_dir, "p", today=date(2026, 11, 14))
        self.assertEqual(state["recent_illness_days"], 2)
        self.assertFalse(state["weak_constitution"])

    def test_harmful_actions_extend_recovery(self):
        self.update(SICK, 0)
        self.update(dict(WELL, fever=False), 1)
        worse = self.update(
            dict(WELL, symptoms=["发烧"], harmful_actions=["跑步5公里"]), 2
        )
        self.assertEqual((worse["health_status"], worse["recovery_required_days"]), ("recovering", 3))
        self.assertIn("不太适合养病", worse["summary"])

    def test_repeated_illness_makes_constitution_weak(self):
        offset = 0
        for _ in range(3):
            for day in range(3):
                self.update(SICK, offset + day)
            offset += 3
            for day in range(4):
                self.update(WELL, offset + day)
            offset += 4
        state = health_journal.persona_state(self.data_dir, "p", today=(DAY + timedelta(days=offset)).date())
        self.assertGreaterEqual(state["recent_illness_days"], 7)
        self.assertTrue(state["weak_constitution"])

    def test_invalid_input_passthrough(self):
        self.assertEqual(health_journal.update(self.data_dir, "", {"a": 1}, DAY), {"a": 1})
        self.assertEqual(health_journal.persona_state(self.data_dir, ""), {})
        self.assertEqual(health_journal.persona_state(self.data_dir, "nobody"), {})
        health_journal.journal_path(self.data_dir).write_text("[]", encoding="utf-8")
        self.assertEqual(self.update(WELL, 0)["health_status"], "healthy")


if __name__ == "__main__":
    unittest.main()
