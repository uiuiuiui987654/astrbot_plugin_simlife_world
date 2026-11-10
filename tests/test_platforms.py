import asyncio
import base64
import json
import struct
import tempfile
import unittest
import zlib
from datetime import datetime
from pathlib import Path

from astrbot_plugin_simlife_world.core import platforms


class FakeImage:
    def __init__(self, kind, value):
        self.kind, self.value = kind, value

    @classmethod
    def fromBase64(cls, value):  # noqa: N802 - mirrors AstrBot's API
        return cls("base64", value)

    @classmethod
    def fromURL(cls, value):  # noqa: N802
        return cls("url", value)

    @classmethod
    def fromFileSystem(cls, value):  # noqa: N802
        return cls("file", value)


class PngTests(unittest.TestCase):
    def test_tiny_png_is_valid(self):
        data = platforms.tiny_png(8, (1, 2, 3))
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        width, height = struct.unpack(">II", data[16:24])
        self.assertEqual((width, height), (8, 8))
        idat_length = struct.unpack(">I", data[33:37])[0]
        pixels = zlib.decompress(data[41 : 41 + idat_length])
        self.assertEqual(pixels[:4], b"\x00\x01\x02\x03")


class SendImageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self.png = platforms.tiny_png()
        self.data_url = "data:image/png;base64," + base64.b64encode(self.png).decode()

    def tearDown(self):
        self._tmp.cleanup()

    def run_send(self, image, accepts):
        tried = []

        async def send(component):
            tried.append(component.kind)
            if component.kind == "raise":
                raise RuntimeError
            return component.kind in accepts

        result = asyncio.run(platforms.send_image(send, FakeImage, image, data_dir=self.data_dir))
        return result, tried

    def test_base64_first(self):
        self.assertEqual(self.run_send(self.data_url, {"base64", "file"}), ((True, "base64"), ["base64"]))

    def test_base64_rejected_falls_back_to_file(self):
        (ok, kind), tried = self.run_send(self.data_url, {"file"})
        self.assertEqual((ok, kind, tried), (True, "file", ["base64", "file"]))
        spooled = list((self.data_dir / platforms.SPOOL_DIR).iterdir())
        self.assertEqual(spooled[0].read_bytes(), self.png)

    def test_everything_rejected(self):
        (ok, error), _ = self.run_send(self.data_url, set())
        self.assertFalse(ok)
        self.assertIn("file", error)

    def test_url_and_path(self):
        self.assertEqual(self.run_send("https://x/y.png", {"url"})[0], (True, "url"))
        self.assertEqual(self.run_send("/tmp/a.png", {"file"})[0], (True, "file"))
        self.assertEqual(self.run_send("", {"file"})[0], (False, "没有可发送的图片"))

    def test_adapter_exception_is_caught(self):
        async def send(_component):
            raise ConnectionError("down")

        ok, error = asyncio.run(platforms.send_image(send, FakeImage, "/a.png"))
        self.assertFalse(ok)
        self.assertEqual(error, "file: ConnectionError")

    def test_spool_folder_rotates(self):
        for _ in range(platforms.MAX_SPOOL_FILES + 5):
            platforms.spool_image(self.data_dir, b"x")
        self.assertLessEqual(len(list((self.data_dir / platforms.SPOOL_DIR).iterdir())), platforms.MAX_SPOOL_FILES)


class CheckRecordTests(unittest.TestCase):
    def test_record_and_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self.assertIn("还没有平台测试记录", platforms.format_checks(platforms.load_checks(data_dir)))
            platforms.record_check(
                data_dir,
                "telegram",
                {"text": "ok", "image_file": "ok", "image_base64": "fail: 平台返回发送失败", "reply_image": "sent"},
                now=datetime(2026, 11, 10, 9, 30),
            )
            platforms.record_check(data_dir, "aiocqhttp", {"text": "ok"}, now=datetime(2026, 11, 10, 9, 0))
            stored = json.loads((data_dir / platforms.CHECKS_FILE).read_text(encoding="utf-8"))
            self.assertEqual(set(stored["platforms"]), {"telegram", "aiocqhttp"})
            text = platforms.format_checks(platforms.load_checks(data_dir))
            self.assertIn("Telegram（2026-11-10T09:30）：✅主动发文字 ✅主动发图片（本地文件） ❌主动发图片（base64） 📨指令回复图片", text)
            self.assertIn("QQ（OneBot / aiocqhttp）", text)
            self.assertEqual(platforms.platform_label("matrix"), "matrix")


if __name__ == "__main__":
    unittest.main()


class PlatformTestCommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_command_runs_every_check_and_records_it(self):
        from types import SimpleNamespace

        from astrbot_plugin_simlife_world.main import ProactiveVirtualDailyPlugin

        with tempfile.TemporaryDirectory() as tmp:
            sent = []

            async def send_message(umo, chain):
                sent.append(chain)
                # pretend this platform cannot take base64 images
                return not any("base64" in vars(part) for part in chain)

            plugin = object.__new__(ProactiveVirtualDailyPlugin)
            plugin.data_dir = Path(tmp)
            plugin.context = SimpleNamespace(send_message=send_message)
            plugin._now = lambda: datetime(2026, 11, 10, 9, 0)
            event = SimpleNamespace(
                unified_msg_origin="telegram:FriendMessage:1",
                get_platform_name=lambda: "telegram",
                plain_result=lambda text: ("text", text),
                image_result=lambda path: ("image", path),
            )
            replies = [item async for item in plugin.platform_test(event)]

            self.assertEqual(len(sent), 3)
            self.assertEqual(replies[0][0], "text")
            self.assertIn("Telegram", replies[0][1])
            self.assertEqual(replies[1][0], "image")
            self.assertTrue(Path(replies[1][1]).is_file())
            results = platforms.load_checks(Path(tmp))["telegram"]["results"]
            self.assertEqual(
                results,
                {"text": "ok", "image_file": "ok", "image_base64": "fail: 平台返回发送失败", "reply_image": "sent"},
            )
