import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from astrbot_plugin_simlife_world.core import jsonio, money


class AtomicWriteTests(unittest.TestCase):
    def test_format_matches_legacy_write_text(self):
        payload = {"名字": "月月", "items": [1, 2.5, None], "nested": {"ok": True}}
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sub" / "state.json"
            jsonio.atomic_write_json(target, payload)
            legacy = Path(tmp) / "legacy.json"
            legacy.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            self.assertEqual(target.read_bytes(), legacy.read_bytes())
            self.assertEqual(sorted(p.name for p in target.parent.iterdir()), ["state.json"])

    def test_failed_serialisation_keeps_old_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "state.json"
            jsonio.atomic_write_json(target, {"v": 1})
            with self.assertRaises(TypeError):
                jsonio.atomic_write_json(target, {"v": object()})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"v": 1})
            self.assertEqual([p.name for p in Path(tmp).iterdir()], ["state.json"])

    def test_failed_replace_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "state.json"
            jsonio.atomic_write_json(target, {"v": 1})
            with mock.patch.object(jsonio.os, "replace", side_effect=OSError("disk")):
                with self.assertRaises(OSError):
                    jsonio.atomic_write_json(target, {"v": 2})
            self.assertEqual([p.name for p in Path(tmp).iterdir()], ["state.json"])
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"v": 1})

    def test_replace_retries_transient_permission_error(self):
        real_replace = jsonio.os.replace
        calls = []

        def flaky(src, dst):
            calls.append(src)
            if len(calls) < 3:
                raise PermissionError("locked by reader")
            return real_replace(src, dst)

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(jsonio, "_REPLACE_DELAY", 0):
            target = Path(tmp) / "state.json"
            with mock.patch.object(jsonio.os, "replace", side_effect=flaky):
                jsonio.atomic_write_json(target, {"v": 3})
            self.assertEqual(len(calls), 3)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"v": 3})


class ConcurrentMutationTests(unittest.TestCase):
    def test_parallel_money_adds_do_not_lose_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            start = money.balance(data_dir, "alice")
            threads = [
                threading.Thread(target=lambda: [money.add(data_dir, "alice", 1, "测试") for _ in range(20)])
                for _ in range(8)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertAlmostEqual(money.balance(data_dir, "alice"), start + 160)


if __name__ == "__main__":
    unittest.main()
