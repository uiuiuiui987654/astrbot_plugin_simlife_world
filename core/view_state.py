"""State calculations for the embedded plugin view; no standalone server."""

from __future__ import annotations

import json
import random
import re
import time
import uuid
from datetime import date, datetime
from datetime import time as dt_time
from pathlib import Path

from .wardrobe import appearance_for
from . import (
    affection,
    books,
    delivery,
    furniture_state,
    garage,
    goods,
    health_journal,
    item_effects,
    life_state,
    money,
    mood_history,
    world_events,
)

CORE_DIR = Path(__file__).resolve().parent


def find_home_items_path(plans_path: Path) -> Path:
    return CORE_DIR / "home_items.json"


def find_food_catalog_path(plans_path: Path) -> Path:
    return CORE_DIR / "food_catalog.json"


SEASON_WEATHER_POOLS = {
    "春": ("晴朗", "多云", "微风", "小雨", "阴天"),
    "夏": ("晴朗", "闷热", "雷阵雨", "多云", "微风"),
    "秋": ("晴朗", "凉爽", "多云", "微风", "小雨"),
    "冬": ("晴朗", "阴天", "大风", "寒冷", "小雨"),
}

SEASON_TEMPERATURES = {
    "春": (12, 22),
    "夏": (24, 33),
    "秋": (15, 24),
    "冬": (3, 12),
}

WEATHER_TEMP_DELTAS = {
    "晴朗": (1, 2),
    "多云": (0, 0),
    "阴天": (-1, 0),
    "小雨": (-2, -1),
    "雷阵雨": (-2, 0),
    "大风": (-3, -1),
    "寒冷": (-4, -2),
    "闷热": (2, 3),
    "微风": (0, 1),
    "凉爽": (-1, 0),
}

WEATHER_DESCRIPTIONS = {
    "晴朗": "阳光充足，适合外出",
    "多云": "云量较多，光线柔和",
    "阴天": "天色偏灰，体感偏凉",
    "小雨": "有间歇小雨，出门记得带伞",
    "雷阵雨": "午后可能有雷阵雨，尽量减少户外停留",
    "大风": "风力较大，注意保暖",
    "寒冷": "气温偏低，注意保暖",
    "闷热": "湿度较高，体感闷热",
    "微风": "有微风，体感舒适",
    "凉爽": "天气凉爽，体感舒适",
}


def default_weather(date_text: str) -> dict:
    try:
        target = date.fromisoformat(str(date_text or ""))
    except ValueError:
        return {
            "condition": "",
            "temperature_low": None,
            "temperature_high": None,
            "description": "",
        }
    month = target.month
    season = (
        "春"
        if month in (3, 4, 5)
        else "夏"
        if month in (6, 7, 8)
        else "秋"
        if month in (9, 10, 11)
        else "冬"
    )
    pool = SEASON_WEATHER_POOLS[season]
    condition = pool[target.toordinal() % len(pool)]
    low, high = SEASON_TEMPERATURES[season]
    low_delta, high_delta = WEATHER_TEMP_DELTAS.get(condition, (0, 0))
    low += low_delta
    high += high_delta
    low = min(low, high)
    return {
        "condition": condition,
        "temperature_low": low,
        "temperature_high": high,
        "description": WEATHER_DESCRIPTIONS.get(condition, ""),
    }


ROOM_FLOORS = {
    "客厅": 1,
    "浴室": 1,
    "厨房": 1,
    "餐厅": 1,
    "健身室": 1,
    "阳台": 1,
    "玄关": 1,
    "车库": 1,
    "卧室": 2,
    "衣帽间": 2,
    "书房": 2,
    "画室": 2,
    "影音室": 2,
    "露台": 2,
    "楼梯厅": 2,
}

HOME_ROOM_NAMES = (
    "卧室",
    "浴室",
    "书房",
    "客厅",
    "厨房",
    "阳台",
    "玄关",
    "车库",
    "走廊",
    "餐厅",
    "衣帽间",
    "健身室",
    "画室",
    "影音室",
    "露台",
    "楼梯厅",
)

ROOM_ALIASES = {
    "卧室": "卧室",
    "床": "卧室",
    "浴室": "浴室",
    "洗手间": "浴室",
    "卫生间": "浴室",
    "书房": "书房",
    "书桌": "书房",
    "客厅": "客厅",
    "沙发": "客厅",
    "厨房": "厨房",
    "餐厅": "厨房",
    "阳台": "阳台",
    "玄关": "玄关",
    "门口": "玄关",
}

TRANSIT_WORDS = ("路上", "通勤", "地铁", "公交", "车站", "机场", "打车", "高铁")

ACTIVITY_ROOM_HINTS = (
    ("睡眠", "卧室"),
    ("午睡", "卧室"),
    ("小睡", "卧室"),
    ("起床", "卧室"),
    ("洗漱", "卧室"),
    ("早餐", "厨房"),
    ("午餐", "厨房"),
    ("晚餐", "厨房"),
    ("做饭", "厨房"),
    ("读书", "书房"),
    ("学习", "书房"),
    ("工作", "书房"),
    ("手账", "书房"),
    ("看剧", "客厅"),
    ("听黑胶", "客厅"),
    ("沙发", "客厅"),
    ("闲聊", "客厅"),
    ("泡澡", "浴室"),
    ("洗澡", "浴室"),
    ("阳台", "阳台"),
)


def load_home_items(
    plans_path: Path,
    persona: str | None = None,
    *,
    apply_overrides: bool = True,
) -> tuple[list[dict], str]:
    path = find_home_items_path(plans_path)
    if path is None:
        return [], ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], str(path)
    items = payload.get("items", []) if isinstance(payload, dict) else []
    items = [item for item in items if isinstance(item, dict)]
    if apply_overrides:
        from . import home_decor

        target = str(persona or "").strip() or active_persona(plans_path)
        if target:
            items = home_decor.apply_items(items, plans_path.parent, target)
    return items, str(path)


def active_persona(plans_path: Path) -> str:
    """Resolve today's persona when the view does not pass one explicitly."""
    try:
        plans = load_plans(plans_path)
        plan, _personas = select_plan(plans, None, date.today())
    except (OSError, ValueError, TypeError):
        return ""
    return plan_persona(plan) if plan else ""


def _room_name(value: object) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^[12一二]楼[·・•\\s-]*", "", text)
    return text[:10]


def load_placed_items(plans_path: Path, persona: str | None = None) -> list[dict]:
    """把已摆放到房间的持有物转成可渲染、可点击的家具条目。"""
    target = str(persona or "").strip() or active_persona(plans_path)
    if not target:
        return []
    result: list[dict] = []
    for index, raw in enumerate(money.possessions(plans_path.parent, target)):
        if not isinstance(raw, dict):
            continue
        room = _room_name(raw.get("room"))
        if not room:
            continue
        place = raw.get("place")
        if not isinstance(place, dict):
            continue
        try:
            x = max(0.05, min(0.95, float(place.get("x"))))
            y = max(0.05, min(0.95, float(place.get("y"))))
        except (TypeError, ValueError):
            continue
        name = str(raw.get("name") or raw.get("id") or "物品").strip()
        category = str(raw.get("category") or "物品").strip() or "物品"
        possession_id = str(raw.get("id") or name).strip()
        catalog = goods.find_goods(possession_id) or {}
        catalog_actions = [
            str(action).strip()
            for action in (catalog.get("actions") or [])
            if str(action).strip()
        ]
        if catalog_actions:
            actions = catalog_actions[:4]
        elif category == "饮品":
            actions = ["喝掉", "看看"]
        elif category in ("食物", "零食"):
            actions = ["吃掉", "看看"]
        else:
            actions = ["看看"]
        safe = re.sub(r"[^A-Za-z0-9_.-]", "", possession_id) or str(index)
        item_id = f"placed-{safe}-{index}"
        result.append(
            {
                "id": item_id,
                "possession_id": possession_id,
                "name": name,
                "category": category,
                "description": (
                    f"你亲手装到{room}的{name}。"
                    if raw.get("slot_id")
                    else f"你亲手摆到{room}的{name}。"
                ),
                "room": room,
                "floor": ROOM_FLOORS.get(room, 1),
                "actions": actions,
                "interact_label": str(
                    catalog.get("interact_label")
                    or (actions[0] if actions else "")
                ),
                "hotspot": True,
                "placed": True,
                "slot_id": str(raw.get("slot_id") or ""),
                "slot_label": str(raw.get("slot_label") or ""),
                "place": {
                    "x": round(x, 3),
                    "y": round(y, 3),
                    "facing": str(place.get("facing") or "S"),
                    "z_cm": float(place.get("z_cm") or 0),
                    "surface_id": str(place.get("surface_id") or ""),
                },
            }
        )
    return result


def load_food_catalog(plans_path: Path) -> tuple[dict, str]:
    path = find_food_catalog_path(plans_path)
    if path is None:
        return {}, ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, str(path)
    meals = payload.get("meals", {}) if isinstance(payload, dict) else {}
    return (meals if isinstance(meals, dict) else {}), str(path)


def fridge_path(plans_path: Path) -> Path:
    return plans_path.parent / "fridge_inventory.json"


def _quantity(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_fridge(plans_path: Path) -> dict:
    path = fridge_path(plans_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"ingredients": [], "updated_at": "", "source": "virtual_life"}
    ingredients = payload.get("ingredients", []) if isinstance(payload, dict) else []
    return {
        "ingredients": [item for item in ingredients if isinstance(item, dict)],
        "updated_at": str(payload.get("updated_at") or "")
        if isinstance(payload, dict)
        else "",
        "source": "virtual_life",
    }


def load_food_state(plans_path: Path) -> dict:
    path = plans_path.parent / "food_state.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def current_menu(
    plans_path: Path, *, persona: str | None = None, today: date | None = None
) -> dict:
    state = load_food_state(plans_path)
    menus = state.get("menus")
    if not isinstance(menus, dict):
        return {}
    today = (today or date.today()).isoformat()
    candidates = [
        menu
        for key, menu in menus.items()
        if str(key).startswith(today + "::")
        and (not persona or str(key) == today + "::" + persona)
        and isinstance(menu, dict)
    ]
    if not candidates:
        return {}
    return candidates[-1]


def pick_recipe(plans_path: Path) -> dict | None:
    fridge = load_fridge(plans_path)
    names = {
        str(item.get("name") or "").strip()
        for item in fridge["ingredients"]
        if str(item.get("name") or "").strip() and _quantity(item.get("quantity")) > 0
    }
    meals, source = load_food_catalog(plans_path)
    candidates: list[tuple] = []
    for meal_name, dishes in meals.items():
        if not isinstance(dishes, list):
            continue
        for dish in dishes:
            if not isinstance(dish, dict):
                continue
            name = str(dish.get("name") or "").strip()
            if not name:
                continue
            raw_ingredients = dish.get("ingredients", [])
            ingredients = (
                [str(item).strip() for item in raw_ingredients if str(item).strip()]
                if isinstance(raw_ingredients, list)
                else []
            )
            if not ingredients:
                continue
            available = [item for item in ingredients if item in names]
            missing = [item for item in ingredients if item not in names]
            candidates.append(
                (
                    len(missing),
                    -len(available),
                    name,
                    meal_name,
                    ingredients,
                    available,
                    missing,
                    dish,
                )
            )
    if not candidates:
        return None
    best_missing = min(candidate[0] for candidate in candidates)
    best = [candidate for candidate in candidates if candidate[0] == best_missing]
    missing, _score, name, meal_name, ingredients, available, missing_items, dish = (
        random.choice(best)
    )
    return {
        "name": name,
        "meal": meal_name,
        "ingredients": ingredients,
        "available": available,
        "missing": missing_items,
        "method": str(dish.get("method") or "").strip(),
        "source": source,
    }


def wishes_path(plans_path: Path) -> Path:
    return plans_path.parent / "home_item_wishes.json"


def load_wishes(plans_path: Path) -> list[dict]:
    path = wishes_path(plans_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    wishes = payload.get("wishes", []) if isinstance(payload, dict) else []
    return [wish for wish in wishes if isinstance(wish, dict)]


def save_wishes(plans_path: Path, wishes: list[dict]) -> None:
    path = wishes_path(plans_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "wishes": wishes[-200:]}
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


PENDING_ACTION_STALE_SECONDS = 7200


def pending_actions_path(plans_path: Path) -> Path:
    return plans_path.parent / "home_pending_actions.json"


def _load_pending_actions_raw(plans_path: Path) -> list[dict]:
    try:
        payload = json.loads(
            pending_actions_path(plans_path).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return []
    actions = payload.get("actions", []) if isinstance(payload, dict) else []
    return [action for action in actions if isinstance(action, dict)]


def _save_pending_actions_raw(plans_path: Path, actions: list[dict]) -> None:
    path = pending_actions_path(plans_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "actions": actions[-10:]}
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def load_pending_actions(
    plans_path: Path, persona: str | None = None
) -> list[dict]:
    current_ts = time.time()
    actions = []
    for action in _load_pending_actions_raw(plans_path):
        if str(action.get("status") or "pending") != "pending":
            continue
        if persona and str(action.get("persona") or "") != str(persona):
            continue
        try:
            created_ts = datetime.fromisoformat(
                str(action.get("created_at") or "")
            ).timestamp()
        except (TypeError, ValueError):
            continue
        if current_ts - created_ts > PENDING_ACTION_STALE_SECONDS:
            continue
        actions.append(action)
    return actions[-10:]


def queue_pending_action(
    plans_path: Path,
    *,
    persona: str,
    label: str,
    source: str,
    kind: str = "gift",
    amount: float = 0.0,
    reason: str = "",
    now: datetime | None = None,
) -> dict:
    moment = now or datetime.now()
    actions = _load_pending_actions_raw(plans_path)
    actions = [
        action
        for action in actions
        if not (
            str(action.get("status") or "pending") == "pending"
            and str(action.get("persona") or "") == str(persona)
            and (
                str(action.get("source") or "") == str(source)
                or str(action.get("label") or "") == str(label)
            )
        )
    ]
    action = {
        "id": "pa-" + uuid.uuid4().hex,
        "persona": str(persona),
        "kind": str(kind or "gift")[:20],
        "amount": round(float(amount or 0.0), 2),
        "reason": str(reason or "").strip()[:200],
        "label": str(label or "把东西递给他").strip()[:40],
        "source": str(source or "").strip()[:300],
        "created_at": moment.isoformat(timespec="seconds"),
        "status": "pending",
    }
    actions.append(action)
    _save_pending_actions_raw(plans_path, actions)
    return action


def pop_pending_action(plans_path: Path, action_id: str) -> dict | None:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "", str(action_id or ""))
    if not safe:
        return None
    actions = _load_pending_actions_raw(plans_path)
    found = None
    remaining = []
    for action in actions:
        if (
            found is None
            and str(action.get("id") or "") == safe
            and str(action.get("status") or "pending") == "pending"
        ):
            found = action
            continue
        remaining.append(action)
    if found is not None:
        _save_pending_actions_raw(plans_path, remaining)
    return found


def clear_pending_actions(
    plans_path: Path, persona: str | None = None
) -> int:
    actions = _load_pending_actions_raw(plans_path)
    remaining = []
    cleared = 0
    for action in actions:
        pending = str(action.get("status") or "pending") == "pending"
        matches = not persona or str(action.get("persona") or "") == str(persona)
        if pending and matches:
            cleared += 1
            continue
        remaining.append(action)
    if cleared:
        _save_pending_actions_raw(plans_path, remaining)
    return cleared


INTERACTION_KINDS = {"dish", "chat", "game"}

INTERACTION_STALE_SECONDS = 900


def interaction_dir(plans_path: Path) -> Path:
    return plans_path.parent / "interactions"


def interaction_requests_dir(plans_path: Path) -> Path:
    return interaction_dir(plans_path) / "requests"


def interaction_responses_dir(plans_path: Path) -> Path:
    return interaction_dir(plans_path) / "responses"


def build_interaction_request(
    plans_path: Path, payload: dict, *, now: datetime | None = None
) -> dict:
    """Validate a window payload and turn it into a request for the plugin."""
    kind = str(payload.get("kind") or "chat").strip()
    if kind not in INTERACTION_KINDS:
        raise ValueError("kind 只能是 dish、chat 或 game")
    text = str(payload.get("text") or "").strip()[:200]
    if kind == "chat" and not text:
        raise ValueError("聊天内容不能为空")
    items, _source = load_home_items(plans_path)
    payload_persona = str(payload.get("persona") or "").strip() or None
    items = items + load_placed_items(plans_path, payload_persona)
    item_id = str(payload.get("item_id") or "").strip()
    item = next((entry for entry in items if str(entry.get("id")) == item_id), None)
    payload_item_name = str(payload.get("item_name") or "").strip()[:40]
    state = build_state(
        plans_path, str(payload.get("persona") or "").strip() or None, now=now
    )
    current = state.get("now") or {}
    furniture_context = furniture_state.furniture_context(
        plans_path, item_id, now=now
    )
    return {
        "id": "it-" + uuid.uuid4().hex,
        "created_at": (now or datetime.now()).isoformat(timespec="seconds"),
        "kind": kind,
        "item_id": item_id,
        "item_name": str(
            (item or {}).get("name") or payload_item_name or ""
        ),
        "room": str((item or {}).get("room") or payload.get("room") or ""),
        "action": str(payload.get("action") or ""),
        "affection_action": str(payload.get("affection_action") or "")[:20],
        "text": text,
        "game_name": str(payload.get("game_name") or "")[:24],
        "game_result": str(payload.get("game_result") or "")[:16],
        "game_score": str(payload.get("game_score") or "")[:40],
        "game_summary": str(payload.get("game_summary") or "")[:120],
        "gift_source": str(payload.get("gift_source") or "")[:300],
        "persona": str(state.get("persona") or ""),
        "plan_date": str(state.get("plan_date") or ""),
        "mood": str(state.get("mood") or "")[:20],
        "current": {
            "start": current.get("start"),
            "end": current.get("end"),
            "activity": current.get("activity"),
            "state": current.get("state"),
            "location": current.get("location"),
            "kind": current.get("kind"),
            "scene": current.get("scene"),
            "city": current.get("city"),
        },
        "weather": state.get("weather") or {},
        "appearance": state.get("appearance") or {},
        "timeline": state.get("timeline") or [],
        "next": state.get("next") or [],
        "current_time": state.get("now_time"),
        "needs": state.get("needs") or {},
        "furniture_context": furniture_context,
        "source": "window",
    }


def write_interaction_request(plans_path: Path, request: dict) -> None:
    directory = interaction_requests_dir(plans_path)
    directory.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - INTERACTION_STALE_SECONDS
    for path in directory.glob("*.json"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink(missing_ok=True)
        except OSError:
            continue
    target = directory / f"{request['id']}.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(target)


def load_interaction_response(plans_path: Path, request_id: str) -> dict | None:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "", str(request_id or ""))
    if not safe:
        return None
    path = interaction_responses_dir(plans_path) / f"{safe}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_plans(path: Path) -> dict[str, dict]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    plans = data.get("plans", {}) if isinstance(data, dict) else {}
    if not isinstance(plans, dict):
        return {}
    return {str(key): value for key, value in plans.items() if isinstance(value, dict)}


def plan_date(plan: dict) -> str:
    return str(plan.get("date") or "")


def plan_persona(plan: dict) -> str:
    return str(plan.get("persona_id") or "角色")


def plan_score(plan: dict) -> tuple[str, str]:
    return plan_date(plan), str(plan.get("revision") or "")


def select_plan(
    plans: dict[str, dict],
    requested_persona: str | None = None,
    today: date | None = None,
) -> tuple[dict | None, list[dict]]:
    if not plans:
        return None, []
    personas: dict[str, str] = {}
    for plan in plans.values():
        persona = plan_persona(plan)
        current = personas.get(persona, "")
        if plan_date(plan) > current:
            personas[persona] = plan_date(plan)
    persona_list = [
        {"id": name, "date": latest}
        for name, latest in sorted(
            personas.items(), key=lambda item: item[1], reverse=True
        )
    ]
    candidates = list(plans.values())
    if requested_persona:
        filtered = [
            plan for plan in candidates if plan_persona(plan) == requested_persona
        ]
        if not filtered:
            return None, persona_list
        candidates = filtered
    today = (today or date.today()).isoformat()
    todays = [plan for plan in candidates if plan_date(plan) == today]
    if todays:
        return max(todays, key=plan_score), persona_list
    past = [plan for plan in candidates if plan_date(plan) and plan_date(plan) <= today]
    if past:
        return max(past, key=plan_score), persona_list
    return max(candidates, key=plan_score), persona_list


def parse_hhmm(value) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    try:
        hour_text, minute_text = text.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except (TypeError, ValueError):
        return None
    if hour == 24 and minute == 0:
        return 1440
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return hour * 60 + minute
    return None


def minute_text(minutes: int) -> str:
    minutes = int(minutes) % 1440
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def minute_text_end(minutes: int) -> str:
    if int(minutes) == 1440:
        return "24:00"
    return minute_text(minutes)


def event_minutes(item: dict) -> tuple[int | None, int | None]:
    start = parse_hhmm(item.get("start"))
    end = parse_hhmm(item.get("end"))
    if end == 0:
        end = 1440
    return start, end


def find_current(plan: dict | None, now: datetime) -> dict | None:
    if not plan:
        return None
    current = now.hour * 60 + now.minute + now.second / 60.0
    for item in plan.get("timeline", []) or []:
        if not isinstance(item, dict):
            continue
        start, end = event_minutes(item)
        if start is None or end is None:
            continue
        if start <= current < end:
            return item
    return None


def upcoming_items(plan: dict | None, now: datetime, limit: int = 3) -> list[dict]:
    if not plan:
        return []
    current = now.hour * 60 + now.minute
    result = []
    for item in plan.get("timeline", []) or []:
        if not isinstance(item, dict):
            continue
        start, _end = event_minutes(item)
        if start is not None and start > current:
            result.append(item)
    result.sort(key=lambda item: event_minutes(item)[0] or 0)
    return result[:limit]


def room_for_item(item: dict | None) -> str | None:
    if not item:
        return None
    location = str(item.get("location") or "").strip()
    if split_city(location)[0]:
        return None
    activity = str(item.get("activity") or "")
    for name in HOME_ROOM_NAMES:
        if name in location:
            return name
    for alias, room in ROOM_ALIASES.items():
        if alias in location:
            return room
    if location in ("家", "家里", "家中", ""):
        for alias, room in ROOM_ALIASES.items():
            if alias in activity:
                return room
        for keyword, room in ACTIVITY_ROOM_HINTS:
            if keyword in activity:
                return room
        return "客厅"
    return None


def event_kind(item: dict | None) -> str:
    if not item:
        return "home"
    location = str(item.get("location") or "")
    state = str(item.get("state") or "")
    if state == "transit" or any(word in location for word in TRANSIT_WORDS):
        return "transit"
    if room_for_item(item):
        return "home"
    return "outside"


def split_city(location: str) -> tuple[str, str]:
    """Split ``京都·清水寺`` into the city and the place inside it."""
    text = str(location or "").strip()
    for separator in CITY_SEPARATORS:
        if separator and separator in text:
            city, _, rest = text.partition(separator)
            city = city.strip()
            rest = rest.strip()
            if city in ("一楼", "二楼", "1楼", "2楼", "1F", "2F", "家", "家里"):
                return "", rest
            if city and city not in HOME_ROOM_NAMES and len(city) <= 12:
                return city, rest
    return "", text


def scene_key_for(item: dict | None) -> str:
    if not item:
        return "generic"
    location = str(item.get("location") or "")
    city, _rest = split_city(location)
    for scene_key, words in [
        ("botanical", ("植物园",)),
        ("riverside", ("河岸步道",)),
        ("lakeside", ("湖畔",)),
        ("campsite", ("露营地",)),
        ("amusement", ("游乐园",)),
        ("flower_shop", ("花店",)),
        ("bakery", ("面包店",)),
        ("library", ("图书馆",)),
    ]:
        if any(word in location for word in words):
            return scene_key
    if any(word in location for word in TRAVEL_AIRPORT_WORDS):
        return "airport"
    if any(word in location for word in TRAVEL_STATION_WORDS):
        return "station"
    if any(word in location for word in TRAVEL_HOTEL_WORDS):
        return "hotel"
    if "夜市" in location:
        return "nightmarket"
    if any(word in location for word in TRAVEL_TEMPLE_WORDS):
        return "temple"
    if any(word in location for word in TRAVEL_ONSEN_WORDS):
        return "onsen"
    if any(word in location for word in TRAVEL_HARBOR_WORDS):
        return "harbor"
    if any(word in location for word in TRAVEL_IZAKAYA_WORDS):
        return "izakaya"
    if any(word in location for word in TRAVEL_MOUNTAIN_WORDS):
        return "mountain"
    if city:
        return "travel"
    if "咖啡" in location:
        return "cafe"
    if "公园" in location or "花园" in location or "植物园" in location:
        return "park"
    if "书店" in location or "图书" in location:
        return "bookstore"
    if "美术" in location or "展" in location or "博物" in location:
        return "museum"
    if "电影" in location or "影院" in location:
        return "cinema"
    if "海" in location or "沙滩" in location:
        return "beach"
    if (
        "菜市场" in location
        or "菜场" in location
        or "集市" in location
        or "市场" in location
    ):
        return "market"
    if "超市" in location or "生鲜" in location:
        return "supermarket"
    if "杂货" in location or "便利店" in location:
        return "grocery"
    if "商场" in location or "购物" in location:
        return "mall"
    if "办公" in location or "公司" in location or "会议" in location:
        return "office"
    if "街" in location or "巷" in location or "城市" in location:
        return "street"
    if "食堂" in location or "馆子" in location or "餐" in location:
        return "food"
    if any(word in location for word in TRANSIT_WORDS):
        return "transit"
    return "generic"


def compact_item(item: dict | None) -> dict | None:
    if not item:
        return None
    start, end = event_minutes(item)
    kind = event_kind(item)
    return {
        "id": str(item.get("id") or ""),
        "start": minute_text(start or 0),
        "end": minute_text_end(end or 0),
        "start_min": start or 0,
        "end_min": end or 0,
        "activity": str(item.get("activity") or ""),
        "location": str(item.get("location") or ""),
        "state": str(item.get("state") or "available"),
        "availability": str(item.get("availability") or "normal"),
        "kind": kind,
        "room": room_for_item(item),
        "floor": ROOM_FLOORS.get(room_for_item(item), 1) if kind == "home" else None,
        "scene": None if kind in ("home", "sleep") else scene_key_for(item),
        "city": split_city(str(item.get("location") or ""))[0],
    }


def _bookshelf(
    plans_path: Path,
    persona: str,
    possessions: list[dict],
) -> list[dict]:
    shelf: list[dict] = []
    seen: set[str] = set()
    for item in possessions or []:
        book = books.find_book(
            str(item.get("book_id") or item.get("name") or "")
        )
        if book is None:
            continue
        book_id = str(book.get("id") or "")
        if book_id in seen:
            continue
        seen.add(book_id)
        total = max(1, len(book.get("chapters") or []))
        progress = books.get_progress(plans_path.parent, persona, book_id)
        shelf.append(
            {
                "id": book_id,
                "title": str(book.get("title") or ""),
                "author": str(book.get("author") or ""),
                "genre": str(book.get("genre") or ""),
                "chapter": int(progress.get("chapter") or 0),
                "total_chapters": total,
                "finished": bool(progress.get("finished")),
                "notes": len(progress.get("notes") or []),
            }
        )
    return shelf


def build_state(
    plans_path: Path,
    persona: str | None = None,
    preview_time: dt_time | None = None,
    *,
    now: datetime | None = None,
) -> dict:
    error = ""
    plans = {}
    try:
        plans = load_plans(plans_path)
    except (OSError, ValueError, TypeError):
        error = "日程暂不可用，请先生成虚拟日程"
    now = now or datetime.now()
    today = now.date()
    plan, personas = select_plan(plans, persona, today)
    if preview_time:
        now = now.replace(
            hour=preview_time.hour,
            minute=preview_time.minute,
            second=preview_time.second,
        )
    current = find_current(plan, now)
    timeline = [
        compact_item(item)
        for item in ((plan or {}).get("timeline", []) or [])
        if isinstance(item, dict)
    ]
    next_items = [compact_item(item) for item in upcoming_items(plan, now, limit=3)]
    outfit = (plan or {}).get("outfit", {}) if plan else {}
    if not isinstance(outfit, dict):
        outfit = {}
    weather = (plan or {}).get("weather", {}) if plan else {}
    if not isinstance(weather, dict):
        weather = {}
    if not str(weather.get("condition") or "").strip():
        weather = default_weather(plan_date(plan) if plan else today.isoformat())
    try:
        furniture_states = furniture_state.live_states(plans_path, now=now)
        history_plans = []
        if plan:
            current_day = str((plan or {}).get("date") or "")
            current_persona = str((plan or {}).get("persona_id") or "")
            history_plans = sorted(
                (
                    value
                    for value in plans.values()
                    if isinstance(value, dict)
                    and str(value.get("date") or "") < current_day
                    and (
                        not current_persona
                        or str(value.get("persona_id") or "") == current_persona
                    )
                ),
                key=lambda value: str(value.get("date") or ""),
            )[-3:]
        needs = life_state.compute(
            plan,
            now,
            furniture_states=furniture_states,
            history_plans=history_plans,
            weak_constitution=bool(
                health_journal.persona_state(
                    plans_path.parent,
                    str((plan or {}).get("persona_id") or "角色"),
                    today=now.date(),
                ).get("weak_constitution")
            ),
            recent_illness_days=int(
                health_journal.persona_state(
                    plans_path.parent,
                    str((plan or {}).get("persona_id") or "角色"),
                    today=now.date(),
                ).get("recent_illness_days")
                or 0
            )
            if plan
            else 0,
        )
        if plan and not preview_time and plan_date(plan) == today.isoformat():
            needs = health_journal.update(
                plans_path.parent,
                str(plan.get("persona_id") or "角色"),
                needs,
                now,
            )
            needs = item_effects.apply(
                plans_path.parent,
                str(plan.get("persona_id") or "角色"),
                needs,
                now,
            )
            try:
                mood_history.record(
                    plans_path.parent,
                    str(plan.get("persona_id") or "角色"),
                    needs,
                    now=now,
                )
            except Exception:
                pass
    except (OSError, TypeError, ValueError):
        needs = {}
    persona_id = plan_persona(plan) if plan else "未连接"
    try:
        delivery.deliver_due(plans_path.parent, persona_id, now)
        deliveries = delivery.list_orders(plans_path.parent, persona_id)
    except (OSError, TypeError, ValueError):
        deliveries = []
    return {
        "ok": not error and plan is not None,
        "error": error,
        "persona": persona_id,
        "personas": personas,
        "plan_date": plan_date(plan) if plan else "",
        "is_today": bool(plan and plan_date(plan) == today.isoformat()),
        "theme": str((plan or {}).get("theme") or "未生成"),
        "mood": str((plan or {}).get("mood") or "未知"),
        "weather": {
            "condition": str(weather.get("condition") or ""),
            "temperature_low": weather.get("temperature_low"),
            "temperature_high": weather.get("temperature_high"),
            "description": str(weather.get("description") or ""),
        },
        "outfit": {
            "style": str(outfit.get("style") or ""),
            "summary": str(outfit.get("summary") or ""),
            "items": [
                {
                    "category": str(entry.get("category") or ""),
                    "name": str(entry.get("name") or ""),
                    "details": str(entry.get("details") or ""),
                }
                for entry in (outfit.get("items") or [])
                if isinstance(entry, dict)
                and str(entry.get("category") or "").strip()
                and str(entry.get("name") or "").strip()
            ],
        },
        "appearance": appearance_for(
            (current or {}).get("location", ""),
            (current or {}).get("activity", ""),
            (current or {}).get("state", ""),
            now,
            home=event_kind(current or {}) == "home" if current else False,
            timeline=(plan or {}).get("timeline", []),
            outfit=outfit,
        ),
        "money": money.snapshot(
            plans_path.parent,
            plan_persona(plan) if plan else "未连接",
            limit=1,
        ),
        "garage": garage.snapshot(
            plans_path.parent,
            plan_persona(plan) if plan else "未连接",
            now=now,
        ),
        "bookshelf": _bookshelf(
            plans_path,
            plan_persona(plan) if plan else "未连接",
            money.snapshot(
                plans_path.parent,
                plan_persona(plan) if plan else "未连接",
                limit=1,
            ).get("possessions")
            or [],
        ),
        "deliveries": deliveries,
        "affection": affection.snapshot(plans_path.parent, persona_id),
        "world_event": world_events.recent(
            plans_path.parent, persona_id, now.date().isoformat()
        ),
        "mood_history": mood_history.list_entries(
            plans_path.parent, persona_id, limit=30
        ),
        "now": compact_item(current),
        "needs": needs,
        "timeline": timeline,
        "next": next_items,
        "now_time": now.strftime("%H:%M:%S"),
        "preview": bool(preview_time),
    }


def parse_preview_time(text: str | None) -> dt_time | None:
    if not text:
        return None
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


CITY_SEPARATORS = ("·", "・", "•", " - ", "-")

TRAVEL_HOTEL_WORDS = (
    "酒店",
    "民宿",
    "旅馆",
    "客栈",
    "旅店",
    "青旅",
    "住处",
    "公寓",
    "民宿",
)

TRAVEL_STATION_WORDS = ("车站", "高铁", "动车", "火车站", "站台", "月台", "候车", "站")

TRAVEL_AIRPORT_WORDS = ("机场", "航站", "登机", "值机", "安检", "候机")

TRAVEL_TEMPLE_WORDS = ("寺", "神社", "大社", "庙", "佛", "塔", "参道", "鸟居", "稻荷")

TRAVEL_ONSEN_WORDS = ("温泉", "泡汤", "汤池", "浴场", "汤屋", "足汤")

TRAVEL_HARBOR_WORDS = ("港口", "码头", "渔村", "海湾", "港湾", "船坞", "小镇", "港")

TRAVEL_MOUNTAIN_WORDS = (
    "山顶",
    "山道",
    "登山",
    "缆车",
    "观景台",
    "高原",
    "山野",
    "山",
    "峰",
)

TRAVEL_IZAKAYA_WORDS = (
    "居酒屋",
    "小酒馆",
    "酒馆",
    "酒吧",
    "烧鸟",
    "串烧",
    "酒场",
    "清吧",
)
