from __future__ import annotations

import logging
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from . import (
    books,
    delivery,
    diary,
    garage,
    goods,
    health_journal,
    money,
    mood_history,
    view_state,
)

logger = logging.getLogger("astrbot")

CORE_DIR = Path(__file__).resolve().parent
PLUGIN_DIR = CORE_DIR.parent


def _plugin_version() -> str:
    try:
        text = (PLUGIN_DIR / "metadata.yaml").read_text(encoding="utf-8")
        match = re.search(r"(?m)^version:\s*(\S+)", text)
        return match.group(1).strip() if match else "未知"
    except OSError:
        return "未知"


def _frontend_version() -> str:
    try:
        text = (PLUGIN_DIR / "views" / "life" / "index.html").read_text(
            encoding="utf-8"
        )
        match = re.search(r"app\.js\?v=([^\"'&<>]+)", text)
        return match.group(1).strip() if match else "未知"
    except OSError:
        return "未知"


def build(
    data_dir: Path,
    plans_path: Path,
    persona: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    moment = now or datetime.now()
    all_books = books.load_books()
    all_goods = goods.load_goods()
    sample = books.find_book("book_tide_light")
    sample_chapters = len(sample.get("chapters") or []) if sample else 0
    try:
        home_items, _ = view_state.load_home_items(plans_path)
    except Exception:
        logger.debug("[虚拟人生] build 出错，已忽略", exc_info=True)
        home_items = []
    try:
        state = view_state.build_state(plans_path, persona, now=moment)
    except Exception as exc:
        logger.warning("[虚拟人生] build 失败: %s", exc, exc_info=True)
        state = {"ok": False, "error": str(exc)}
    wallet = money.snapshot(plans_path.parent, persona, limit=1)
    garage_state = garage.snapshot(plans_path.parent, persona, now=moment)
    entries = diary.list_entries(data_dir, persona)
    moods = mood_history.list_entries(data_dir, persona, limit=60)
    pending = view_state.load_pending_actions(plans_path, persona)
    try:
        cooking_payload = json.loads(
            (data_dir / "cooking_history.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError, TypeError):
        cooking_payload = []
    cooking_count = len(cooking_payload) if isinstance(cooking_payload, list) else 0
    try:
        food_state = json.loads(
            (data_dir / "food_state.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError, TypeError):
        food_state = {}
    shopping_count = len([
        item for item in (food_state.get("shopping") or [])
        if isinstance(item, dict)
    ]) if isinstance(food_state, dict) else 0
    health_state = health_journal.persona_state(
        data_dir, persona, today=moment.date()
    )
    health_episodes = len([
        item for item in (health_state.get("episodes") or [])
        if isinstance(item, dict)
    ])
    checks = [
        {
            "id": "books",
            "label": "书籍目录",
            "ok": len(all_books) >= 20 and all(
                book.get("chapters") for book in all_books
            ),
            "detail": f"{len(all_books)} 本书",
        },
        {
            "id": "book_txt",
            "label": "轻小说 TXT",
            "ok": sample_chapters >= 20,
            "detail": f"样例 {sample_chapters} 章",
        },
        {
            "id": "goods",
            "label": "商店目录",
            "ok": len(all_goods) >= 70,
            "detail": f"{len(all_goods)} 件商品",
        },
        {
            "id": "plan",
            "label": "今日日程",
            "ok": bool(state.get("ok") and state.get("is_today")),
            "detail": str(state.get("plan_date") or state.get("error") or "未生成"),
        },
        {
            "id": "garage",
            "label": "车库状态",
            "ok": bool(garage_state.get("vehicle")),
            "detail": (
                f"油量 {garage_state.get('vehicle', {}).get('fuel', 0)}% · "
                f"{garage_state.get('vehicle', {}).get('status', '未知')}"
            ),
        },
        {
            "id": "wallet",
            "label": "钱包账本",
            "ok": isinstance(wallet.get("balance"), (int, float)),
            "detail": f"余额 {money.format_money(wallet.get('balance') or 0)} 元",
        },
        {
            "id": "cooking",
            "label": "下厨记录",
            "ok": isinstance(cooking_payload, list),
            "detail": f"{cooking_count} 道菜",
        },
        {
            "id": "health",
            "label": "健康记录",
            "ok": isinstance(health_state, dict),
            "detail": (
                f"{health_state.get('status') or '未知'} · "
                f"{health_episodes} 次生病"
            ),
        },
        {
            "id": "ui",
            "label": "观察窗版本",
            "ok": _frontend_version() != "未知",
            "detail": _frontend_version(),
        },
    ]
    invalid_scenes = [
        item
        for item in (state.get("timeline") or [])
        if item.get("kind") in ("home", "sleep") and item.get("scene")
    ]
    checks.append(
        {
            "id": "scenes",
            "label": "日程场景",
            "ok": not invalid_scenes,
            "detail": (
                f"{len(invalid_scenes)} 条居家/睡眠日程带室外场景"
                if invalid_scenes
                else "居家和睡眠日程没有错误场景"
            ),
        }
    )
    return {
        "ok": True,
        "persona": persona,
        "time": moment.strftime("%Y-%m-%d %H:%M:%S"),
        "plugin_version": _plugin_version(),
        "frontend_version": _frontend_version(),
        "counts": {
            "books": len(all_books),
            "sample_chapters": sample_chapters,
            "goods": len(all_goods),
            "home_items": len(home_items),
            "destinations": len(garage.DESTINATIONS),
            "diary": len(entries),
            "mood_days": len(moods),
            "pending": len(pending),
            "deliveries": len(delivery.list_orders(plans_path.parent, persona)),
            "cooking": cooking_count,
            "shopping": shopping_count,
            "health_episodes": health_episodes,
        },
        "wallet": {
            "balance": wallet.get("balance"),
            "goal": wallet.get("goal"),
        },
        "garage": {
            "vehicle": garage_state.get("vehicle"),
            "trip": garage_state.get("trip"),
        },
        "plan": {
            "ok": bool(state.get("ok") and state.get("is_today")),
            "date": state.get("plan_date") or "",
            "theme": state.get("theme") or "",
        },
        "checks": checks,
        "all_ok": all(check["ok"] for check in checks),
    }
