"""Shared helpers: tolerant JSON extraction, stable randomness, dates, plan text."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .models import OUTFIT_CATEGORY_LABELS, DailyPlan, TimelineItem, minute_of_day

# ------------------------------------------------------------------ JSON from LLM output

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_TRAILING_COMMA = re.compile(r",\s*([}\]])")


def _as_object(text: str) -> dict | None:
    try:
        value = json.loads(text)
    except (ValueError, TypeError):
        return None
    return value if isinstance(value, dict) else None


@dataclass
class _Scan:
    """Structure of a JSON-ish fragment, ignoring brackets inside strings."""

    closers: list[str] = field(default_factory=list)  # pending "}" / "]" (innermost last)
    in_string: bool = False
    escaped: bool = False
    broken: bool = False  # met a closer with nothing open
    end: int | None = None  # just past the "}" that brings the brace depth back to 0
    cuts: list[int] = field(default_factory=list)  # value boundaries usable for truncation


def _scan(text: str, *, stop_when_balanced: bool = False) -> _Scan:
    state, braces = _Scan(), 0
    for index, char in enumerate(text):
        if state.in_string:
            if state.escaped:
                state.escaped = False
            elif char == "\\":
                state.escaped = True
            elif char == '"':
                state.in_string = False
            continue
        if char == '"':
            state.in_string = True
        elif char == ",":
            state.cuts.append(index)
        elif char in "{[":
            state.closers.append("}" if char == "{" else "]")
            state.cuts.append(index + 1)
            braces += char == "{"
        elif char in "}]":
            if state.closers:
                state.closers.pop()
            else:
                state.broken = True
            if char == "}":
                braces -= 1
                if stop_when_balanced and braces == 0:
                    state.end = index + 1
                    return state
    return state


def _close(text: str) -> str | None:
    """Append whatever closes a truncated fragment; ``None`` if it cannot be closed."""
    state = _scan(text)
    if state.broken:
        return None
    if state.in_string:
        body = (text[:-1] if state.escaped else text) + '"'
    else:
        body = text.rstrip()
        if body.endswith(","):
            body = body[:-1].rstrip()
    return body + "".join(reversed(state.closers))


def _repairs(fragment: str, balanced: bool):
    """Candidate repairs of one fragment, most faithful first, without duplicates."""
    produced: set[str] = set()

    def offer(candidate: str | None):
        for variant in (candidate, _TRAILING_COMMA.sub(r"\1", candidate) if candidate else None):
            if variant and variant not in produced:
                produced.add(variant)
                yield variant

    if balanced:
        yield from offer(fragment)
        return
    yield from offer(_close(fragment))
    for cut in sorted(_scan(fragment).cuts[-10:], reverse=True):
        yield from offer(_close(fragment[:cut]))


def extract_json_object(text: str) -> dict:
    """First usable JSON object in an LLM completion.

    Handles code fences, prose around (or with stray braces before) the object,
    several objects, trailing commas and completions cut off mid-object.
    """
    body = _FENCE.sub("", str(text).strip()).strip().lstrip("﻿​").strip()
    whole = _as_object(body)
    if whole is not None:
        return whole
    starts = [match.start() for match in re.finditer(r"\{", body)]
    if not starts:
        raise ValueError("LLM response does not contain a JSON object")
    decoder = json.JSONDecoder()
    for start in starts:  # valid object somewhere in the text
        try:
            value, _ = decoder.raw_decode(body, start)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    for start in starts:  # otherwise repair the fragment that starts there
        scan = _scan(body[start:], stop_when_balanced=True)
        fragment = body[start : start + scan.end] if scan.end else body[start:]
        for candidate in _repairs(fragment, balanced=scan.end is not None):
            value = _as_object(candidate)
            if value is not None:
                return value
    raise ValueError("unable to parse JSON object")


# ------------------------------------------------------------------ stable randomness


def _hash64(seed: str) -> int:
    return int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:8], "big")


def deterministic_int(seed: str, minimum: int, maximum: int) -> int:
    """Integer in [minimum, maximum] that only depends on ``seed``."""
    if maximum <= minimum:
        return minimum
    return minimum + _hash64(seed) % (maximum - minimum + 1)


def deterministic_probability(seed: str) -> float:
    return _hash64(seed) / float(2**64 - 1)


# ------------------------------------------------------------------ dates


def now_in(timezone: ZoneInfo) -> datetime:
    return datetime.now(timezone)


def parse_datetime(value: str, timezone: ZoneInfo) -> datetime:
    moment = datetime.fromisoformat(value)
    return (moment if moment.tzinfo else moment.replace(tzinfo=timezone)).astimezone(timezone)


_RANGE_HELP = "日期应为 YYYY-MM-DD、MM-DD、DD，或使用 .. 连接的日期区间"


def _date_numbers(text: str) -> list[int]:
    pieces = text.split("-")
    if not 1 <= len(pieces) <= 3 or not all(piece.isdigit() for piece in pieces):
        raise ValueError(_RANGE_HELP)
    return [int(piece) for piece in pieces]


def _next_month(day: date) -> tuple[int, int]:
    return (day.year + 1, 1) if day.month == 12 else (day.year, day.month + 1)


def parse_schedule_date_range(value: str, reference: date) -> tuple[date, date]:
    """``YYYY-MM-DD`` / ``MM-DD`` / ``DD``, optionally ``start..end``.

    Missing parts come from ``reference`` (start) or from the start date (end);
    an end that would fall before the start rolls over to the next year / month.
    """
    ends = [part.strip() for part in str(value).split("..")]
    if len(ends) > 2 or not all(ends):
        raise ValueError(_RANGE_HELP)
    first = _date_numbers(ends[0])
    try:
        start = date(*([reference.year, reference.month][: 3 - len(first)] + first))
    except ValueError as exc:
        raise ValueError(f"无效的开始日期：{ends[0]}") from exc
    if len(ends) == 1:
        return start, start
    last = _date_numbers(ends[1])
    try:
        if len(last) == 3:
            end = date(*last)
        elif len(last) == 2:
            end = date(start.year, *last)
            if end < start:
                end = date(start.year + 1, *last)
        else:
            end = date(start.year, start.month, last[0])
            if end < start:
                end = date(*_next_month(start), last[0])
    except ValueError as exc:
        raise ValueError(f"无效的结束日期：{ends[1]}") from exc
    if end < start:
        raise ValueError("结束日期不能早于开始日期")
    return start, end


def prune_date_keys(values: dict[str, object], keep_days: int, today: date) -> dict[str, object]:
    """Drop ``"YYYY-MM-DD::…"`` keys older than ``keep_days``; keys without a date stay."""
    cutoff = today - timedelta(days=max(1, keep_days))

    def keep(key: str) -> bool:
        try:
            return date.fromisoformat(key.split("::", 1)[0]) >= cutoff
        except ValueError:
            return True

    return {key: value for key, value in values.items() if keep(key)}


# ------------------------------------------------------------------ timeline lookups


def _minute(moment: datetime) -> int:
    return moment.hour * 60 + moment.minute


def timeline_item_at(plan: DailyPlan, moment: datetime) -> TimelineItem | None:
    now = _minute(moment)
    return next(
        (item for item in plan.timeline if minute_of_day(item.start) <= now < minute_of_day(item.end)),
        None,
    )


def next_available_at(plan: DailyPlan, moment: datetime) -> datetime | None:
    """Start of the next later segment where she is awake and reachable."""
    now = _minute(moment)
    for item in plan.timeline:
        if minute_of_day(item.start) > now and item.state != "sleep" and item.availability in ("normal", "high"):
            hour, minute = (int(part) for part in item.start.split(":"))
            return moment.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return None


# ------------------------------------------------------------------ plan as chat text


def _weather_text(plan: DailyPlan) -> str:
    return plan.weather.prompt_text if plan.weather else "未记录"


def _outfit_parts(plan: DailyPlan) -> str:
    return "；".join(f"{OUTFIT_CATEGORY_LABELS[part.category]}：{part.name}" for part in plan.outfit.items)


def _timeline_lines(plan: DailyPlan) -> list[str]:
    return [
        f"- {item.start}-{item.end} {item.activity}" + (f" @ {item.location}" if item.location else "")
        for item in plan.timeline
    ]


def format_plan(plan: DailyPlan, moment: datetime | None = None) -> str:
    if not plan.has_schedule:
        return format_outfit(plan) if plan.has_outfit else f"📅 {plan.date}\n今日没有日程和穿搭。"
    lines = [f"📅 {plan.date} · {plan.theme}", f"💭 心情：{plan.mood}", f"🌤️ 天气：{_weather_text(plan)}"]
    if plan.outfit:
        parts = _outfit_parts(plan)
        lines.append(f"👗 穿搭：{plan.outfit.summary}" + (f"（{parts}）" if parts else ""))
    current = timeline_item_at(plan, moment) if moment else None
    if current:
        lines.append(f"📍 当前：{current.activity}" + (f"（{current.location}）" if current.location else ""))
    return "\n".join([*lines, "📝 日程：", *_timeline_lines(plan)])


def format_timeline(
    plan: DailyPlan,
    moment: datetime | None = None,
    long_term_day: dict[str, object] | None = None,
) -> str:
    day = long_term_day or {}
    lines = [
        f"📅 {plan.date} 虚拟日程",
        f"💡 今日主题：{plan.theme}",
        f"💭 心情状态：{plan.mood}",
        f"🌤️ 今日天气：{_weather_text(plan)}",
    ]
    stage = day.get("stage")
    lines.append(
        f"🗓️ 当前大时间段：{stage['name']}（{stage['start_date']} 至 {stage['end_date']}）"
        if isinstance(stage, dict)
        else "🗓️ 当前大时间段：暂无当前阶段"
    )
    for period in day.get("active_periods", []):
        rules = "；".join(period.get("constraints", []))
        lines.append(
            f"⚠️ 特殊时间段：{period['name']}（{period['start_date']} 至 {period['end_date']}）"
            + (f" · {rules}" if rules else "")
        )
    if day.get("holidays", []):
        lines.append("🎉 今日节日：" + "、".join(holiday["name"] for holiday in day["holidays"]))
    current = timeline_item_at(plan, moment) if moment else None
    if current:
        where = f" @ {current.location}" if current.location else ""
        lines.append(f"📍 当前时段：{current.start}-{current.end} {current.activity}{where}")
    return "\n".join([*lines, "📝 24 小时时间轴：", *_timeline_lines(plan)])


def format_outfit(plan: DailyPlan) -> str:
    if plan.outfit is None:
        return f"📅 {plan.date}\n今日没有穿搭。"
    lines = [f"👗 {plan.date} 今日穿搭", f"🎨 穿搭风格：{plan.outfit.style}"]
    if plan.has_schedule:
        lines += [f"💡 今日主题：{plan.theme}", f"💭 今日心情：{plan.mood}", f"🌤️ 今日天气：{_weather_text(plan)}"]
    lines.append(f"✨ 造型概述：{plan.outfit.summary}")
    parts = _outfit_parts(plan)
    if parts:
        lines.append(f"🧥 穿搭明细：{parts}")
    return "\n".join(lines)
