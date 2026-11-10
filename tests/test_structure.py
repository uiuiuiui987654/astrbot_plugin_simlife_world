"""Structural regression guards for the refactor.

* the set of AstrBot handlers (commands, LLM tools, event hooks) must not change by accident;
* the concatenated frontend bundles must match their ``src/`` fragments;
* ``life_state.compute`` must keep producing the same numbers for a fixed set of random days.

Intentional changes: regenerate the golden files with ``UPDATE_GOLDEN=1 pytest tests/test_structure.py``.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from astrbot_plugin_simlife_world.core import life_state

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).resolve().parent / "data"
UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"


def _golden(name: str, value):
    path = DATA / name
    if UPDATE or not path.exists():
        path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


class HandlerRegistryTests(unittest.TestCase):
    def test_registered_handlers_match_golden(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "snap.json"
            subprocess.run(
                [sys.executable, str(ROOT / "tools" / "plugin_snapshot.py"), str(ROOT), str(out)],
                check=True,
                capture_output=True,
            )
            handlers = json.loads(out.read_text(encoding="utf-8"))["handlers"]
        self.assertEqual(handlers, _golden("handlers.json", handlers))


class FrontendBundleTests(unittest.TestCase):
    def test_bundles_are_up_to_date(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_frontend.py"), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


ACTIVITIES = [
    "睡觉", "起床洗漱", "吃早饭", "午饭", "晚饭", "宵夜", "手冲咖啡", "做饭", "外卖炸鸡火锅", "喝水",
    "跑步", "健身房力量训练", "瑜伽拉伸", "傍晚散步", "通勤地铁", "加班", "开会", "午睡", "读书",
    "看电影", "弹钢琴", "打游戏", "打扫卫生", "泡澡", "朋友聚会", "小酌红酒", "晒太阳", "海边", "冥想",
]


def _random_plan(rng: random.Random, day: datetime) -> dict:
    minute, items = 0, []
    while minute < 24 * 60 - 20:
        end = min(24 * 60, minute + rng.choice([15, 30, 45, 60, 90, 120, 180, 420]))
        activity = rng.choice(ACTIVITIES)
        items.append({
            "id": f"i{minute}",
            "start": "%02d:%02d" % divmod(minute, 60),
            "end": "24:00" if end >= 1440 else "%02d:%02d" % divmod(end, 60),
            "activity": activity,
            "location": rng.choice(["家", "厨房", "公司", "公园", "健身房", "路上"]),
            "state": "sleep" if "睡" in activity else rng.choice(["available", "busy"]),
        })
        minute = end + rng.choice([0, 0, 5, 10])
    low = rng.randint(-5, 30)
    return {
        "date": day.strftime("%Y-%m-%d"), "persona_id": "p", "theme": "x",
        "mood": rng.choice(["开心", "平静", "低落", "疲惫", ""]), "timeline": items,
        "weather": {"condition": rng.choice(["晴", "多云", "小雨", "暴雨", "雪", "高温"]),
                    "temperature_low": low, "temperature_high": low + rng.randint(2, 12)},
        "outfit": {"summary": rng.choice(["雨衣 羽绒服", "短袖 防晒帽", "毛衣"]), "items": []},
    }


class LifeStateGoldenTests(unittest.TestCase):
    def test_compute_is_stable(self):
        rng = random.Random(20261110)
        digests = []
        for _ in range(300):
            day = datetime(2026, rng.randint(1, 12), rng.randint(1, 28))
            history = [_random_plan(rng, day - timedelta(days=k)) for k in range(rng.randint(0, 6), 0, -1)]
            plan = _random_plan(rng, day)
            now = day.replace(hour=rng.randint(0, 23), minute=rng.randint(0, 59))
            result = life_state.compute(
                plan, now,
                history_plans=history or None,
                weak_constitution=rng.random() < 0.3,
                recent_illness_days=rng.choice([0, 0, 1, 3]),
                furniture_states=rng.choice([None, {"aroma_diffuser": {"on": True}}]),
            )
            blob = json.dumps(result, ensure_ascii=False, sort_keys=True, default=str)
            digests.append(hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16])
        self.assertEqual(digests, _golden("life_state_compute.json", digests))


if __name__ == "__main__":
    unittest.main()
