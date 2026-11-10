"""Meals, caffeine and hydration."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .base import (
    _activity_kind,
    _item_get,
    _minute,
    _plan_day,
    _timeline,
)
from .weather import (
    _season_for_plan,
)


def _late_caffeine(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> bool:
    if not isinstance(furniture_states, dict):
        return False
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if any(
            word in action
            for word in ("热茶", "姜茶", "花草茶", "洋甘菊", "无咖啡因")
        ):
            continue
        if not any(word in action for word in ("咖啡", "拿铁", "手冲", "茶", "奶茶")):
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if 0 <= age <= 480 and moment.hour >= 15:
            return True
    return False


def _recent_heavy_food_days(
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
            total += int(_has_heavy_food(item, now_minute))
        else:
            total += int(_has_heavy_food(item))
    return total


def _has_light_diet(plan: Any, now_minute: int | None = None) -> bool:
    words = ("粥", "汤", "清淡", "热水", "温水", "热茶", "姜茶", "绿豆汤", "淡盐水", "西瓜")
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if now_minute is not None and start > now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in words):
            return True
    return False


def _light_diet_streak(
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
            light = _has_light_diet(item, now_minute)
            heavy = _has_heavy_food(item, now_minute)
        else:
            light = _has_light_diet(item)
            heavy = _has_heavy_food(item)
        if not light or heavy:
            break
        streak += 1
        day -= timedelta(days=1)
    return streak


def _recent_late_dinner_days(
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
            total += int(_has_late_dinner(item, now_minute))
        else:
            total += int(_has_late_dinner(item))
    return total


def _meal_end_minute(plan: Any) -> int:
    ends: list[int] = []
    for item in _timeline(plan):
        state = str(_item_get(item, "state", "") or "")
        activity = str(_item_get(item, "activity", "") or "")
        if _activity_kind(activity, state) != "eat":
            continue
        ends.append(_minute(_item_get(item, "end")))
    return max(ends) if ends else 0


def _has_dinner(plan: Any) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start < 17 * 60 or start >= 21 * 60:
            continue
        state = str(_item_get(item, "state", "") or "")
        activity = str(_item_get(item, "activity", "") or "")
        if _activity_kind(activity, state) == "eat":
            return True
    return False


def _has_late_dinner(plan: Any, now_minute: int | None = None) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start < 20 * 60 or start >= 21 * 60:
            continue
        if now_minute is not None and start > now_minute:
            continue
        state = str(_item_get(item, "state", "") or "")
        activity = str(_item_get(item, "activity", "") or "")
        if _activity_kind(activity, state) == "eat":
            return True
    return False


def _has_lunch(plan: Any) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start < 11 * 60 or start >= 15 * 60:
            continue
        state = str(_item_get(item, "state", "") or "")
        activity = str(_item_get(item, "activity", "") or "")
        if _activity_kind(activity, state) == "eat":
            return True
    return False


def _recent_baking_days(
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
        if _baking_minutes(item, cutoff) >= 20:
            total += 1
    return total


def _recent_home_cooked_days(
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
        if _cooking_minutes(item, cutoff) >= 30:
            total += 1
    return total


def _meal_start_in_window(
    plan: Any,
    window_start: int,
    window_end: int,
) -> int | None:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start < window_start or start >= window_end:
            continue
        state = str(_item_get(item, "state", "") or "")
        activity = str(_item_get(item, "activity", "") or "")
        if _activity_kind(activity, state) == "eat":
            return start
    return None


def _meal_time_irregular(
    history_plans: list[Any] | None,
    current_plan: Any,
    days: int = 7,
) -> bool:
    try:
        current_day = date.fromisoformat(_plan_day(current_plan)[:10])
    except (TypeError, ValueError):
        return False
    earliest = current_day - timedelta(days=max(1, days) - 1)
    plans = []
    for item in list(history_plans or []) + [current_plan]:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        if earliest <= day <= current_day:
            plans.append(item)
    for window_start, window_end, threshold in (
        (7 * 60, 10 * 60 + 30, 60),
        (11 * 60, 15 * 60, 90),
        (17 * 60, 21 * 60, 90),
    ):
        starts = [
            start
            for plan in plans
            if (start := _meal_start_in_window(plan, window_start, window_end))
            is not None
        ]
        if len(starts) >= 3 and max(starts) - min(starts) >= threshold:
            return True
    return False


def _breakfast_eaten_by(plan: Any, now_minute: int) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start > now_minute or start >= 10 * 60 + 30:
            continue
        state = str(_item_get(item, "state", "") or "")
        activity = str(_item_get(item, "activity", "") or "")
        if _activity_kind(activity, state) == "eat":
            return True
    return False


def _has_breakfast(plan: Any) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start >= 10 * 60 + 30:
            continue
        state = str(_item_get(item, "state", "") or "")
        activity = str(_item_get(item, "activity", "") or "")
        if _activity_kind(activity, state) == "eat":
            return True
    return False


def _recent_lunch_skip_days(
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
        if day == current_day and now_minute is not None and now_minute < 15 * 60:
            continue
        if not _has_lunch(item):
            total += 1
    return total


def _recent_meal_regular_days(
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
        if not (_has_breakfast(item) and _has_lunch(item) and _has_dinner(item)):
            continue
        if day == current_day and now_minute is not None:
            if _has_late_meal(item, now_minute):
                continue
            if now_minute < _meal_end_minute(item):
                continue
        elif _has_late_meal(item):
            continue
        total += 1
    return total


def _recent_breakfast_skip_days(
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
        if day == current_day and now_minute is not None and now_minute < 10 * 60 + 30:
            continue
        if not _has_breakfast(item):
            total += 1
    return total


def _has_late_meal(plan: Any, now_minute: int | None = None) -> bool:
    words = ("夜宵", "吃", "面", "烧烤", "火锅", "零食", "泡面")
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start < 21 * 60:
            continue
        if now_minute is not None and start > now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in words):
            return True
    return False


def _recent_late_meal_days(
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
            total += int(_has_late_meal(item, now_minute))
        else:
            total += int(_has_late_meal(item))
    return total


def _has_heavy_food(plan: Any, now_minute: int | None = None) -> bool:
    words = ("辣", "火锅", "烧烤", "炸", "重口", "麻辣", "啤酒", "白酒", "红酒")
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if now_minute is not None and start > now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in words):
            return True
    return False


def _recent_morning_coffee(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> bool:
    if not isinstance(furniture_states, dict):
        return False
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if not any(word in action for word in ("咖啡", "拿铁", "手冲")):
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if 0 <= age <= 120 and 5 <= moment.hour < 11:
            return True
    return False


def _plan_morning_coffee(plan: Any, now_minute: int) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start > now_minute or now_minute - start > 120:
            continue
        if not (5 * 60 <= start < 11 * 60):
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in ("咖啡", "拿铁", "手冲")):
            return True
    return False


def _caffeine_crash(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> bool:
    if not isinstance(furniture_states, dict):
        return False
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if not any(word in action for word in ("咖啡", "拿铁", "手冲", "茶", "奶茶")):
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if 180 <= age <= 420:
            return True
    return False


def _late_baking(plan: Any, now_minute: int) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start < 18 * 60 or start >= now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in ("烘焙", "烤蛋糕", "烤面包", "做甜点")):
            return True
    return False


def _baking_minutes(plan: Any, now_minute: int) -> int:
    total = 0
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if start >= now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in ("烘焙", "烤蛋糕", "烤面包", "做甜点")):
            total += max(0, min(end, now_minute) - start)
    return total


def _cooking_minutes(plan: Any, now_minute: int) -> int:
    total = 0
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if start >= now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in ("做饭", "下厨", "做菜", "烘焙")):
            total += max(0, min(end, now_minute) - start)
    return total


def _hydration_at(plan: Any, now_minute: int) -> float:
    hydration = 65.0
    summer = _season_for_plan(plan) == "summer"
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if start >= now_minute:
            continue
        duration = max(0, min(end, now_minute) - start)
        if duration <= 0:
            continue
        state = str(_item_get(item, "state", "") or "")
        activity = str(_item_get(item, "activity", "") or "")
        kind = _activity_kind(activity, state)
        if state == "sleep":
            hydration += duration * 0.012
        else:
            drain = duration * 0.045
            if kind == "exercise":
                drain *= 1.6
            if summer:
                drain *= 1.2
            hydration -= drain
        if kind == "eat":
            hydration += 6.0
        if any(word in activity for word in ("果汁", "牛奶", "喝水", "热水", "温水", "汤")):
            hydration += 20.0
        elif any(word in activity for word in ("奶茶", "茶")):
            hydration += 16.0
        elif "咖啡" in activity:
            hydration += 10.0
        if any(word in activity for word in ("啤酒", "白酒", "红酒", "酒")):
            hydration -= 12.0
    return hydration


def _apply_hydration_effects(
    hydration: float,
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> float:
    if not isinstance(furniture_states, dict):
        return hydration
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if not action or action == "自动关闭":
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if age < 0 or age > 480:
            continue
        if any(word in action for word in ("酒", "啤酒", "白酒", "红酒")):
            hydration -= 12.0
        elif any(word in action for word in ("水", "汤", "果汁", "牛奶")):
            hydration += 20.0
        elif any(word in action for word in ("茶", "奶茶")):
            hydration += 16.0
        elif any(word in action for word in ("咖啡", "拿铁", "手冲")):
            hydration += 10.0
        elif any(word in action for word in ("吃", "饭", "早餐", "午餐", "晚餐")):
            hydration += 5.0
    return hydration
