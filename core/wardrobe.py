"""Deterministic wardrobe shared by the observer and virtual-life AI.

Clothing follows the actual activity and dressing transitions. The bundled
appearance assets do not define a personality, biography or conversation history.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

HOME_ROOMS = (
    "卧室",
    "浴室",
    "书房",
    "客厅",
    "厨房",
    "阳台",
    "玄关",
    "走廊",
    "餐厅",
    "衣帽间",
    "健身室",
    "画室",
    "影音室",
    "露台",
    "楼梯厅",
)
FLOOR_PREFIXES = {"一楼", "二楼", "1楼", "2楼", "1F", "2F", "家", "家里"}
DAILY = {
    "key": "daily",
    "name": "白紫日常装",
    "src": "/assets/character_daily.png",
    "description": "白紫色系日常装，按当天风格搭配",
}
SLEEPWEAR = (
    {
        "key": "sleepwear_whale",
        "name": "白紫鲸鱼连帽睡衣",
        "src": "/assets/character_sleepwear_whale.png",
        "description": "白紫鲸鱼连帽连体睡衣，柔软宽松，搭配浅紫袜子",
    },
    {
        "key": "sleepwear_set",
        "name": "白紫鲸鱼印花睡衣",
        "src": "/assets/character_sleepwear_set.png",
        "description": "白紫鲸鱼印花翻领睡衣上装与长裤，搭配鲸鱼拖鞋",
    },
)

_CUSTOM_CHARACTER_SOURCES: dict[str, list[str]] = {}
_CHARACTER_ROTATION_SECONDS = 86400


def set_custom_character_sources(
    sources: dict[str, str | list[str]] | None,
    *,
    rotation_seconds: int = 86400,
) -> None:
    """Register user-uploaded character image galleries for this plugin load."""
    global _CUSTOM_CHARACTER_SOURCES, _CHARACTER_ROTATION_SECONDS
    normalized: dict[str, list[str]] = {}
    for key, value in (sources or {}).items():
        values = value if isinstance(value, (list, tuple)) else [value]
        urls = [str(item).strip() for item in values if str(item).strip()]
        if urls:
            normalized[str(key)] = urls
    _CUSTOM_CHARACTER_SOURCES = normalized
    try:
        _CHARACTER_ROTATION_SECONDS = max(30, min(86400, int(rotation_seconds)))
    except (TypeError, ValueError):
        _CHARACTER_ROTATION_SECONDS = 86400


def _rotation_index(now: datetime, count: int) -> int:
    if count <= 1:
        return 0
    seconds = max(30, _CHARACTER_ROTATION_SECONDS)
    if seconds >= 86400:
        # A daily (or multi-day) portrait cycle should change at local midnight,
        # not at the UTC epoch boundary.
        days = max(1, seconds // 86400)
        bucket = now.date().toordinal() // days
    else:
        try:
            bucket = int(now.timestamp()) // seconds
        except (OSError, OverflowError, ValueError):
            bucket = 0
    return bucket % count


def character_source(
    slot: str, fallback: str, *, now: datetime | None = None
) -> str:
    values = _CUSTOM_CHARACTER_SOURCES.get(str(slot)) or []
    if not values:
        return fallback
    return values[_rotation_index(now or datetime.now(), len(values))] or fallback


def _apply_character_sources(look: dict, now: datetime) -> dict:
    slot = str(look.get("key") or "daily")
    if slot == "daily_outfit":
        slot = "daily"
    custom = _CUSTOM_CHARACTER_SOURCES.get(slot) or []
    if custom:
        index = _rotation_index(now, len(custom))
        look["src"] = custom[index] or str(look.get("src") or DAILY["src"])
        look["rotation_index"] = index
        look["rotation_seconds"] = _CHARACTER_ROTATION_SECONDS
        # Keep the appearance key changed as well. Older cached frontends use
        # only appearance.key in their room signature and would otherwise skip
        # re-rendering after the image was replaced.
        base_key = str(look.get("key") or slot)
        if not base_key.endswith("_custom"):
            look["key"] = base_key + "_custom"
    else:
        look["src"] = str(look.get("src") or DAILY["src"])
    look["avatar_src"] = character_source("avatar", look["src"], now=now)
    return look



def outfit_description(outfit, *, home: bool = False) -> str:
    """把今日穿搭（plan.outfit）压成一句可塞进上下文的穿着描述。"""
    if not outfit:
        return ""
    if isinstance(outfit, dict):
        style = str(outfit.get("style") or "").strip()
        summary = str(outfit.get("summary") or "").strip()
        raw_items = outfit.get("items") or []
    else:
        style = str(getattr(outfit, "style", "") or "").strip()
        summary = str(getattr(outfit, "summary", "") or "").strip()
        raw_items = getattr(outfit, "items", []) or []
    visible = (
        "headwear",
        "top",
        "dress",
        "bottom",
        "outerwear",
        "legwear",
        "accessory",
        "bag",
    )
    if not home:
        visible = visible[:4] + ("shoes",) + visible[4:]
    names = []
    for item in raw_items:
        if isinstance(item, dict):
            category = str(item.get("category") or "")
            name = str(item.get("name") or "").strip()
        else:
            category = str(getattr(item, "category", "") or "")
            name = str(getattr(item, "name", "") or "").strip()
        if name and category in visible:
            names.append(name)
    pieces = "、".join(names[:6])
    if style and summary:
        base = f"{style}——{summary}"
    else:
        base = summary or pieces or style
    if pieces and pieces not in (summary or ""):
        base = f"{base}（{pieces}）"
    if home:
        base += "；在家已脱外出鞋，赤脚或穿室内拖鞋。"
    return base


def appearance_for(
    location: str,
    activity: str,
    state: str,
    now: datetime,
    *,
    home: bool | None = None,
    timeline=None,
    outfit=None,
) -> dict:
    """Resolve visual clothing from activity, time and completed dressing.

    Args:
        location: Actual scheduled location rather than a preview destination.
        activity: Current timeline activity.
        state: Current timeline state, including sleep.
        now: Local moment used for clothing transitions and a stable night ID.
        home: Optional observer classification of a residential location.
        timeline: Today's dicts or TimelineItem objects for dressing transitions.
        outfit: Today's planned outfit (dict or object) used as the real clothing.

    Returns:
        Serializable outfit metadata with an asset path and stable night ID.
    """
    location, activity, state = (
        str(location or ""),
        str(activity or ""),
        str(state or ""),
    )
    if home is None:
        home = (
            "·" not in location or location.split("·", 1)[0] in FLOOR_PREFIXES
        ) and (
            any(room in location for room in HOME_ROOMS)
            or location in {"家", "家里", "家中", "在家", "住宅"}
        )
    resting_inside = home or any(word in location for word in ("酒店", "旅馆", "民宿"))
    night = now.date() - timedelta(days=1) if now.hour < 12 else now.date()
    sleepwear = False
    if resting_inside:
        day_change = any(
            word in activity
            for word in (
                "脱下睡衣",
                "换下睡衣",
                "日常服",
                "日常装",
                "女仆装",
                "穿衣",
                "出门",
                "外出",
            )
        )
        explicit_pajamas = any(
            word in activity
            for word in (
                "换睡衣",
                "换上睡衣",
                "穿睡衣",
                "睡前",
                "准备睡觉",
                "准备入睡",
                "就寝",
            )
        )
        changing = (
            any(word in activity for word in ("换装", "换衣", "换上"))
            and not explicit_pajamas
        )
        active = any(
            word in activity
            for word in (
                "运动",
                "跑步",
                "健身",
                "瑜伽",
                "做饭",
                "烹饪",
                "煎",
                "炒",
                "工作",
                "会议",
            )
        )
        nap = (
            any(word in activity for word in ("午睡", "午休", "小憩", "小睡"))
            and 9 <= now.hour < 19
        )
        sleeping = state.casefold() in {"sleep", "sleeping", "睡眠", "睡觉"} or any(
            word in activity for word in ("睡眠", "睡觉", "入睡", "熟睡")
        )
        # Follow completed dressing transitions in today's schedule. This keeps
        # pajamas after an early bedtime, and daily wear after morning dressing.
        last_change = None
        minute = now.hour * 60 + now.minute
        for item in sorted(
            timeline or [],
            key=lambda i: str(
                i.get("start", "") if isinstance(i, dict) else getattr(i, "start", "")
            ),
        ):

            def value(key, item=item):
                return str(
                    item.get(key, "")
                    if isinstance(item, dict)
                    else getattr(item, key, "")
                )

            try:
                hour_text, minute_text = value("start").split(":")[:2]
                start = int(hour_text) * 60 + int(minute_text)
            except (ValueError, TypeError):
                continue
            if start > minute or (now.hour >= 12 and start < 18 * 60):
                continue
            text = value("activity")
            if any(
                word in text
                for word in (
                    "脱下睡衣",
                    "换下睡衣",
                    "日常服",
                    "日常装",
                    "女仆装",
                    "穿衣",
                    "出门",
                    "外出",
                )
            ):
                last_change = False
            elif any(
                word in text
                for word in (
                    "换睡衣",
                    "换上睡衣",
                    "穿睡衣",
                    "睡前",
                    "准备睡觉",
                    "准备入睡",
                    "就寝",
                )
            ):
                last_change = True
            elif any(word in text for word in ("换装", "换衣", "换上")):
                last_change = False
        period_default = now.hour >= 22 or now.hour < 9
        if now.hour < 12 and last_change is False:
            period_default = False
        elif now.hour >= 18 and last_change is True:
            period_default = True
        sleepwear = not (day_change or changing or active or nap) and (
            explicit_pajamas or sleeping or period_default
        )
    day_outfit = outfit_description(outfit, home=home)
    if sleepwear:
        look = dict(
            SLEEPWEAR[night.toordinal() % len(SLEEPWEAR)],
            is_sleepwear=True,
            night_id=night.isoformat(),
            day_outfit=day_outfit,
        )
    elif day_outfit:
        look = {
            "key": "daily_outfit",
            "name": "今日穿搭",
            "src": DAILY["src"],
            "description": day_outfit,
            "is_sleepwear": False,
            "night_id": "",
            "day_outfit": day_outfit,
        }
    else:
        look = dict(DAILY, is_sleepwear=False, night_id="", day_outfit="")
    return _apply_character_sources(look, now)


def appearance_context(
    location: str,
    activity: str,
    state: str,
    now: datetime,
    *,
    timeline=None,
    outfit=None,
) -> str:
    look = appearance_for(
        location, activity, state, now, timeline=timeline, outfit=outfit
    )
    if look.get("is_sleepwear"):
        text = f"当前实际服装：{look['name']}（{look['description']}）。"
        if look.get("day_outfit"):
            text += f"今日穿搭：{look['day_outfit']}，白天按这套穿。"
        return text + "以此为准回应穿着问题。"
    if look.get("day_outfit"):
        return f"当前实际服装：{look['day_outfit']}（今日穿搭，当前就按这套穿）。以此为准回应穿着问题；界面立绘为固定形象，旧穿搭记录只作参考。"
    return f"当前实际服装：{look['name']}（{look['description']}）。以此为准回应穿着问题，今日穿搭未记录，旧穿搭记录只作参考。"


def wardrobe_prompt() -> str:
    return "【衣柜规则】立绘只固定银白长发、紫色眼睛、鲸鱼耳鳍和鲸鱼尾，不固定日常服装。日常与外出按当天风格自由搭配，可选休闲、通勤、运动、居家、裙装、衬衫、毛衣、卫衣等；女仆装只是其中一个选项，仅当今日穿搭明确选择女仆装时才写女仆裙。在家要脱掉外出鞋，赤脚或穿室内拖鞋；出门才换外出鞋。居家睡前、夜间睡眠与起床尚未换衣时穿睡衣。两套白紫睡衣为鲸鱼连帽连体款、鲸鱼印花上下装，每晚交替，过午夜保持同一套；白天午睡不强制换装。早晨安排洗漱和换日常装，睡前安排换睡衣，不要让人穿睡衣外出或运动。今日穿搭主套装应与当天风格一致，可补充合适配饰。立绘和服装只定义外观，不预置性格、经历、关系或记忆，人格使用 AstrBot 当前配置。"


_LEGACY_FORCED_MAID = {
    "白紫鲸鱼女仆裙上装": "白紫收腰针织上衣",
    "固定立绘的白紫女仆裙上装": "白紫针织上衣",
    "白紫女仆裙裙摆": "白紫百褶半身裙",
    "白紫女仆裙打底": "白紫针织上衣与半身裙打底",
    "女仆裙": "半身裙",
}


def _clean_legacy_maid_text(text: str) -> str:
    cleaned = str(text or "")
    for old, new in _LEGACY_FORCED_MAID.items():
        cleaned = cleaned.replace(old, new)
    return cleaned.replace("女仆", "")


def migrate_legacy_forced_outfit(outfit):
    """清理旧版「固定衣柜」强制写入的女仆装文案。

    只处理带有旧版固定立绘标记的穿搭；用户明确选择的普通女仆装不动。
    """
    if outfit is None:
        return outfit
    summary = str(getattr(outfit, "summary", "") or "")
    items = tuple(getattr(outfit, "items", ()) or ())
    legacy = "不改固定形象" in summary or any(
        "固定立绘的白紫女仆裙上装" in str(getattr(item, "details", "") or "")
        for item in items
    )
    if not legacy:
        return outfit
    cleaned_summary = _clean_legacy_maid_text(summary)
    cleaned_items = []
    changed = cleaned_summary != summary
    for item in items:
        name = str(getattr(item, "name", "") or "")
        details = str(getattr(item, "details", "") or "")
        new_name = _clean_legacy_maid_text(name)
        new_details = _clean_legacy_maid_text(details)
        if new_name != name or new_details != details:
            item = replace(item, name=new_name, details=new_details)
            changed = True
        cleaned_items.append(item)
    if not changed:
        return outfit
    return replace(
        outfit,
        summary=cleaned_summary,
        items=tuple(cleaned_items),
    )
