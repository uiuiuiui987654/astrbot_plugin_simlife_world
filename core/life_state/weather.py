"""Weather, sun and heat exposure."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .base import (
    _item_get,
    _minute,
    _plan_day,
    _timeline,
)


def _sunburn_on(plan: Any) -> bool:
    return bool(
        _weather_high_temp(plan, 20) >= 32
        and _heat_exposure_minutes(plan, 24 * 60) >= 60
        and _heat_protection(plan) >= 1.0
    )


def _sunburn_yesterday(
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
        if day == previous_day and _sunburn_on(item):
            return True
    return False


def _has_evening_walk(plan: Any, now_minute: int) -> bool:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start < 18 * 60 or start >= now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in ("散步", "走路", "慢走", "遛弯")):
            return True
    return False


def _weather_value(plan: Any, key: str, default: Any = "") -> Any:
    weather = _item_get(plan, "weather", None)
    if weather is None:
        return default
    if isinstance(weather, dict):
        return weather.get(key, default)
    return getattr(weather, key, default)


def _weather_is_bad(plan: Any) -> bool:
    text = " ".join(
        str(_weather_value(plan, key, "") or "")
        for key in ("condition", "description", "text", "weather")
    )
    if any(
        word in text
        for word in ("雨", "雪", "雷", "暴", "台风", "寒", "霜", "冰", "雾")
    ):
        return True
    for key in ("temp_low", "temperature_low", "temp_min", "low_temp"):
        try:
            return float(_weather_value(plan, key, 99)) < 8
        except (TypeError, ValueError):
            continue
    return False


def _temperature_swing(plan: Any) -> int:
    low = high = None
    for key in ("temperature_low", "temp_low", "low_temp"):
        try:
            low = float(_weather_value(plan, key, ""))
            break
        except (TypeError, ValueError):
            continue
    for key in ("temperature_high", "temp_high", "high_temp"):
        try:
            high = float(_weather_value(plan, key, ""))
            break
        except (TypeError, ValueError):
            continue
    if low is None or high is None:
        return 0
    return int(max(0.0, high - low))


def _consecutive_bad_weather(
    plan: Any,
    history_plans: list[Any] | None,
) -> int:
    entries: dict[date, Any] = {}
    for item in list(history_plans or []) + [plan]:
        day_text = _plan_day(item)[:10]
        try:
            day = date.fromisoformat(day_text)
        except (TypeError, ValueError):
            continue
        entries[day] = item
    current_day_text = _plan_day(plan)[:10]
    try:
        current_day = date.fromisoformat(current_day_text)
    except (TypeError, ValueError):
        return 0
    streak = 0
    day = current_day
    while day in entries and _weather_is_bad(entries[day]):
        streak += 1
        day -= timedelta(days=1)
    return streak


HOME_WORDS = (
    "家",
    "卧室",
    "客厅",
    "书房",
    "厨房",
    "浴室",
    "卫生间",
    "阳台",
    "玄关",
    "楼梯",
    "衣帽间",
    "影音室",
    "画室",
    "工作室",
    "餐厅",
    "床上",
    "沙发",
)


def _weather_low_temp(plan: Any, default: float = 20.0) -> float:
    for key in ("temperature_low", "temp_low", "low_temp"):
        try:
            return float(_weather_value(plan, key, default))
        except (TypeError, ValueError):
            continue
    return default


def _weather_high_temp(plan: Any, default: float = 20.0) -> float:
    for key in ("temperature_high", "temp_high", "high_temp"):
        try:
            return float(_weather_value(plan, key, default))
        except (TypeError, ValueError):
            continue
    return default


def _heat_exposure_minutes(plan: Any, now_minute: int) -> int:
    if _weather_high_temp(plan, 20) < 30:
        return 0
    total = 0
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if end <= start or start >= now_minute:
            continue
        location = str(_item_get(item, "location", "") or "")
        state = str(_item_get(item, "state", "") or "")
        activity = str(_item_get(item, "activity", "") or "")
        home = any(word in location for word in HOME_WORDS)
        outdoors = bool(location) and not home
        if state == "transit":
            outdoors = True
        elif not location and any(
            word in activity for word in ("通勤", "出门", "散步", "跑步", "逛街")
        ):
            outdoors = True
        if not outdoors:
            continue
        overlap = min(end, now_minute, 17 * 60) - max(start, 10 * 60)
        if overlap > 0:
            total += overlap
    return total


def _heat_protection(plan: Any) -> float:
    outfit = _item_get(plan, "outfit", None)
    text = ""
    if isinstance(outfit, dict):
        text = str(outfit.get("summary") or "")
        text += " " + " ".join(str(item.get("name") or "") for item in outfit.get("items") or [] if isinstance(item, dict))
    elif outfit is not None:
        text = str(getattr(outfit, "summary", "") or "")
        text += " " + " ".join(str(getattr(item, "name", "") or "") for item in getattr(outfit, "items", ()) or ())
    if any(word in text for word in ("伞", "帽", "防晒", "遮阳", "冰袖", "轻薄")):
        return 0.6
    return 1.0


def _outfit_weather_protection(plan: Any) -> tuple[bool, bool, float]:
    outfit = _item_get(plan, "outfit", None)
    parts: list[str] = []
    if isinstance(outfit, dict):
        parts.append(str(outfit.get("summary") or ""))
        for item in outfit.get("items") or []:
            if isinstance(item, dict):
                parts.extend(
                    str(item.get(key) or "")
                    for key in ("name", "details", "category")
                )
    elif outfit is not None:
        parts.append(str(getattr(outfit, "summary", "") or ""))
        for item in getattr(outfit, "items", ()) or ():
            parts.append(str(getattr(item, "name", "") or ""))
            parts.append(str(getattr(item, "details", "") or ""))
    text = " ".join(parts)
    warm = any(
        word in text
        for word in ("外套", "大衣", "羽绒", "毛衣", "针织", "围巾", "加绒", "风衣")
    )
    rain_gear = any(
        word in text for word in ("伞", "雨衣", "防水", "雨靴", "冲锋衣")
    )
    multiplier = 1.0
    if rain_gear:
        multiplier *= 0.65
    if warm:
        multiplier *= 0.7
    elif _weather_low_temp(plan, 20) < 12:
        multiplier *= 1.2
    return warm, rain_gear, multiplier


def _weather_exposure_minutes(plan: Any, now_minute: int) -> int:
    if not _weather_is_bad(plan):
        return 0
    total = 0
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if end <= start or start >= now_minute:
            continue
        duration = min(end, now_minute) - start
        if duration <= 0:
            continue
        location = str(_item_get(item, "location", "") or "")
        state = str(_item_get(item, "state", "") or "")
        activity = str(_item_get(item, "activity", "") or "")
        home = any(word in location for word in HOME_WORDS)
        outdoors = bool(location) and not home
        if state == "transit":
            outdoors = True
        elif not location and any(
            word in activity for word in ("通勤", "出门", "散步", "跑步", "逛街")
        ):
            outdoors = True
        if outdoors:
            total += duration
    return total


def _season_for_plan(plan: Any) -> str:
    day_text = _plan_day(plan)[:10]
    try:
        month = date.fromisoformat(day_text).month
    except (TypeError, ValueError):
        month = datetime.now().month
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


def _consecutive_good_weather(
    plan: Any,
    history_plans: list[Any] | None,
) -> int:
    entries: dict[date, Any] = {}
    for item in list(history_plans or []) + [plan]:
        try:
            day = date.fromisoformat(_plan_day(item)[:10])
        except (TypeError, ValueError):
            continue
        entries[day] = item
    try:
        day = date.fromisoformat(_plan_day(plan)[:10])
    except (TypeError, ValueError):
        return 0
    streak = 0
    while day in entries and not _weather_is_bad(entries[day]):
        streak += 1
        day -= timedelta(days=1)
    return streak


def _recent_sun_days(
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
    count = 0
    for day, item in entries.items():
        if day < earliest or day > current_day:
            continue
        cutoff = now_minute if day == current_day and now_minute is not None else 24 * 60
        if _sunlight_minutes(item, cutoff) >= 30:
            count += 1
    return count


def _outdoor_minutes(plan: Any, now_minute: int) -> int:
    total = 0
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if end <= start or start >= now_minute:
            continue
        duration = min(end, now_minute) - start
        if duration <= 0:
            continue
        location = str(_item_get(item, "location", "") or "")
        state = str(_item_get(item, "state", "") or "")
        activity = str(_item_get(item, "activity", "") or "")
        home = any(word in location for word in HOME_WORDS)
        outdoors = bool(location) and not home
        if state == "transit":
            outdoors = True
        elif not location and any(
            word in activity for word in ("通勤", "出门", "散步", "跑步", "逛街")
        ):
            outdoors = True
        if outdoors:
            total += duration
    return total


def _sunlight_minutes(plan: Any, now_minute: int) -> int:
    if _weather_is_bad(plan):
        return 0
    daylight_start = 8 * 60
    daylight_end = 17 * 60
    total = 0
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if end <= start or start >= now_minute:
            continue
        location = str(_item_get(item, "location", "") or "")
        state = str(_item_get(item, "state", "") or "")
        activity = str(_item_get(item, "activity", "") or "")
        home = any(word in location for word in HOME_WORDS)
        outdoors = bool(location) and not home
        if state == "transit":
            outdoors = True
        elif not location and any(
            word in activity for word in ("通勤", "出门", "散步", "跑步", "逛街")
        ):
            outdoors = True
        if not outdoors:
            continue
        overlap = min(end, daylight_end, now_minute) - max(start, daylight_start)
        if overlap > 0:
            total += overlap
    return total
