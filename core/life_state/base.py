"""Shared constants and timeline primitives for life-state computation."""
from __future__ import annotations

from datetime import date
from typing import Any

# Baseline per-minute drift.  Meals, washing and exercise are applied as events
# below instead of being smeared across the whole activity block.
RATES = {
    "sleep": {"energy": 0.070, "satiety": -0.010, "hygiene": -0.004, "mood": 0.004},
    "awake": {"energy": -0.045, "satiety": -0.040, "hygiene": -0.015, "mood": 0.000},
}


MOOD_BASE = [
    (("开心", "愉快", "兴奋", "满足", "期待", "雀跃", "幸福"), 78),
    (("平静", "放松", "日常", "慵懒", "安稳", "悠闲"), 66),
    (("低落", "疲惫", "烦躁", "焦虑", "难过", "失落", "紧张"), 46),
]


LABELS = {
    "energy": ((75, "精神很好"), (50, "正常"), (30, "有点累"), (0, "很累")),
    "satiety": ((75, "很饱"), (50, "正常"), (25, "有点饿"), (0, "饿了")),
    "hygiene": ((70, "清爽"), (45, "正常"), (0, "需要洗漱")),
    "hydration": ((70, "水分充足"), (50, "正常"), (35, "有点口渴"), (0, "很渴")),
    "mood": ((75, "心情不错"), (55, "平静"), (35, "有点低落"), (0, "心情低落")),
    "willingness": ((70, "有精神"), (45, "正常"), (25, "有点懒"), (0, "不太想动")),
    "health": ((85, "状态不错"), (65, "正常"), (45, "有点疲惫"), (35, "不太舒服"), (0, "很虚弱")),
}


def _item_get(item: Any, key: str, default: Any = "") -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _minute(value: Any) -> int:
    text = str(value or "")
    try:
        hour, minute = text.split(":", 1)
        return max(0, min(24 * 60, int(hour) * 60 + int(minute)))
    except (TypeError, ValueError):
        return 0


def _timeline(plan: Any) -> list[Any]:
    if isinstance(plan, dict):
        items = plan.get("timeline") or []
    else:
        items = getattr(plan, "timeline", ()) or ()
    return [item for item in items if item]


def _mood_score(plan: Any) -> int:
    mood = str(_item_get(plan, "mood", "") or "")
    for words, score in MOOD_BASE:
        if any(word in mood for word in words):
            return score
    return 62


def _history_mood_average(
    history_plans: list[Any] | None,
    current_plan: Any,
) -> int | None:
    if not history_plans:
        return None
    current_day = _plan_day(current_plan)
    entries: list[tuple[str, int]] = []
    for plan in history_plans:
        day = _plan_day(plan)
        if not day or (current_day and day >= current_day):
            continue
        entries.append((day, _mood_score(plan)))
    if not entries:
        return None
    entries.sort()
    scores = [score for _day, score in entries[-7:]]
    return int(round(sum(scores) / len(scores)))


def _low_mood_streak(
    history_plans: list[Any] | None,
    current_plan: Any,
) -> int:
    """Count consecutive recent days whose planned mood was low."""
    if not history_plans:
        return 0
    current_day = _plan_day(current_plan)
    entries: list[tuple[str, int]] = []
    for plan in history_plans:
        day = _plan_day(plan)
        if not day or (current_day and day >= current_day):
            continue
        entries.append((day, _mood_score(plan)))
    entries.sort()
    streak = 0
    for _day, score in reversed(entries):
        if score >= 50:
            break
        streak += 1
    return streak


def _mood_base(plan: Any, history_plans: list[Any] | None = None) -> int:
    base = _mood_score(plan)
    historical = _history_mood_average(history_plans, plan)
    if historical is None:
        return base
    # Emotional state has inertia: a good day does not instantly erase a low
    # previous week, and a bad night does not erase a generally good mood.
    return int(round(base * 0.7 + historical * 0.3))


def _plan_day(plan: Any) -> str:
    return str(_item_get(plan, "date", "") or "")


def _activity_kind(activity: str, state: str) -> str:
    text = f"{activity} {state}"
    if "sleep" in text.lower() or any(word in text for word in ("睡觉", "睡眠", "入睡", "午睡", "小憩")):
        return "sleep"
    if any(word in text for word in ("洗澡", "淋浴", "泡澡", "洗漱", "洗头", "沐浴")):
        return "bath"
    if any(
        word in text
        for word in ("吃饭", "用餐", "早餐", "午餐", "晚餐", "夜宵", "吃点", "吃")
    ):
        return "eat"
    if any(
        word in text
        for word in ("跑步", "健身", "瑜伽", "拉伸", "运动", "力量", "锻炼", "慢跑")
    ):
        return "exercise"
    if any(
        word in text
        for word in ("休息", "发呆", "躺着", "放松", "葛优", "坐一会儿", "晒太阳")
    ):
        return "rest"
    if any(
        word in text
        for word in ("工作", "学习", "看书", "阅读", "写", "专注", "整理", "做饭", "备菜")
    ):
        return "work"
    if state == "social" or any(
        word in text
        for word in (
            "聊天",
            "朋友",
            "聚会",
            "电话",
            "社交",
            "一起",
            "约会",
            "聊心事",
            "深聊",
            "倾诉",
            "谈心",
        )
    ):
        return "social"
    return "awake"


def _label(kind: str, value: float) -> str:
    for threshold, label in LABELS[kind]:
        if value >= threshold:
            return label
    return LABELS[kind][-1][1]


def _clamp(value: float) -> int:
    return int(round(max(0.0, min(100.0, value))))


def _activity_minutes(plan: Any, now_minute: int, kind: str) -> int:
    total = 0
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
        if _activity_kind(activity, state) == kind:
            total += duration
    return total


def _current_activity_kind(plan: Any, now_minute: int) -> str:
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if start <= now_minute < end:
            state = str(_item_get(item, "state", "") or "")
            activity = str(_item_get(item, "activity", "") or "")
            return _activity_kind(activity, state)
    return ""


def _weekday(plan: Any) -> int:
    try:
        return date.fromisoformat(_plan_day(plan)[:10]).weekday()
    except (TypeError, ValueError):
        return -1


def _is_weekend(plan: Any) -> bool:
    try:
        return date.fromisoformat(_plan_day(plan)[:10]).weekday() >= 5
    except (TypeError, ValueError):
        return False
