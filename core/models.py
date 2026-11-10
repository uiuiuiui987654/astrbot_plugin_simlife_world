"""Plan data: timeline segments, proactive windows, outfit, weather and the daily plan.

Every class validates itself on construction, so a ``DailyPlan`` that exists is
always usable. ``from_dict`` / ``to_dict`` define the on-disk JSON format of
``plans.json`` and ``sessions.json`` — field names and order must not change.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, fields
from datetime import date, time
from typing import Any, Literal

State = Literal["sleep", "busy", "focus", "transit", "available", "social"]
Availability = Literal["blocked", "low", "normal", "high"]
Audience = Literal["private", "group", "both"]

STATES = frozenset(State.__args__)
AVAILABILITIES = frozenset(Availability.__args__)
AUDIENCES = frozenset(Audience.__args__)

# category -> Chinese label (also the set of valid categories)
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
OUTFIT_CATEGORIES = frozenset(OUTFIT_CATEGORY_LABELS)
# names models tend to invent, mapped onto a real category
OUTFIT_CATEGORY_ALIASES = {
    **dict.fromkeys(
        ("hair_accessory", "hair-accessory", "hair accessories", "hair_accessories", "hairpin", "hair_pin",
         "hair_bow", "hairclip", "hair_clip"),
        "headwear",
    ),
    **dict.fromkeys(("earring", "earrings", "jewellery", "jewelry", "necklace"), "accessory"),
}
REQUIRED_OUTFIT_PARTS = ("hairstyle", "underwear", "underpants", "shoes")


def _clean(value: Any) -> str:
    return str(value).strip()


_HHMM = re.compile(r"([01]\d|2[0-3]):([0-5]\d)")


def parse_hhmm(value: str, *, allow_2400: bool = False) -> time:
    """Strict zero-padded ``HH:MM``; ``24:00`` (end of day) only when allowed."""
    if allow_2400 and value == "24:00":
        return time.max
    if not isinstance(value, str) or not value:
        raise ValueError("expected a non-empty HH:MM time")
    match = _HHMM.fullmatch(value)
    if match is None:
        raise ValueError(f"not a valid HH:MM time: {value!r}")
    return time(int(match[1]), int(match[2]))


def minute_of_day(value: str) -> int:
    if value == "24:00":
        return 24 * 60
    moment = parse_hhmm(value)
    return moment.hour * 60 + moment.minute


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
        if not (self.id and self.activity):
            raise ValueError("every timeline segment needs an id and an activity")
        if self.state not in STATES:
            raise ValueError(f"unknown state {self.state!r}")
        if self.availability not in AVAILABILITIES:
            raise ValueError(f"unknown availability {self.availability!r}")
        if minute_of_day(self.start) >= minute_of_day(self.end):
            raise ValueError("a timeline segment must end after it starts")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> TimelineItem:
        raw_people = value.get("participant_ids", [])
        people = (_clean(person) for person in (raw_people if isinstance(raw_people, list) else [])[:20])
        return cls(
            id=_clean(value.get("id", "")),
            start=_clean(value.get("start", "")),
            end=_clean(value.get("end", "")),
            activity=_clean(value.get("activity", "")),
            location=_clean(value.get("location", "")),
            state=str(value.get("state", "available")),
            availability=str(value.get("availability", "normal")),
            participant_ids=tuple(dict.fromkeys(person for person in people if person)),
        )


@dataclass(slots=True, frozen=True)
class ProactiveWindow:
    id: str
    at: str
    intent: str
    audience: Audience = "both"
    source_item_id: str = ""

    def __post_init__(self) -> None:
        if not (self.id and self.intent):
            raise ValueError("every proactive window needs an id and an intent")
        parse_hhmm(self.at)
        if self.audience not in AUDIENCES:
            raise ValueError(f"unknown audience {self.audience!r}")
        if not self.source_item_id:
            raise ValueError("a proactive window must name its source_item_id")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ProactiveWindow:
        return cls(
            id=_clean(value.get("id", "")),
            at=_clean(value.get("at", "")),
            intent=_clean(value.get("intent", "")),
            audience=str(value.get("audience", "both")),
            source_item_id=_clean(value.get("source_item_id", "")),
        )


@dataclass(slots=True, frozen=True)
class OutfitItem:
    category: str
    name: str
    details: str = ""

    def __post_init__(self) -> None:
        key = self.category.strip().lower()
        category = OUTFIT_CATEGORY_ALIASES.get(key) or key
        if category not in OUTFIT_CATEGORIES:
            raise ValueError(f"unknown outfit category {self.category!r}")
        if not self.name:
            raise ValueError("every outfit item needs a name")
        object.__setattr__(self, "category", category)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> OutfitItem:
        return cls(
            category=_clean(value.get("category", "")),
            name=_clean(value.get("name", "")),
            details=_clean(value.get("details", "")),
        )


@dataclass(slots=True, frozen=True)
class Outfit:
    summary: str
    items: tuple[OutfitItem, ...]
    style: str = "未记录"

    def __post_init__(self) -> None:
        if not self.summary:
            raise ValueError("the outfit needs a summary")

    def validate_complete(self) -> None:
        """A wearable outfit: the basics, a main garment, and a bottom unless it is a dress."""
        present = {item.category for item in self.items}
        missing = next((part for part in REQUIRED_OUTFIT_PARTS if part not in present), None)
        if missing:
            raise ValueError(f"the outfit is missing the {missing} category")
        if present.isdisjoint({"top", "dress", "other"}):
            raise ValueError("the outfit needs a main garment: top, dress or other")
        if "dress" not in present and "bottom" not in present:
            raise ValueError("an outfit without a dress needs a bottom")

    @classmethod
    def from_dict(cls, value: object) -> Outfit:
        if not isinstance(value, dict):
            raise ValueError("the outfit must be a JSON object")
        pieces = value.get("items")
        if not isinstance(pieces, list):
            raise ValueError("outfit items must be a list")
        if not all(isinstance(piece, dict) for piece in pieces):
            raise ValueError("each outfit item must be a JSON object")
        return cls(
            summary=_clean(value.get("summary", "")),
            items=tuple(OutfitItem.from_dict(piece) for piece in pieces),
            style=_clean(value.get("style", "")) or "未记录",
        )


# --------------------------------------------------------------------- weather

# condition -> (low adjustment, high adjustment, note)
WEATHER_KINDS: dict[str, tuple[int, int, str]] = {
    "晴朗": (1, 2, "阳光充足，适合外出"),
    "多云": (0, 0, "云量较多，光线柔和"),
    "阴天": (-1, 0, "天色偏灰，体感偏凉"),
    "小雨": (-2, -1, "有间歇小雨，出门记得带伞"),
    "雷阵雨": (-2, 0, "午后可能有雷阵雨，尽量减少户外停留"),
    "大风": (-3, -1, "风力较大，注意保暖"),
    "寒冷": (-4, -2, "气温偏低，注意保暖"),
    "闷热": (2, 3, "湿度较高，体感闷热"),
    "微风": (0, 1, "有微风，体感舒适"),
    "凉爽": (-1, 0, "天气凉爽，体感舒适"),
}
# season -> (base low, base high, conditions cycled day by day)
SEASONS: dict[str, tuple[int, int, tuple[str, ...]]] = {
    "春": (12, 22, ("晴朗", "多云", "微风", "小雨", "阴天")),
    "夏": (24, 33, ("晴朗", "闷热", "雷阵雨", "多云", "微风")),
    "秋": (15, 24, ("晴朗", "凉爽", "多云", "微风", "小雨")),
    "冬": (3, 12, ("晴朗", "阴天", "大风", "寒冷", "小雨")),
}
# kept for callers that read the tables separately
SEASON_WEATHER_POOLS = {season: pool for season, (_, _, pool) in SEASONS.items()}
SEASON_TEMPERATURES = {season: (low, high) for season, (low, high, _) in SEASONS.items()}
WEATHER_TEMP_DELTAS = {name: (low, high) for name, (low, high, _) in WEATHER_KINDS.items()}
WEATHER_DESCRIPTIONS = {name: note for name, (_, _, note) in WEATHER_KINDS.items()}


@dataclass(slots=True, frozen=True)
class Weather:
    condition: str
    temperature_low: int
    temperature_high: int
    description: str = ""

    def __post_init__(self) -> None:
        if not self.condition:
            raise ValueError("weather needs a condition")
        for name in ("temperature_low", "temperature_high"):
            if not -30 <= getattr(self, name) <= 45:
                raise ValueError(f"weather {name} must be between -30 and 45")
        if self.temperature_low > self.temperature_high:
            raise ValueError("weather temperature_low is above temperature_high")
        if len(self.description) > 160:
            raise ValueError("weather description is longer than 160 characters")

    @property
    def label(self) -> str:
        return f"{self.condition} {self.temperature_low}~{self.temperature_high}°C"

    @property
    def prompt_text(self) -> str:
        return f"{self.label}，{self.description}" if self.description else self.label

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Weather:
        if not isinstance(value, dict):
            raise ValueError("weather must be a JSON object")
        return cls(
            condition=_clean(value.get("condition", "")),
            temperature_low=int(value.get("temperature_low", value.get("low", 18))),
            temperature_high=int(value.get("temperature_high", value.get("high", 25))),
            description=_clean(value.get("description", "")),
        )


SEASON_OF_MONTH = ("冬", "冬", "春", "春", "春", "夏", "夏", "夏", "秋", "秋", "秋", "冬")


def season_for_date(target: date) -> str:
    return SEASON_OF_MONTH[target.month - 1]


def weather_for_date(target: date) -> Weather:
    """Default weather when none was generated: cycles through the season's conditions."""
    base_low, base_high, pool = SEASONS[season_for_date(target)]
    condition = pool[target.toordinal() % len(pool)]
    shift_low, shift_high, note = WEATHER_KINDS.get(condition, (0, 0, ""))
    high = base_high + shift_high
    return Weather(condition, min(base_low + shift_low, high), high, note)


# ----------------------------------------------------------------- daily plan


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
        day = date.fromisoformat(self.date)
        if self.weather is None:
            object.__setattr__(self, "weather", weather_for_date(day))
        if not self.persona_id:
            raise ValueError("a plan needs a persona_id")
        if self.status == "ok" and self.outfit is not None:
            self.outfit.validate_complete()
        self._check_timeline()
        if self.status == "ok" and self.timeline:
            if (self.timeline[0].start, self.timeline[-1].end) != ("00:00", "24:00"):
                raise ValueError("the timeline must run from 00:00 to 24:00")
            self._check_windows()
        elif self.proactive_windows:
            raise ValueError("proactive windows need a schedule to attach to")

    def _check_timeline(self) -> None:
        cursor, seen = 0, set()
        for item in self.timeline:
            begin = minute_of_day(item.start)
            if seen and begin != cursor:
                raise ValueError("timeline segments must follow each other without gaps or overlaps")
            if begin < cursor:
                raise ValueError("timeline segments are out of order or overlap")
            if item.id in seen:
                raise ValueError("two timeline segments share an id")
            cursor = minute_of_day(item.end)
            seen.add(item.id)

    def _check_windows(self) -> None:
        segments = {item.id: item for item in self.timeline}
        seen: set[str] = set()
        for window in self.proactive_windows:
            if window.id in seen:
                raise ValueError("two proactive windows share an id")
            seen.add(window.id)
            source = segments.get(window.source_item_id)
            if source is None:
                raise ValueError("a proactive window points at a timeline segment that does not exist")
            if not minute_of_day(source.start) <= minute_of_day(window.at) < minute_of_day(source.end):
                raise ValueError("a proactive window time must fall inside its source segment")

    @property
    def has_schedule(self) -> bool:
        return self.status == "ok" and bool(self.timeline)

    @property
    def has_outfit(self) -> bool:
        return self.status == "ok" and self.outfit is not None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> DailyPlan:
        bonus = value.get("budget_bonus") or {}
        weather, outfit = value.get("weather"), value.get("outfit")
        return cls(
            date=str(value["date"]),
            persona_id=str(value["persona_id"]),
            theme=str(value.get("theme", "日常")),
            mood=str(value.get("mood", "平静")),
            weather=Weather.from_dict(weather) if isinstance(weather, dict) else None,
            outfit=Outfit.from_dict(outfit) if outfit is not None else None,
            timeline=tuple(map(TimelineItem.from_dict, value.get("timeline", []))),
            proactive_windows=tuple(map(ProactiveWindow.from_dict, value.get("proactive_windows", []))),
            private_bonus=int(bonus.get("private", value.get("private_bonus", 0))),
            group_bonus=int(bonus.get("group", value.get("group_bonus", 0))),
            status=str(value.get("status", "ok")),
            revision=str(value.get("revision", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["budget_bonus"] = {"private": data.pop("private_bonus"), "group": data.pop("group_bonus")}
        return data


@dataclass(slots=True, frozen=True)
class ScheduleRequirement:
    """An admin instruction applied once to every plan generated in [start_date, end_date]."""

    id: str
    persona_id: str
    start_date: str
    end_date: str
    requirement: str
    created_at: str
    consumed_dates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        first, last = date.fromisoformat(self.start_date), date.fromisoformat(self.end_date)
        if not (self.id and self.persona_id):
            raise ValueError("a schedule requirement needs an id and a persona_id")
        if last < first:
            raise ValueError("a schedule requirement ends before it starts")
        if not self.requirement:
            raise ValueError("a schedule requirement needs text")
        if len(self.requirement) > 500:
            raise ValueError("a schedule requirement is longer than 500 characters")
        if len(set(self.consumed_dates)) != len(self.consumed_dates):
            raise ValueError("a schedule requirement lists a used date twice")
        if any(not first <= date.fromisoformat(day) <= last for day in self.consumed_dates):
            raise ValueError("a used date lies outside the requirement range")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ScheduleRequirement:
        return cls(
            **{key: _clean(value.get(key, "")) for key in ("id", "persona_id", "start_date", "end_date", "requirement", "created_at")},
            consumed_dates=tuple(str(day) for day in value.get("consumed_dates", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SessionState:
    """Per-chat proactive-message counters for one day (sessions.json)."""

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
        known = {item.name for item in fields(cls)}
        return cls(**{key: item for key, item in value.items() if key in known})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
