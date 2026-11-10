"""The character's memory of what actually happened, day by day.

The schedule says what she *planned*; this module remembers what *happened*:
what she ate, the small things she saw on the way, what the owner did with
her in the panel, what she bought, where they drove, what the owner cooked,
photos, gifts, the world event, relationship milestones.

``sync_day`` gathers these from the plugin's stores for one date and merges
them into ``life_memory.json`` (so a day stays remembered after the source
stores roll over). The formatting helpers turn them into short context for

* chat replies (``today_context`` / ``recent_context``),
* proactive messages (``unshared_encounter`` + ``mark_shared``),
* the next day's schedule generation (``recent_context``),
* the panel's 「动态」 timeline (``day_items``).
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from . import encounters
from .jsonio import atomic_write_json, synchronized

logger = logging.getLogger("astrbot")

FILE = "life_memory.json"
SCHEMA_VERSION = 1
KEEP_DAYS = 45

MEAL_DEFAULT_TIME = {"早餐": "07:30", "午餐": "12:00", "晚餐": "18:30"}
MEAL_WORDS = {
    "早餐": ("早餐", "早饭", "吃早"),
    "午餐": ("午餐", "午饭", "吃午", "中饭"),
    "晚餐": ("晚餐", "晚饭", "吃晚"),
}
SOURCE_TEXT = {"home": "在家做的", "out": "在外面吃的", "simple": "简单对付了一下", "delivery": "点的外卖"}
KIND_ICON = {
    "meal": "🍚",
    "encounter": "👀",
    "outing": "🚶",
    "interaction": "💬",
    "purchase": "🛍️",
    "money": "💰",
    "drive": "🚗",
    "delivery": "📦",
    "cooked": "🍳",
    "photo": "📷",
    "world": "🌤️",
    "milestone": "💗",
    "diary": "📔",
    "shopping": "🧺",
}


# --------------------------------------------------------------------- storage


def _path(data_dir: Path) -> Path:
    return Path(data_dir) / FILE


def _load(data_dir: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_path(data_dir).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": SCHEMA_VERSION, "personas": {}}
    if not isinstance(payload, dict) or not isinstance(payload.get("personas"), dict):
        return {"schema_version": SCHEMA_VERSION, "personas": {}}
    return payload


def _day_entry(payload: dict[str, Any], persona: str, day: str) -> dict[str, Any]:
    days = payload["personas"].setdefault(str(persona), {})
    entry = days.setdefault(day, {"items": [], "shared": []})
    entry.setdefault("items", [])
    entry.setdefault("shared", [])
    return entry


def _trim(payload: dict[str, Any], today: date) -> None:
    cutoff = (today - timedelta(days=KEEP_DAYS)).isoformat()
    for days in payload["personas"].values():
        for key in [key for key in days if key < cutoff]:
            del days[key]


def _item(day: str, time: str, kind: str, text: str, importance: int, key: str) -> dict[str, Any]:
    return {
        "key": key,
        "date": day,
        "time": str(time or "")[:5],
        "kind": kind,
        "icon": KIND_ICON.get(kind, "·"),
        "text": str(text or "").strip()[:160],
        "importance": max(1, min(3, int(importance))),
    }


# --------------------------------------------------------------------- sources


def _hhmm(value: Any) -> str:
    text = str(value or "")
    if len(text) >= 16 and text[10] in "T ":
        return text[11:16]
    return text[:5] if len(text) >= 5 and text[2:3] == ":" else ""


def _on_day(value: Any, day: str) -> bool:
    return str(value or "")[:10] == day


def _timeline(plan: Any) -> list[Any]:
    return sorted(getattr(plan, "timeline", ()) or (), key=lambda item: str(getattr(item, "start", "")))


def _weather(plan: Any) -> tuple[str, float | None]:
    weather = getattr(plan, "weather", None)
    condition = str(getattr(weather, "condition", "") or "")
    try:
        high = float(getattr(weather, "temperature_high", None))
    except (TypeError, ValueError):
        high = None
    return condition, high


def _minutes(text: str) -> int:
    try:
        hour, minute = str(text).split(":")[:2]
        return int(hour) * 60 + int(minute)
    except (TypeError, ValueError):
        return 0


def _meals(data_dir: Path, persona: str, day: str, plan: Any) -> list[dict[str, Any]]:
    try:
        state = json.loads((Path(data_dir) / "food_state.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    times: dict[str, str] = {}
    for item in _timeline(plan):
        for meal, words in MEAL_WORDS.items():
            if meal not in times and any(word in str(item.activity) for word in words):
                times[meal] = str(item.start)
    eaten: dict[str, dict[str, Any]] = {}
    for entry in state.get("log") or []:
        if isinstance(entry, dict) and str(entry.get("date")) == day and str(entry.get("persona_id")) == str(persona):
            if entry.get("meal"):
                eaten.setdefault(str(entry["meal"]), entry)
    # 日程里写的是「吃早饭」而没写菜名时，菜单记录对不上；这时按当天菜单补上
    menu = (state.get("menus") or {}).get(f"{day}::{persona}") or {}
    for entry in menu.get("meals") or [] if isinstance(menu, dict) else []:
        if isinstance(entry, dict) and str(entry.get("meal") or "") in times:
            eaten.setdefault(str(entry["meal"]), entry)
    result = []
    for meal, entry in eaten.items():
        dish = str(entry.get("dish") or "").strip()
        source = str(entry.get("source") or "")
        if not dish:
            continue
        how = SOURCE_TEXT.get(source, "")
        text = f"{meal}吃了{dish}" + (f"（{how}）" if how else "")
        time = times.get(meal) or MEAL_DEFAULT_TIME.get(meal, "")
        result.append(_item(day, time, "meal", text, 1, f"meal:{meal}"))
    for entry in state.get("shopping") or []:
        if not isinstance(entry, dict) or str(entry.get("date")) != day or str(entry.get("persona_id")) != str(persona):
            continue
        items = "、".join(str(name) for name in (entry.get("items") or [])[:5])
        if items:
            scene = str(entry.get("scene") or "超市")
            result.append(_item(day, "", "shopping", f"去{scene}买了{items}", 1, f"shopping:{scene}:{items}"))
    return result


def _timeline_items(persona: str, day: str, plan: Any, now: datetime | None) -> list[dict[str, Any]]:
    condition, high = _weather(plan)
    result: list[dict[str, Any]] = []
    used: set[str] = set()
    limit = now.hour * 60 + now.minute if now is not None and now.date().isoformat() == day else 24 * 60
    for item in _timeline(plan):
        activity = str(getattr(item, "activity", "") or "")
        location = str(getattr(item, "location", "") or "")
        state = str(getattr(item, "state", "") or "")
        end = _minutes(str(getattr(item, "end", "")))
        if end > limit:
            continue
        if encounters.is_on_the_way(activity, location, state):
            tags = encounters.context_tags(activity, location, condition, _minutes(str(item.start)) // 60, high)
            text = encounters.pick(f"{persona}|{day}|{item.start}|{activity}", tags, exclude=used)
            if text:
                used.add(text)
                result.append(_item(day, str(item.end), "encounter", f"{activity}时，{text}", 1, f"encounter:{item.start}"))
    return result


def _read(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _store_items(data_dir: Path, persona: str, day: str) -> list[dict[str, Any]]:
    data_dir = Path(data_dir)
    result: list[dict[str, Any]] = []
    # wallet: purchases, money from / to the owner, wishes
    wallet = ((_read(data_dir / "money.json") or {}).get("wallets") or {}).get(str(persona)) or {}
    for entry in wallet.get("transactions") or []:
        if not isinstance(entry, dict) or not _on_day(entry.get("at"), day):
            continue
        kind = str(entry.get("kind") or "")
        amount = float(entry.get("amount") or 0)
        reason = str(entry.get("reason") or "").strip()
        key = f"money:{entry.get('at')}:{reason}"
        if kind == "purchase":
            result.append(_item(day, _hhmm(entry.get("at")), "purchase", reason or "买了点东西", 2 if -amount >= 50 else 1, key))
        elif kind == "master":
            result.append(_item(day, _hhmm(entry.get("at")), "money", f"主人给了 {amount:g} 元" + (f"（{reason}）" if reason else ""), 2, key))
        elif kind == "wish":
            result.append(_item(day, _hhmm(entry.get("at")), "milestone", reason or "实现了一个愿望", 3, key))
    # garage trips
    garage = (((_read(data_dir / "garage.json") or {}).get("personas") or {}).get(str(persona)) or {})
    for trip in garage.get("trips") or []:
        if not isinstance(trip, dict) or not _on_day(trip.get("started_at"), day):
            continue
        destination = str(trip.get("destination") or "外面")
        car = str(trip.get("vehicle_name") or "车")
        with_owner = trip.get("driver") == "master"
        text = f"主人开着{car}带她去了{destination}" if with_owner else f"她自己开着{car}去了{destination}"
        result.append(_item(day, _hhmm(trip.get("started_at")), "drive", text, 3 if with_owner else 2, f"drive:{trip.get('id')}"))
    # panel interactions with the owner
    history = (_read(data_dir / "interactions" / "history.json") or {}).get("items") or []
    for entry in history:
        if not isinstance(entry, dict) or not _on_day(entry.get("at"), day):
            continue
        kind = str(entry.get("kind") or "")
        item_name = str(entry.get("item_name") or "").strip()
        action = str(entry.get("action") or "").strip()
        dish = entry.get("dish") if isinstance(entry.get("dish"), dict) else {}
        if kind == "dish" and dish.get("name"):
            text = f"给主人做了{dish['name']}"
        elif action == "give" and item_name:
            text = f"主人递来了{item_name}"
        elif item_name and action:
            text = f"主人在{item_name}那儿{action}"
        elif kind == "game":
            text = "和主人玩了一会儿小游戏"
        else:
            text = "和主人在观察窗里说了几句话"
        result.append(_item(day, _hhmm(entry.get("at")), "interaction", text, 2, f"interaction:{entry.get('id')}"))
    # deliveries
    for entry in (_read(data_dir / "deliveries.json") or {}).get("delivered") or []:
        if not isinstance(entry, dict) or str(entry.get("persona")) != str(persona) or not _on_day(entry.get("delivered_at"), day):
            continue
        goods = entry.get("goods") or {}
        result.append(_item(day, _hhmm(entry.get("delivered_at")), "delivery", f"快递送到了：{goods.get('name') or '包裹'}", 1, f"delivery:{entry.get('id')}"))
    # the owner cooked for her
    for entry in _read(data_dir / "cooking_history.json") or []:
        if not isinstance(entry, dict) or not _on_day(entry.get("served_at") or entry.get("at"), day) or not entry.get("eaten_by_ai"):
            continue
        label = str(entry.get("label") or "")
        result.append(_item(day, _hhmm(entry.get("served_at")), "cooked", f"主人下厨做了{entry.get('dish')}" + (f"，味道「{label}」" if label else ""), 2, f"cooked:{entry.get('at')}"))
    # photos
    camera = (((_read(data_dir / "camera_events.json") or {}).get("personas") or {}).get(str(persona))) or []
    for entry in camera if isinstance(camera, list) else []:
        if isinstance(entry, dict) and _on_day(entry.get("at"), day):
            subject = str(entry.get("item_name") or "") or {"character": "她", "room": "房间"}.get(str(entry.get("target")), "")
            result.append(_item(day, _hhmm(entry.get("at")), "photo", f"主人给{subject}拍了照片", 2, f"photo:{entry.get('id')}"))
    # the world event of the day
    world = ((((_read(data_dir / "world_events.json") or {}).get("personas") or {}).get(str(persona))) or {}).get(day)
    if isinstance(world, dict) and world.get("title"):
        result.append(_item(day, "", "world", f"{world['title']}：{world.get('summary') or ''}", 1, "world"))
    # relationship milestones
    relation = (((_read(data_dir / "affection.json") or {}).get("personas") or {}).get(str(persona))) or {}
    for entry in relation.get("milestones") or []:
        if isinstance(entry, dict) and _on_day(entry.get("at"), day):
            result.append(_item(day, _hhmm(entry.get("at")), "milestone", f"和主人的关系变成了「{entry.get('level')}」", 3, f"milestone:{entry.get('level')}"))
    # diary
    diary = ((((_read(data_dir / "diary.json") or {}).get("personas") or {}).get(str(persona))) or {}).get("entries") or []
    for entry in diary:
        if isinstance(entry, dict) and str(entry.get("date")) == day:
            result.append(_item(day, "", "diary", f"写了日记《{entry.get('title') or '这天'}》", 1, f"diary:{entry.get('source')}"))
    return result


# --------------------------------------------------------------------- public API


@synchronized
def sync_day(
    data_dir: Path,
    persona: str,
    day: date,
    plan: Any = None,
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Collect what happened on ``day`` (up to ``now`` for today) and remember it."""
    if not persona:
        return []
    day_text = day.isoformat()
    collected: list[dict[str, Any]] = []
    sources: list[tuple[str, Any]] = [("stores", lambda: _store_items(data_dir, persona, day_text))]
    if plan is not None:
        sources.append(("meals", lambda: _meals(data_dir, persona, day_text, plan)))
        sources.append(("timeline", lambda: _timeline_items(persona, day_text, plan, now)))
    for name, source in sources:
        try:
            collected.extend(source())
        except Exception:
            logger.debug("[虚拟人生] 生活记忆 %s 读取失败", name, exc_info=True)
    if now is not None and now.date() == day:
        limit = now.strftime("%H:%M")
        collected = [item for item in collected if not item["time"] or item["time"] <= limit or item["kind"] != "meal"]
    payload = _load(data_dir)
    entry = _day_entry(payload, persona, day_text)
    known = {item.get("key"): item for item in entry["items"] if isinstance(item, dict)}
    changed = False
    for item in collected:
        if known.get(item["key"]) != item:
            known[item["key"]] = item
            changed = True
    if changed:
        entry["items"] = sorted(known.values(), key=lambda item: (item.get("time") or "99:99", item.get("key") or ""))
        _trim(payload, now.date() if now else day)
        payload["schema_version"] = SCHEMA_VERSION
        atomic_write_json(_path(data_dir), payload)
    return list(entry["items"])


def day_items(data_dir: Path, persona: str, day: date) -> list[dict[str, Any]]:
    payload = _load(data_dir)
    entry = (payload["personas"].get(str(persona)) or {}).get(day.isoformat()) or {}
    return [item for item in entry.get("items") or [] if isinstance(item, dict)]


def remembered_days(data_dir: Path, persona: str) -> list[str]:
    return sorted((_load(data_dir)["personas"].get(str(persona)) or {}).keys(), reverse=True)


def _join(items: Iterable[dict[str, Any]], limit: int) -> str:
    texts = [str(item.get("text") or "") for item in items if item.get("text")]
    return "；".join(texts[:limit])


def today_context(data_dir: Path, persona: str, today: date, *, limit: int = 8) -> str:
    """What already happened today, for chat replies (meals, way, owner)."""
    items = day_items(data_dir, persona, today)
    if not items:
        return ""
    meals = [item for item in items if item["kind"] == "meal"]
    others = [item for item in items if item["kind"] not in {"meal", "world", "diary"}]
    parts = []
    if meals:
        parts.append(_join(meals, 3))
    if others:
        parts.append(_join(sorted(others, key=lambda item: -int(item.get("importance") or 1))[:limit], limit))
    text = "；".join(part for part in parts if part)
    if not text:
        return ""
    return (
        f"【今天已经发生的事】{text}。"
        "这些是真实经历：被问到（比如早餐吃了什么、路上怎么样）时按这里回答，"
        "聊天中可以自然提起，但不要一次全说出来。"
    )


def recent_context(data_dir: Path, persona: str, today: date, *, days: int = 4, per_day: int = 4) -> str:
    """Important things from the previous days (excluding today)."""
    lines = []
    for offset in range(1, days + 1):
        day = today - timedelta(days=offset)
        items = [item for item in day_items(data_dir, persona, day) if int(item.get("importance") or 1) >= 2]
        meals = [item for item in day_items(data_dir, persona, day) if item["kind"] == "meal"] if offset == 1 else []
        if not items and not meals:
            continue
        label = {1: "昨天", 2: "前天"}.get(offset, f"{offset} 天前")
        chosen = sorted(items, key=lambda item: -int(item.get("importance") or 1))[:per_day]
        text = _join(chosen + meals[:1], per_day + 1)
        lines.append(f"- {label}（{day.isoformat()}）：{text}")
    if not lines:
        return ""
    return "【前几天发生的重要事】\n" + "\n".join(lines)


def unshared_encounter(data_dir: Path, persona: str, today: date) -> dict[str, Any] | None:
    payload = _load(data_dir)
    entry = (payload["personas"].get(str(persona)) or {}).get(today.isoformat()) or {}
    shared = set(entry.get("shared") or [])
    candidates = [item for item in entry.get("items") or [] if item.get("kind") == "encounter" and item.get("key") not in shared]
    return candidates[-1] if candidates else None


@synchronized
def mark_shared(data_dir: Path, persona: str, today: date, key: str) -> None:
    payload = _load(data_dir)
    entry = _day_entry(payload, persona, today.isoformat())
    if key not in entry["shared"]:
        entry["shared"].append(key)
        atomic_write_json(_path(data_dir), payload)
