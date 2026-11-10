"""Panel → plugin interaction queue, fridge consumption and reply parsing."""

import json
import os
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from astrbot_plugin_simlife_world.core import interaction, view_state
from astrbot_plugin_simlife_world.core.interaction import InteractionService


def request(request_id, *, minutes_ago=0, **extra):
    created = datetime.now() - timedelta(minutes=minutes_ago)
    return {"id": request_id, "kind": "chat", "created_at": created.isoformat(timespec="seconds"), **extra}


class QueueTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self.plans_path = self.data_dir / "plans.json"
        self.service = InteractionService(self.data_dir)

    def tearDown(self):
        self._tmp.cleanup()

    def test_panel_and_plugin_share_the_same_directories(self):
        self.assertEqual(view_state.interaction_requests_dir(self.plans_path), self.service.requests_dir())
        self.assertEqual(view_state.interaction_responses_dir(self.plans_path), self.service.responses_dir())

    def test_full_round_trip(self):
        view_state.write_interaction_request(self.plans_path, request("r1", action="摸摸头"))
        pending = self.service.pending()
        self.assertEqual([item["id"] for item in pending], ["r1"])
        self.assertTrue(self.service.claim(pending[0]))
        self.assertFalse(self.service.claim(pending[0]), "second claim must fail")
        self.assertEqual(self.service.pending(), [])

        response = self.service.write_response(pending[0], {"speech": "嗯？" * 200, "mood": "开心"})
        self.assertEqual(len(response["speech"]), interaction.MAX_SPEECH_CHARS)
        self.assertEqual(view_state.load_interaction_response(self.plans_path, "r1")["mood"], "开心")
        history = self.service.recent()
        self.assertEqual([(item["id"], item["action"]) for item in history], [("r1", "摸摸头")])
        self.service.record(pending[0], response)  # recording the same response twice keeps one entry
        self.assertEqual(len(self.service.recent()), 1)

        # the same request written again (window retry) is dropped
        view_state.write_interaction_request(self.plans_path, request("r1"))
        self.assertEqual(self.service.pending(), [])
        self.assertFalse(self.service.claim(request("r1")))

    def test_stale_and_duplicate_requests_are_dropped(self):
        directory = self.service.requests_dir()
        directory.mkdir(parents=True)
        (directory / "old.json").write_text(json.dumps(request("old", minutes_ago=interaction.STALE_MINUTES + 1)), encoding="utf-8")
        (directory / "a.json").write_text(json.dumps(request("dup")), encoding="utf-8")
        (directory / "b.json").write_text(json.dumps(request("dup")), encoding="utf-8")
        (directory / "junk.json").write_text("not json", encoding="utf-8")
        self.assertEqual([item["id"] for item in self.service.pending()], ["dup"])
        self.assertFalse((directory / "old.json").exists())
        self.assertEqual(len([path for path in directory.glob("*.json") if "dup" in path.read_text(encoding="utf-8")]), 1)

    def test_pending_is_oldest_first_and_limited(self):
        directory = self.service.requests_dir()
        directory.mkdir(parents=True)
        for index, name in enumerate(("c", "a", "b")):
            path = directory / f"{name}.json"
            path.write_text(json.dumps(request(name)), encoding="utf-8")
            stamp = time.time() - 100 + index
            os.utime(path, (stamp, stamp))
        self.assertEqual([item["id"] for item in self.service.pending(limit=2)], ["c", "a"])

    def test_claim_sent_only_once(self):
        self.assertTrue(self.service.claim_sent("r9"))
        self.assertFalse(self.service.claim_sent("r9"))
        self.service.release_sent("r9")
        self.assertTrue(self.service.claim_sent("r9"))

    def test_request_ids_cannot_escape_the_directory(self):
        path = self.service.response_path("../../etc/passwd")
        self.assertEqual(path.parent, self.service.responses_dir())
        self.assertNotIn("/", path.name)
        self.assertIsNone(view_state.load_interaction_response(self.plans_path, "../"))


class FridgeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.service = InteractionService(Path(self._tmp.name))
        self.service.fridge_path().write_text(
            json.dumps(
                {
                    "ingredients": [
                        {"name": "西红柿", "quantity": 3, "unit": "个"},
                        {"name": "土鸡蛋", "quantity": 1, "unit": "个"},
                        {"name": "面粉", "quantity": 100, "unit": "克"},
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def fridge(self):
        return {item["name"]: item["quantity"] for item in json.loads(self.service.fridge_path().read_text(encoding="utf-8"))["ingredients"]}

    def test_consumes_matching_and_reports_missing(self):
        result = self.service.consume_dish({"name": "番茄炒蛋", "ingredients": ["西红柿", "鸡蛋", "葱"]})
        self.assertEqual([item["name"] for item in result["used"]], ["西红柿", "土鸡蛋"])
        self.assertEqual(result["missing"], ["葱"])
        self.assertEqual(self.fridge(), {"西红柿": 2, "面粉": 100}, "used-up eggs are removed")

    def test_never_goes_negative(self):
        result = self.service.consume_dish({"ingredients": ["面粉"]})
        self.assertEqual(result["used"][0]["amount"], 100)
        self.assertNotIn("面粉", self.fridge())

    def test_disabled_or_invalid_input_does_nothing(self):
        before = self.fridge()
        self.assertEqual(self.service.consume_dish({"ingredients": ["西红柿"]}, {"consume_ingredients": False}), {"used": [], "missing": []})
        self.assertEqual(self.service.consume_dish(None), {"used": [], "missing": []})
        self.assertEqual(self.service.consume_dish({"ingredients": "西红柿"}), {"used": [], "missing": []})
        self.assertEqual(self.fridge(), before)


class ReplyParsingTests(unittest.TestCase):
    def setUp(self):
        self.service = InteractionService(None)

    def test_json_reply_with_dish(self):
        raw = '好的～\n{"speech": "（接过盘子）给你做好啦", "mood": "开心", "dish": {"name": "蛋炒饭", "ingredients": ["米饭", "鸡蛋", ""], "method": "炒"}}'
        result = self.service.parse_reply(raw)
        self.assertEqual(result["speech"], "给你做好啦")
        self.assertEqual(result["dish"]["ingredients"], ["米饭", "鸡蛋"])
        self.assertEqual(self.service.qq_text({}, result), "🍽️ 蛋炒饭\n给你做好啦")

    def test_plain_text_and_empty_reply(self):
        self.assertEqual(self.service.parse_reply("就这样吧")["speech"], "就这样吧")
        self.assertEqual(self.service.parse_reply("")["speech"], "嗯，我在呢。")
        self.assertIsNone(self.service.parse_reply('{"speech": "x", "dish": {"name": ""}}')["dish"])

    def test_schedule_decision(self):
        decision = InteractionService.parse_schedule_decision('```json\n{"insert": "yes", "activity": "陪主人看电影", "minutes": 999}\n```')
        self.assertEqual((decision["insert"], decision["minutes"]), (True, 120))
        self.assertEqual(InteractionService.parse_schedule_decision("不知道"), {})
        self.assertEqual(InteractionService.parse_schedule_decision('{"activity": "x"}'), {})

    def test_repeat_guard(self):
        history = [
            {"role": "user", "content": "在吗"},
            {"role": "assistant", "content": "我在看书呢，等会儿陪你"},
            {"role": "assistant", "content": [{"type": "text", "text": "今天好冷"}]},
        ]
        recent = InteractionService.recent_assistant_texts(history)
        self.assertEqual(recent[1], "我在看书呢，等会儿陪你")
        self.assertTrue(InteractionService.is_repetitive("我在看书呢，等会儿陪你哦", recent))
        self.assertFalse(InteractionService.is_repetitive("要不要一起去散步？", recent))

    def test_settings_clamped(self):
        config = InteractionService.settings({"max_reply_chars": 9999, "poll_seconds": 0, "enable": "off"})
        self.assertEqual((config["max_reply_chars"], config["poll_seconds"], config["enable"]), (400, 1, False))


if __name__ == "__main__":
    unittest.main()
