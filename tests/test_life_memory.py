import json
import tempfile
import unittest
import unittest.mock
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from astrbot_plugin_simlife_world.core import affection, encounters, garage, life_memory, money
from astrbot_plugin_simlife_world.core.models import TimelineItem, Weather

DAY = date(2026, 11, 10)


def plan_for(day, rows, condition="小雨"):
    items = tuple(
        TimelineItem.from_dict(
            {"id": f"t{i}", "start": s, "end": e, "activity": a, "location": loc, "state": st, "availability": "normal"}
        )
        for i, (s, e, a, loc, st) in enumerate(rows)
    )
    weather = Weather.from_dict({"condition": condition, "temperature_low": 12, "temperature_high": 18})
    return SimpleNamespace(date=day.isoformat(), timeline=items, weather=weather, persona_id="p")


ROWS = [
    ("00:00", "07:00", "睡觉", "卧室", "sleep"),
    ("07:00", "07:40", "吃早饭", "餐厅", "available"),
    ("07:40", "08:30", "坐地铁去公司", "路上", "transit"),
    ("08:30", "12:00", "在公司开会", "公司", "busy"),
    ("12:00", "13:00", "吃午饭", "公司食堂", "available"),
    ("13:00", "18:00", "写方案", "公司", "focus"),
    ("18:00", "18:40", "骑单车回家", "路上", "transit"),
    ("18:40", "19:30", "吃晚饭", "餐厅", "available"),
    ("19:30", "24:00", "看书然后睡觉", "卧室", "available"),
]


class MemoryTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self.plan = plan_for(DAY, ROWS)
        (self.data_dir / "food_state.json").write_text(
            json.dumps(
                {
                    "log": [{"date": DAY.isoformat(), "persona_id": "p", "meal": "早餐", "dish": "葱油拌面", "source": "home"}],
                    "menus": {
                        f"{DAY.isoformat()}::p": {
                            "meals": [
                                {"meal": "早餐", "dish": "燕麦牛奶碗", "source": "home"},
                                {"meal": "午餐", "dish": "牛肉饭", "source": "out"},
                                {"meal": "晚餐", "dish": "番茄炒蛋", "source": "home"},
                            ]
                        }
                    },
                    "shopping": [{"date": DAY.isoformat(), "persona_id": "p", "scene": "菜市场", "items": ["番茄", "鸡蛋"]}],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def sync(self, hour=23, minute=0, day=DAY, plan=None):
        moment = datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute)
        return life_memory.sync_day(self.data_dir, "p", day, plan or self.plan, now=moment)


class EncounterTests(unittest.TestCase):
    def test_tags(self):
        tags = encounters.context_tags("坐地铁去公司", "路上", "小雨", 8)
        self.assertEqual(tags, {"subway", "rain", "morning"})
        self.assertIn("walk", encounters.context_tags("出门", "路上", "晴", 15))
        self.assertIn("hot", encounters.context_tags("骑车", "路上", "", 13, temperature=35))

    def test_on_the_way(self):
        self.assertTrue(encounters.is_on_the_way("坐地铁去公司", "路上", "transit"))
        self.assertTrue(encounters.is_on_the_way("骑单车回家", "路上"))
        self.assertFalse(encounters.is_on_the_way("在客厅散步", "客厅"))
        self.assertFalse(encounters.is_on_the_way("开会", "公司"))

    def test_pick_is_deterministic_and_respects_tags(self):
        tags = {"subway", "rain", "morning"}
        first = encounters.pick("seed", tags, chance=1)
        self.assertEqual(first, encounters.pick("seed", tags, chance=1))
        allowed = {text for need, text in encounters.ENCOUNTERS if need <= tags}
        for index in range(50):
            text = encounters.pick(f"s{index}", tags, chance=1)
            self.assertIn(text, allowed)
        self.assertEqual(encounters.pick("seed", tags, chance=0), "")
        self.assertNotEqual(encounters.pick("seed", tags, chance=1, exclude={first}), first)


class SyncTests(MemoryTestCase):
    def test_meals_log_first_then_menu_fallback(self):
        items = self.sync()
        meals = {item["key"]: item["text"] for item in items if item["kind"] == "meal"}
        self.assertEqual(meals["meal:早餐"], "早餐吃了葱油拌面（在家做的）")
        self.assertEqual(meals["meal:午餐"], "午餐吃了牛肉饭（在外面吃的）")
        self.assertEqual(meals["meal:晚餐"], "晚餐吃了番茄炒蛋（在家做的）")
        times = {item["key"]: item["time"] for item in items if item["kind"] == "meal"}
        self.assertEqual(times["meal:晚餐"], "18:40")
        self.assertTrue(any(item["kind"] == "shopping" and "番茄" in item["text"] for item in items))

    def test_only_what_already_happened_today(self):
        items = self.sync(hour=9)
        kinds = [(item["kind"], item["key"]) for item in items]
        self.assertIn(("meal", "meal:早餐"), kinds)
        self.assertNotIn(("meal", "meal:午餐"), kinds)
        self.assertFalse(any(key == "encounter:18:00" for _, key in kinds), "evening ride has not happened yet")

    def test_encounters_on_transit_segments(self):
        with unittest.mock.patch.object(encounters, "CHANCE", 1.0):
            items = self.sync()
            rides = {item["key"]: item["text"] for item in items if item["kind"] == "encounter"}
            self.assertEqual(set(rides), {"encounter:07:40", "encounter:18:00"})
            self.assertTrue(rides["encounter:07:40"].startswith("坐地铁去公司时，"))
            self.assertTrue(rides["encounter:18:00"].startswith("骑单车回家时，"))
            self.assertNotEqual(rides["encounter:07:40"].split("，", 1)[1], rides["encounter:18:00"].split("，", 1)[1])
            # deterministic: syncing again changes nothing
            self.assertEqual(self.sync(), items)
        with unittest.mock.patch.object(encounters, "CHANCE", 0.0):
            fresh = life_memory.sync_day(self.data_dir, "q", DAY, self.plan)
        self.assertFalse(any(item["kind"] == "encounter" for item in fresh))

    def test_store_events_are_remembered_after_the_store_rolls_over(self):
        at = datetime.combine(DAY, datetime.min.time()).replace(hour=15)
        money.add(self.data_dir, "p", 200, "零花钱", kind="master", at=at)
        money.spend(self.data_dir, "p", 120, "买耳机×1", kind="purchase", at=at)
        garage.start(self.data_dir, "p", "海边", "master", now=at, minutes=60)
        for day_offset in range(5):
            affection.add(self.data_dir, "p", 20, "陪伴", now=at + timedelta(days=day_offset - 4))
        (self.data_dir / "interactions").mkdir()
        (self.data_dir / "interactions" / "history.json").write_text(
            json.dumps({"items": [{"id": "i1", "kind": "chat", "item_name": "奶茶", "action": "give", "at": at.isoformat()}]}),
            encoding="utf-8",
        )
        texts = {item["kind"]: item["text"] for item in self.sync()}
        self.assertEqual(texts["money"], "主人给了 200 元（零花钱）")
        self.assertEqual(texts["purchase"], "买耳机×1")
        self.assertEqual(texts["drive"], "主人开着白色小车带她去了海边")
        self.assertEqual(texts["interaction"], "主人递来了奶茶")
        self.assertEqual(texts["milestone"], "和主人的关系变成了「眼熟」")

        # wipe the source stores: the day is still remembered
        for name in ("money.json", "garage.json", "affection.json"):
            (self.data_dir / name).unlink()
        kept = {item["kind"] for item in life_memory.day_items(self.data_dir, "p", DAY)}
        self.assertTrue({"money", "purchase", "drive", "milestone"} <= kept)

    def test_old_days_are_forgotten(self):
        old = DAY - timedelta(days=life_memory.KEEP_DAYS + 2)
        self.sync(day=old, plan=plan_for(old, ROWS))
        self.assertIn(old.isoformat(), life_memory.remembered_days(self.data_dir, "p"))
        money.add(self.data_dir, "p", 5, "x", kind="master", at=datetime.combine(DAY, datetime.min.time()).replace(hour=9))
        self.sync()
        self.assertNotIn(old.isoformat(), life_memory.remembered_days(self.data_dir, "p"))


class ContextTests(MemoryTestCase):
    def test_today_context(self):
        self.sync(hour=20)
        text = life_memory.today_context(self.data_dir, "p", DAY)
        self.assertTrue(text.startswith("【今天已经发生的事】早餐吃了葱油拌面"))
        self.assertIn("被问到", text)
        self.assertEqual(life_memory.today_context(self.data_dir, "p", DAY + timedelta(days=1)), "")

    def test_recent_context_keeps_important_things_and_yesterdays_meal(self):
        at = datetime.combine(DAY, datetime.min.time()).replace(hour=15)
        garage.start(self.data_dir, "p", "海边", "master", now=at, minutes=60)
        self.sync()
        text = life_memory.recent_context(self.data_dir, "p", DAY + timedelta(days=1))
        self.assertTrue(text.startswith("【前几天发生的重要事】\n- 昨天（2026-11-10）："))
        self.assertIn("主人开着白色小车带她去了海边", text)
        self.assertIn("早餐吃了葱油拌面", text)
        self.assertNotIn("路上", text.split("：", 1)[1].split("；")[0])
        self.assertEqual(life_memory.recent_context(self.data_dir, "p", DAY), "")

    def test_encounter_is_shared_once(self):
        with unittest.mock.patch.object(encounters, "CHANCE", 1.0):
            self.sync()
        first = life_memory.unshared_encounter(self.data_dir, "p", DAY)
        self.assertIsNotNone(first)
        life_memory.mark_shared(self.data_dir, "p", DAY, first["key"])
        second = life_memory.unshared_encounter(self.data_dir, "p", DAY)
        self.assertNotEqual(second and second["key"], first["key"])


class PluginIntegrationTests(MemoryTestCase):
    def plugin(self):
        from astrbot_plugin_simlife_world.main import SimLifeWorldPlugin

        plugin = object.__new__(SimLifeWorldPlugin)
        plugin.data_dir = self.data_dir
        plans = {DAY.isoformat(): self.plan}
        plugin.storage = SimpleNamespace(get_plan=lambda day, persona: plans.get(day))
        return plugin

    def test_chat_context_recalls_earlier_days_only_when_asked(self):
        plugin = self.plugin()
        at = datetime.combine(DAY, datetime.min.time()).replace(hour=15)
        garage.start(self.data_dir, "p", "海边", "master", now=at, minutes=60)
        tomorrow = at + timedelta(days=1, hours=-6)
        plain = plugin._life_memory_context("p", tomorrow, "早上好")
        recall = plugin._life_memory_context("p", tomorrow, "还记得昨天去哪了吗")
        self.assertNotIn("前几天", plain)
        self.assertIn("主人开着白色小车带她去了海边", recall)


if __name__ == "__main__":
    unittest.main()
