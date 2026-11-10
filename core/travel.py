"""Multi-day travel planning for the virtual life schedule.

The module keeps a small ``trips.json`` store next to the plugin data and turns
each trip into a phase (countdown, eve, depart, away, return, afterglow) that the
daily schedule generator can inject into its prompt.  Timeline locations are
normalised afterwards so an away-from-home day never falls back to a bedroom in
the character's own flat.
"""

from __future__ import annotations

import hashlib
import json
import random
import threading
from dataclasses import asdict, dataclass, replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from .jsonio import atomic_write_json

SCHEMA_VERSION = 1

PHASES = ("none", "countdown", "eve", "depart", "away", "return", "afterglow")
AWAY_PHASES = ("depart", "away", "return")

HOME_ROOMS = ('客厅', '浴室', '厨房', '餐厅', '健身室', '阳台', '玄关', '卧室', '衣帽间', '书房', '画室', '影音室', '露台', '楼梯厅', '车库')
HOME_WORDS = ("家", "在家", "家里", "家中", "自己家", "宅家")
TRANSIT_WORDS = (
    "机场",
    "高铁",
    "动车",
    "火车",
    "车站",
    "飞机",
    "航班",
    "大巴",
    "长途",
    "高速",
    "服务区",
    "登机",
    "值机",
    "安检",
    "海关",
    "边检",
    "地铁",
    "打车",
    "路上",
)
LODGING_WORDS = ("住处", "酒店", "民宿", "旅馆", "客栈", "公寓", "青旅", "别墅")

TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "海": ("海", "潜水", "冲浪", "沙滩", "岛", "海鲜"),
    "湖": ("湖", "水", "安静", "发呆"),
    "山": ("山", "徒步", "爬山", "自然"),
    "自然": ("自然", "徒步", "极光", "雪山", "风景"),
    "古城": ("古", "历史", "老城", "遗迹"),
    "历史": ("历史", "古", "博物馆", "文物"),
    "寺": ("寺", "庙", "参拜", "神社"),
    "美食": ("吃", "美食", "料理", "探店", "小吃"),
    "小吃": ("小吃", "夜市", "路边摊"),
    "慢": ("慢", "发呆", "安静", "咖啡", "散步"),
    "都市": ("都市", "城市", "购物", "逛街", "咖啡"),
    "购物": ("购物", "逛街", "买"),
    "艺术": ("艺术", "画", "展", "设计", "博物"),
    "建筑": ("建筑", "房子", "街"),
    "茶": ("茶",),
    "温泉": ("温泉", "泡汤"),
    "度假": ("度假", "躺", "休息"),
    "冰雪": ("雪", "冰", "冬"),
    "热带": ("热", "海", "夏"),
    "公路": ("自驾", "公路", "开车"),
    "文艺": ("文艺", "拍照", "手账"),
    "夜生活": ("夜", "酒", "宵夜"),
    "熊猫": ("熊猫", "动物"),
    "异域": ("异国", "外"),
    "评弹": ("曲", "戏", "音乐"),
    "园林": ("园", "庭院"),
    "江南": ("江南", "水乡"),
    "戈壁": ("沙漠", "戈壁", "荒"),
    "山水": ("山", "水", "江"),
}

DEFAULT_SETTINGS: dict[str, Any] = {
    "enable": True,
    "auto_plan": True,
    "chance_per_day": 0.07,
    "min_gap_days": 45,
    "lead_days": 18,
    "min_days": 2,
    "max_days": 7,
    "allow_overseas": True,
    "overseas_ratio": 0.4,
    "afterglow_days": 2,
    "require_city_prefix": True,
    "countdown_days": 14,
}

SEASONS = {
    "spring": ("春", (3, 4, 5)),
    "summer": ("夏", (6, 7, 8)),
    "autumn": ("秋", (9, 10, 11)),
    "winter": ("冬", (12, 1, 2)),
}


def season_of(target: date) -> str:
    """Return the Chinese season name for a date."""
    month = target.month
    if month in (3, 4, 5):
        return "春"
    if month in (6, 7, 8):
        return "夏"
    if month in (9, 10, 11):
        return "秋"
    return "冬"


def _unit(seed: str) -> float:
    """Deterministic float in [0, 1) derived from a seed string."""
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / float(0x100000000)


def _randint(seed: str, low: int, high: int) -> int:
    if high <= low:
        return low
    return low + int(_unit(seed) * (high - low + 1)) % (high - low + 1)


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, payload)


def _as_int(value: Any, default: int, low: int = 0, high: int = 9999) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def _as_float(value: Any, default: float, low: float = 0.0, high: float = 1.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "开", "是"}


def is_home_location(location: str) -> bool:
    text = str(location or "").strip()
    if not text:
        return False
    # 日程里常直接写「家」「家里」；「农家乐」「家具店」这类不算
    if text in HOME_WORDS or text.startswith(("家·", "家里", "家中")):
        return True
    return any(room in text for room in HOME_ROOMS)


def is_transit_location(location: str) -> bool:
    text = str(location or "").strip()
    return any(word in text for word in TRANSIT_WORDS)


def is_lodging_location(location: str) -> bool:
    text = str(location or "").strip()
    return any(word in text for word in LODGING_WORDS)


@dataclass(slots=True, frozen=True)
class TripDay:
    """One day of a trip itinerary."""

    date: str
    title: str
    highlights: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "title": self.title,
            "highlights": list(self.highlights),
        }

    @classmethod
    def from_dict(cls, value: Any) -> TripDay | None:
        if not isinstance(value, dict):
            return None
        try:
            day = str(value.get("date") or "").strip()
            date.fromisoformat(day)
        except (TypeError, ValueError):
            return None
        raw = value.get("highlights", [])
        highlights = (
            tuple(str(item).strip() for item in raw if str(item).strip())
            if isinstance(raw, list)
            else ()
        )
        return cls(
            date=day,
            title=str(value.get("title") or "").strip(),
            highlights=highlights,
        )


@dataclass(slots=True, frozen=True)
class Trip:
    """A planned or finished multi-day trip."""

    id: str
    persona_id: str
    destination_key: str
    city: str
    country: str
    region: str
    transport: str
    depart: str
    back: str
    lodging: str
    days: int = 0
    style: str = ""
    budget_level: str = "comfortable"
    source: str = "auto"
    status: str = "planned"
    created_at: str = ""
    notes: str = ""
    itinerary: tuple[TripDay, ...] = ()
    packing: tuple[str, ...] = ()
    foods: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        start = date.fromisoformat(self.depart)
        end = date.fromisoformat(self.back)
        if end < start:
            raise ValueError("trip return date must not precede depart date")

    @property
    def depart_date(self) -> date:
        return date.fromisoformat(self.depart)

    @property
    def back_date(self) -> date:
        return date.fromisoformat(self.back)

    @property
    def length(self) -> int:
        return (self.back_date - self.depart_date).days + 1

    @property
    def overseas(self) -> bool:
        return self.region == "overseas"

    def day(self, target: date) -> TripDay | None:
        key = target.isoformat()
        return next((item for item in self.itinerary if item.date == key), None)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["itinerary"] = [item.to_dict() for item in self.itinerary]
        value["packing"] = list(self.packing)
        value["foods"] = list(self.foods)
        return value

    @classmethod
    def from_dict(cls, value: Any) -> Trip | None:
        if not isinstance(value, dict):
            return None
        try:
            itinerary = tuple(
                day
                for day in (
                    TripDay.from_dict(item) for item in value.get("itinerary", [])
                )
                if day is not None
            )
            trip = cls(
                id=str(value.get("id") or "").strip(),
                persona_id=str(value.get("persona_id") or "default").strip()
                or "default",
                destination_key=str(value.get("destination_key") or "").strip(),
                city=str(value.get("city") or "").strip(),
                country=str(value.get("country") or "").strip(),
                region=str(value.get("region") or "domestic").strip(),
                transport=str(value.get("transport") or "高铁").strip(),
                depart=str(value.get("depart") or "").strip(),
                back=str(value.get("back") or "").strip(),
                lodging=str(value.get("lodging") or "").strip(),
                days=_as_int(value.get("days"), 0, 0, 60),
                style=str(value.get("style") or "").strip(),
                budget_level=str(value.get("budget_level") or "comfortable").strip(),
                source=str(value.get("source") or "auto").strip(),
                status=str(value.get("status") or "planned").strip(),
                created_at=str(value.get("created_at") or "").strip(),
                notes=str(value.get("notes") or "").strip(),
                itinerary=itinerary,
                packing=tuple(
                    str(item).strip()
                    for item in value.get("packing", [])
                    if str(item).strip()
                ),
                foods=tuple(
                    str(item).strip()
                    for item in value.get("foods", [])
                    if str(item).strip()
                ),
            )
        except (TypeError, ValueError):
            return None
        if not trip.id or not trip.city:
            return None
        return trip


class TravelService:
    """Persist trips and expose phase-aware prompt and validation helpers."""

    def __init__(self, data_dir: Path | None, catalog_path: Path):
        self.data_dir = Path(data_dir) if data_dir else None
        self.catalog_path = Path(catalog_path)
        self.lock = threading.RLock()
        self._catalog: list[dict[str, Any]] | None = None
        self._trips: list[Trip] | None = None

    # ------------------------------------------------------------------ config

    @staticmethod
    def settings(raw: dict[str, Any] | None) -> dict[str, Any]:
        """Merge the user configuration with the defaults."""
        merged = dict(DEFAULT_SETTINGS)
        if isinstance(raw, dict):
            merged.update({key: value for key, value in raw.items() if value is not None})
        merged["enable"] = _as_bool(merged.get("enable"), True)
        merged["auto_plan"] = _as_bool(merged.get("auto_plan"), True)
        merged["allow_overseas"] = _as_bool(merged.get("allow_overseas"), True)
        merged["require_city_prefix"] = _as_bool(
            merged.get("require_city_prefix"), True
        )
        merged["chance_per_day"] = _as_float(
            merged.get("chance_per_day"), 0.07, 0.0, 1.0
        )
        merged["overseas_ratio"] = _as_float(
            merged.get("overseas_ratio"), 0.4, 0.0, 1.0
        )
        merged["min_gap_days"] = _as_int(merged.get("min_gap_days"), 45, 0, 3650)
        merged["lead_days"] = _as_int(merged.get("lead_days"), 18, 0, 365)
        merged["min_days"] = _as_int(merged.get("min_days"), 2, 1, 30)
        merged["max_days"] = _as_int(merged.get("max_days"), 7, 1, 30)
        if merged["max_days"] < merged["min_days"]:
            merged["max_days"] = merged["min_days"]
        merged["afterglow_days"] = _as_int(merged.get("afterglow_days"), 2, 0, 14)
        merged["countdown_days"] = _as_int(merged.get("countdown_days"), 14, 0, 60)
        return merged

    # ------------------------------------------------------------------ catalog

    def catalog(self) -> list[dict[str, Any]]:
        with self.lock:
            if self._catalog is None:
                payload = _read_json(self.catalog_path, {})
                items = (
                    payload.get("destinations", [])
                    if isinstance(payload, dict)
                    else []
                )
                self._catalog = [
                    item
                    for item in items
                    if isinstance(item, dict) and item.get("name")
                ]
            return self._catalog

    def destination(self, key_or_name: str) -> dict[str, Any] | None:
        text = str(key_or_name or "").strip()
        if not text:
            return None
        lowered = text.lower()
        for item in self.catalog():
            if str(item.get("key") or "").lower() == lowered:
                return item
            if str(item.get("name") or "") == text:
                return item
            if text and text in str(item.get("name") or ""):
                return item
        return None

    def destination_names(self) -> list[str]:
        return [str(item.get("name") or "") for item in self.catalog()]

    # ------------------------------------------------------------------ storage

    def path(self) -> Path | None:
        if self.data_dir is None:
            return None
        return self.data_dir / "trips.json"

    def load(self) -> list[Trip]:
        with self.lock:
            if self._trips is not None:
                return list(self._trips)
            path = self.path()
            payload = _read_json(path, {}) if path else {}
            raw = payload.get("trips", []) if isinstance(payload, dict) else []
            trips: list[Trip] = []
            for item in raw:
                trip = Trip.from_dict(item)
                if trip is not None:
                    trips.append(trip)
            trips.sort(key=lambda item: item.depart)
            self._trips = trips
            return list(self._trips)

    def save(self, trips: list[Trip] | None = None) -> None:
        with self.lock:
            if self._trips is None or trips is not None:
                self._trips = list(trips or self._trips or [])
            path = self.path()
            if path is None:
                return
            self._trips.sort(key=lambda item: item.depart)
            _write_json(
                path,
                {
                    "schema_version": SCHEMA_VERSION,
                    "updated_at": date.today().isoformat(),
                    "trips": [item.to_dict() for item in self._trips],
                },
            )

    def trips_for(self, persona_id: str) -> list[Trip]:
        return [item for item in self.load() if item.persona_id == persona_id]

    # ------------------------------------------------------------------- phase

    def phase(self, trip: Trip | None, target: date, settings: dict | None = None) -> str:
        if trip is None:
            return "none"
        config = self.settings(settings)
        depart = trip.depart_date
        back = trip.back_date
        if target < depart:
            gap = (depart - target).days
            if gap == 1:
                return "eve"
            if gap <= config["countdown_days"]:
                return "countdown"
            return "none"
        if target == depart:
            return "depart"
        if depart < target < back:
            return "away"
        if target == back:
            return "return"
        gap = (target - back).days
        if 0 < gap <= config["afterglow_days"]:
            return "afterglow"
        return "none"

    def covering(
        self, persona_id: str, target: date, settings: dict | None = None
    ) -> tuple[Trip, str] | None:
        """Return the trip that flavours ``target`` and its phase."""
        config = self.settings(settings)
        candidates = [
            trip
            for trip in self.trips_for(persona_id)
            if trip.status not in {"cancelled"}
            and trip.depart_date - timedelta(days=config["countdown_days"])
            <= target
            <= trip.back_date + timedelta(days=config["afterglow_days"])
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item.depart_date, item.id))
        for trip in candidates:
            phase = self.phase(trip, target, config)
            if phase != "none":
                return trip, phase
        return None

    def current(self, persona_id: str, target: date) -> Trip | None:
        found = self.covering(persona_id, target)
        return found[0] if found else None

    def upcoming(self, persona_id: str, target: date) -> Trip | None:
        future = [
            trip
            for trip in self.trips_for(persona_id)
            if trip.status in {"planned", "active"} and trip.back_date >= target
        ]
        future.sort(key=lambda item: item.depart_date)
        return future[0] if future else None

    # --------------------------------------------------------------- auto plan

    def ensure(
        self,
        persona_id: str,
        target: date,
        persona_prompt: str = "",
        *,
        holiday: str = "",
        settings: dict | None = None,
    ) -> tuple[Trip, str] | None:
        """Return the trip covering ``target``, planning a new one when due."""
        config = self.settings(settings)
        if not config["enable"]:
            return None
        with self.lock:
            found = self.covering(persona_id, target, config)
            if found is not None:
                return found
            if not config["auto_plan"]:
                return None
            trips = self.load()
            existing = [item for item in trips if item.persona_id == persona_id]
            active = [
                item
                for item in existing
                if item.status in {"planned", "active"} and item.back_date >= target
            ]
            if active:
                return None
            past = [
                item
                for item in existing
                if item.status != "cancelled" and item.back_date < target
            ]
            if past:
                latest = max(item.back_date for item in past)
                if (target - latest).days < config["min_gap_days"]:
                    return None
            chance = config["chance_per_day"] * (2.5 if holiday else 1.0)
            if _unit(f"{persona_id}|{target.isoformat()}|trip-plan") >= chance:
                return None
            trip = self._build_trip(
                persona_id,
                target,
                persona_prompt,
                config,
                holiday=holiday,
                source="auto",
            )
            if trip is None:
                return None
            trips.append(trip)
            self._trips = trips
            self.save()
            return trip, self.phase(trip, target, config)

    def _pick_destination(
        self,
        target: date,
        persona_prompt: str,
        config: dict[str, Any],
        seed: str,
    ) -> dict[str, Any] | None:
        catalog = self.catalog()
        if not catalog:
            return None
        rng = random.Random(seed)
        domestic = [item for item in catalog if item.get("region") != "overseas"]
        overseas = [item for item in catalog if item.get("region") == "overseas"]
        pools: list[list[dict[str, Any]]] = []
        if domestic:
            pools.append(domestic)
        if overseas and config["allow_overseas"]:
            pools.append(overseas)
        if not pools:
            pools = [catalog]
        chosen_pool = pools[0]
        if len(pools) > 1:
            if _unit(seed + "|region") < config["overseas_ratio"]:
                chosen_pool = pools[1]
            else:
                chosen_pool = pools[0]
        season = season_of(target)
        text = str(persona_prompt or "")
        scored: list[tuple[float, dict[str, Any]]] = []
        for item in chosen_pool:
            score = 1.0
            for tag in item.get("tags", []) or []:
                for keyword in TAG_KEYWORDS.get(str(tag), ()):  # persona affinity
                    if keyword and keyword in text:
                        score += 1.4
                        break
            seasons = [str(value) for value in item.get("seasons", [])]
            score += 1.6 if season in seasons else -0.7
            scored.append((max(0.15, score), item))
        total = sum(weight for weight, _ in scored)
        roll = rng.random() * total
        for weight, item in scored:
            roll -= weight
            if roll <= 0:
                return item
        return scored[-1][1] if scored else None

    def _build_trip(
        self,
        persona_id: str,
        target: date,
        persona_prompt: str,
        config: dict[str, Any],
        *,
        holiday: str = "",
        source: str = "auto",
        destination: dict[str, Any] | None = None,
        depart: date | None = None,
        days: int | None = None,
        align_weekend: bool = True,
    ) -> Trip | None:
        seed = f"{persona_id}|{target.isoformat()}|trip-build"
        destination = destination or self._pick_destination(
            depart or target, persona_prompt, config, seed
        )
        if destination is None:
            return None
        name = str(destination.get("name") or "").strip()
        if not name:
            return None
        start = depart or (target + timedelta(days=max(0, config["lead_days"])))
        min_days = _as_int(destination.get("min_days"), 2, 1, 30)
        max_days = _as_int(destination.get("max_days"), min_days, min_days, 30)
        length = days if days is not None else _randint(
            seed + "|days", min_days, max_days
        )
        low = max(1, config["min_days"])
        high = max(low, config["max_days"])
        length = max(low, min(high, int(length)))
        if (
            align_weekend
            and str(destination.get("region")) == "domestic"
            and length <= 4
            and start.weekday() < 4
        ):
            start = start + timedelta(days=4 - start.weekday())
        back = start + timedelta(days=length - 1)
        lodging = str(
            random.Random(seed + "|lodging").choice(
                list(destination.get("lodging") or [f"{name}的住处"])
            )
        )
        foods = tuple(str(item) for item in destination.get("foods", []) or [])
        packing = tuple(str(item) for item in destination.get("packing", []) or [])
        itinerary = self._itinerary(destination, start, length, seed, lodging)
        trip_id = f"trip-{start:%Y%m%d}-{destination.get('key') or name}"
        existing_ids = {item.id for item in self.load()}
        suffix = 1
        base_id = trip_id
        while trip_id in existing_ids:
            suffix += 1
            trip_id = f"{base_id}-{suffix}"
        return Trip(
            id=trip_id,
            persona_id=persona_id,
            destination_key=str(destination.get("key") or ""),
            city=name,
            country=str(destination.get("country") or ""),
            region=str(destination.get("region") or "domestic"),
            transport=str(destination.get("transport") or "高铁"),
            depart=start.isoformat(),
            back=back.isoformat(),
            lodging=lodging,
            days=length,
            style=",".join(str(item) for item in destination.get("tags", []) or []),
            budget_level="comfortable",
            source=source,
            status="planned",
            created_at=target.isoformat(),
            notes=holiday.strip(),
            itinerary=itinerary,
            packing=packing,
            foods=foods,
        )

    def _itinerary(
        self,
        destination: dict[str, Any],
        depart: date,
        days: int,
        seed: str,
        lodging: str,
    ) -> tuple[TripDay, ...]:
        name = str(destination.get("name") or "")
        transport = str(destination.get("transport") or "高铁")
        pool = [str(item) for item in destination.get("highlights", []) or []]
        rng = random.Random(seed + "|itinerary")
        rng.shuffle(pool)
        foods = [str(item) for item in destination.get("foods", []) or []]
        first: list[str] = [f"坐{transport}到{name}", f"入住{lodging}"]
        if pool:
            first.append(pool.pop(0))
        if foods:
            first.append(f"吃{foods[0]}")
        itinerary = [
            TripDay(
                date=depart.isoformat(),
                title=f"出发 · 抵达{name}",
                highlights=tuple(first),
            )
        ]
        if days <= 1:
            return tuple(itinerary)
        middle = max(0, days - 2)
        for index in range(middle):
            picks: list[str] = []
            for _ in range(2):
                if pool:
                    picks.append(pool.pop(0))
            if foods:
                picks.append("吃" + foods[(index + 1) % len(foods)])
            itinerary.append(
                TripDay(
                    date=(depart + timedelta(days=1 + index)).isoformat(),
                    title=f"{name}第{index + 2}天",
                    highlights=tuple(picks),
                )
            )
        last: list[str] = ["退房"]
        if pool:
            last.append(pool.pop(0))
        last.append(f"坐{transport}返程")
        itinerary.append(
            TripDay(
                date=(depart + timedelta(days=days - 1)).isoformat(),
                title=f"返程 · 离开{name}",
                highlights=tuple(last),
            )
        )
        return tuple(itinerary)

    # ------------------------------------------------------------ prompt block

    def prompt_block(
        self,
        trip: Trip,
        phase: str,
        target: date,
        settings: dict | None = None,
    ) -> str:
        if trip is None or phase == "none":
            return ""
        day = trip.day(target)
        highlights = "、".join(day.highlights) if day else ""
        foods = "、".join(trip.foods) or "当地的家常菜"
        packing = "、".join(trip.packing) or "证件、充电器、换洗衣物"
        header = {
            "countdown": f"【旅行计划 · 距离出发还有 {(trip.depart_date - target).days} 天】",
            "eve": f"【明天出发去{trip.city}】",
            "depart": f"【今天出发去{trip.city}】",
            "away": (
                f"【旅行中 · {trip.city} 第 "
                f"{(target - trip.depart_date).days + 1}/{trip.length} 天】"
            ),
            "return": f"【今天从{trip.city}返程】",
            "afterglow": (
                f"【刚结束的{trip.city}之行 · 回来第 "
                f"{(target - trip.back_date).days} 天】"
            ),
        }.get(phase, "")
        lines = [header] if header else []
        if phase == "countdown":
            lines.extend(
                [
                    f"- {trip.depart} 到 {trip.back} 你会去{trip.city}"
                    f"（{trip.country}），住{trip.lodging}，{trip.transport}往返。",
                    "- 今天还不在旅途中，白天照常过；可以自然地把一件和这趟旅行有关的小事"
                    "排进 timeline（查攻略、看游记、订票、列清单、跟朋友说起），最多一项，"
                    "不要占掉大半天。",
                    f"- 不要提前出现在{trip.city}，也不要写“已经在旅行”；"
                    "今天的地点仍然在家或本市场景里。",
                ]
            )
        elif phase == "eve":
            lines.extend(
                [
                    f"- 明天出发去{trip.city}，今晚要收拾行李：{packing}；"
                    "顺便查一下当地天气，把充电器、证件、换洗衣物装好。",
                    "- 晚上安排成“收拾行李 + 早点睡”，不要排太晚的活动。",
                    "- 收拾行李可以写成一项 activity（例如“收拾去"
                    f"{trip.city}的行李”），location 用卧室或客厅。",
                ]
            )
        elif phase == "depart":
            spots = [
                item
                for item in (day.highlights if day else ())
                if trip.transport not in item
                and not item.startswith("入住")
                and not item.startswith("吃")
            ]
            lines.extend(
                [
                    f"- 今天从家出发，坐{trip.transport}去{trip.city}；从出门到上车/登机要留出 2-3 小时。",
                    "- 出发前的时间可以在家：起床、吃早饭、最后检查行李；"
                    f"出发后到入住前，location 必须写成「{trip.city}·机场」"
                    f"「{trip.city}·车站」「{trip.city}·{trip.lodging}」这样的格式。",
                    "- 抵达后先去住处放行李，再安排一个近处的活动"
                    + (f"：{'、'.join(spots)}。" if spots else "。"),
                    f"- 晚饭吃当地的东西：{foods}。",
                    "- 从家到车站/机场要有 40-90 分钟的 transit，长途交通本身也写成 "
                    f"transit（例如“飞往{trip.city}”“坐{trip.transport}去{trip.city}”）。",
                ]
            )
        elif phase == "away":
            lines.extend(
                [
                    f"- 你住在{trip.lodging}，今天全天在{trip.city}，不需要回家。",
                    f"- 今天可用的行程素材：{highlights or '在住处附近随便走走'}。",
                    f"- 所有 location 必须写成「{trip.city}·<具体地点>」；禁止出现家里的房间名"
                    "（卧室、厨房、客厅、书房、浴室、阳台、玄关）。",
                    f"- 三餐都在当地吃，写清菜名：{foods}；不要写在家做饭、买菜、回家。",
                    "- 在城里移动用 transit，停留用 available 或 social；晚上回住处睡。",
                ]
            )
        elif phase == "return":
            lines.extend(
                [
                    f"- 今天从{trip.city}回来：退房、买点伴手礼，坐{trip.transport}返程。",
                    f"- 到家前的 location 用「{trip.city}·…」或「路上」；到家之后可以恢复成"
                    "家里的房间（客厅、卧室）。",
                    "- 晚上会很累：洗澡、收拾行李、随手整理照片，早点睡。",
                    f"- 可以带一点当地的东西回来：{foods}。",
                ]
            )
        elif phase == "afterglow":
            lines.extend(
                [
                    "- 旅行结束了，今天恢复正常生活；可以自然地提到这趟旅行："
                    "整理照片、洗衣服、把带回来的东西分给朋友、写两句游记。",
                    f"- 不要再说自己还在{trip.city}，也不要安排需要长途交通的活动。",
                    f"- 今天的地点写回家里和本市场景，不要再出现「{trip.city}·」开头的地点。",
                    "- 旅行余韵最多占一到两项 activity，其余按平常的节奏过。",
                ]
            )
        lines.append(
            "- 以上旅行安排是事实，不要和它冲突；不确认真实营业时间时，用“大概”“听说”这类说法。"
        )
        return "\n".join(lines)

    # -------------------------------------------------------------- validation

    def apply(
        self,
        plan: Any,
        trip: Trip | None,
        phase: str,
        settings: dict | None = None,
    ) -> tuple[Any, list[str]]:
        """Normalise timeline locations for days spent away from home."""
        config = self.settings(settings)
        if (
            trip is None
            or phase not in AWAY_PHASES
            or not config["require_city_prefix"]
        ):
            return plan, []
        timeline = list(getattr(plan, "timeline", ()) or ())
        if not timeline:
            return plan, []
        city = trip.city
        city_hits = [
            index
            for index, item in enumerate(timeline)
            if city in str(item.location or "")
            or is_transit_location(item.location)
        ]
        if not city_hits:
            if phase != "away":
                return plan, []
            start, end = 0, len(timeline)
        elif phase == "return":
            start, end = 0, city_hits[-1] + 1
        else:
            start, end = city_hits[0], len(timeline)
        changes: list[str] = []
        fixed = timeline
        for index in range(start, end):
            item = fixed[index]
            location = str(item.location or "").strip()
            if not location or city in location:
                continue
            if is_home_location(location):
                new_location = f"{city}·住处"
            elif is_transit_location(location):
                new_location = f"{city}·{location}"
            else:
                new_location = f"{city}·{location}"
            fixed[index] = replace(item, location=new_location)
            changes.append(f"{location}→{new_location}")
        if not changes:
            return plan, []
        return replace(plan, timeline=tuple(fixed)), changes

    # ------------------------------------------------------------------ manual

    def plan(
        self,
        persona_id: str,
        destination_name: str,
        *,
        depart: date | None = None,
        days: int | None = None,
        persona_prompt: str = "",
        today: date | None = None,
        settings: dict | None = None,
        holiday: str = "",
    ) -> tuple[Trip | None, str]:
        """Create a trip from an explicit admin request."""
        config = self.settings(settings)
        if not config["enable"]:
            return None, "旅行功能已关闭，先在配置里打开「旅行与外出过夜」。"
        destination = self.destination(destination_name)
        if destination is None:
            names = "、".join(self.destination_names())
            return None, f"没有找到目的地「{destination_name}」。可选：{names}"
        today = today or date.today()
        start = depart or (today + timedelta(days=max(1, config["lead_days"])))
        if start < today:
            return None, "出发日期不能早于今天。"
        with self.lock:
            trip = self._build_trip(
                persona_id,
                today,
                persona_prompt,
                config,
                holiday=holiday,
                source="admin",
                destination=destination,
                depart=start,
                days=days,
                align_weekend=False,
            )
            if trip is None:
                return None, "没能生成这趟行程，请稍后再试。"
            overlap = [
                item
                for item in self.trips_for(persona_id)
                if item.status in {"planned", "active"}
                and item.depart_date <= trip.back_date
                and item.back_date >= trip.depart_date
            ]
            if overlap:
                other = overlap[0]
                return (
                    None,
                    f"这段时间已经安排了 {other.city}（{other.depart} → {other.back}），"
                    "先取消它再规划新的。",
                )
            trips = self.load()
            trips.append(trip)
            self._trips = trips
            self.save()
            return trip, ""

    def cancel(self, persona_id: str, target: date | None = None) -> Trip | None:
        with self.lock:
            trips = self.load()
            target = target or date.today()
            candidates = [
                item
                for item in trips
                if item.persona_id == persona_id
                and item.status in {"planned", "active"}
                and item.back_date >= target
            ]
            if not candidates:
                return None
            candidates.sort(key=lambda item: item.depart_date)
            chosen = candidates[0]
            updated = [
                replace(item, status="cancelled") if item.id == chosen.id else item
                for item in trips
            ]
            self._trips = updated
            self.save()
            return chosen

    # ------------------------------------------------------------------- text

    def describe(self, trip: Trip, target: date | None = None) -> str:
        """Human readable trip summary for chat commands."""
        lines = [
            f"✈️ {trip.city}（{trip.country}）· {trip.depart} → {trip.back} · "
            f"{trip.length} 天 · {trip.transport}",
            f"住处：{trip.lodging}",
        ]
        if trip.foods:
            lines.append("想吃的：" + "、".join(trip.foods))
        if trip.packing:
            lines.append("要带的：" + "、".join(trip.packing))
        if trip.itinerary:
            lines.append("行程：")
            for day in trip.itinerary:
                detail = "、".join(day.highlights)
                lines.append(f"- {day.date} {day.title}" + (f"：{detail}" if detail else ""))
        if target is not None:
            phase = self.phase(trip, target)
            labels = {
                "countdown": f"还有 {(trip.depart_date - target).days} 天出发",
                "eve": "明天出发",
                "depart": "今天出发",
                "away": f"已出发第 {(target - trip.depart_date).days + 1} 天",
                "return": "今天返程",
                "afterglow": "刚回来",
            }
            if phase in labels:
                lines.insert(0, f"当前状态：{labels[phase]}")
        return "\n".join(lines)

    def destination_list_text(self, region: str | None = None) -> str:
        catalog = self.catalog()
        if not catalog:
            return "目的地库是空的。"
        domestic = [item for item in catalog if item.get("region") != "overseas"]
        overseas = [item for item in catalog if item.get("region") == "overseas"]
        lines = ["✈️ 可选目的地（用「/日程 旅行 规划 <名字> <出发日期> <天数>」安排）"]
        if region != "overseas" and domestic:
            lines.append(
                "国内："
                + "、".join(
                    f"{item['name']}（{item.get('min_days')}-{item.get('max_days')}天，"
                    f"{'/'.join(str(value) for value in item.get('seasons', []))}）"
                    for item in domestic
                )
            )
        if region != "domestic" and overseas:
            lines.append(
                "境外："
                + "、".join(
                    f"{item['name']}（{item.get('min_days')}-{item.get('max_days')}天）"
                    for item in overseas
                )
            )
        return "\n".join(lines)
