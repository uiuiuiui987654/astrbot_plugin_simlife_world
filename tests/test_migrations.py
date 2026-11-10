import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from astrbot_plugin_simlife_world.core import migrations
from astrbot_plugin_simlife_world.core.migrations import Schema

NOW = datetime(2026, 11, 10, 8, 0)


def write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_current_files_are_not_rewritten(self):
        path = self.data_dir / "money.json"
        write(path, {"schema_version": 1, "wallets": {}})
        before = path.stat().st_mtime_ns
        manifest = migrations.migrate_all(self.data_dir, plugin_version="v9", now=NOW)
        self.assertEqual(path.stat().st_mtime_ns, before)
        self.assertEqual(manifest["files"], {"money.json": {"status": "current", "version": 1}})
        self.assertEqual(manifest["plugin_version"], "v9")
        self.assertFalse((self.data_dir / migrations.BACKUP_DIR).exists())

    def test_step_by_step_upgrade_with_backup(self):
        def v1_to_v2(payload):
            payload["wallets"] = {name: {"balance": value} for name, value in payload.pop("balances").items()}
            return payload

        def v2_to_v3(payload):
            for wallet in payload["wallets"].values():
                wallet["currency"] = "元"
            return payload

        schemas = {"money.json": Schema(current=3, steps={1: v1_to_v2, 2: v2_to_v3})}
        path = self.data_dir / "money.json"
        write(path, {"schema_version": 1, "balances": {"p": 12}})

        manifest = migrations.migrate_all(self.data_dir, schemas=schemas, now=NOW)
        self.assertEqual(read(path), {"schema_version": 3, "wallets": {"p": {"balance": 12, "currency": "元"}}})
        self.assertEqual(manifest["files"]["money.json"], {"status": "upgraded", "version": 3, "from_version": 1})
        backups = list((self.data_dir / migrations.BACKUP_DIR).iterdir())
        self.assertEqual([path.name for path in backups], ["money.json.v1.20261110080000.json"])
        self.assertEqual(read(backups[0])["balances"], {"p": 12})

        # running again is a no-op
        again = migrations.migrate_all(self.data_dir, schemas=schemas, now=NOW + timedelta(minutes=1))
        self.assertEqual(again["files"]["money.json"]["status"], "current")

    def test_missing_version_uses_assumed_version_and_is_stamped(self):
        path = self.data_dir / "plans.json"
        write(path, {"plans": {}, "schedule_requirements": {}})
        manifest = migrations.migrate_all(self.data_dir, now=NOW)
        self.assertEqual(read(path)["schema_version"], 3)
        self.assertEqual(manifest["files"]["plans.json"]["from_version"], 3)

    def test_newer_data_is_left_alone(self):
        path = self.data_dir / "garage.json"
        write(path, {"schema_version": 7, "personas": {"p": {}}})
        with self.assertLogs("astrbot", "WARNING"):
            manifest = migrations.migrate_all(self.data_dir, now=NOW)
        self.assertEqual(read(path)["schema_version"], 7)
        self.assertEqual(manifest["files"]["garage.json"]["status"], "newer")
        self.assertIn("来自更新版插件", migrations.summary(manifest))

    def test_unreadable_and_broken_steps_do_not_block_others(self):
        (self.data_dir / "diary.json").write_text("{nope", encoding="utf-8")
        write(self.data_dir / "affection.json", ["not", "an", "object"])

        def explode(_payload):
            raise KeyError("x")

        write(self.data_dir / "money.json", {"schema_version": 1})
        write(self.data_dir / "garage.json", {"schema_version": 1})
        schemas = dict(migrations.SCHEMAS)
        schemas["money.json"] = Schema(current=2, steps={1: explode})
        with self.assertLogs("astrbot", "WARNING"):
            manifest = migrations.migrate_all(self.data_dir, schemas=schemas, now=NOW)
        files = manifest["files"]
        self.assertEqual(files["diary.json"]["status"], "unreadable")
        self.assertEqual(files["affection.json"]["status"], "unreadable")
        self.assertEqual(files["money.json"]["status"], "unreadable")
        self.assertEqual(read(self.data_dir / "money.json"), {"schema_version": 1}, "failed migration keeps the file")
        self.assertEqual(files["garage.json"]["status"], "current")
        self.assertIn("无法读取", migrations.summary(manifest))

    def test_backups_are_rotated(self):
        schemas = {"money.json": Schema(current=2)}
        for minute in range(migrations.MAX_BACKUPS_PER_FILE + 3):
            write(self.data_dir / "money.json", {"schema_version": 1})
            migrations.migrate_all(self.data_dir, schemas=schemas, now=NOW + timedelta(minutes=minute))
        self.assertEqual(len(list((self.data_dir / migrations.BACKUP_DIR).iterdir())), migrations.MAX_BACKUPS_PER_FILE)

    def test_nested_file_backup_name(self):
        write(self.data_dir / "interactions" / "history.json", {"items": []})
        migrations.migrate_all(self.data_dir, now=NOW)
        names = [path.name for path in (self.data_dir / migrations.BACKUP_DIR).iterdir()]
        self.assertEqual(names, ["interactions__history.json.v1.20261110080000.json"])

    def test_registered_versions_match_what_the_code_writes(self):
        """A module that bumps its schema_version must also bump SCHEMAS."""
        from astrbot_plugin_simlife_world.core import (
            affection,
            delivery,
            diary,
            garage,
            health_journal,
            home_decor,
            item_effects,
            money,
            mood_history,
            world_events,
        )

        writers = {
            "money.json": money._load(self.data_dir),
            "deliveries.json": delivery._load(self.data_dir),
            "garage.json": garage._load(self.data_dir),
            "affection.json": affection._load(self.data_dir),
            "diary.json": diary._load(self.data_dir),
            "mood_history.json": mood_history._load(self.data_dir),
            "home_decor.json": home_decor._load(self.data_dir),
            "item_effects.json": item_effects._load(self.data_dir),
            "world_events.json": world_events._load(self.data_dir),
            "health_journal.json": health_journal._load(self.data_dir),
        }
        for name, empty in writers.items():
            with self.subTest(file=name):
                self.assertEqual(empty["schema_version"], migrations.SCHEMAS[name].current)

    def test_summary_without_manifest(self):
        self.assertIn("尚未检查", migrations.summary(migrations.load_manifest(self.data_dir)))


if __name__ == "__main__":
    unittest.main()
