"""普通聊天里的日程/菜单自动补写。

聊天里已经确定的活动（例如「在瑜伽垫做平板支撑」「晚饭做牛腩」）往往不会
被写进当天的日程或菜单，导致主动消息、观察窗和聊天里的说法对不上。本模块
提供：关键词预筛、判定提示词、结果解析、状态冷却、菜单改写与日程文案同步。
"""

from __future__ import annotations

import logging
import json
import re
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .utils import extract_json_object
from .jsonio import atomic_write_json

logger = logging.getLogger("astrbot")

DEFAULT_KEYWORDS = [
    "瑜伽",
    "平板",
    "支撑",
    "运动",
    "锻炼",
    "健身",
    "跑步",
    "拉伸",
    "出汗",
    "训练",
    "做饭",
    "做菜",
    "煮饭",
    "煮",
    "炒",
    "炖",
    "切菜",
    "下厨",
    "备菜",
    "菜谱",
    "菜单",
    "改菜",
    "换菜",
    "晚餐",
    "晚饭",
    "午饭",
    "午餐",
    "早餐",
    "早饭",
    "牛腩",
    "牛肉",
    "鸡蛋",
    "洗碗",
    "洗锅",
    "收拾厨房",
    "烤箱",
    "烘焙",
    "吃饭",
    "一起吃",
    "买菜",
    "采购",
    "食谱",
    "出门",
    "公园",
    "散步",
    "看电影",
    "看剧",
]

DEFAULT_SETTINGS: dict[str, Any] = {
    "enable": True,
    "private_only": True,
    "keyword_filter_enable": True,
    "keywords": DEFAULT_KEYWORDS,
    "cooldown_seconds": 180,
    "max_inserts_per_day": 12,
    "insert_activity": True,
    "update_menu": True,
    "update_plan_text": True,
    "default_minutes": 30,
    "max_minutes": 120,
    "history_minutes": 30,
    "history_messages": 6,
    "skip_when_sleeping": True,
}


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on", "启用", "是"}:
        return True
    if text in {"0", "false", "no", "n", "off", "禁用", "否"}:
        return False
    return default


def _as_int(value: Any, default: int, low: int = 0, high: int = 100000) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(low, min(high, number))


def _clean(value: Any, limit: int = 120) -> str:
    return str(value or "").strip()[:limit]


def settings(raw: Any) -> dict[str, Any]:
    """合并默认值与插件配置。"""
    merged = dict(DEFAULT_SETTINGS)
    if isinstance(raw, dict):
        for key, value in raw.items():
            if value is not None:
                merged[key] = value
    merged["enable"] = _as_bool(merged.get("enable"), True)
    merged["private_only"] = _as_bool(merged.get("private_only"), True)
    merged["keyword_filter_enable"] = _as_bool(
        merged.get("keyword_filter_enable"), True
    )
    merged["insert_activity"] = _as_bool(merged.get("insert_activity"), True)
    merged["update_menu"] = _as_bool(merged.get("update_menu"), True)
    merged["update_plan_text"] = _as_bool(merged.get("update_plan_text"), True)
    merged["skip_when_sleeping"] = _as_bool(
        merged.get("skip_when_sleeping"), True
    )
    raw_keywords = merged.get("keywords")
    if isinstance(raw_keywords, str):
        keywords = [item.strip() for item in re.split(r"[,;\n]", raw_keywords)]
    elif isinstance(raw_keywords, list):
        keywords = [str(item).strip() for item in raw_keywords]
    else:
        keywords = []
    merged["keywords"] = [item for item in keywords if item] or list(DEFAULT_KEYWORDS)
    merged["cooldown_seconds"] = _as_int(
        merged.get("cooldown_seconds"), 180, 5, 86400
    )
    merged["max_inserts_per_day"] = _as_int(
        merged.get("max_inserts_per_day"), 12, 0, 200
    )
    merged["default_minutes"] = _as_int(
        merged.get("default_minutes"), 30, 5, 240
    )
    merged["max_minutes"] = _as_int(merged.get("max_minutes"), 120, 5, 240)
    merged["history_minutes"] = _as_int(
        merged.get("history_minutes"), 30, 0, 1440
    )
    merged["history_messages"] = _as_int(
        merged.get("history_messages"), 6, 0, 30
    )
    return merged


def looks_relevant(text: str, config: dict[str, Any]) -> bool:
    """关键词预筛，避免每一句普通闲聊都调用判定模型。"""
    if not config.get("keyword_filter_enable", True):
        return True
    body = str(text or "")
    if not body.strip():
        return False
    return any(str(word).lower() in body.lower() for word in config.get("keywords") or [])


def format_schedule_text(plan: Any, now: datetime, limit: int = 20) -> str:
    """把当日时间线压成简短提示词，标出当前时段。"""
    try:
        items = list(getattr(plan, "timeline", ()) or ())
    except Exception:
        logger.debug("[模拟人生] format_schedule_text 出错，已忽略", exc_info=True)
        return ""
    if not items:
        return ""
    current_min = now.hour * 60 + now.minute
    lines: list[str] = []
    for item in items[-limit:]:
        line = f"- {item.start}-{item.end} {item.activity}"
        if str(getattr(item, "location", "") or "").strip():
            line += f"（{item.location}）"
        try:
            start = int(item.start.split(":")[0]) * 60 + int(item.start.split(":")[1])
            end = 24 * 60 if item.end == "24:00" else int(item.end.split(":")[0]) * 60 + int(item.end.split(":")[1])
            if start <= current_min < end:
                line += " ← 现在"
        except Exception:
            logger.debug("[模拟人生] format_schedule_text 出错，已忽略", exc_info=True)
        lines.append(line)
    return "\n".join(lines)


def format_menu_text(menu: dict[str, Any]) -> str:
    if not isinstance(menu, dict) or not menu:
        return ""
    windows = menu.get("windows") if isinstance(menu.get("windows"), dict) else {}
    source_labels = {"home": "在家做", "out": "外食", "simple": "简单解决"}
    lines = [f"【{menu.get('date', '')} 菜单】"]
    for meal in menu.get("meals", []) or []:
        if not isinstance(meal, dict):
            continue
        name = str(meal.get("meal") or "").strip()
        dish = str(meal.get("dish") or "").strip()
        source = str(meal.get("source") or "simple")
        window = windows.get(name)
        suffix = f" 用餐时间 {window}" if window else ""
        if source == "simple" or not dish:
            lines.append(f"- {name}：剩菜、加餐或自行安排{suffix}")
            continue
        detail = [source_labels.get(source, source)]
        ingredients = [
            str(item).strip() for item in meal.get("ingredients", []) or [] if str(item).strip()
        ]
        if ingredients:
            detail.append("食材：" + "、".join(ingredients[:10]))
        if meal.get("method"):
            detail.append("做法：" + str(meal["method"])[:80])
        lines.append(f"- {name}：{dish}（" + "；".join(detail) + "）" + suffix)
    return "\n".join(lines)


def build_detection_prompt(
    *,
    persona_prompt: str,
    now: datetime,
    current_activity: str,
    current_location: str,
    schedule_text: str,
    menu_text: str,
    history_text: str,
    user_text: str,
    reply_text: str,
) -> tuple[str, str]:
    system = (
        (persona_prompt or "你是一个有自己生活的普通人。").strip()
        + "\n\n你正在做一次事后整理：判断刚才的聊天里，有没有已经确定、应该写进"
        "今天日程或菜单的事实。只按真实发生或明确约定判断，不要把玩笑、假设、"
        "没定下来的事写进去，也不要重复已经写进日程的事。"
    )
    user = (
        f"现在是 {now.strftime('%Y-%m-%d %H:%M')}。\n"
        f"你当前的活动：{current_activity or '自由活动'}"
        f"（{current_location or '地点未说明'}）。\n\n"
        "今天的日程（节选）：\n"
        f"{schedule_text or '（没有日程）'}\n\n"
        "今天的菜单：\n"
        f"{menu_text or '（没有菜单记录）'}\n\n"
        "最近的对话（旧→新）：\n"
        f"{history_text or '（没有更早的对话）'}\n\n"
        f"对方刚说：{user_text}\n"
        f"你刚回复：{reply_text}\n\n"
        "判断规则：\n"
        "1. schedule.insert：只有聊天里已经确定发生、或明确约定要做，且会持续至少 5 分钟、"
        "会改变你接下来安排的具体活动才写 true；只是嘴硬、玩笑、假设、没定时间或没定做不做的，"
        "写 false。当前日程里已经包含同一件事（描述相近或时间段已经覆盖）时也不要重复插入。\n"
        "2. schedule.start：现在就在做的写 \"now\"；之后某个时间确定要做的写 24 小时制 "
        "\"HH:MM\"（不要早于现在；做饭/吃饭参考菜单里的用餐时间）。\n"
        "3. food.update：聊天里明确决定了某一餐的新菜、主要食材或改了菜谱时更新。\n"
        "   - 有明确菜名就写菜名；没有明确菜名但明确了主要食材/主食"
        "（例如“牛腩归我切”“今晚吃牛腩”），dish 写简短食材名（如“牛腩”）"
        "或常见的简单菜名（如“番茄牛腩”），ingredients 至少包含该食材；"
        "method 不确定就留空，不要编造复杂做法。\n"
        "   - 只是随口提到某样食材、没有确定要做/没有确定由谁做，不要更新。\n"
        "   - 只改提到的那一餐，没提到的内容保持原样。\n"
        "4. 不确定、没有必要、或者只是普通闲聊，就两项都写 false。\n"
        "参考示例：\n"
        "- 聊天「输的煮晚餐」「牛腩归我切」且赌局已经结束、结果明确 → food.update=true，"
        "meal=\"晚餐\"，dish=\"牛腩\"或\"番茄牛腩\"，ingredients=[\"牛腩\"]；"
        "如果当前日程里已经有做饭/吃饭的条目，schedule.insert=false（只改菜名，不重复插入）。\n"
        "- 聊天「我下去跑两圈」，当前日程没有跑步 → schedule.insert=true，"
        "activity=\"下楼跑步\"，start=\"now\"，minutes=20。\n"
        "- 只是开玩笑、说“再说”、没有定下来 → 两项 false。\n"
        "只输出 JSON，不要解释，不要 Markdown："
        '{"schedule":{"insert":false,"activity":"","minutes":30,"location":"","start":"now","reason":""},'
        '"food":{"update":false,"meal":"晚餐","dish":"","ingredients":[],"method":"","reason":""}}'
    )
    return system, user


def parse_detection(
    raw: str, *, default_minutes: int = 30, max_minutes: int = 120
) -> dict[str, Any]:
    """把判定模型输出解析为规范结构；解析失败返回空动作。"""
    payload: Any
    try:
        payload = extract_json_object(str(raw or ""))
    except Exception:
        logger.debug("[模拟人生] parse_detection 出错，已忽略", exc_info=True)
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    schedule_raw = payload.get("schedule")
    if not isinstance(schedule_raw, dict):
        schedule_raw = {}
    food_raw = payload.get("food")
    if not isinstance(food_raw, dict):
        food_raw = {}
    insert = _as_bool(schedule_raw.get("insert"), False)
    activity = _clean(schedule_raw.get("activity"), 80)
    minutes = _as_int(
        schedule_raw.get("minutes"), default_minutes, 5, max_minutes
    )
    start = _clean(schedule_raw.get("start"), 10) or "now"
    if insert and not activity:
        insert = False
    ingredients_raw = food_raw.get("ingredients")
    if isinstance(ingredients_raw, str):
        ingredients = [
            item.strip() for item in re.split(r"[,;、\n]", ingredients_raw)
        ]
    elif isinstance(ingredients_raw, list):
        ingredients = [str(item).strip() for item in ingredients_raw]
    else:
        ingredients = []
    seen: set[str] = set()
    ingredients = [
        item
        for item in ingredients
        if item and not (item in seen or seen.add(item))
    ][:12]
    food = {
        "update": _as_bool(food_raw.get("update"), False),
        "meal": _clean(food_raw.get("meal"), 10),
        "dish": _clean(food_raw.get("dish"), 40),
        "ingredients": ingredients,
        "method": _clean(food_raw.get("method"), 120),
        "reason": _clean(food_raw.get("reason"), 80),
    }
    if food["update"] and not food["dish"]:
        food["update"] = False
    return {
        "schedule": {
            "insert": insert,
            "activity": activity,
            "minutes": minutes,
            "location": _clean(schedule_raw.get("location"), 30),
            "start": start,
            "reason": _clean(schedule_raw.get("reason"), 80),
        },
        "food": food,
    }


def resolve_start(now: datetime, value: Any) -> datetime:
    """把 "now" / "18:00" 解析为今天的 datetime；过早的过去时间回退到现在。"""
    text = str(value or "now").strip()
    if not text or text in {"now", "现在", "马上"}:
        return now
    match = re.match(r"^(\d{1,2}):(\d{2})$", text)
    if not match:
        return now
    hour = int(match.group(1))
    minute = int(match.group(2))
    if hour > 23 or minute > 59:
        return now
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target < now - timedelta(minutes=15):
        return now
    return target


def _norm(value: Any) -> str:
    return re.sub(r"[\s\W_]+", "", str(value or ""))


_MEAL_ALIASES = {
    "早饭": "早餐",
    "早餐": "早餐",
    "午饭": "午餐",
    "午餐": "午餐",
    "中饭": "午餐",
    "晚饭": "晚餐",
    "晚餐": "晚餐",
    "夜宵": "加餐",
    "宵夜": "加餐",
    "加餐": "加餐",
}


def _canonical_meal(value: Any) -> str:
    text = str(value or "").strip()
    for alias, canonical in _MEAL_ALIASES.items():
        if alias in text:
            return canonical
    return text


def schedule_has_similar(
    plan: Any, activity: str, moment: datetime, minutes: int
) -> bool:
    """同一时间段里已有相近活动时视为重复，不再插入。"""
    target = _norm(activity)
    if len(target) < 4:
        return False
    start = moment.hour * 60 + moment.minute
    end = start + max(5, int(minutes))
    for item in getattr(plan, "timeline", ()) or ():
        try:
            item_start = int(str(item.start).split(":")[0]) * 60 + int(str(item.start).split(":")[1])
            item_end = 24 * 60 if item.end == "24:00" else int(str(item.end).split(":")[0]) * 60 + int(str(item.end).split(":")[1])
        except Exception:
            logger.debug("[模拟人生] schedule_has_similar 出错，已忽略", exc_info=True)
            continue
        if item_end <= start or item_start >= end:
            continue
        text = _norm(item.activity)
        if not text:
            continue
        if target in text or text in target:
            return True
        # 近似：共同双字片段占比
        target_bigrams = {target[i : i + 2] for i in range(len(target) - 1)}
        text_bigrams = {text[i : i + 2] for i in range(len(text) - 1)}
        if target_bigrams and text_bigrams:
            overlap = len(target_bigrams & text_bigrams) / min(
                len(target_bigrams), len(text_bigrams)
            )
            if overlap >= 0.45:
                return True
    return False


def replace_dish_in_timeline(
    plan: Any, old_dish: str, new_dish: str
) -> tuple[Any, bool]:
    """把当天日程里旧菜名替换成新菜名。返回 (新计划, 是否改动)。"""
    old = str(old_dish or "").strip()
    new = str(new_dish or "").strip()
    if not old or not new or old == new:
        return plan, False
    items = []
    changed = False
    for item in getattr(plan, "timeline", ()) or ():
        text = str(getattr(item, "activity", "") or "")
        if old in text:
            items.append(replace(item, activity=text.replace(old, new)))
            changed = True
        else:
            items.append(item)
    if not changed:
        return plan, False
    try:
        return replace(plan, timeline=tuple(items)), True
    except Exception:
        logger.debug("[模拟人生] replace_dish_in_timeline 出错，已忽略", exc_info=True)
        return plan, False


def update_menu_state(
    state: dict[str, Any],
    *,
    menu_key: str,
    date_str: str,
    persona_id: str,
    meal: str,
    dish: str,
    ingredients: list[str],
    method: str,
    now: datetime,
) -> tuple[str, bool]:
    """把菜单中某一餐改成新菜；返回 (旧菜名, 是否改动)。"""
    menus = state.get("menus")
    if not isinstance(menus, dict):
        return "", False
    menu = menus.get(menu_key)
    if not isinstance(menu, dict):
        return "", False
    meals = menu.get("meals")
    if not isinstance(meals, list):
        return "", False
    wanted = _canonical_meal(meal)
    target = None
    for entry in meals:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("meal") or "").strip()
        canonical_name = _canonical_meal(name)
        if canonical_name and wanted and canonical_name == wanted:
            target = entry
            break
        if name and (name == wanted or (wanted and wanted in name) or (name in wanted)):
            target = entry
            break
    if target is None:
        return "", False
    old_dish = str(target.get("dish") or "").strip()
    target["dish"] = str(dish or "").strip()
    target["ingredients"] = list(ingredients or [])
    target["method"] = str(method or "").strip()
    target["source"] = "home"
    target["missing"] = []
    state["updated_at"] = date_str
    log = state.setdefault("log", [])
    log.append(
        {
            "date": date_str,
            "persona_id": persona_id,
            "source": "chat",
            "meal": target.get("meal"),
            "dish": target["dish"],
            "at": now.isoformat(timespec="seconds"),
        }
    )
    if len(log) > 100:
        del log[:-100]
    return old_dish, True


class ChatScheduleState:
    """聊天日程检测的冷却与插入记录（落盘在插件数据目录）。"""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._data: dict[str, Any] | None = None

    def load(self) -> dict[str, Any]:
        if self._data is not None:
            return self._data
        payload: dict[str, Any] = {}
        try:
            if self.path.exists():
                raw = self.path.read_text(encoding="utf-8")
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    payload = parsed
        except Exception:
            logger.debug("[模拟人生] load 出错，已忽略", exc_info=True)
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        payload.setdefault("schema_version", 1)
        payload.setdefault("checks", {})
        payload.setdefault("recent", [])
        self._data = payload
        return payload

    def save(self, data: dict[str, Any]) -> None:
        self._data = data
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(self.path, data)
        except Exception:
            logger.debug("[模拟人生] save 出错，已忽略", exc_info=True)


def allow_check(
    data: dict[str, Any], umo: str, now: datetime, config: dict[str, Any]
) -> bool:
    checks = data.get("checks")
    if not isinstance(checks, dict):
        return True
    record = checks.get(str(umo or ""))
    if not isinstance(record, dict):
        return True
    try:
        last = float(record.get("last_checked_ts") or 0)
    except (TypeError, ValueError):
        return True
    cooldown = int(config.get("cooldown_seconds") or 0)
    return cooldown <= 0 or now.timestamp() - last >= cooldown


def mark_checked(data: dict[str, Any], umo: str, now: datetime) -> None:
    checks = data.setdefault("checks", {})
    if not isinstance(checks, dict):
        checks = {}
        data["checks"] = checks
    checks[str(umo or "")] = {
        "last_checked_ts": now.timestamp(),
        "last_checked_at": now.isoformat(timespec="seconds"),
    }
    if len(checks) > 100:
        for key in list(checks)[:-100]:
            checks.pop(key, None)


def count_schedule_inserts_today(data: dict[str, Any], date_str: str) -> int:
    recent = data.get("recent")
    if not isinstance(recent, list):
        return 0
    count = 0
    for entry in recent:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("kind")) != "schedule":
            continue
        if str(entry.get("date") or "")[:10] == date_str:
            count += 1
    return count


def recently_inserted(
    data: dict[str, Any], umo: str, activity: str, now: datetime, hours: float = 3
) -> bool:
    target = _norm(activity)
    if not target:
        return False
    recent = data.get("recent")
    if not isinstance(recent, list):
        return False
    threshold = now.timestamp() - max(1, hours) * 3600
    for entry in reversed(recent[-30:]):
        if not isinstance(entry, dict):
            continue
        if str(entry.get("umo") or "") != str(umo or ""):
            continue
        try:
            at = float(entry.get("ts") or 0)
        except (TypeError, ValueError):
            at = 0
        if at < threshold:
            continue
        text = _norm(entry.get("activity"))
        if not text:
            continue
        if text == target or target in text or text in target:
            return True
        target_bigrams = {target[i : i + 2] for i in range(len(target) - 1)}
        text_bigrams = {text[i : i + 2] for i in range(len(text) - 1)}
        if target_bigrams and text_bigrams:
            if len(target_bigrams & text_bigrams) / min(
                len(target_bigrams), len(text_bigrams)
            ) >= 0.7:
                return True
    return False


def record_insert(
    data: dict[str, Any],
    *,
    umo: str,
    activity: str,
    kind: str,
    now: datetime,
) -> None:
    recent = data.setdefault("recent", [])
    if not isinstance(recent, list):
        recent = []
        data["recent"] = recent
    recent.append(
        {
            "umo": str(umo or ""),
            "activity": str(activity or "")[:120],
            "kind": str(kind or "schedule"),
            "date": now.date().isoformat(),
            "at": now.isoformat(timespec="seconds"),
            "ts": now.timestamp(),
        }
    )
    if len(recent) > 100:
        del recent[:-100]
