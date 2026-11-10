"""DailyPlan parsing: what a valid day looks like and which mistakes are refused."""

import unittest

from astrbot_plugin_simlife_world.core.models import DailyPlan

from tests.fixtures import simple_day


def without(categories, payload):
    payload["outfit"]["items"] = [item for item in payload["outfit"]["items"] if item["category"] not in categories]
    return payload


class PlanParsing(unittest.TestCase):
    def test_round_trip_of_a_full_day(self):
        payload = simple_day()
        payload["timeline"][1]["participant_ids"] = ["p1", "p1"]
        plan = DailyPlan.from_dict(payload)
        self.assertEqual((plan.private_bonus, plan.group_bonus), (2, 1))
        self.assertEqual(plan.timeline[-1].end, "24:00")
        self.assertEqual(plan.timeline[1].participant_ids, ("p1",))  # duplicates collapse
        self.assertEqual(plan.to_dict()["timeline"][1]["participant_ids"], ("p1",))
        self.assertEqual((plan.outfit.style, plan.outfit.items[1].category), ("日常休闲风", "underwear"))

    def test_old_outfits_without_style_still_load(self):
        payload = simple_day()
        del payload["outfit"]["style"]
        self.assertEqual(DailyPlan.from_dict(payload).outfit.style, "未记录")

    def test_halves_can_exist_alone(self):
        schedule_only = DailyPlan.from_dict(simple_day(outfit=None))
        self.assertEqual((schedule_only.has_schedule, schedule_only.has_outfit), (True, False))
        self.assertIsNone(schedule_only.to_dict()["outfit"])
        outfit_only = DailyPlan.from_dict(simple_day(theme="", mood="", timeline=[], proactive_windows=[]))
        self.assertEqual((outfit_only.has_schedule, outfit_only.has_outfit), (False, True))

    def test_refused_payloads(self):
        def edit(change):
            payload = simple_day()
            change(payload)
            return payload

        cases = {
            "empty time": (edit(lambda p: p["timeline"][0].update(start="")), "non-empty HH:MM"),
            "no underpants": (without({"underpants"}, simple_day()), "underpants"),
            "no underwear": (without({"underwear"}, simple_day()), "underwear"),
            "outfit as text": (simple_day(outfit="白衬衫和长裙"), "JSON object"),
            "windows without schedule": (simple_day(timeline=[]), "need a schedule"),
            "gap in the day": (edit(lambda p: p["timeline"][1].update(start="08:00")), ""),
            "unknown window source": (edit(lambda p: p["proactive_windows"][0].update(source_item_id="missing")), ""),
            "window outside its source": (edit(lambda p: p["proactive_windows"][0].update(at="06:59")), "inside"),
            "window without source": (edit(lambda p: p["proactive_windows"][0].pop("source_item_id")), "source_item_id"),
        }
        for name, (payload, message) in cases.items():
            with self.subTest(name), self.assertRaisesRegex(ValueError, message):
                DailyPlan.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
