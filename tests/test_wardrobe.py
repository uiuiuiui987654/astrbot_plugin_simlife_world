import unittest
from datetime import datetime

from astrbot_plugin_simlife_world.core import wardrobe
from astrbot_plugin_simlife_world.core.models import Outfit, OutfitItem

OUTFIT = {
    "style": "通勤",
    "summary": "白衬衫配半身裙",
    "items": [
        {"category": "top", "name": "白衬衫"},
        {"category": "bottom", "name": "灰色半身裙"},
        {"category": "shoes", "name": "乐福鞋"},
        {"category": "underwear", "name": "不该出现"},
    ],
}


def at(hour, minute=0):
    return datetime(2026, 11, 10, hour, minute)


class OutfitDescriptionTests(unittest.TestCase):
    def test_outside_lists_shoes_inside_does_not(self):
        outside = wardrobe.outfit_description(OUTFIT)
        self.assertEqual(outside, "通勤——白衬衫配半身裙（白衬衫、灰色半身裙、乐福鞋）")
        inside = wardrobe.outfit_description(OUTFIT, home=True)
        self.assertNotIn("乐福鞋", inside)
        self.assertTrue(inside.endswith("赤脚或穿室内拖鞋。"))
        self.assertNotIn("不该出现", outside)

    def test_object_outfit_and_empty(self):
        outfit = Outfit.from_dict(OUTFIT)
        self.assertIn("白衬衫", wardrobe.outfit_description(outfit))
        self.assertEqual(wardrobe.outfit_description(None), "")


class AppearanceTests(unittest.TestCase):
    def test_night_at_home_is_sleepwear(self):
        look = wardrobe.appearance_for("卧室", "睡觉", "sleep", at(2), outfit=OUTFIT)
        self.assertTrue(look["is_sleepwear"])
        self.assertEqual(look["night_id"], "2026-11-09", "after midnight keeps the previous night's set")

    def test_daytime_home_uses_day_outfit(self):
        look = wardrobe.appearance_for("客厅", "看书", "available", at(15), outfit=OUTFIT)
        self.assertFalse(look["is_sleepwear"])
        self.assertEqual(look["key"], "daily_outfit")

    def test_outside_never_sleepwear(self):
        look = wardrobe.appearance_for("公司", "睡觉", "sleep", at(23), outfit=OUTFIT)
        self.assertFalse(look["is_sleepwear"])

    def test_hotel_counts_as_resting_inside(self):
        self.assertTrue(wardrobe.appearance_for("杭州·民宿", "睡觉", "sleep", at(1))["is_sleepwear"])

    def test_nap_and_activity_keep_day_clothes(self):
        self.assertFalse(wardrobe.appearance_for("卧室", "午睡", "sleep", at(13))["is_sleepwear"])
        self.assertFalse(wardrobe.appearance_for("客厅", "做饭", "busy", at(23))["is_sleepwear"])

    def test_morning_dressing_in_timeline_ends_pajamas(self):
        timeline = [{"start": "07:00", "activity": "洗漱换日常装"}, {"start": "07:30", "activity": "吃早饭"}]
        self.assertTrue(wardrobe.appearance_for("餐厅", "吃早饭", "available", at(7, 45))["is_sleepwear"])
        self.assertFalse(
            wardrobe.appearance_for("餐厅", "吃早饭", "available", at(7, 45), timeline=timeline)["is_sleepwear"]
        )

    def test_early_bedtime_in_timeline_starts_pajamas(self):
        timeline = [{"start": "19:30", "activity": "换上睡衣"}]
        self.assertTrue(
            wardrobe.appearance_for("客厅", "看电视", "available", at(20, 30), timeline=timeline)["is_sleepwear"]
        )

    def test_context_text(self):
        text = wardrobe.appearance_context("客厅", "看书", "available", at(15))
        self.assertIn("今日穿搭未记录", text)
        text = wardrobe.appearance_context("卧室", "睡觉", "sleep", at(23), outfit=OUTFIT)
        self.assertIn("今日穿搭：", text)


class LegacyMigrationTests(unittest.TestCase):
    def test_legacy_forced_maid_text_is_cleaned(self):
        outfit = Outfit(
            style="日常",
            summary="不改固定形象的白紫女仆裙",
            items=(OutfitItem(category="top", name="白紫鲸鱼女仆裙上装", details="固定立绘的白紫女仆裙上装"),),
        )
        cleaned = wardrobe.migrate_legacy_forced_outfit(outfit)
        self.assertNotIn("女仆", cleaned.summary)
        self.assertEqual(cleaned.items[0].name, "白紫收腰针织上衣")

    def test_user_chosen_maid_outfit_is_kept(self):
        outfit = Outfit(style="女仆", summary="今天想穿女仆装", items=(OutfitItem(category="dress", name="黑白女仆裙"),))
        self.assertIs(wardrobe.migrate_legacy_forced_outfit(outfit), outfit)
        self.assertIsNone(wardrobe.migrate_legacy_forced_outfit(None))


if __name__ == "__main__":
    unittest.main()
