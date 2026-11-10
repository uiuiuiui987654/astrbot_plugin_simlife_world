"""Social contact, solitude and alcohol."""
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


def _recent_solitude_minutes(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> int:
    if not isinstance(furniture_states, dict):
        return 0
    best = 0
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if not any(
            word in action
            for word in ("休息", "躺", "安静", "独处", "发呆")
        ):
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = int((now - moment).total_seconds() // 60)
        if 0 <= age <= 240:
            best = max(best, age)
    return best


SOCIAL_WORDS = (
    "聚会",
    "朋友",
    "聊天",
    "见面",
    "约会",
    "约饭",
    "咖啡馆",
    "酒馆",
    "同事",
    "聊心事",
    "深聊",
    "倾诉",
    "谈心",
    "安慰",
    "抱抱",
)


def _plan_has_social(plan: Any, now_minute: int | None = None) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if now_minute is not None and start > now_minute:
            continue
        if str(_item_get(item, "state", "") or "") == "social":
            return True
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in SOCIAL_WORDS):
            return True
    return False


def _plan_has_alcohol(plan: Any, now_minute: int | None = None) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if now_minute is not None and start > now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in ("喝酒", "酒吧", "微醺", "啤酒", "红酒", "白酒")):
            return True
    return False


def _plan_alcohol_minutes(plan: Any) -> int:
    total = 0
    for item in _timeline(plan):
        activity = str(_item_get(item, "activity", "") or "")
        if any(
            word in activity
            for word in ("喝酒", "酒吧", "微醺", "啤酒", "红酒", "白酒")
        ):
            start = _minute(_item_get(item, "start"))
            end = _minute(_item_get(item, "end"))
            total += max(0, end - start)
    return total


def _alcohol_last_night_severity(
    history_plans: list[Any] | None,
    current_plan: Any,
) -> str:
    try:
        current_day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return ""
    previous_day = current_day - timedelta(days=1)
    for item in history_plans or []:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        if day != previous_day:
            continue
        minutes = _plan_alcohol_minutes(item)
        if minutes <= 0:
            return ""
        text = " ".join(
            str(_item_get(entry, "activity", "") or "")
            for entry in _timeline(item)
        )
        if (
            minutes >= 120
            or "酒吧" in text
            or "喝多" in text
            or any(word in text for word in ("白酒", "红酒", "威士忌", "伏特加", "烈酒"))
        ):
            return "severe"
        return "mild"
    return ""


def _alcohol_last_night(
    history_plans: list[Any] | None,
    current_plan: Any,
) -> bool:
    return bool(_alcohol_last_night_severity(history_plans, current_plan))


def _recent_alcohol_days(
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
        if day == current_day and now_minute is not None:
            total += int(_plan_has_alcohol(item, now_minute))
        else:
            total += int(_plan_has_alcohol(item))
    return total


def _sober_days(
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
        day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return 0
    current_day = day
    streak = 0
    while day in entries:
        item = entries[day]
        if day == current_day and now_minute is not None:
            if _plan_has_alcohol(item, now_minute):
                break
            # 今天还没过完，不把今天算作完整清醒日。
            day -= timedelta(days=1)
            continue
        if _plan_has_alcohol(item):
            break
        streak += 1
        day -= timedelta(days=1)
    return streak


def _alcohol_current(plan: Any, now_minute: int) -> bool:
    for item in _timeline(plan):
        activity = str(_item_get(item, "activity", "") or "")
        if not any(
            word in activity
            for word in ("喝酒", "酒吧", "微醺", "啤酒", "红酒", "白酒")
        ):
            continue
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if start <= now_minute <= end + 180:
            return True
    return False


def _completed_social_today(plan: Any, now_minute: int) -> bool:
    for item in _timeline(plan):
        end = _minute(_item_get(item, "end"))
        if end > now_minute:
            continue
        if str(_item_get(item, "state", "") or "") == "social":
            return True
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in SOCIAL_WORDS):
            return True
    return False


def _recent_social_days(
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
        if day == current_day and now_minute is not None:
            total += int(_plan_has_social(item, now_minute))
        else:
            total += int(_plan_has_social(item))
    return total


def _plan_has_hug(plan: Any, now_minute: int | None = None) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if now_minute is not None and start > now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in ("抱抱", "拥抱", "牵手", "靠着")):
            return True
    return False


def _hug_yesterday(
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
        if day == previous_day and _plan_has_hug(item):
            return True
    return False


def _plan_has_deep_social(plan: Any, now_minute: int | None = None) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if now_minute is not None and start > now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(
            word in activity
            for word in ("聊心事", "深聊", "倾诉", "抱抱", "安慰", "谈心")
        ):
            return True
    return False


def _yesterday_social_minutes(
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
            return _activity_minutes(item, 24 * 60, "social")
    return 0


def _deep_social_yesterday(
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
        if day == previous_day and _plan_has_deep_social(item):
            return True
    return False


def _days_since_social(
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
        if day == current_day and now_minute is not None:
            if _plan_has_social(entries[day], now_minute):
                return 0
            continue
        if _plan_has_social(entries[day]):
            return max(0, (current_day - day).days)
    return 99
