"""玩家下厨：用当前冰箱库存匹配可做的料理、评分并消耗食材。

观察窗的「由我下厨」按钮走这里：列出食材齐全的菜 -> 前端小游戏 ->
按分数评定味道 -> 把做好的菜写入记录 -> 点击菜呼叫角色来吃饭。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from .jsonio import atomic_write_json, synchronized

COOK_HISTORY_FILE = "cooking_history.json"
MAX_HISTORY = 50
KITCHEN_TABLE_ID = "dining_table"


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, payload)


def _normalize(name: Any) -> str:
    return re.sub(r"[\s\W_]+", "", str(name or ""))


def _clean(value: Any, limit: int = 80) -> str:
    return str(value or "").strip()[:limit]


def _inventory_by_name(food: Any) -> dict[str, dict[str, Any]]:
    """返回库存里数量足够的食材，按规范化名称建索引。"""
    try:
        inventory = food.load_inventory()
    except Exception:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for name, item in (inventory or {}).items():
        if not isinstance(item, dict):
            continue
        try:
            quantity = float(item.get("quantity") or 0)
        except (TypeError, ValueError):
            quantity = 0.0
        if quantity <= 0.05:
            continue
        key = _normalize(name)
        if key:
            result[key] = item
    return result


def _match_ingredient(inventory: dict[str, dict[str, Any]], name: str) -> str:
    """在库存里找食材，返回库存里的正式名称；找不到返回空串。"""
    target = _normalize(name)
    if not target:
        return ""
    for key, item in inventory.items():
        stored = _normalize(item.get("name") or key)
        if not stored:
            continue
        if stored == target or (len(stored) >= 2 and len(target) >= 2 and (
            stored in target or target in stored
        )):
            return str(item.get("name") or key)
    return ""


def makeable_dishes(food: Any, limit: int = 40) -> list[dict[str, Any]]:
    """从菜谱里挑出食材齐全的菜，按食材数和菜名排序。"""
    catalog = {}
    try:
        catalog = food.load_catalog()
    except Exception:
        catalog = {}
    meals = catalog.get("meals") if isinstance(catalog, dict) else {}
    if not isinstance(meals, dict):
        return []
    inventory = _inventory_by_name(food)
    if not inventory:
        return []
    dishes: dict[str, dict[str, Any]] = {}
    for meal_name, meal_dishes in meals.items():
        if not isinstance(meal_dishes, list):
            continue
        for raw in meal_dishes:
            if not isinstance(raw, dict):
                continue
            name = _clean(raw.get("name"), 40)
            if not name:
                continue
            ingredients = [
                _clean(item, 20)
                for item in raw.get("ingredients") or []
                if _clean(item, 20)
            ]
            if not ingredients:
                continue
            resolved = [_match_ingredient(inventory, item) for item in ingredients]
            if any(not item for item in resolved):
                continue
            entry = dishes.setdefault(
                name,
                {
                    "name": name,
                    "ingredients": ingredients,
                    "resolved_ingredients": resolved,
                    "method": _clean(raw.get("method"), 40),
                    "meals": [],
                },
            )
            meal_text = _clean(meal_name, 10)
            if meal_text and meal_text not in entry["meals"]:
                entry["meals"].append(meal_text)
    result = list(dishes.values())
    result.sort(
        key=lambda item: (
            -len(item.get("ingredients") or []),
            -len(item.get("meals") or []),
            str(item.get("name") or ""),
        )
    )
    return result[: max(1, int(limit))]


def rate_taste(score: Any, ingredient_count: int = 0) -> dict[str, Any]:
    """按小游戏分数评定味道（后端统一，前端只展示）。"""
    try:
        value = max(0, min(100, int(round(float(score)))))
    except (TypeError, ValueError):
        value = 0
    if value >= 92:
        grade, label, comment = (
            "S",
            "封神之作",
            "火候、咸淡和卖相都在线，月月嘴上挑刺，筷子倒很诚实。",
        )
    elif value >= 80:
        grade, label, comment = (
            "A",
            "意外好吃",
            "本来没抱多大希望，结果一口下去挺像回事。",
        )
    elif value >= 65:
        grade, label, comment = (
            "B",
            "像样的一餐",
            "不惊艳，但热乎、能吃饱，配一句毒舌刚好。",
        )
    elif value >= 45:
        grade, label, comment = (
            "C",
            "勉强能咽",
            "味道有点飘，胜在没把厨房点着。",
        )
    elif value >= 25:
        grade, label, comment = (
            "D",
            "有点糊",
            "边缘焦了，中间还生着，属于勇气可嘉型料理。",
        )
    else:
        grade, label, comment = (
            "E",
            "黑暗料理",
            "建议端上桌之前先给厨房和自己道个歉。",
        )
    if ingredient_count >= 5 and value >= 80:
        comment += " 食材给得够实在。"
    return {
        "score": value,
        "grade": grade,
        "label": label,
        "comment": comment,
    }


def consume_ingredients(plugin: Any, dish: dict[str, Any]) -> dict[str, Any]:
    """复用即时互动的食材扣减逻辑，扣掉这道菜用到的库存。"""
    service = getattr(plugin, "interactions", None)
    settings = {}
    try:
        settings = plugin.config.get("interaction_settings", {}) or {}
    except Exception:
        settings = {}
    if service is None:
        return {"used": [], "missing": list(dish.get("ingredients") or [])}
    try:
        return service.consume_dish(
            {
                "name": dish.get("name"),
                "ingredients": list(dish.get("ingredients") or []),
            },
            settings,
        )
    except Exception:
        return {"used": [], "missing": list(dish.get("ingredients") or [])}


@synchronized
def record_cook(
    plugin: Any,
    dish: dict[str, Any],
    taste: dict[str, Any],
    usage: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """把这次下厨写进 cooking_history.json，并返回记录。"""
    data_dir = getattr(plugin, "data_dir", None)
    moment = now or datetime.now()
    record = {
        "at": moment.isoformat(timespec="seconds"),
        "dish": _clean(dish.get("name"), 40),
        "ingredients": list(dish.get("ingredients") or []),
        "method": _clean(dish.get("method"), 40),
        "score": int(taste.get("score") or 0),
        "grade": str(taste.get("grade") or ""),
        "label": str(taste.get("label") or ""),
        "used": usage.get("used") or [],
        "missing": usage.get("missing") or [],
        "eaten_by_ai": False,
    }
    if data_dir is None:
        return record
    path = Path(data_dir) / COOK_HISTORY_FILE
    payload = _read_json(path, [])
    history = payload if isinstance(payload, list) else []
    history.append(record)
    _write_json(path, history[-MAX_HISTORY:])
    return record


@synchronized
def mark_served(plugin: Any, dish_name: str, *, now: datetime | None = None) -> None:
    """标记最近一次同菜名记录已被端给角色（供后续查询/调试）。"""
    data_dir = getattr(plugin, "data_dir", None)
    if data_dir is None:
        return
    path = Path(data_dir) / COOK_HISTORY_FILE
    payload = _read_json(path, [])
    if not isinstance(payload, list):
        return
    target = _clean(dish_name, 40)
    for item in reversed(payload):
        if not isinstance(item, dict) or item.get("dish") != target:
            continue
        item["eaten_by_ai"] = True
        item["served_at"] = (now or datetime.now()).isoformat(timespec="seconds")
        break
    _write_json(path, payload[-MAX_HISTORY:])


def serve_interaction_payload(
    dish_name: str, taste_label: str, *, persona: str = ""
) -> dict[str, Any]:
    """构造点击菜品后发给角色的即时互动 payload。"""
    label = _clean(taste_label, 20) or "还行"
    text = f"我下厨做了{_clean(dish_name, 40)}（{label}），来吃饭吧。"
    return {
        "kind": "chat",
        "item_id": KITCHEN_TABLE_ID,
        "action": "吃饭",
        "text": text[:200],
        "persona": persona,
    }
