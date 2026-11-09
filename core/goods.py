from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from . import delivery, item_effects, money

CORE_DIR = Path(__file__).resolve().parent
GOODS_PATH = CORE_DIR / "goods_catalog.json"

CONSUMABLE_CATEGORIES = {"饮品", "零食", "食物"}
DEFAULT_EFFECTS = {
    "饮品": {"hydration": 28, "mood": 3},
    "零食": {"satiety": 12, "mood": 8},
    "食物": {"satiety": 45, "mood": 4},
    "书籍": {"mood": 3},
    "数码": {"mood": 6},
    "穿搭": {"mood": 5},
    "居家": {"mood": 4},
    "兴趣": {"mood": 6},
    "礼物": {"mood": 8},
    "愿望": {"mood": 10},
}


def load_goods(path: Path | None = None) -> list[dict[str, Any]]:
    target = Path(path) if path else GOODS_PATH
    try:
        content = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    goods = content.get("goods") if isinstance(content, dict) else content
    if not isinstance(goods, list):
        return []
    return [item for item in goods if isinstance(item, dict)]


def list_goods(category: str = "", *, limit: int = 40) -> list[dict[str, Any]]:
    items = load_goods()
    category = str(category or "").strip()
    if category:
        items = [
            item for item in items if category in str(item.get("category") or "")
        ]
    return items[: max(1, int(limit or 40))]


def find_goods(query: str) -> dict[str, Any] | None:
    text = str(query or "").strip().casefold()
    if not text:
        return None
    items = load_goods()
    for item in items:
        if text in (
            str(item.get("id") or "").casefold(),
            str(item.get("name") or "").casefold(),
        ):
            return item
    for item in items:
        fields = " ".join(
            str(item.get(key) or "")
            for key in ("name", "category", "description")
        ).casefold()
        if text in fields:
            return item
    return None


def format_goods(items: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"{item.get('icon') or '·'} {item.get('name')} "
        f"（{item.get('category')}）{item.get('price')} 元 · id={item.get('id')}"
        for item in items
    )


def use_item(
    data_dir: Path,
    persona: str,
    query: str,
    *,
    at: datetime | None = None,
) -> dict[str, Any]:
    text = str(query or "").strip().casefold()
    if not text:
        return {"ok": False, "error": "没有指定物品"}
    snapshot = money.snapshot(data_dir, persona, limit=1)
    possession = None
    for item in snapshot.get("possessions") or []:
        if text in (
            str(item.get("id") or "").casefold(),
            str(item.get("name") or "").casefold(),
        ):
            possession = item
            break
    if possession is None:
        return {"ok": False, "error": "她没有这件东西"}
    catalog = find_goods(
        str(possession.get("id") or possession.get("name") or "")
    ) or possession
    category = str(
        catalog.get("category") or possession.get("category") or ""
    )
    effects = DEFAULT_EFFECTS.get(category, {"mood": 2})
    consumed = category in CONSUMABLE_CATEGORIES
    if not consumed:
        effects = {
            key: round(float(value) / 2.0, 1)
            for key, value in effects.items()
        }
    result = item_effects.add(
        data_dir,
        persona,
        effects,
        label=str(possession.get("name") or "物品"),
        now=at,
        ttl_minutes=120 if consumed else 60,
    )
    if not result.get("ok"):
        return result
    if consumed:
        removed = money.remove_possession(
            data_dir,
            persona,
            str(possession.get("id") or possession.get("name") or ""),
        )
        if not removed.get("ok"):
            return removed
    return {
        "ok": True,
        "item": possession,
        "category": category,
        "effects": effects,
        "consumed": consumed,
    }


def purchase(
    data_dir: Path,
    persona: str,
    query: str,
    quantity: int = 1,
    *,
    at: datetime | None = None,
    delivery_minutes: int = 0,
) -> dict[str, Any]:
    item = find_goods(query)
    if item is None:
        return {"ok": False, "error": "没有这件商品"}
    count = max(1, min(int(quantity or 1), 5))
    unit_price = round(float(item.get("price") or 0.0), 2)
    amount = round(unit_price * count, 2)
    result = money.spend(
        data_dir,
        persona,
        amount,
        f"买{item.get('name')}×{count}",
        kind="purchase",
        at=at,
    )
    if not result.get("ok"):
        return result
    if delivery_minutes > 0:
        order = delivery.place_order(
            data_dir,
            persona,
            item,
            count,
            amount,
            now=at,
            minutes=delivery_minutes,
        )
        return {
            "ok": True,
            "goods": item,
            "quantity": count,
            "amount": amount,
            "balance": result["balance"],
            "delivery": True,
            "order": order,
        }
    for _ in range(count):
        money.add_possession(
            data_dir,
            persona,
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "category": item.get("category"),
                "price": unit_price,
                "book_id": item.get("book_id"),
            },
            source="purchase",
            at=at,
        )
    return {
        "ok": True,
        "goods": item,
        "quantity": count,
        "amount": amount,
        "balance": result["balance"],
    }
