from __future__ import annotations

import json
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Any

from . import transport as transport_modes

DEFAULT_HOURLY_RATE = 20.0
MAX_TRANSACTIONS = 60

WORK_KEYWORDS = (
    "工作",
    "上班",
    "开会",
    "会议",
    "写代码",
    "加班",
    "项目",
    "拍摄",
    "演出",
    "上课",
    "备课",
    "值班",
    "客户",
    "报告",
    "画图",
    "做方案",
    "剪辑",
    "修图",
    "直播",
    "接单",
    "兼职",
    "跑腿",
)

BREAKFAST_WORDS = ("早餐", "早饭", "吃早")
LUNCH_WORDS = ("午餐", "午饭", "吃午", "中饭")
DINNER_WORDS = ("晚餐", "晚饭", "吃晚")
MEAL_WORDS = ("吃饭", "用餐", "下馆子", "外卖")
TRANSPORT_WORDS = (
    "通勤",
    "出门",
    "外出",
    "地铁",
    "公交",
    "打车",
    "路上",
    "赶路",
    "去公司",
    "回家",
)

_LOCK = threading.RLock()


def _money_path(data_dir: Path) -> Path:
    return Path(data_dir) / "money.json"


def _load(data_dir: Path) -> dict[str, Any]:
    path = _money_path(data_dir)
    if not path.exists():
        return {"schema_version": 1, "wallets": {}}
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "wallets": {}}
    if not isinstance(content, dict):
        return {"schema_version": 1, "wallets": {}}
    if not isinstance(content.get("wallets"), dict):
        content["wallets"] = {}
    return content


def _save(data_dir: Path, content: dict[str, Any]) -> None:
    path = _money_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def _wallet(content: dict[str, Any], persona: str) -> dict[str, Any]:
    wallets = content.setdefault("wallets", {})
    wallet = wallets.setdefault(
        str(persona),
        {
            "balance": 0.0,
            "settled_work_dates": [],
            "settled_work_segments": [],
            "settled_expense_segments": [],
            "goal": None,
            "possessions": [],
            "transactions": [],
        },
    )
    wallet.setdefault("balance", 0.0)
    wallet.setdefault("settled_work_dates", [])
    wallet.setdefault("settled_work_segments", [])
    wallet.setdefault("settled_expense_segments", [])
    wallet.setdefault("goal", None)
    wallet.setdefault("possessions", [])
    wallet.setdefault("transactions", [])
    return wallet


def balance(data_dir: Path, persona: str) -> float:
    with _LOCK:
        wallet = _wallet(_load(data_dir), persona)
        return round(float(wallet.get("balance") or 0.0), 2)


def possessions(data_dir: Path, persona: str) -> list[dict[str, Any]]:
    """Return every stored possession (including placed ones)."""
    with _LOCK:
        wallet = _wallet(_load(data_dir), persona)
        return [
            item
            for item in (wallet.get("possessions") or [])
            if isinstance(item, dict)
        ]


def snapshot(data_dir: Path, persona: str, limit: int = 5) -> dict[str, Any]:
    with _LOCK:
        wallet = _wallet(_load(data_dir), persona)
        transactions = wallet.get("transactions") or []
        balance_value = round(float(wallet.get("balance") or 0.0), 2)
        goal = wallet.get("goal")
        goal_info = None
        if isinstance(goal, dict):
            target = round(float(goal.get("target") or 0.0), 2)
            goal_info = {
                "name": str(goal.get("name") or "").strip()[:40],
                "wish": str(goal.get("wish") or "").strip()[:120],
                "target": target,
                "progress": balance_value,
                "remaining": round(max(0.0, target - balance_value), 2),
                "achieved": target > 0 and balance_value >= target,
                "fulfilled": bool(goal.get("fulfilled")),
                "requested_at": str(goal.get("requested_at") or ""),
                "created_at": str(goal.get("created_at") or ""),
            }
        return {
            "persona": str(persona),
            "balance": balance_value,
            "goal": goal_info,
            "possessions": _enrich_possessions(wallet),
            "transactions": transactions[-max(1, limit) :],
        }


def _enrich_possessions(wallet: dict[str, Any]) -> list[dict[str, Any]]:
    """Attach catalog placement flags for the inventory UI."""
    from . import goods

    result: list[dict[str, Any]] = []
    for raw in (wallet.get("possessions") or [])[-10:]:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        catalog = goods.find_goods(
            str(item.get("id") or item.get("name") or "")
        ) or {}
        item["installable"] = bool(catalog.get("installable"))
        if catalog.get("actions"):
            item["actions"] = [
                str(action) for action in (catalog.get("actions") or [])
            ][:4]
        if catalog.get("interact_label"):
            item["interact_label"] = str(catalog.get("interact_label"))
        result.append(item)
    return result


def add(
    data_dir: Path,
    persona: str,
    amount: float,
    reason: str,
    *,
    kind: str = "income",
    at: datetime | None = None,
) -> dict[str, Any]:
    value = round(float(amount), 2)
    if value == 0:
        return snapshot(data_dir, persona)
    now = at or datetime.now()
    with _LOCK:
        content = _load(data_dir)
        wallet = _wallet(content, persona)
        wallet["balance"] = round(
            float(wallet.get("balance") or 0.0) + value, 2
        )
        transactions = wallet.get("transactions") or []
        transactions.append(
            {
                "at": now.isoformat(timespec="seconds"),
                "amount": value,
                "reason": str(reason or "")[:120],
                "kind": str(kind or "income")[:20],
            }
        )
        wallet["transactions"] = transactions[-MAX_TRANSACTIONS:]
        _save(data_dir, content)
        return {
            "persona": str(persona),
            "balance": wallet["balance"],
            "amount": value,
        }


def backfill_placements(data_dir: Path) -> bool:
    """给旧数据里「只写了房间、没有坐标」的物品补上稳定摆位。"""
    changed = False
    with _LOCK:
        content = _load(data_dir)
        wallets = content.get("wallets")
        if not isinstance(wallets, dict):
            return False
        for wallet in wallets.values():
            if not isinstance(wallet, dict):
                continue
            items = [
                item
                for item in (wallet.get("possessions") or [])
                if isinstance(item, dict)
            ]
            for item in items:
                room = str(item.get("room") or "").strip()
                if not room or _normalize_place(item.get("place")) is not None:
                    continue
                item["place"] = _next_placement(items, room)
                item["placed_at"] = datetime.now().isoformat(timespec="seconds")
                changed = True
            if changed:
                wallet["possessions"] = items
        if changed:
            _save(data_dir, content)
    return changed


def remove_possession(
    data_dir: Path,
    persona: str,
    query: str,
) -> dict[str, Any]:
    text = str(query or "").strip().casefold()
    if not text:
        return {"ok": False, "error": "没有指定物品"}
    with _LOCK:
        content = _load(data_dir)
        wallet = _wallet(content, persona)
        possessions = list(wallet.get("possessions") or [])
        index = None
        for position, item in enumerate(possessions):
            keys = (
                str(item.get("id") or "").casefold(),
                str(item.get("name") or "").casefold(),
            )
            if text in keys:
                index = position
                break
        if index is None:
            return {"ok": False, "error": "她没有这件东西"}
        removed = possessions.pop(index)
        wallet["possessions"] = possessions
        _save(data_dir, content)
        return {"ok": True, "item": removed}


PLACEMENT_SLOTS = (
    (0.22, 0.30),
    (0.72, 0.30),
    (0.38, 0.56),
    (0.62, 0.70),
    (0.24, 0.72),
    (0.78, 0.56),
    (0.50, 0.40),
    (0.18, 0.50),
)


def _normalize_place(value: Any) -> dict[str, float] | None:
    if not isinstance(value, dict):
        return None
    try:
        x = float(value.get("x"))
        y = float(value.get("y"))
    except (TypeError, ValueError):
        return None
    return {
        "x": round(max(0.05, min(0.95, x)), 3),
        "y": round(max(0.05, min(0.95, y)), 3),
    }


def _next_placement(
    possessions: list[dict[str, Any]],
    room: str,
    *,
    x: Any = None,
    y: Any = None,
) -> dict[str, float]:
    explicit = _normalize_place({"x": x, "y": y})
    if explicit is not None:
        return explicit
    used = [
        place
        for item in possessions
        if str(item.get("room") or "") == room
        for place in (_normalize_place(item.get("place")),)
        if place is not None
    ]
    for index, slot in enumerate(PLACEMENT_SLOTS):
        while index < len(PLACEMENT_SLOTS):
            candidate = PLACEMENT_SLOTS[index]
            if not any(
                abs(candidate[0] - place["x"]) < 0.08
                and abs(candidate[1] - place["y"]) < 0.08
                for place in used
            ):
                return {"x": round(candidate[0], 3), "y": round(candidate[1], 3)}
            index += 1
    count = len(used)
    return {
        "x": round(min(0.9, 0.18 + (count % 5) * 0.16), 3),
        "y": round(min(0.9, 0.22 + (count // 5) * 0.13), 3),
    }


def place_possession(
    data_dir: Path,
    persona: str,
    query: str,
    room: str,
    *,
    x: Any = None,
    y: Any = None,
    slot_id: str = "",
    auto_slot: bool = False,
    z_cm: Any = None,
    surface_id: str = "",
) -> dict[str, Any]:
    text = str(query or "").strip().casefold()
    room_name = str(room or "").strip()[:10]
    slot_key = str(slot_id or "").strip()
    if not text or (not room_name and not slot_key and not auto_slot):
        return {"ok": False, "error": "要指定物品和房间"}
    with _LOCK:
        content = _load(data_dir)
        wallet = _wallet(content, persona)
        possessions = list(wallet.get("possessions") or [])
        for item in possessions:
            if text in (
                str(item.get("id") or "").casefold(),
                str(item.get("name") or "").casefold(),
            ):
                if slot_key or auto_slot:
                    from . import furniture_slots, goods

                    catalog_item = goods.find_goods(
                        str(item.get("id") or item.get("name") or "")
                    )
                    if not catalog_item or not catalog_item.get("installable"):
                        return {"ok": False, "error": "这件东西不能安装到家具点位"}
                    slot = (
                        furniture_slots.find_slot(slot_key)
                        if slot_key
                        else furniture_slots.first_free_slot(
                            data_dir, persona, catalog_item, room_name
                        )
                    )
                    if not slot:
                        return {"ok": False, "error": "没有匹配的空闲预留点位"}
                    if not furniture_slots.slot_fits(slot, catalog_item):
                        return {"ok": False, "error": "这个点位放不下这件东西"}
                    for other in possessions:
                        if other is item:
                            continue
                        if str(other.get("slot_id") or "") == str(slot.get("id")):
                            return {"ok": False, "error": "这个点位已经被占用了"}
                    item["room"] = str(slot.get("room") or room_name)
                    item["slot_id"] = str(slot.get("id") or "")
                    item["slot_label"] = str(slot.get("label") or "")
                    item["place"] = {
                        "x": float(slot.get("x") or 0.5),
                        "y": float(slot.get("y") or 0.5),
                        "facing": str(slot.get("facing") or "S"),
                        "z_cm": float(slot.get("z_cm") or 0),
                    }
                    item["placed_at"] = datetime.now().isoformat(timespec="seconds")
                    wallet["possessions"] = possessions
                    _save(data_dir, content)
                    return {
                        "ok": True,
                        "item": item,
                        "room": item["room"],
                        "slot": slot,
                    }
                moved_room = str(item.get("room") or "") != room_name
                has_explicit = x is not None and y is not None
                item["room"] = room_name
                item.pop("slot_id", None)
                item.pop("slot_label", None)
                if (
                    moved_room
                    or has_explicit
                    or _normalize_place(item.get("place")) is None
                ):
                    item["place"] = _next_placement(
                        possessions,
                        room_name,
                        x=x,
                        y=y,
                    )
                if isinstance(item.get("place"), dict):
                    try:
                        item["place"]["z_cm"] = round(
                            max(0.0, min(200.0, float(z_cm or 0))), 1
                        )
                    except (TypeError, ValueError):
                        item["place"]["z_cm"] = 0
                    item["place"]["surface_id"] = str(surface_id or "")[:40]
                item["placed_at"] = datetime.now().isoformat(timespec="seconds")
                wallet["possessions"] = possessions
                _save(data_dir, content)
                return {"ok": True, "item": item, "room": room_name}
        return {"ok": False, "error": "她没有这件东西"}


def add_possession(
    data_dir: Path,
    persona: str,
    goods: dict[str, Any],
    *,
    source: str = "purchase",
    at: datetime | None = None,
) -> dict[str, Any]:
    now = at or datetime.now()
    with _LOCK:
        content = _load(data_dir)
        wallet = _wallet(content, persona)
        possessions = wallet.get("possessions") or []
        possessions.append(
            {
                "id": str(goods.get("id") or "")[:40],
                "name": str(goods.get("name") or "物品")[:40],
                "wish": str(goods.get("wish") or "")[:120],
                "category": str(goods.get("category") or "")[:20],
                "price": round(float(goods.get("price") or 0.0), 2),
                "book_id": str(goods.get("book_id") or "")[:40],
                "installable": bool(goods.get("installable")),
                "slot_tags": [
                    str(tag)[:24] for tag in (goods.get("slot_tags") or [])
                ],
                "source": str(source or "purchase")[:20],
                "at": now.isoformat(timespec="seconds"),
            }
        )
        wallet["possessions"] = possessions[-100:]
        _save(data_dir, content)
        return {
            "ok": True,
            "possessions": wallet["possessions"][-10:],
        }


def set_goal(
    data_dir: Path,
    persona: str,
    name: str,
    target: float,
    *,
    wish: str = "",
    at: datetime | None = None,
) -> dict[str, Any]:
    goal_name = str(name or "").strip()[:40]
    target_value = round(float(target or 0.0), 2)
    if not goal_name:
        return {"ok": False, "error": "目标名称不能为空"}
    if target_value <= 0:
        return {"ok": False, "error": "目标金额必须大于 0"}
    now = at or datetime.now()
    with _LOCK:
        content = _load(data_dir)
        wallet = _wallet(content, persona)
        wallet["goal"] = {
            "name": goal_name,
            "wish": str(wish or "").strip()[:120],
            "target": target_value,
            "created_at": now.isoformat(timespec="seconds"),
            "fulfilled": False,
            "requested_at": "",
        }
        _save(data_dir, content)
    return {"ok": True, "goal": snapshot(data_dir, persona)["goal"]}


def clear_goal(data_dir: Path, persona: str) -> dict[str, Any]:
    with _LOCK:
        content = _load(data_dir)
        wallet = _wallet(content, persona)
        cleared = isinstance(wallet.get("goal"), dict)
        wallet["goal"] = None
        _save(data_dir, content)
    return {"ok": True, "cleared": cleared}


def mark_goal_requested(
    data_dir: Path, persona: str, *, at: datetime | None = None
) -> dict[str, Any]:
    now = at or datetime.now()
    with _LOCK:
        content = _load(data_dir)
        wallet = _wallet(content, persona)
        goal = wallet.get("goal")
        if not isinstance(goal, dict):
            return {"ok": False, "error": "没有存款目标"}
        goal["requested_at"] = now.isoformat(timespec="seconds")
        wallet["goal"] = goal
        _save(data_dir, content)
    return {"ok": True, "goal": snapshot(data_dir, persona)["goal"]}


def fulfill_goal(
    data_dir: Path, persona: str, *, at: datetime | None = None
) -> dict[str, Any]:
    """Spend the saved target amount and mark the goal fulfilled."""
    now = at or datetime.now()
    with _LOCK:
        content = _load(data_dir)
        wallet = _wallet(content, persona)
        goal = wallet.get("goal")
        if not isinstance(goal, dict):
            return {"ok": False, "error": "没有存款目标"}
        if bool(goal.get("fulfilled")):
            return {"ok": False, "error": "这个愿望已经实现过了"}
        target = round(float(goal.get("target") or 0.0), 2)
        balance_value = round(float(wallet.get("balance") or 0.0), 2)
        if target <= 0 or balance_value < target:
            return {
                "ok": False,
                "error": "月月还没攒够钱",
                "balance": balance_value,
                "target": target,
            }
        wallet["balance"] = round(balance_value - target, 2)
        transactions = wallet.get("transactions") or []
        transactions.append(
            {
                "at": now.isoformat(timespec="seconds"),
                "amount": -target,
                "reason": f"实现愿望：{goal.get('name') or ''}",
                "kind": "wish",
            }
        )
        wallet["transactions"] = transactions[-MAX_TRANSACTIONS:]
        goal["fulfilled"] = True
        goal["fulfilled_at"] = now.isoformat(timespec="seconds")
        wallet["goal"] = goal
        possessions = wallet.get("possessions") or []
        possessions.append(
            {
                "id": str(goal.get("name") or "wish"),
                "name": str(goal.get("name") or "愿望"),
                "wish": str(goal.get("wish") or ""),
                "category": "愿望",
                "price": target,
                "source": "wish",
                "at": now.isoformat(timespec="seconds"),
            }
        )
        wallet["possessions"] = possessions[-100:]
        _save(data_dir, content)
        return {
            "ok": True,
            "amount": target,
            "balance": wallet["balance"],
            "goal": snapshot(data_dir, persona)["goal"],
        }


def _minutes(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        hour, minute = text.split(":", 1)
        return int(hour) * 60 + int(minute)
    except (TypeError, ValueError):
        return None


def _timeline_items(plan: Any) -> list[Any]:
    timeline = getattr(plan, "timeline", None)
    if timeline is None and isinstance(plan, dict):
        timeline = plan.get("timeline")
    return list(timeline or [])


def _segment_fields(item: Any) -> tuple[str, Any, Any]:
    if isinstance(item, dict):
        return (
            str(item.get("activity") or ""),
            item.get("start"),
            item.get("end"),
        )
    return (
        str(getattr(item, "activity", "") or ""),
        getattr(item, "start", ""),
        getattr(item, "end", ""),
    )


def work_segments(plan: Any, *, before: datetime | None = None) -> list[dict[str, Any]]:
    """Return completed work segments, optionally only those ending before ``before``."""
    before_minutes = None
    if before is not None:
        before_minutes = before.hour * 60 + before.minute
    segments: list[dict[str, Any]] = []
    for item in _timeline_items(plan):
        activity, start_text, end_text = _segment_fields(item)
        if not any(word in activity for word in WORK_KEYWORDS):
            continue
        start = _minutes(start_text)
        end = _minutes(end_text)
        if start is None or end is None or end <= start:
            continue
        if before_minutes is not None and end > before_minutes:
            continue
        item_id = (
            str(item.get("id") or "")
            if isinstance(item, dict)
            else str(getattr(item, "id", "") or "")
        )
        key = item_id or f"{start_text}-{end_text}-{activity}"
        segments.append(
            {
                "key": key,
                "activity": activity,
                "start": start,
                "end": end,
                "minutes": min(end - start, 16 * 60),
            }
        )
    return segments


def expense_segments(
    plan: Any,
    *,
    before: datetime | None = None,
    breakfast: float = 8.0,
    lunch: float = 18.0,
    dinner: float = 22.0,
    transport: float = 4.0,
) -> list[dict[str, Any]]:
    """Return completed meal/transport expense segments for a plan."""
    before_minutes = None
    if before is not None:
        before_minutes = before.hour * 60 + before.minute
    costs = {
        "breakfast": max(0.0, float(breakfast)),
        "lunch": max(0.0, float(lunch)),
        "dinner": max(0.0, float(dinner)),
        "transport": max(0.0, float(transport)),
    }
    labels = {
        "breakfast": "早餐",
        "lunch": "午餐",
        "dinner": "晚餐",
        "transport": "出行",
    }
    segments: list[dict[str, Any]] = []
    for item in _timeline_items(plan):
        activity, start_text, end_text = _segment_fields(item)
        start = _minutes(start_text)
        end = _minutes(end_text)
        if start is None or end is None or end <= start:
            continue
        if before_minutes is not None and end > before_minutes:
            continue
        if any(word in activity for word in BREAKFAST_WORDS):
            kind = "breakfast"
        elif any(word in activity for word in LUNCH_WORDS):
            kind = "lunch"
        elif any(word in activity for word in DINNER_WORDS):
            kind = "dinner"
        elif any(word in activity for word in MEAL_WORDS):
            kind = "lunch"
        elif any(word in activity for word in TRANSPORT_WORDS):
            kind = "transport"
        else:
            continue
        if kind == "transport":
            cost = transport_modes.cost_for(activity, costs["transport"])
        else:
            cost = costs[kind]
        if cost <= 0:
            continue
        item_id = (
            str(item.get("id") or "")
            if isinstance(item, dict)
            else str(getattr(item, "id", "") or "")
        )
        key = item_id or f"{start_text}-{end_text}-{activity}"
        segments.append(
            {
                "key": key,
                "kind": kind,
                "label": labels[kind],
                "activity": activity,
                "cost": round(cost, 2),
            }
        )
    return segments


def settle_expense_segments(
    data_dir: Path,
    persona: str,
    day: str,
    plan: Any,
    *,
    before: datetime | None = None,
    breakfast: float = 8.0,
    lunch: float = 18.0,
    dinner: float = 22.0,
    transport: float = 4.0,
    at: datetime | None = None,
) -> dict[str, Any]:
    """Charge completed living-cost segments; balance may go negative (debt)."""
    day_text = str(day or "").strip()
    if not day_text:
        return {
            "amount": 0.0,
            "settled_count": 0,
            "skipped": True,
        }
    segments = expense_segments(
        plan,
        before=before,
        breakfast=breakfast,
        lunch=lunch,
        dinner=dinner,
        transport=transport,
    )
    if not segments:
        return {
            "amount": 0.0,
            "settled_count": 0,
            "skipped": True,
        }
    with _LOCK:
        content = _load(data_dir)
        wallet = _wallet(content, persona)
        settled = {
            str(value)
            for value in wallet.get("settled_expense_segments") or []
        }
        fresh = [
            segment
            for segment in segments
            if f"{day_text}::{segment['key']}" not in settled
        ]
        if not fresh:
            return {
                "amount": 0.0,
                "settled_count": 0,
                "skipped": True,
                "balance": round(float(wallet.get("balance") or 0.0), 2),
            }
        amount = round(sum(segment["cost"] for segment in fresh), 2)
        wallet["balance"] = round(
            float(wallet.get("balance") or 0.0) - amount, 2
        )
        transactions = wallet.get("transactions") or []
        labels = "、".join(segment["label"] for segment in fresh)
        transactions.append(
            {
                "at": (at or datetime.now()).isoformat(timespec="seconds"),
                "amount": -amount,
                "reason": f"{day_text} 生活开销（{labels}）",
                "kind": "living",
            }
        )
        wallet["transactions"] = transactions[-MAX_TRANSACTIONS:]
        wallet["settled_expense_segments"] = sorted(
            [
                *settled,
                *(f"{day_text}::{segment['key']}" for segment in fresh),
            ]
        )
        _save(data_dir, content)
        return {
            "amount": amount,
            "settled_count": len(fresh),
            "skipped": False,
            "balance": wallet["balance"],
        }


def work_minutes(plan: Any, *, before: datetime | None = None) -> int:
    return sum(segment["minutes"] for segment in work_segments(plan, before=before))


def settle_work_segments(
    data_dir: Path,
    persona: str,
    day: str,
    plan: Any,
    *,
    before: datetime | None = None,
    hourly_rate: float = DEFAULT_HOURLY_RATE,
    at: datetime | None = None,
) -> dict[str, Any]:
    """Credit newly completed work segments, idempotent per segment."""
    day_text = str(day or "").strip()
    if not day_text:
        return {
            "amount": 0.0,
            "minutes": 0,
            "settled_count": 0,
            "skipped": True,
        }
    segments = work_segments(plan, before=before)
    if not segments:
        return {
            "amount": 0.0,
            "minutes": 0,
            "settled_count": 0,
            "skipped": True,
        }
    with _LOCK:
        content = _load(data_dir)
        wallet = _wallet(content, persona)
        legacy = {
            str(value) for value in wallet.get("settled_work_dates") or []
        }
        if day_text in legacy:
            return {
                "amount": 0.0,
                "minutes": 0,
                "settled_count": 0,
                "skipped": True,
                "balance": round(float(wallet.get("balance") or 0.0), 2),
            }
        settled = {
            str(value) for value in wallet.get("settled_work_segments") or []
        }
        fresh = [
            segment
            for segment in segments
            if f"{day_text}::{segment['key']}" not in settled
        ]
        if not fresh:
            return {
                "amount": 0.0,
                "minutes": 0,
                "settled_count": 0,
                "skipped": True,
                "balance": round(float(wallet.get("balance") or 0.0), 2),
            }
        minutes = sum(segment["minutes"] for segment in fresh)
        amount = round(
            (minutes / 60.0) * max(0.0, float(hourly_rate)), 2
        )
        if amount > 0:
            wallet["balance"] = round(
                float(wallet.get("balance") or 0.0) + amount, 2
            )
            transactions = wallet.get("transactions") or []
            transactions.append(
                {
                    "at": (at or datetime.now()).isoformat(timespec="seconds"),
                    "amount": amount,
                    "reason": (
                        f"{day_text} 工作 {minutes} 分钟"
                        f"（{len(fresh)} 段）"
                    ),
                    "kind": "work",
                }
            )
            wallet["transactions"] = transactions[-MAX_TRANSACTIONS:]
        wallet["settled_work_segments"] = sorted(
            [
                *settled,
                *(f"{day_text}::{segment['key']}" for segment in fresh),
            ]
        )
        _save(data_dir, content)
        return {
            "amount": amount,
            "minutes": minutes,
            "settled_count": len(fresh),
            "skipped": False,
            "balance": round(float(wallet.get("balance") or 0.0), 2),
        }


def settle_work_income(
    data_dir: Path,
    persona: str,
    day: str,
    plan: Any,
    *,
    hourly_rate: float = DEFAULT_HOURLY_RATE,
    at: datetime | None = None,
) -> dict[str, Any]:
    """Backward-compatible full-day settlement wrapper."""
    return settle_work_segments(
        data_dir,
        persona,
        day,
        plan,
        hourly_rate=hourly_rate,
        at=at,
    )


def spent_on(data_dir: Path, persona: str, day: str) -> float:
    """Sum of spending-kind transactions on a given day."""
    prefix = str(day or "").strip()
    if not prefix:
        return 0.0
    with _LOCK:
        wallet = _wallet(_load(data_dir), persona)
    total = 0.0
    for item in wallet.get("transactions") or []:
        if str(item.get("kind") or "") != "spend":
            continue
        if str(item.get("at") or "")[:10] != prefix:
            continue
        total += max(0.0, -float(item.get("amount") or 0.0))
    return round(total, 2)


def spend(
    data_dir: Path,
    persona: str,
    amount: float,
    reason: str,
    *,
    kind: str = "spend",
    at: datetime | None = None,
) -> dict[str, Any]:
    value = round(abs(float(amount or 0.0)), 2)
    if value <= 0:
        return {"ok": False, "error": "金额必须大于 0"}
    now = at or datetime.now()
    with _LOCK:
        content = _load(data_dir)
        wallet = _wallet(content, persona)
        balance_value = round(float(wallet.get("balance") or 0.0), 2)
        if balance_value < value:
            return {
                "ok": False,
                "error": "余额不足",
                "balance": balance_value,
            }
        wallet["balance"] = round(balance_value - value, 2)
        transactions = wallet.get("transactions") or []
        transactions.append(
            {
                "at": now.isoformat(timespec="seconds"),
                "amount": -value,
                "reason": str(reason or "").strip()[:120] or "日常开销",
                "kind": str(kind or "spend")[:20],
            }
        )
        wallet["transactions"] = transactions[-MAX_TRANSACTIONS:]
        _save(data_dir, content)
        return {
            "ok": True,
            "amount": value,
            "balance": wallet["balance"],
        }


def format_money(value: float) -> str:
    number = round(float(value or 0.0), 2)
    if number == int(number):
        return f"{int(number)}"
    return f"{number:.2f}"
