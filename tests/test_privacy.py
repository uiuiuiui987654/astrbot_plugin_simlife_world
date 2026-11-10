import os
import unittest
from unittest import mock

from astrbot_plugin_simlife_world.core import privacy


class SecretTests(unittest.TestCase):
    def test_env_references(self):
        with mock.patch.dict(os.environ, {"IMG_KEY": " sk-123 ", "SIMLIFE_IMAGE_API_KEY": "fallback"}):
            self.assertEqual(privacy.resolve_secret("env:IMG_KEY"), "sk-123")
            self.assertEqual(privacy.resolve_secret("${IMG_KEY}"), "sk-123")
            self.assertEqual(privacy.resolve_secret(" plain-key "), "plain-key")
            self.assertEqual(privacy.resolve_secret("", fallback_env="SIMLIFE_IMAGE_API_KEY"), "fallback")
            self.assertEqual(privacy.resolve_secret(None), "")
            self.assertEqual(privacy.resolve_secret("env:MISSING_VAR"), "")
            # not a reference: used literally
            self.assertEqual(privacy.resolve_secret("env:"), "env:")

    def test_describe_never_reveals_the_secret(self):
        with mock.patch.dict(os.environ, {"IMG_KEY": "sk-secret"}, clear=False):
            text = privacy.describe_secret_source("env:IMG_KEY")
            self.assertEqual(text, "环境变量 IMG_KEY（已设置）")
            self.assertEqual(privacy.describe_secret_source("sk-secret"), "插件配置（明文）")
            self.assertEqual(privacy.describe_secret_source("", fallback_env="NOPE_NOT_SET"), "未设置")


class SafeBackupTests(unittest.TestCase):
    def test_origins_are_redacted_everywhere(self):
        files = {
            "sessions.json": {"sessions": {"aiocqhttp:FriendMessage:123": {}}},
            "chat_schedule_state.json": {
                "schema_version": 1,
                "checks": {"aiocqhttp:FriendMessage:123": {"at": "x"}, "telegram:GroupMessage:-100": {"at": "y"}},
                "entries": [{"umo": "aiocqhttp:FriendMessage:123", "activity": "聊天"}],
            },
            "money.json": {"wallets": {"p": {"balance": 3}}},
        }
        safe, report = privacy.sanitize_backup(files)
        self.assertEqual(report["excluded"], ["sessions.json"])
        self.assertNotIn("sessions.json", safe)
        state = safe["chat_schedule_state.json"]
        self.assertEqual(sorted(state["checks"]), [privacy.REDACTED, privacy.REDACTED + "#2"])
        self.assertEqual(state["entries"][0], {"umo": privacy.REDACTED, "activity": "聊天"})
        self.assertEqual(safe["money.json"], files["money.json"])
        self.assertIn("aiocqhttp:FriendMessage:123", files["chat_schedule_state.json"]["checks"], "input untouched")

    def test_safe_backup_endpoint(self):
        import sys
        import tempfile
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
        import panel_server

        with tempfile.TemporaryDirectory() as tmp:
            api = panel_server.make_api(Path(tmp))
            (Path(tmp) / "sessions.json").write_text('{"sessions": {"kook:GroupMessage:9": {}}}', encoding="utf-8")
            full = api.dispatch("backup", "GET", {}, {})
            safe = api.dispatch("backup", "GET", {"safe": "1"}, {})
        self.assertIn("sessions.json", full["files"])
        self.assertNotIn("sessions.json", safe["files"])
        self.assertIn("plans.json", safe["files"])
        self.assertEqual(safe["privacy"]["excluded"], ["sessions.json"])


if __name__ == "__main__":
    unittest.main()


class CameraKeyTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_reads_key_from_environment(self):
        from types import SimpleNamespace

        from astrbot_plugin_simlife_world.core import camera_photo

        seen = {}

        async def fake_proxy(prompt, **kwargs):
            seen.update(kwargs)
            return "data:image/png;base64,AAAA"

        plugin = SimpleNamespace(config={"camera_settings": {"api_key": "env:TEST_IMG_KEY"}})
        state = {"now": {"activity": "看书", "location": "客厅", "room": "客厅", "kind": "home"}, "persona": "p"}
        with mock.patch.dict(os.environ, {"TEST_IMG_KEY": "sk-env"}), mock.patch.object(camera_photo, "_generate_via_proxy", fake_proxy):
            result = await camera_photo.generate(plugin, state, target=camera_photo.TARGET_ROOM)
        self.assertTrue(result["ok"])
        self.assertEqual(seen["api_key"], "sk-env")
