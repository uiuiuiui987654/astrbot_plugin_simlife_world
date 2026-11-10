"""Exercise, recovery, work load and hygiene."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .base import (
    _activity_minutes,
    _item_get,
    _minute,
    _plan_day,
    _timeline,
)
from .meals import (
    _baking_minutes,
)


def _recent_overtraining_days(
    history_plans: list[Any] | None,
    current_plan: Any,
    days: int = 7,
    now_minute: int | None = None,
) -> int:
    entries: dict[date, Any] = {}
    for item in list(history_plans or []) + [current_plan]:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        entries[day] = item
    try:
        current_day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return 0
    earliest = current_day - timedelta(days=max(1, days) - 1)
    total = 0
    for day, item in entries.items():
        if not (earliest <= day <= current_day):
            continue
        cutoff = now_minute if day == current_day and now_minute is not None else 24 * 60
        if _activity_minutes(item, cutoff, "exercise") >= 120:
            total += 1
    return total


def _recent_exercise_days(
    history_plans: list[Any] | None,
    current_plan: Any,
    days: int = 7,
    now_minute: int | None = None,
) -> int:
    entries: dict[date, Any] = {}
    for item in list(history_plans or []) + [current_plan]:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        entries[day] = item
    try:
        current_day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return 0
    earliest = current_day - timedelta(days=max(1, days) - 1)
    total = 0
    for day, item in entries.items():
        if not (earliest <= day <= current_day):
            continue
        cutoff = now_minute if day == current_day and now_minute is not None else 24 * 60
        if _activity_minutes(item, cutoff, "exercise") >= 20:
            total += 1
    return total


def _yesterday_exercise_minutes(
    history_plans: list[Any] | None,
    current_plan: Any,
) -> int:
    try:
        current_day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return 0
    previous_day = current_day - timedelta(days=1)
    for item in history_plans or []:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        if day == previous_day:
            return _activity_minutes(item, 24 * 60, "exercise")
    return 0


def _exercise_yesterday(
    history_plans: list[Any] | None,
    current_plan: Any,
) -> bool:
    try:
        current_day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return False
    previous_day = current_day - timedelta(days=1)
    for item in history_plans or []:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        if day == previous_day and _activity_minutes(item, 24 * 60, "exercise") >= 20:
            return True
    return False


def _recent_brushing_days(
    history_plans: list[Any] | None,
    current_plan: Any,
    days: int = 7,
    now_minute: int | None = None,
) -> int:
    entries: dict[date, Any] = {}
    for item in list(history_plans or []) + [current_plan]:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        entries[day] = item
    try:
        current_day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return 0
    earliest = current_day - timedelta(days=max(1, days) - 1)
    total = 0
    for day, item in entries.items():
        if not (earliest <= day <= current_day):
            continue
        cutoff = now_minute if day == current_day and now_minute is not None else 24 * 60
        if _has_brushed_teeth(item, cutoff):
            total += 1
    return total


def _recent_tooth_neglect_days(
    history_plans: list[Any] | None,
    current_plan: Any,
    days: int = 7,
    now_minute: int | None = None,
) -> int:
    entries: dict[date, Any] = {}
    for item in list(history_plans or []) + [current_plan]:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        entries[day] = item
    try:
        current_day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return 0
    earliest = current_day - timedelta(days=max(1, days) - 1)
    total = 0
    for day, item in entries.items():
        if not (earliest <= day <= current_day):
            continue
        cutoff = now_minute if day == current_day and now_minute is not None else 24 * 60
        if _baking_minutes(item, cutoff) >= 20 and not _has_brushed_teeth(item, cutoff):
            total += 1
    return total


def _recovery_light_movement(recovering: bool, exercise_minutes: int) -> bool:
    return bool(recovering and 10 <= exercise_minutes <= 45)


def _days_since_overwork(
    history_plans: list[Any] | None,
    current_plan: Any,
    now_minute: int | None = None,
) -> int:
    entries: dict[date, Any] = {}
    for item in list(history_plans or []) + [current_plan]:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        entries[day] = item
    try:
        current_day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return 0
    for day in sorted(entries, reverse=True):
        if day > current_day:
            continue
        cutoff = now_minute if day == current_day and now_minute is not None else 24 * 60
        if _work_minutes(entries[day], cutoff) >= 480:
            return max(0, (current_day - day).days)
    return 99


def _recent_overwork_days(
    history_plans: list[Any] | None,
    current_plan: Any,
    days: int = 7,
    now_minute: int | None = None,
) -> int:
    entries: dict[date, Any] = {}
    for item in list(history_plans or []) + [current_plan]:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        entries[day] = item
    try:
        current_day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return 0
    earliest = current_day - timedelta(days=max(1, days) - 1)
    total = 0
    for day, item in entries.items():
        if not (earliest <= day <= current_day):
            continue
        cutoff = now_minute if day == current_day and now_minute is not None else 24 * 60
        if _work_minutes(item, cutoff) >= 480:
            total += 1
    return total


def _recent_long_commute_days(
    history_plans: list[Any] | None,
    current_plan: Any,
    days: int = 7,
) -> int:
    entries: dict[date, Any] = {}
    for item in list(history_plans or []) + [current_plan]:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        entries[day] = item
    try:
        current_day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return 0
    earliest = current_day - timedelta(days=max(1, days) - 1)
    return sum(
        1
        for day, item in entries.items()
        if earliest <= day <= current_day
        and _transit_minutes(item, 24 * 60) >= 90
    )


def _stiff_neck_yesterday(
    history_plans: list[Any] | None,
    current_plan: Any,
) -> bool:
    try:
        current_day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return False
    previous_day = current_day - timedelta(days=1)
    for item in history_plans or []:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        if day != previous_day:
            continue
        if _work_minutes(item, 24 * 60) < 480:
            continue
        if _has_stretch(item, 24 * 60):
            continue
        if _activity_minutes(item, 24 * 60, "rest") >= 30:
            continue
        return True
    return False


def _has_stretch(plan: Any, now_minute: int) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start >= now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in ("拉伸", "伸展", "活动肩颈", "起身走动")):
            return True
    return False


def _transit_minutes(plan: Any, now_minute: int) -> int:
    total = 0
    for item in _timeline(plan):
        if str(_item_get(item, "state", "") or "") != "transit":
            continue
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if start >= now_minute:
            continue
        total += max(0, min(end, now_minute) - start)
    return total


def _brushed_in_window(
    plan: Any,
    window_start: int,
    window_end: int,
    now_minute: int,
) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start < window_start or start >= window_end or start >= now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in ("刷牙", "洗漱")):
            return True
    return False


def _has_brushed_teeth(plan: Any, now_minute: int) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start < 18 * 60 or start >= now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in ("刷牙", "洗漱")):
            return True
    return False


def _work_minutes(plan: Any, now_minute: int) -> int:
    return _activity_minutes(plan, now_minute, "work")


def _recent_recovery_actions(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> list[str]:
    """Recent sleep/rest/warm-food actions that can help recovery."""
    words = (
        "睡",
        "午睡",
        "小憩",
        "休息",
        "躺",
        "澡",
        "洗",
        "淋浴",
        "洗漱",
        "热水",
        "热茶",
        "茶",
        "咖啡",
        "拿铁",
        "手冲",
        "凉",
        "芦荟",
        "粥",
        "汤",
        "清淡",
        "吃",
        "拉伸",
        "按摩",
        "热敷",
        "音乐",
        "听",
        "书",
        "呼吸",
        "冥想",
        "香薰",
        "精油",
    )
    if not isinstance(furniture_states, dict):
        return []
    actions: list[str] = []
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if not action or action == "自动关闭":
            continue
        if not any(word in action for word in words):
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if 0 <= age <= 240 and action not in actions:
            actions.append(action)
    return actions[:4]


def _recent_harmful_actions(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> list[str]:
    """Recent actions that are counterproductive while recovering."""
    if not isinstance(furniture_states, dict):
        return []
    words = (
        "跑步",
        "慢跑",
        "健身",
        "运动",
        "锻炼",
        "冷饮",
        "冰",
        "吹风",
        "淋雨",
        "熬夜",
        "通宵",
        "酒",
        "辣",
        "火锅",
        "烧烤",
    )
    actions: list[str] = []
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if not action or action == "自动关闭":
            continue
        if not any(word in action for word in words):
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if 0 <= age <= 480 and action not in actions:
            actions.append(action)
    return actions[:4]


def _plan_recovery_text(plan: Any, now_minute: int) -> str:
    words = (
        "茶",
        "咖啡",
        "热水",
        "温水",
        "洗",
        "澡",
        "散步",
        "走动",
        "拉伸",
        "休息",
        "躺",
        "闭眼",
        "远眺",
        "凉",
        "芦荟",
        "口罩",
        "安静",
        "独处",
        "音乐",
        "听",
        "书",
        "呼吸",
        "冥想",
        "香薰",
        "精油",
    )
    actions: list[str] = []
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start > now_minute or now_minute - start > 240:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in words):
            actions.append(activity)
    return " ".join(actions)
