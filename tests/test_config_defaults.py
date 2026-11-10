"""The shipped generation prompts must ask for what the generator validates."""

import json
import unittest
from pathlib import Path

SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "_conf_schema.json").read_text(encoding="utf-8"))


def default(section, key):
    return SCHEMA[section]["items"][key]["default"]


class GenerationPromptDefaults(unittest.TestCase):
    def test_switches_and_retries(self):
        self.assertEqual(default("schedule_settings", "generation_retries"), 2)
        self.assertTrue(default("schedule_settings", "daily_schedule_generation_enable"))
        self.assertTrue(default("schedule_settings", "daily_outfit_generation_enable"))
        self.assertNotIn("followup_settings", SCHEMA)

    def test_prompts_are_collapsed_and_complete(self):
        prompts = SCHEMA["prompt_settings"]["items"]
        self.assertTrue(all(item["collapsed"] for item in prompts.values()))
        expected = {
            "schedule_generation_system_prompt": ['"timeline"', "timeline 第一项"],
            "complete_generation_prompt_template": ["{outfit_style}", "{history}", "timeline、proactive_windows、budget_bonus 和 outfit"],
            "schedule_prompt_template": ["{outfit_context}"],
            "outfit_generation_system_prompt": ['"outfit"', "underwear", "underpants", "outfit 必须是包含非空 style、summary 和 items 数组"],
            "outfit_prompt_template": ["{outfit_style}"],
            "generation_retry_prompt_template": ["{previous_output}", "{error}", "重写穿搭时"],
        }
        for key, needles in expected.items():
            for needle in needles:
                with self.subTest(key=key, needle=needle):
                    self.assertIn(needle, prompts[key]["default"])
        self.assertNotIn("{history}", prompts["schedule_prompt_template"]["default"])

    def test_retry_prompt_renders_outfit_example(self):
        rendered = default("prompt_settings", "generation_retry_prompt_template").format(
            mode="重写穿搭", attempt=2, error="missing structured outfit", previous_output="{}"
        )
        self.assertIn('{"outfit": {"style": "指定风格", "summary": "非空概述", "items": []}}', rendered)


if __name__ == "__main__":
    unittest.main()
