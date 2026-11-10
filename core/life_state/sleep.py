"""Sleep debt, sleep windows and late-night patterns."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .base import (
    _item_get,
    _minute,
    _plan_day,
    _timeline,
)
from .body import (
    _recent_exercise_days,
    _transit_minutes,
)
from .meals import (
    _has_heavy_food,
    _has_late_dinner,
    _has_late_meal,
    _has_light_diet,
    _hydration_at,
    _meal_time_irregular,
)
from .weather import (
    _weather_high_temp,
    _weather_low_temp,
)


def _sleep_minutes(plan: Any) -> int:
    total = 0
    for item in _timeline(plan):
        if str(_item_get(item, "state", "") or "") != "sleep":
            continue
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        total += max(0, end - start)
    return total


def _sleep_debt(
    history_plans: list[Any] | None,
    current_plan: Any,
    *,
    target_minutes: int = 420,
    now: datetime | None = None,
) -> int:
    """Carry sleep debt across nights, plus today's completed naps."""
    current_day = _plan_day(current_plan)
    debt = 0
    entries: list[tuple[str, int]] = []
    for plan in history_plans or []:
        day = _plan_day(plan)
        if not day or (current_day and day >= current_day):
            continue
        entries.append((day, _sleep_minutes(plan)))
    entries.sort()
    for _day, slept in entries[-2:]:
        if slept < target_minutes:
            debt += target_minutes - slept
        elif slept > target_minutes:
            debt = max(0, debt - int((slept - target_minutes) * 0.5))

    if now is not None and current_day and current_day == now.date().isoformat():
        now_minute = now.hour * 60 + now.minute
        night_sleep = 0
        nap_sleep = 0
        for item in _timeline(current_plan):
            if str(_item_get(item, "state", "") or "") != "sleep":
                continue
            start = _minute(_item_get(item, "start"))
            end = _minute(_item_get(item, "end"))
            if end > now_minute:
                continue
            duration = max(0, end - start)
            if start < 8 * 60:
                night_sleep += duration
            else:
                nap_sleep += duration
        if night_sleep:
            if night_sleep < target_minutes:
                debt += target_minutes - night_sleep
            else:
                debt = max(0, debt - int((night_sleep - target_minutes) * 0.5))
        if nap_sleep:
            debt = max(0, debt - int(nap_sleep * 0.5))
    try:
        exercise_days = _recent_exercise_days(
            history_plans,
            current_plan,
            now_minute=(now.hour * 60 + now.minute) if now is not None else None,
        )
        if exercise_days >= 3:
            debt = max(0, debt - 20)
        elif exercise_days == 0:
            debt += 15
    except NameError:
        pass
    try:
        if _has_heavy_food(current_plan) and not _has_light_diet(current_plan):
            debt += 10
    except NameError:
        pass
    try:
        if _has_late_meal(current_plan):
            debt += 10
    except NameError:
        pass
    try:
        if _has_late_dinner(current_plan):
            debt += 10
    except NameError:
        pass
    try:
        if _transit_minutes(current_plan, 24 * 60) >= 90:
            debt += 10
    except NameError:
        pass
    try:
        if _hydration_at(current_plan, 24 * 60) < 30:
            debt += 10
    except NameError:
        pass
    try:
        if (
            _weather_high_temp(current_plan, 20) >= 30
            or _weather_low_temp(current_plan, 20) <= 10
        ):
            debt += 10
    except NameError:
        pass
    try:
        if _meal_time_irregular(history_plans, current_plan):
            debt += 10
    except NameError:
        pass
    return min(300, max(0, debt))


def _nap_minutes(plan: Any, now_minute: int) -> int:
    total = 0
    for item in _timeline(plan):
        if str(_item_get(item, "state", "") or "") != "sleep":
            continue
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if start < 10 * 60 or start >= now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if "晚" in activity or "夜间" in activity:
            continue
        total += max(0, min(end, now_minute) - start)
    return total


def _sleep_window_completed(window: tuple[int, int], now_minute: int) -> bool:
    start, end = window
    if start >= end:
        return False
    return end <= now_minute


def _good_sleep_days(
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
    good = 0
    for day, item in entries.items():
        if not (earliest <= day <= current_day):
            continue
        window = _main_sleep_window(item)
        if window is None:
            continue
        if day == current_day and now_minute is not None:
            if not _sleep_window_completed(window, now_minute):
                continue
        start, end = window
        midpoint = ((start + end) // 2) % (24 * 60)
        if midpoint <= 4 * 60 and end - start >= 360:
            good += 1
    return good


def _good_sleep_streak(
    history_plans: list[Any] | None,
    current_plan: Any,
    now_minute: int | None = None,
) -> bool:
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
        return False
    good = 0
    for offset in range(1, 5):
        day = current_day - timedelta(days=offset - 1)
        item = entries.get(day)
        if item is None:
            break
        window = _main_sleep_window(item)
        if day == current_day and now_minute is not None:
            if window is None or not _sleep_window_completed(window, now_minute):
                continue
        if window is None:
            return False
        start, end = window
        midpoint = ((start + end) // 2) % (24 * 60)
        if midpoint <= 4 * 60 and end - start >= 360:
            good += 1
        else:
            return False
    return good >= 3


def _main_sleep_window(plan: Any) -> tuple[int, int] | None:
    best: tuple[int, int] | None = None
    best_duration = 0
    for item in _timeline(plan):
        if str(_item_get(item, "state", "") or "") != "sleep":
            continue
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        duration = max(0, end - start)
        if duration > best_duration:
            best_duration = duration
            best = (start, end)
    return best if best_duration >= 180 else None


def _sleep_midpoint(plan: Any) -> int | None:
    window = _main_sleep_window(plan)
    if window is None:
        return None
    start, end = window
    return ((start + end) // 2) % (24 * 60)


def _sleep_regularity_minutes(
    history_plans: list[Any] | None,
    current_plan: Any,
    now_minute: int | None = None,
) -> int:
    entries: dict[str, Any] = {}
    for item in list(history_plans or []) + [current_plan]:
        day = _plan_day(item)[:10]
        if day:
            entries[day] = item
    current_day = _plan_day(current_plan)[:10]
    points: list[int] = []
    for day in sorted(entries)[-4:]:
        if day == current_day and now_minute is not None:
            window = _main_sleep_window(entries[day])
            if window is None or not _sleep_window_completed(window, now_minute):
                continue
        midpoint = _sleep_midpoint(entries[day])
        if midpoint is not None:
            points.append(midpoint)
    if len(points) < 2:
        return 0
    spreads = []
    for shift in (0, 24 * 60, -24 * 60):
        values = [point + shift for point in points]
        spreads.append(max(values) - min(values))
    return max(0, min(spreads))


def _late_night_streak(
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
        window = _main_sleep_window(entries[day])
        if window is None:
            break
        if day == current_day and now_minute is not None and window[0] > now_minute:
            day -= timedelta(days=1)
            continue
        start = window[0]
        if not (60 <= start < 18 * 60):
            break
        streak += 1
        day -= timedelta(days=1)
    return streak


def _recent_late_nights(
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
        window = _main_sleep_window(item)
        if window is None:
            continue
        if day == current_day and now_minute is not None and window[0] > now_minute:
            continue
        if 60 <= window[0] < 18 * 60:
            count += 1
    return count


def _social_jetlag_minutes(
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
    current_day = _plan_day(current_plan)[:10]
    weekday_points: list[int] = []
    weekend_points: list[int] = []
    for day in sorted(entries)[-7:]:
        if day.isoformat() == current_day and now_minute is not None:
            window = _main_sleep_window(entries[day])
            if window is None or not _sleep_window_completed(window, now_minute):
                continue
        midpoint = _sleep_midpoint(entries[day])
        if midpoint is None:
            continue
        if day.weekday() >= 5:
            weekend_points.append(midpoint)
        else:
            weekday_points.append(midpoint)
    if not weekday_points or not weekend_points:
        return 0
    weekday = sum(weekday_points) / len(weekday_points)
    weekend = sum(weekend_points) / len(weekend_points)
    direct = abs(weekend - weekday)
    return int(round(min(direct, 24 * 60 - direct)))
