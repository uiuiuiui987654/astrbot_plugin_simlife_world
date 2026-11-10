"""Home habits: aroma, chores, music, screens, reading, furniture effects."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .base import (
    _item_get,
    _minute,
    _plan_day,
    _timeline,
)


def _apply_furniture_effects(
    energy: float,
    satiety: float,
    hygiene: float,
    mood: float,
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> tuple[float, float, float, float]:
    """User-driven furniture actions leave a small, short-lived physical trace."""
    if not isinstance(furniture_states, dict):
        return energy, satiety, hygiene, mood
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
        if any(word in action for word in ("咖啡", "拿铁", "手冲", "茶", "奶茶")):
            energy += 7.0
            satiety += 3.0
            mood += 1.0
        elif any(word in action for word in ("吃", "饭", "早餐", "午餐", "晚餐", "夜宵", "泡面", "零食")):
            satiety += 14.0
            energy += 3.0
            mood += 1.0
        elif "澡" in action or any(word in action for word in ("淋浴", "洗漱", "洗头", "面膜", "护肤")):
            hygiene += 18.0
            mood += 2.0
        elif any(word in action for word in ("睡", "午睡", "小憩", "赖床", "休息", "躺")):
            energy += 7.0
            mood += 1.0
        elif "跑" in action or any(word in action for word in ("健身", "瑜伽", "拉伸", "锻炼", "运动", "平板")):
            energy -= 8.0
            hygiene -= 3.0
            mood += 5.0
        elif any(word in action for word in ("打扫", "洗衣服", "吸尘", "收拾", "整理", "洗碗", "熨")):
            energy -= 3.0
            mood += 1.0
        elif any(word in action for word in ("做饭", "烘焙", "烤", "煮", "备菜", "拉花")):
            satiety += 3.0
            mood += 2.0
        elif any(word in action for word in ("游戏", "电视", "电影", "音乐", "唱片", "播客", "剧", "唱歌", "弹琴", "画画")):
            mood += 3.0
            energy -= 2.0
    return energy, satiety, hygiene, mood


def _late_movie_yesterday(
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
        for entry in _timeline(item):
            start = _minute(_item_get(entry, "start"))
            if start < 22 * 60:
                continue
            activity = str(_item_get(entry, "activity", "") or "")
            if any(word in activity for word in ("电影", "看剧", "刷剧", "追剧")):
                return True
    return False


def _recent_aroma(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> bool:
    if not isinstance(furniture_states, dict):
        return False
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if "香薰" not in action and "精油" not in action:
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if 0 <= age <= 240:
            return True
    return False


def _recent_fresh_clothes(
    furniture_states: dict[str, Any] | None,
    plan: Any,
    now: datetime,
    now_minute: int,
) -> bool:
    if isinstance(furniture_states, dict):
        for state in furniture_states.values():
            if not isinstance(state, dict):
                continue
            action = str(state.get("last_action") or "")
            if not any(word in action for word in ("洗衣", "晾衣服", "换衣服")):
                continue
            try:
                moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
            except (TypeError, ValueError):
                continue
            if moment.tzinfo is None and now.tzinfo is not None:
                moment = moment.replace(tzinfo=now.tzinfo)
            age = (now - moment).total_seconds() / 60.0
            if 0 <= age <= 180:
                return True
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        if start >= now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in ("换衣服", "换身衣服", "换上干净")):
            return True
    return False


def _recent_popcorn(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> bool:
    if not isinstance(furniture_states, dict):
        return False
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if "爆米花" not in action:
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if 0 <= age <= 180:
            return True
    return False


def _recent_chore(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> bool:
    if not isinstance(furniture_states, dict):
        return False
    words = (
        "洗衣",
        "吸尘",
        "扫地",
        "拖地",
        "洗碗",
        "晾衣服",
        "擦桌",
        "整理",
    )
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if not any(word in action for word in words):
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if 0 <= age <= 180:
            return True
    return False


def _recent_instrument(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> bool:
    if not isinstance(furniture_states, dict):
        return False
    words = ("弹", "练琴", "拉小提琴", "吹", "架子鼓")
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if not any(word in action for word in words):
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if 0 <= age <= 180:
            return True
    return False


def _recent_audio_action(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> str:
    if not isinstance(furniture_states, dict):
        return ""
    words = (
        "音乐",
        "听歌",
        "唱片",
        "播客",
        "电台",
        "钢琴曲",
        "摇滚",
        "轻音乐",
        "快歌",
        "舞曲",
        "电音",
        "白噪音",
        "雨声",
        "音箱",
        "耳机",
        "放歌",
    )
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if not any(word in action for word in words):
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if 0 <= age <= 180:
            return action
    return ""


def _recent_audio_relax(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> bool:
    if not isinstance(furniture_states, dict):
        return False
    words = ("音乐", "听歌", "唱片", "播客", "电台", "钢琴", "吉他")
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if not any(word in action for word in words):
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if 0 <= age <= 180:
            return True
    return False


def _recent_screen_time(
    furniture_states: dict[str, Any] | None,
    now: datetime,
) -> bool:
    if not isinstance(furniture_states, dict):
        return False
    words = (
        "游戏",
        "电视",
        "电影",
        "刷剧",
        "手机",
        "电脑",
        "视频",
        "直播",
        "综艺",
        "投影",
        "显示器",
        "幕布",
        "平板",
    )
    for state in furniture_states.values():
        if not isinstance(state, dict):
            continue
        action = str(state.get("last_action") or "")
        if not any(word in action for word in words):
            continue
        try:
            moment = datetime.fromisoformat(str(state.get("updated_at") or ""))
        except (TypeError, ValueError):
            continue
        if moment.tzinfo is None and now.tzinfo is not None:
            moment = moment.replace(tzinfo=now.tzinfo)
        age = (now - moment).total_seconds() / 60.0
        if 0 <= age <= 180:
            return True
    return False


def _reading_minutes(plan: Any, now_minute: int) -> int:
    total = 0
    for item in _timeline(plan):
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if start >= now_minute:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        if any(word in activity for word in ("看书", "阅读", "读书")):
            total += max(0, min(end, now_minute) - start)
    return total
