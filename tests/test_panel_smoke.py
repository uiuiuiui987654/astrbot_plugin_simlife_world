"""Headless-browser smoke test for the life panel (2D and 3D).

The panel is served by ``tools/panel_server.py``: real static files plus the
plugin's real ``VirtualLifeViewAPI.dispatch`` on a temp data dir with a demo
day. Needs Playwright with Chromium; skipped otherwise.

    pip install playwright && python -m playwright install --with-deps chromium
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - optional dependency
    sync_playwright = None

import panel_server  # noqa: E402

CHROMIUM_ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]


def _executable() -> str | None:
    """Prefer Playwright's own Chromium; fall back to a system Chrome."""
    explicit = os.environ.get("PANEL_SMOKE_CHROME")
    if explicit:
        return explicit
    for candidate in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(candidate)
        if found:
            return found
    return None


def current_demo_activity(now: datetime) -> str:
    minute = now.hour * 60 + now.minute
    for start, end, activity, *_ in panel_server.DEMO_DAY:
        begin = int(start[:2]) * 60 + int(start[3:])
        finish = int(end[:2]) * 60 + int(end[3:])
        if begin <= minute < finish:
            return activity
    return ""


@unittest.skipIf(sync_playwright is None, "playwright is not installed")
class PanelSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.data_dir = Path(cls._tmp.name)
        cls.server, cls.url = panel_server.start(cls.data_dir)
        cls._pw = sync_playwright().start()
        try:
            cls.browser = cls._pw.chromium.launch(args=CHROMIUM_ARGS)
        except Exception:  # Playwright's browser not downloaded
            executable = _executable()
            if executable is None:
                cls._pw.stop()
                cls.server.shutdown()
                raise unittest.SkipTest("no Chromium available for Playwright")
            cls.browser = cls._pw.chromium.launch(executable_path=executable, args=CHROMIUM_ARGS)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls._pw.stop()
        cls.server.shutdown()
        cls._tmp.cleanup()

    def open(self, mode: str):
        page = self.browser.new_page(viewport={"width": 1400, "height": 900})
        self.errors: list[str] = []
        page.on("pageerror", lambda error: self.errors.append(str(error)))
        page.add_init_script(f"localStorage.setItem('vl-render', '{mode}')")
        page.goto(self.url + "/")
        # the first /api/state can take a few seconds on a cold CI runner
        page.wait_for_function(
            "name => (document.getElementById('persona') || {}).textContent.trim() === name",
            arg=panel_server.PERSONA,
            timeout=45000,
        )
        page.wait_for_function("document.querySelectorAll('#timeline > *').length > 1", timeout=20000)
        self.addCleanup(page.close)
        return page

    @staticmethod
    def use_menu(page, target: str):
        """Go through the ☰ 功能 menu like a user (the legacy toolbar is hidden)."""
        page.click("#menu-toggle")
        page.locator(f'#function-menu [data-menu-target="{target}"]').first.click()

    def assertNoPageErrors(self):
        self.assertEqual(self.errors, [])

    def test_2d_panel_renders_real_state(self):
        page = self.open("2d")
        self.assertEqual(page.inner_text("#persona").strip(), panel_server.PERSONA)
        self.assertGreaterEqual(page.locator("#timeline > *").count(), len(panel_server.DEMO_DAY) - 1)
        activity = current_demo_activity(datetime.now())
        if activity:
            self.assertIn(activity, page.inner_text("#activity"))
        self.assertGreater(page.locator("#home-svg *").count(), 50)
        self.assertIn("2D", page.inner_text("#render-toggle"))
        self.assertEqual(page.locator(".bedroom-3d").count(), 0)
        self.assertFalse(page.evaluate("!!window.Room3D"), "3D scripts must not load in 2D mode")
        self.assertNoPageErrors()

    def test_3d_scene_mounts(self):
        page = self.open("3d")
        page.wait_for_selector(".bedroom-3d[data-ready]", timeout=60000)
        status = page.get_attribute(".bedroom-3d", "data-ready")
        self.assertNotEqual(status, "failed")
        self.assertIn("3D", page.inner_text("#render-toggle"))
        self.assertNoPageErrors()

    def test_switching_render_mode_rerenders_scene(self):
        page = self.open("2d")
        self.use_menu(page, "render-toggle")  # 2D -> auto
        self.use_menu(page, "render-toggle")  # auto -> 3D
        page.wait_for_selector(".bedroom-3d", timeout=60000)
        self.use_menu(page, "render-toggle")  # 3D -> 2D
        page.wait_for_function("document.querySelectorAll('.bedroom-3d').length === 0", timeout=10000)
        self.assertNoPageErrors()

    def test_talk_box_queues_an_interaction(self):
        page = self.open("2d")
        page.fill("#talk-input", "冒烟测试：在干嘛呢")
        page.click("#talk-send")
        requests_dir = self.data_dir / "interactions" / "requests"
        deadline = time.time() + 10
        texts: list[str] = []
        while time.time() < deadline and not texts:
            texts = [path.read_text(encoding="utf-8") for path in requests_dir.glob("*.json")] if requests_dir.exists() else []
            time.sleep(0.2)
        self.assertTrue(any("冒烟测试" in text for text in texts), texts)
        request = json.loads(next(text for text in texts if "冒烟测试" in text))
        self.assertEqual(request.get("persona"), panel_server.PERSONA)
        self.assertNoPageErrors()

    def test_toolbar_panels_open_without_errors(self):
        page = self.open("2d")
        targets = page.eval_on_selector_all(
            "#function-menu [data-menu-target]", "nodes => nodes.map(node => node.dataset.menuTarget)"
        )
        skip = {"render-toggle", "anim-toggle", "camera-toggle"}  # toggles, or need a drawing API
        for target in dict.fromkeys(targets):
            if target in skip:
                continue
            with self.subTest(target=target):
                self.use_menu(page, target)
                page.wait_for_timeout(400)
                page.keyboard.press("Escape")
                page.wait_for_timeout(150)
        self.assertNoPageErrors()


if __name__ == "__main__":
    unittest.main()
