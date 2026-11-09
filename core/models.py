from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import date, datetime, time
from typing import Any, Literal

State = Literal["sleep", "busy", "focus", "transit", "available", "social"]
Availability = Literal["blocked", "low", "normal", "high"]
Audience = Literal["private", "group", "both"]

STATES = {"sleep", "busy", "focus", "transit", "available", "social"}
AVAILABILITIES = {"blocked", "low", "normal", "high"}
AUDIENCES = {"private", "group", "both"}
OUTFIT_CATEGORIES = {
    "hairstyle",
    "headwear",
    "underwear",
    "underpants",
    "top",
    "bottom",
    "dress",
    "legwear",
    "outerwear",
    "shoes",
    "accessory",
    "bag",
    "makeup",
    "fragrance",
    "other",
}
OUTFIT_CATEGORY_ALIASES = {
    "hair_accessory": "headwear",
    "hair-accessory": "headwear",
    "hair accessories": "headwear",
    "hair_accessories": "headwear",
    "hairpin": "headwear",
    "hair_pin": "headwear",
    "hair_bow": "headwear",
    "hairclip": "headwear",
    "hair_clip": "headwear",
    "earring": "accessory",
    "earrings": "accessory",
    "jewellery": "accessory",
    "jewelry": "accessory",
    "necklace": "accessory",
}
OUTFIT_CATEGORY_LABELS = {
    "hairstyle": "发型",
    "headwear": "帽子与发饰",
    "underwear": "内衣与打底",
    "underpants": "内裤",
    "top": "上装",
    "bottom": "下装",
    "dress": "连衣裙与连体服",
    "legwear": "袜子与腿部穿搭",
    "outerwear": "外套",
    "shoes": "鞋履",
    "accessory": "配饰",
    "bag": "包具",
    "makeup": "妆容",
    "fragrance": "香氛",
    "other": "其他",
}


def parse_hhmm(value: str, *, allow_2400: bool = False) -> time:
    if allow_2400 and value == "24:00":
        return time.max
    if not isinstance(value, str) or not value:
        raise ValueError("time must be a non-empty HH:MM string")
    try:
        parsed = datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"invalid HH:MM value: {value!r}") from exc
    if parsed.strftime("%H:%M") != value:
        raise ValueError(f"invalid HH:MM value: {value}")
    return parsed


def minute_of_day(value: str) -> int:
    if value == "24:00":
        return 1440
    parsed = parse_hhmm(value)
    return parsed.hour * 60 + parsed.minute


@dataclass(slots=True, frozen=True)
class TimelineItem:
    id: str
    start: str
    end: str
    activity: str
    location: str = ""
    state: State = "available"
    availability: Availability = "normal"
    participant_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id or not self.activity:
            raise ValueError("timeline id and activity are required")
        if self.state not in STATES:
            raise ValueError(f"invalid state: {self.state}")
        if self.availability not in AVAILABILITIES:
            raise ValueError(f"invalid availability: {self.availability}")
        if minute_of_day(self.start) >= minute_of_day(self.end):
            raise ValueError("timeline start must be earlier than end")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> TimelineItem:
        participant_ids = value.get("participant_ids", [])
        if not isinstance(participant_ids, list):
            participant_ids = []
        return cls(
            id=str(value.get("id", "")).strip(),
            start=str(value.get("start", "")).strip(),
            end=str(value.get("end", "")).strip(),
            activity=str(value.get("activity", "")).strip(),
            location=str(value.get("location", "")).strip(),
            state=str(value.get("state", "available")),
            availability=str(value.get("availability", "normal")),
            participant_ids=tuple(
                dict.fromkeys(
                    str(item).strip()
                    for item in participant_ids[:20]
                    if str(item).strip()
                )
            ),
        )


@dataclass(slots=True, frozen=True)
class ProactiveWindow:
    id: str
    at: str
    intent: str
    audience: Audience = "both"
    source_item_id: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.intent:
            raise ValueError("window id and intent are required")
        parse_hhmm(self.at)
        if self.audience not in AUDIENCES:
            raise ValueError(f"invalid audience: {self.audience}")
        if not self.source_item_id:
            raise ValueError("window source_item_id is required")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ProactiveWindow:
        return cls(
            id=str(value.get("id", "")).strip(),
            at=str(value.get("at", "")).strip(),
            intent=str(value.get("intent", "")).strip(),
            audience=str(value.get("audience", "both")),
            source_item_id=str(value.get("source_item_id", "")).strip(),
        )


@dataclass(slots=True, frozen=True)
class OutfitItem:
    category: str
    name: str
    details: str = ""

    def __post_init__(self) -> None:
        category = (
            OUTFIT_CATEGORY_ALIASES.get(self.category.strip().lower())
            or self.category.strip().lower()
        )
        if category not in OUTFIT_CATEGORIES:
            raise ValueError(f"invalid outfit category: {self.category}")
        if not self.name:
            raise ValueError("outfit item name is required")
        object.__setattr__(self, "category", category)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> OutfitItem:
        return cls(
            category=str(value.get("category", "")).strip(),
            name=str(value.get("name", "")).strip(),
            details=str(value.get("details", "")).strip(),
        )


@dataclass(slots=True, frozen=True)
class Outfit:
    summary: str
    items: tuple[OutfitItem, ...]
    style: str = "未记录"

    def __post_init__(self) -> None:
        if not self.summary:
            raise ValueError("outfit summary is required")

    def validate_complete(self) -> None:
        categories = {item.category for item in self.items}
        for required in ("hairstyle", "underwear", "underpants", "shoes"):
            if required not in categories:
                raise ValueError(f"outfit must contain category: {required}")
        if not categories.intersection({"top", "dress", "other"}):
            raise ValueError(
                "outfit must contain top, dress, or other as the main clothing"
            )
        if "dress" not in categories and "bottom" not in categories:
            raise ValueError("outfit without dress must contain bottom")

    @classmethod
    def from_dict(cls, value: object) -> Outfit:
        if not isinstance(value, dict):
            raise ValueError("outfit must be a structured object")
        raw_items = value.get("items")
        if not isinstance(raw_items, list):
            raise ValueError("outfit items must be an array")
        if any(not isinstance(item, dict) for item in raw_items):
            raise ValueError("every outfit item must be an object")
        return cls(
            summary=str(value.get("summary", "")).strip(),
            items=tuple(OutfitItem.from_dict(item) for item in raw_items),
            style=str(value.get("style", "")).strip() or "未记录",
        )


SEASON_WEATHER_POOLS: dict[str, tuple[str, ...]] = {
    "春": ("晴朗", "多云", "微风", "小雨", "阴天"),
    "夏": ("晴朗", "闷热", "雷阵雨", "多云", "微风"),
    "秋": ("晴朗", "凉爽", "多云", "微风", "小雨"),
    "冬": ("晴朗", "阴天", "大风", "寒冷", "小雨"),
}
SEASON_TEMPERATURES: dict[str, tuple[int, int]] = {
    "春": (12, 22),
    "夏": (24, 33),
    "秋": (15, 24),
    "冬": (3, 12),
}
WEATHER_TEMP_DELTAS: dict[str, tuple[int, int]] = {
    "晴朗": (1, 2),
    "多云": (0, 0),
    "阴天": (-1, 0),
    "小雨": (-2, -1),
    "雷阵雨": (-2, 0),
    "大风": (-3, -1),
    "寒冷": (-4, -2),
    "闷热": (2, 3),
    "微风": (0, 1),
    "凉爽": (-1, 0),
}
WEATHER_DESCRIPTIONS: dict[str, str] = {
    "晴朗": "阳光充足，适合外出",
    "多云": "云量较多，光线柔和",
    "阴天": "天色偏灰，体感偏凉",
    "小雨": "有间歇小雨，出门记得带伞",
    "雷阵雨": "午后可能有雷阵雨，尽量减少户外停留",
    "大风": "风力较大，注意保暖",
    "寒冷": "气温偏低，注意保暖",
    "闷热": "湿度较高，体感闷热",
    "微风": "有微风，体感舒适",
    "凉爽": "天气凉爽，体感舒适",
}


@dataclass(slots=True, frozen=True)
class Weather:
    condition: str
    temperature_low: int
    temperature_high: int
    description: str = ""

    def __post_init__(self) -> None:
        if not self.condition:
            raise ValueError("weather condition is required")
        if not -30 <= self.temperature_low <= 45:
            raise ValueError("weather temperature_low out of range")
        if not -30 <= self.temperature_high <= 45:
            raise ValueError("weather temperature_high out of range")
        if self.temperature_low > self.temperature_high:
            raise ValueError("weather temperature_low must not exceed temperature_high")
        if len(self.description) > 160:
            raise ValueError("weather description is too long")

    @property
    def label(self) -> str:
        return (
            f"{self.condition} {self.temperature_low}~{self.temperature_high}°C"
        )

    @property
    def prompt_text(self) -> str:
        text = self.label
        if self.description:
            text += f"，{self.description}"
        return text

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Weather:
        if not isinstance(value, dict):
            raise ValueError("weather must be a structured object")
        return cls(
            condition=str(value.get("condition", "")).strip(),
            temperature_low=int(
                value.get("temperature_low", value.get("low", 18))
            ),
            temperature_high=int(
                value.get("temperature_high", value.get("high", 25))
            ),
            description=str(value.get("description", "")).strip(),
        )


def season_for_date(target: date) -> str:
    month = target.month
    if month in (3, 4, 5):
        return "春"
    if month in (6, 7, 8):
        return "夏"
    if month in (9, 10, 11):
        return "秋"
    return "冬"


def weather_for_date(target: date) -> Weather:
    season = season_for_date(target)
    pool = SEASON_WEATHER_POOLS[season]
    condition = pool[target.toordinal() % len(pool)]
    low, high = SEASON_TEMPERATURES[season]
    low_delta, high_delta = WEATHER_TEMP_DELTAS.get(condition, (0, 0))
    low += low_delta
    high += high_delta
    if low > high:
        low = high
    return Weather(
        condition=condition,
        temperature_low=low,
        temperature_high=high,
        description=WEATHER_DESCRIPTIONS.get(condition, ""),
    )


@dataclass(slots=True, frozen=True)
class DailyPlan:
    date: str
    persona_id: str
    theme: str
    mood: str
    outfit: Outfit | None
    timeline: tuple[TimelineItem, ...]
    proactive_windows: tuple[ProactiveWindow, ...] = ()
    private_bonus: int = 0
    group_bonus: int = 0
    status: str = "ok"
    revision: str = ""
    weather: Weather | None = None

    def __post_init__(self) -> None:
        target_date = date.fromisoformat(self.date)
        if self.weather is None:
            object.__setattr__(self, "weather", weather_for_date(target_date))
        if not self.persona_id:
            raise ValueError("persona_id is required")
        if self.status == "ok" and self.outfit is not None:
            self.outfit.validate_complete()
        previous_end = 0
        ids: set[str] = set()
        for item in self.timeline:
            start = minute_of_day(item.start)
            if ids and start != previous_end:
                raise ValueError(
                    "timeline items must be continuous and non-overlapping"
                )
            if start < previous_end:
                raise ValueError("timeline items overlap or are unsorted")
            previous_end = minute_of_day(item.end)
            if item.id in ids:
                raise ValueError("timeline ids must be unique")
            ids.add(item.id)
        if self.status == "ok" and self.timeline:
            if self.timeline[0].start != "00:00" or self.timeline[-1].end != "24:00":
                raise ValueError("timeline must cover 00:00 through 24:00")
            window_ids: set[str] = set()
            for window in self.proactive_windows:
                if window.id in window_ids:
                    raise ValueError("window ids must be unique")
                window_ids.add(window.id)
                source = next(
                    (
                        item
                        for item in self.timeline
                        if item.id == window.source_item_id
                    ),
                    None,
                )
                if source is None:
                    raise ValueError("window references unknown timeline item")
                planned = minute_of_day(window.at)
                if (
                    not minute_of_day(source.start)
                    <= planned
                    < minute_of_day(source.end)
                ):
                    raise ValueError(
                        "window time must be inside its source timeline item"
                    )
        elif self.proactive_windows:
            raise ValueError("proactive windows require a schedule")

    @property
    def has_schedule(self) -> bool:
        return self.status == "ok" and bool(self.timeline)

    @property
    def has_outfit(self) -> bool:
        return self.status == "ok" and self.outfit is not None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> DailyPlan:
        bonus = value.get("budget_bonus") or {}
        return cls(
            date=str(value["date"]),
            persona_id=str(value["persona_id"]),
            theme=str(value.get("theme", "日常")),
            mood=str(value.get("mood", "平静")),
            weather=(
                Weather.from_dict(value.get("weather"))
                if isinstance(value.get("weather"), dict)
                else None
            ),
            outfit=(
                Outfit.from_dict(value.get("outfit"))
                if value.get("outfit") is not None
                else None
            ),
            timeline=tuple(
                TimelineItem.from_dict(item) for item in value.get("timeline", [])
            ),
            proactive_windows=tuple(
                ProactiveWindow.from_dict(item)
                for item in value.get("proactive_windows", [])
            ),
            private_bonus=int(bonus.get("private", value.get("private_bonus", 0))),
            group_bonus=int(bonus.get("group", value.get("group_bonus", 0))),
            status=str(value.get("status", "ok")),
            revision=str(value.get("revision", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["budget_bonus"] = {
            "private": value.pop("private_bonus"),
            "group": value.pop("group_bonus"),
        }
        return value


@dataclass(slots=True, frozen=True)
class ScheduleRequirement:
    """Persisted instruction applied once per date in an inclusive range."""

    id: str
    persona_id: str
    start_date: str
    end_date: str
    requirement: str
    created_at: str
    consumed_dates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        start = date.fromisoformat(self.start_date)
        end = date.fromisoformat(self.end_date)
        if not self.id or not self.persona_id:
            raise ValueError("requirement id and persona_id are required")
        if end < start:
            raise ValueError("requirement end_date must not precede start_date")
        if not self.requirement:
            raise ValueError("schedule requirement is required")
        if len(self.requirement) > 500:
            raise ValueError("schedule requirement must not exceed 500 characters")
        if len(set(self.consumed_dates)) != len(self.consumed_dates):
            raise ValueError("consumed schedule requirement dates must be unique")
        for value in self.consumed_dates:
            consumed = date.fromisoformat(value)
            if not start <= consumed <= end:
                raise ValueError("consumed date must be inside the requirement range")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ScheduleRequirement:
        return cls(
            id=str(value.get("id", "")).strip(),
            persona_id=str(value.get("persona_id", "")).strip(),
            start_date=str(value.get("start_date", "")).strip(),
            end_date=str(value.get("end_date", "")).strip(),
            requirement=str(value.get("requirement", "")).strip(),
            created_at=str(value.get("created_at", "")).strip(),
            consumed_dates=tuple(str(item) for item in value.get("consumed_dates", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SessionState:
    date: str
    persona_id: str = "default"
    daily_budget: int = 0
    sent_count: int = 0
    unanswered_count: int = 0
    last_user_message_at: str = ""
    last_proactive_at: str = ""
    sleep_drawn: bool = False
    sleep_selected: bool = False

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> SessionState:
        allowed = {item.name for item in fields(cls)}
        return cls(**{key: value[key] for key in allowed if key in value})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
