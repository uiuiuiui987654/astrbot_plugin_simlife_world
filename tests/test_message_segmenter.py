"""Splitting proactive messages into chat-sized pieces and pacing them."""

import json
import math
import unittest
from pathlib import Path
from unittest.mock import patch

from astrbot_plugin_simlife_world.core.message_segmenter import ProactiveMessageSegmenter

SHIPPED = {
    key: value["default"]
    for key, value in json.loads(Path(__file__).resolve().parents[1].joinpath("_conf_schema.json").read_text(encoding="utf-8"))[
        "delivery_settings"
    ]["items"]["segmented_reply_settings"]["items"].items()
    if "default" in value
}


def split(text, **settings):
    return ProactiveMessageSegmenter({**SHIPPED, **settings}).split(text)


def pause(text, **settings):
    return ProactiveMessageSegmenter({**SHIPPED, **settings}).interval_for(text)


UNIFORM = "core.message_segmenter.random.uniform"


class Splitting(unittest.TestCase):
    def test_default_word_split(self):
        result = split("下班啦！Want tea?\n我请客。")
        self.assertEqual((result.segments, result.mode, result.skipped_reason), (["下班啦！", "Want tea?", "我请客。"], "words", ""))

    def test_regex_split_with_groups(self):
        self.assertEqual(split("第一句。第二句！收尾", split_mode="regex", regex=r"(.*?[。！])|(.+$)").segments, ["第一句。", "第二句！", "收尾"])

    def test_cleanup(self):
        self.assertEqual(split("第一句。第二句！", enable_content_cleanup=True, content_cleanup_rule="[。！]").segments, ["第一句", "第二句"])
        self.assertEqual(split("第一句。第二句！", enable_content_cleanup=True, content_cleanup_rule="[").segments, ["第一句。", "第二句！"])

    def test_left_whole(self):
        cases = {
            "longer than threshold": ("第一句。第二句。", {"words_count_threshold": 7}, "over threshold"),
            "threshold zero": ("一句。", {"words_count_threshold": 0}, "over threshold"),
            "broken regex": ("第一句。第二句！", {"split_mode": "regex", "regex": "("}, "invalid regex"),
            "no split words": ("第一句。第二句。", {"split_words": []}, "empty split words"),
        }
        for name, (text, settings, reason) in cases.items():
            with self.subTest(name):
                result = split(text, **settings)
                self.assertEqual((result.segments, result.skipped_reason), ([text], reason))

    def test_unconfigured_means_disabled(self):
        result = ProactiveMessageSegmenter({}).split("第一句。第二句。")
        self.assertEqual((result.segments, result.skipped_reason), (["第一句。第二句。"], "disabled"))


class Pacing(unittest.TestCase):
    def test_random_range_is_ordered(self):
        with patch(UNIFORM, return_value=1.25) as uniform:
            self.assertEqual(pause("消息", interval_method="random", interval="2.0,0.8"), 1.25)
        uniform.assert_called_once_with(0.8, 2.0)

    def test_log_pacing_counts_characters_and_words(self):
        for text, units in (("四个字符", 4), ("two words!", 2)):
            with self.subTest(text), patch(UNIFORM, return_value=3.0) as uniform:
                self.assertEqual(pause(text, log_base=2.6), 3.0)
                low = math.log(units + 1, 2.6)
                uniform.assert_called_once_with(low, low + 0.5)

    def test_bad_interval_means_no_pause(self):
        with patch(UNIFORM) as uniform:
            self.assertEqual(pause("消息", interval_method="random", interval="invalid"), 0.0)
        uniform.assert_not_called()


if __name__ == "__main__":
    unittest.main()
