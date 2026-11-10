"""Run the life panel locally without AstrBot.

Serves ``views/life`` together with a fake ``bridge-sdk.js`` that forwards the
panel's API calls to the plugin's real ``VirtualLifeViewAPI.dispatch`` running
on a throw-away data directory seeded with a demo day.

    python tools/panel_server.py                # http://127.0.0.1:8770/
    python tools/panel_server.py --port 9000 --data-dir /tmp/life-demo

Used by ``tests/test_panel_smoke.py`` and handy for checking UI changes.
AstrBot itself is replaced by ``tests/astrbot_stub.py``.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import mimetypes
import sys
import tempfile
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlsplit

ROOT = Path(__file__).resolve().parents[1]
VIEW_DIR = ROOT / "views" / "life"
PACKAGE = "astrbot_plugin_simlife_world"
PERSONA = "demo"

BRIDGE_SDK = """
(function () {
  'use strict';
  async function call(method, endpoint, payload) {
    var url = '/__view/' + String(endpoint).replace(/^view\\//, '');
    var options = {method: method, headers: {'Content-Type': 'application/json'}};
    if (method === 'GET') {
      var query = new URLSearchParams(payload || {}).toString();
      if (query) url += '?' + query;
    } else {
      options.body = JSON.stringify(payload || {});
    }
    var response = await fetch(url, options);
    return response.json();
  }
  window.AstrBotPluginView = {
    ready: function () { return Promise.resolve(); },
    apiGet: function (endpoint, params) { return call('GET', endpoint, params); },
    apiPost: function (endpoint, body) { return call('POST', endpoint, body); }
  };
})();
"""

# A full, realistic day that passes DailyPlan validation and visits many rooms.
DEMO_DAY = [
    ("00:00", "07:00", "睡觉", "卧室", "sleep", "blocked"),
    ("07:00", "07:30", "洗漱换日常装", "浴室", "available", "normal"),
    ("07:30", "08:00", "吃早饭", "餐厅", "available", "normal"),
    ("08:00", "11:30", "在书房写代码", "书房", "focus", "low"),
    ("11:30", "12:30", "做午饭吃午饭", "厨房", "available", "normal"),
    ("12:30", "13:30", "午睡", "卧室", "sleep", "low"),
    ("13:30", "16:00", "窝在沙发看书", "客厅", "available", "normal"),
    ("16:00", "16:20", "步行去公园", "路上", "transit", "normal"),
    ("16:20", "17:00", "在公园散步", "公园", "available", "normal"),
    ("17:00", "18:00", "泡澡", "浴室", "available", "normal"),
    ("18:00", "19:00", "吃晚饭", "餐厅", "available", "normal"),
    ("19:00", "21:30", "看电影", "影音室", "available", "high"),
    ("21:30", "22:30", "换上睡衣准备睡觉", "卧室", "available", "normal"),
    ("22:30", "24:00", "睡觉", "卧室", "sleep", "blocked"),
]

OUTFIT = {
    "style": "日常休闲风",
    "summary": "白色衬衫配深蓝百褶裙",
    "items": [
        {"category": "hairstyle", "name": "自然披肩发"},
        {"category": "underwear", "name": "浅色无痕内衣"},
        {"category": "underpants", "name": "浅色无痕内裤"},
        {"category": "top", "name": "白色短袖衬衫"},
        {"category": "bottom", "name": "深蓝百褶裙"},
        {"category": "shoes", "name": "黑色乐福鞋"},
    ],
}


def load_plugin_package():
    """Import the plugin as a package with AstrBot stubbed out."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tests import astrbot_stub

    astrbot_stub.install()
    if PACKAGE not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            PACKAGE, ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[PACKAGE] = module
        spec.loader.exec_module(module)
    return sys.modules[PACKAGE]


def _demo_plan(day):
    from astrbot_plugin_simlife_world.core.models import DailyPlan

    timeline = [
        {
            "id": f"demo-{index}",
            "start": start,
            "end": end,
            "activity": activity,
            "location": location,
            "state": state,
            "availability": availability,
        }
        for index, (start, end, activity, location, state, availability) in enumerate(DEMO_DAY)
    ]
    return DailyPlan.from_dict(
        {
            "date": day.isoformat(),
            "persona_id": PERSONA,
            "theme": "慢悠悠的居家日",
            "mood": "平静",
            "outfit": OUTFIT,
            "timeline": timeline,
        }
    )


def seed_demo_day(data_dir: Path, day: datetime) -> None:
    """Today's plan plus a remembered yesterday (meals and a drive with the owner)."""
    from datetime import timedelta

    from astrbot_plugin_simlife_world.core import garage
    from astrbot_plugin_simlife_world.core.food import FoodSystem

    today = day.date()
    yesterday = today - timedelta(days=1)
    plans = {f"{d.isoformat()}::{PERSONA}": _demo_plan(d) for d in (yesterday, today)}
    (data_dir / "plans.json").write_text(
        json.dumps(
            {"schema_version": 3, "plans": {key: plan.to_dict() for key, plan in plans.items()}, "schedule_requirements": {}},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    food = FoodSystem(data_dir, ROOT / "core" / "food_catalog.json")
    for plan in plans.values():
        target = datetime.fromisoformat(plan.date).date()
        food.apply_plan(plan, PERSONA, food.plan_day(target, PERSONA, ""), {})
    start = datetime.combine(yesterday, datetime.min.time()).replace(hour=15)
    garage.start(data_dir, PERSONA, "海边", "master", now=start, minutes=90)
    garage.return_home(data_dir, PERSONA, now=start + timedelta(minutes=90))


def make_plugin(data_dir: Path):
    load_plugin_package()
    from astrbot_plugin_simlife_world.core.food import FoodSystem
    from astrbot_plugin_simlife_world.core.storage import PluginStorage
    from astrbot_plugin_simlife_world.core.user_state import UserStateStore

    timezone = datetime.now().astimezone().tzinfo
    storage = PluginStorage(data_dir)
    asyncio.run(storage.load())

    async def resolve(_value=None):
        return SimpleNamespace(id=PERSONA, prompt="")

    return SimpleNamespace(
        data_dir=data_dir,
        timezone=timezone,
        config={},
        context=None,
        plan_generator=SimpleNamespace(
            food=FoodSystem(data_dir, ROOT / "core" / "food_catalog.json")
        ),
        storage=storage,
        user_states=UserStateStore(data_dir),
        personas=SimpleNamespace(resolve=resolve),
        _now=lambda: datetime.now(timezone),
    )


def make_api(data_dir: Path):
    load_plugin_package()
    from astrbot_plugin_simlife_world.core.view_api import VirtualLifeViewAPI

    data_dir.mkdir(parents=True, exist_ok=True)
    if not (data_dir / "plans.json").exists():
        seed_demo_day(data_dir, datetime.now())
    return VirtualLifeViewAPI(make_plugin(data_dir))


def make_handler(api):
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):  # keep test output quiet
            pass

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _api(self, method: str) -> None:
            url = urlsplit(self.path)
            endpoint = url.path[len("/__view/"):].strip("/")
            params = dict(parse_qsl(url.query))
            payload = {}
            if method == "POST":
                length = int(self.headers.get("Content-Length") or 0)
                try:
                    payload = json.loads(self.rfile.read(length) or b"{}")
                except ValueError:
                    payload = {}
            with lock:
                try:
                    result = api.dispatch(endpoint, method, params, payload)
                except (OSError, ValueError, TypeError) as exc:
                    result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            body = json.dumps(result, ensure_ascii=False, default=str).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")

        def do_POST(self):  # noqa: N802
            if self.path.startswith("/__view/"):
                return self._api("POST")
            self._send(404, b"", "text/plain")

        def do_GET(self):  # noqa: N802
            path = urlsplit(self.path).path
            if path.startswith("/__view/"):
                return self._api("GET")
            if path == "/api/plugin/page/bridge-sdk.js":
                return self._send(200, BRIDGE_SDK.encode("utf-8"), "application/javascript")
            if path == "/favicon.ico":
                return self._send(204, b"", "image/x-icon")
            if path in ("", "/"):
                path = "/index.html"
            target = (VIEW_DIR / path.lstrip("/")).resolve()
            if VIEW_DIR not in target.parents or not target.is_file():
                return self._send(404, b"not found", "text/plain")
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if target.suffix == ".js":
                content_type = "application/javascript"
            self._send(200, target.read_bytes(), content_type)

    return Handler


def start(data_dir: Path, port: int = 0) -> tuple[ThreadingHTTPServer, str]:
    """Start the server in a daemon thread and return it with its base URL."""
    api = make_api(data_dir)
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(api))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8770)
    parser.add_argument("--data-dir", type=Path, default=None, help="defaults to a fresh temp dir")
    args = parser.parse_args()
    data_dir = args.data_dir or Path(tempfile.mkdtemp(prefix="simlife-panel-"))
    server, url = start(data_dir, args.port)
    print(f"panel: {url}/   data: {data_dir}")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
