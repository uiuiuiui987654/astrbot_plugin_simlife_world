"""Stateful furniture actions shared by the view and immediate interactions.

Static ``home_items.json`` only describes what a piece of furniture *can* do.
This module keeps the small amount of live state needed for the observation
window to feel coherent:

* every item remembers its most recent action;
* appliances remember whether they are on or off;
* the view can show a state badge and swap ``开香薰`` / ``关香薰``;
* interaction requests can carry a compact ``furniture_context`` block so the
  character's reply matches what the owner just did.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from .jsonio import atomic_write_json, synchronized

SCHEMA_VERSION = 1
MAX_ITEMS = 200

# on/off labels are exposed as the first action of the item.  Extra actions
# from home_items.json stay available underneath them.
DEVICE_SPECS: dict[str, dict[str, Any]] = {
    "aroma_diffuser": {
        "on": "开香薰",
        "off": "关香薰",
        "on_text": "香薰机开着，卧室里有淡淡的香气",
        "off_text": "香薰机关着",
    },
    "bedside_lamp": {
        "on": "开床头灯",
        "off": "关床头灯",
        "on_text": "床头灯开着，房间里有暖黄色的光",
        "off_text": "床头灯关着",
    },
    "floor_lamp": {
        "on": "开落地灯",
        "off": "关落地灯",
        "on_text": "落地灯开着，客厅一角亮着暖光",
        "off_text": "落地灯关着",
    },
    "tv": {
        "on": "开电视",
        "off": "关电视",
        "on_text": "电视开着，屏幕亮着",
        "off_text": "电视关着",
    },
    "cinema_screen": {
        "on": "开投影幕",
        "off": "关投影幕",
        "on_text": "影音室的投影幕亮着",
        "off_text": "影音室的投影幕收着",
    },
    "record_player": {
        "on": "开唱片机",
        "off": "关唱片机",
        "on_text": "唱片机开着，黑胶正转着",
        "off_text": "唱片机停着",
    },
    "monitor": {
        "on": "开电脑",
        "off": "关电脑",
        "on_text": "电脑开着，显示器亮着",
        "off_text": "电脑关着",
    },
    "waterproof_speaker": {
        "on": "开音箱",
        "off": "关音箱",
        "on_text": "防水音箱开着，放着音乐",
        "off_text": "防水音箱关着",
    },
    "headphones": {
        "on": "戴上耳机",
        "off": "摘下耳机",
        "on_text": "耳机戴在头上，正听着声音",
        "off_text": "耳机放在一边",
    },
    "washing_machine": {
        "on": "启动洗衣机",
        "off": "关洗衣机",
        "on_text": "洗衣机在转，正在洗衣服",
        "off_text": "洗衣机停着",
    },
    "vacuum": {
        "on": "启动吸尘器",
        "off": "关吸尘器",
        "on_text": "吸尘器开着，正在吸地板",
        "off_text": "吸尘器收着",
    },
    "dishwasher": {
        "on": "启动洗碗机",
        "off": "关洗碗机",
        "on_text": "洗碗机在运转",
        "off_text": "洗碗机停着",
    },
    "rice_cooker": {
        "on": "启动电饭煲",
        "off": "关电饭煲",
        "on_text": "电饭煲在工作，冒着热气",
        "off_text": "电饭煲关着",
    },
    "coffee_machine": {
        "on": "开咖啡机",
        "off": "关咖啡机",
        "on_text": "咖啡机开着，刚出过咖啡",
        "off_text": "咖啡机关着",
    },
    "oven": {
        "on": "开烤箱",
        "off": "关烤箱",
        "on_text": "烤箱开着，里面暖暖的",
        "off_text": "烤箱关着",
    },
    "toaster": {
        "on": "开吐司机",
        "off": "关吐司机",
        "on_text": "吐司机开着，飘着面包香",
        "off_text": "吐司机关着",
    },
    "treadmill": {
        "on": "启动跑步机",
        "off": "关跑步机",
        "on_text": "跑步机开着，履带在转",
        "off_text": "跑步机停着",
    },
    "iron": {
        "on": "开熨斗",
        "off": "关熨斗",
        "on_text": "熨斗开着，底板是热的",
        "off_text": "熨斗关着",
    },
    "digital_tablet": {
        "on": "开数位屏",
        "off": "关数位屏",
        "on_text": "数位屏亮着，画笔悬在上面",
        "off_text": "数位屏关着",
    },
    "popcorn_machine": {
        "on": "开爆米花机",
        "off": "关爆米花机",
        "on_text": "爆米花机开着，正在加热",
        "off_text": "爆米花机关着",
    },
    "game_console": {
        "on": "开游戏机",
        "off": "关游戏机",
        "on_text": "游戏机开着，电视上停在游戏画面",
        "off_text": "游戏机关着",
    },
}


# Realistic auto-off windows (minutes).  Zero means the device stays as-is
# until the owner turns it off.  These are intentionally conservative; the
# point is to avoid the flat "on forever" feeling, not to simulate firmware.
DEVICE_AUTO_OFF_MINUTES: dict[str, int] = {
    "aroma_diffuser": 60,
    "bedside_lamp": 0,
    "floor_lamp": 0,
    "tv": 120,
    "cinema_screen": 0,
    "record_player": 90,
    "monitor": 180,
    "waterproof_speaker": 60,
    "headphones": 120,
    "washing_machine": 45,
    "vacuum": 30,
    "dishwasher": 60,
    "rice_cooker": 40,
    "coffee_machine": 10,
    "oven": 30,
    "toaster": 5,
    "treadmill": 40,
    "iron": 15,
    "digital_tablet": 120,
    "popcorn_machine": 10,
    "game_console": 120,
}


def _parse_moment(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _auto_off_remaining(state: dict[str, Any], now: datetime) -> int | None:
    if not state.get("on") or not state.get("auto_off_at"):
        return None
    moment = _parse_moment(state.get("auto_off_at"))
    if moment is None:
        return None
    if moment.tzinfo is None and now.tzinfo is not None:
        moment = moment.replace(tzinfo=now.tzinfo)
    return max(0, int((moment - now).total_seconds() // 60))


def states_path(plans_path: Path) -> Path:
    return plans_path.parent / "home_item_states.json"


def load_states(plans_path: Path) -> dict[str, dict[str, Any]]:
    path = states_path(plans_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    items = payload.get("items", {}) if isinstance(payload, dict) else {}
    if not isinstance(items, dict):
        return {}
    return {
        str(key): value
        for key, value in items.items()
        if isinstance(value, dict)
    }


@synchronized
def save_states(plans_path: Path, states: dict[str, dict[str, Any]]) -> None:
    path = states_path(plans_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(
        states.items(),
        key=lambda pair: str(pair[1].get("updated_at") or ""),
        reverse=True,
    )[:MAX_ITEMS]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "items": dict(reversed(ordered)),
    }
    atomic_write_json(path, payload)


def _now(now: datetime | None = None) -> datetime:
    return now or datetime.now().astimezone()


@synchronized
def live_states(
    plans_path: Path,
    *,
    now: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """Load states and lazily expire devices whose realistic run time ended."""
    current = _now(now)
    states = load_states(plans_path)
    changed = False
    for item_id, state in states.items():
        spec = DEVICE_SPECS.get(item_id)
        if not spec or not state.get("on") or not state.get("auto_off_at"):
            continue
        expiry = _parse_moment(state.get("auto_off_at"))
        if expiry is None:
            continue
        if expiry.tzinfo is None and current.tzinfo is not None:
            expiry = expiry.replace(tzinfo=current.tzinfo)
        if expiry > current:
            continue
        state["on"] = False
        state["last_action"] = "自动关闭"
        state["updated_at"] = expiry.isoformat(timespec="seconds")
        state["auto_off_at"] = ""
        state["started_at"] = ""
        changed = True
    if changed:
        save_states(plans_path, states)
    return states


def _relative_time(value: Any, now: datetime | None = None) -> str:
    try:
        moment = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return "刚刚"
    current = _now(now)
    if moment.tzinfo is None and current.tzinfo is not None:
        moment = moment.replace(tzinfo=current.tzinfo)
    if current.tzinfo is None and moment.tzinfo is not None:
        current = current.replace(tzinfo=moment.tzinfo)
    seconds = max(0, int((current - moment).total_seconds()))
    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{seconds // 60} 分钟前"
    if seconds < 86400:
        return f"{seconds // 3600} 小时前"
    return f"{seconds // 86400} 天前"


def _power_delta(action: str, spec: dict[str, str]) -> bool | None:
    text = str(action or "").strip()
    if not text:
        return None
    off = spec.get("off") or ""
    on = spec.get("on") or ""
    if text == off or text.startswith("关闭") or text.startswith("关掉"):
        return False
    if text == on or text.startswith(("打开", "开启", "启动", "播放", "戴上")):
        return True
    if text.startswith("关") and not text.startswith("开关"):
        return False
    if text.startswith("开") and not text.startswith("开关"):
        return True
    return None


def _item_name(item: dict[str, Any]) -> str:
    return str(item.get("name") or item.get("id") or "家具")


def _state_payload(state: dict[str, Any], now: datetime) -> dict[str, Any]:
    return {
        "on": state.get("on"),
        "last_action": str(state.get("last_action") or ""),
        "updated_at": str(state.get("updated_at") or ""),
        "updated_text": _relative_time(state.get("updated_at"), now),
        "started_at": str(state.get("started_at") or ""),
        "auto_off_at": str(state.get("auto_off_at") or ""),
        "persona": str(state.get("persona") or ""),
    }


def decorate_item(
    item: dict[str, Any],
    state: dict[str, Any] | None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = _now(now)
    state = state if isinstance(state, dict) else {}
    item_id = str(item.get("id") or "")
    spec = DEVICE_SPECS.get(item_id)
    actions = [str(action) for action in (item.get("actions") or []) if str(action).strip()]
    decorated = dict(item)
    decorated["state"] = _state_payload(state, current)
    if spec:
        on = bool(state.get("on"))
        toggle = spec["off"] if on else spec["on"]
        base = [
            action
            for action in actions
            if action not in (spec.get("on"), spec.get("off"))
        ]
        decorated["actions"] = [toggle] + base
        decorated["power_on"] = on
        state_text = spec["on_text"] if on else spec["off_text"]
        remaining = _auto_off_remaining(state, current) if on else None
        auto_text = (
            f"，约 {remaining} 分钟后自动关闭"
            if remaining is not None
            else ""
        )
        decorated["auto_off_minutes"] = remaining
        decorated["state_summary"] = (
            f"{state_text}{auto_text}（{_relative_time(state.get('updated_at'), current)}）"
            if state.get("updated_at")
            else f"{state_text}{auto_text}"
        )
        decorated["state_label"] = (
            f"运行中 · {spec['on_text']}{auto_text}"
            if on
            else f"已关闭 · {spec['off_text']}"
        )
        decorated["state_label_on"] = on
        return decorated

    last_action = str(state.get("last_action") or "")
    if last_action:
        relative = _relative_time(state.get("updated_at"), current)
        decorated["state_summary"] = f"最近动作：{last_action}（{relative}）"
        decorated["state_label"] = f"最近动作：{last_action}（{relative}）"
    return decorated


def decorate_items(
    items: list[dict[str, Any]],
    states: dict[str, dict[str, Any]],
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    return [
        decorate_item(item, states.get(str(item.get("id") or "")), now=now)
        for item in items
    ]


def action_message(item: dict[str, Any], action: str, *, now: datetime | None = None) -> str:
    """Short toast text for the window after an action."""
    current = _now(now)
    item_id = str(item.get("id") or "")
    spec = DEVICE_SPECS.get(item_id)
    name = _item_name(item)
    if spec:
        toggle_text = str(action or "")
        if toggle_text.startswith(("关", "关闭", "关掉")):
            return f"{name}已关闭"
        if toggle_text in (spec.get("on"), spec.get("off")):
            return f"{name}已打开" if toggle_text == spec.get("on") else f"{name}已关闭"
        return f"已记录：{name} · {action}"
    return f"已记录：{name} · {action}"


@synchronized
def record_action(
    plans_path: Path,
    item: dict[str, Any],
    action: str,
    persona: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = _now(now)
    item_id = str(item.get("id") or "")
    if not item_id:
        return decorate_item(item, {}, now=current)
    states = live_states(plans_path, now=current)
    state = dict(states.get(item_id) or {})
    spec = DEVICE_SPECS.get(item_id)
    if spec:
        changed = _power_delta(action, spec)
        if changed is True:
            state["on"] = True
            minutes = int(DEVICE_AUTO_OFF_MINUTES.get(item_id, 0) or 0)
            state["started_at"] = current.isoformat(timespec="seconds")
            state["auto_off_at"] = (
                (current + timedelta(minutes=minutes)).isoformat(timespec="seconds")
                if minutes > 0
                else ""
            )
        elif changed is False:
            state["on"] = False
            state["started_at"] = ""
            state["auto_off_at"] = ""
        elif "on" not in state:
            state["on"] = False
    state["last_action"] = str(action or "")
    state["updated_at"] = current.isoformat(timespec="seconds")
    state["persona"] = str(persona or "")
    states[item_id] = state
    save_states(plans_path, states)
    return decorate_item(item, state, now=current)


@synchronized
def item_state(plans_path: Path, item_id: str) -> dict[str, Any]:
    return dict(live_states(plans_path).get(str(item_id or "")) or {})


@synchronized
def furniture_context(
    plans_path: Path,
    item_id: str,
    *,
    now: datetime | None = None,
) -> str:
    """Build a compact natural-language state block for the interaction prompt."""
    current = _now(now)
    states = live_states(plans_path, now=current)
    if not states and not item_id:
        return ""
    items, _ = _load_items(plans_path)
    by_id = {str(item.get("id") or ""): item for item in items}
    lines: list[str] = []

    current_item = by_id.get(str(item_id or ""))
    current_state = states.get(str(item_id or "")) or {}
    if current_item:
        name = _item_name(current_item)
        room = str(current_item.get("room") or "")
        spec = DEVICE_SPECS.get(str(current_item.get("id") or ""))
        relative = _relative_time(current_state.get("updated_at"), current)
        last_action = str(current_state.get("last_action") or "")
        if spec and current_state:
            on = bool(current_state.get("on"))
            state_text = spec["on_text"] if on else spec["off_text"]
            remaining = _auto_off_remaining(current_state, current) if on else None
            auto_text = (
                f"，约 {remaining} 分钟后自动关闭"
                if remaining is not None
                else ""
            )
            if last_action:
                lines.append(
                    f"主人刚刚在{room}操作了{name}：{last_action}。"
                    f"{state_text}{auto_text}（{relative}）。"
                )
            else:
                lines.append(f"主人现在在{room}的{name}旁边；{state_text}{auto_text}。")
        elif last_action:
            lines.append(
                f"主人刚刚在{room}的{name}做了：{last_action}（{relative}）。"
            )
        else:
            lines.append(f"主人现在在{room}的{name}旁边。")

    active: list[str] = []
    recent: list[tuple[int, str]] = []
    for key, state in states.items():
        item = by_id.get(key)
        if not item:
            continue
        if key == str(item_id or ""):
            continue
        spec = DEVICE_SPECS.get(key)
        name = _item_name(item)
        room = str(item.get("room") or "")
        relative = _relative_time(state.get("updated_at"), current)
        if spec and state.get("on"):
            remaining = _auto_off_remaining(state, current)
            suffix = f"（约 {remaining} 分钟后自动关）" if remaining is not None else ""
            active.append(f"{room}的{name}{suffix}")
        last_action = str(state.get("last_action") or "")
        if last_action:
            try:
                stamp = datetime.fromisoformat(str(state.get("updated_at"))).timestamp()
            except (TypeError, ValueError):
                stamp = 0
            recent.append((int(stamp), f"{name}{last_action}（{relative}）"))

    if active:
        lines.append("现在开着的设备：" + "、".join(active) + "。")
    recent.sort(reverse=True)
    if recent:
        lines.append("最近的家具操作：" + "；".join(text for _, text in recent[:3]) + "。")
    return "\n".join(lines)


def _load_items(plans_path: Path) -> tuple[list[dict[str, Any]], str]:
    from .view_state import load_home_items

    return load_home_items(plans_path)
