from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .models import OUTFIT_CATEGORY_LABELS, DailyPlan, TimelineItem, minute_of_day


def extract_json_object(text: str) -> dict:
    """Extract the first usable JSON object from an LLM completion.

    Tolerates the usual model output quirks: Markdown code fences, explanatory
    prose (including prose that contains stray or unbalanced braces before the
    real object), multiple objects in one completion, trailing commas, and a
    response that was cut off before its closing brackets.
    """
    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$", "", str(text).strip(), flags=re.IGNORECASE
    ).strip()
    cleaned = cleaned.lstrip("\ufeff\u200b").strip()

    value = _loads_json_object(cleaned)
    if value is not None:
        return value

    starts = [match.start() for match in re.finditer(r"\{", cleaned)]
    if not starts:
        raise ValueError("LLM response does not contain a JSON object")

    decoder = json.JSONDecoder()
    for start in starts:
        # A strict decode from each brace handles valid JSON surrounded by
        # prose, and skips prose braces that do not begin a valid object.
        try:
            parsed, _ = decoder.raw_decode(cleaned, start)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(parsed, dict):
            return parsed

    for start in starts:
        # Lenient fallback: repair the best-effort balanced fragment that
        # begins at this brace (trailing commas, truncated tail, dangling key).
        fragment, balanced = _balanced_json_object(cleaned, start)
        repaired = _loads_repaired_json_object(fragment, balanced=balanced)
        if repaired is not None:
            return repaired

    raise ValueError("unable to parse JSON object")


def _loads_json_object(text: str) -> dict | None:
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, ValueError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def _balanced_json_object(text: str, start: int) -> tuple[str, bool]:
    """Return the text from ``start`` to the matching ``}`` (if any)."""
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1], True
    return text[start:], False


def _loads_repaired_json_object(fragment: str, *, balanced: bool) -> dict | None:
    for candidate in _json_object_repair_candidates(fragment, balanced=balanced):
        value = _loads_json_object(candidate)
        if value is not None:
            return value
    return None


def _json_object_repair_candidates(fragment: str, *, balanced: bool):
    seen: set[str] = set()

    def fresh(candidate: str | None) -> bool:
        if not candidate or candidate in seen:
            return False
        seen.add(candidate)
        return True

    if balanced:
        if fresh(fragment):
            yield fragment
        without_trailing_commas = re.sub(r",\s*([}\]])", r"\1", fragment)
        if fresh(without_trailing_commas):
            yield without_trailing_commas
        return

    # First try to close the fragment as-is; the tail may be a complete value.
    closed = _close_unbalanced_json(fragment)
    if fresh(closed):
        yield closed
        without_trailing_commas = re.sub(r",\s*([}\]])", r"\1", closed)
        if fresh(without_trailing_commas):
            yield without_trailing_commas

    # Then drop the dangling tail element(s) and close the remaining prefix.
    for cut in _json_cut_positions(fragment):
        closed = _close_unbalanced_json(fragment[:cut])
        if fresh(closed):
            yield closed
        if closed:
            without_trailing_commas = re.sub(r",\s*([}\]])", r"\1", closed)
            if fresh(without_trailing_commas):
                yield without_trailing_commas


def _close_unbalanced_json(text: str) -> str | None:
    """Best-effort close of a JSON fragment that ends mid-structure."""
    stack: list[str] = []
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            stack.append("}")
        elif char == "[":
            stack.append("]")
        elif char in "}]":
            if not stack:
                return None
            stack.pop()
    result = text
    if in_string:
        if escaped:
            result = result[:-1]
        result += '"'
    else:
        result = result.rstrip()
        if result.endswith(","):
            result = result[:-1].rstrip()
    return result + "".join(reversed(stack))


def _json_cut_positions(text: str) -> list[int]:
    """Positions where a truncated fragment can be cut back to a value boundary."""
    positions: list[int] = []
    in_string = False
    escaped = False
    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == ",":
            positions.append(index)
        elif char in "{[":
            positions.append(index + 1)
    return sorted(positions[-10:], reverse=True)


def deterministic_int(seed: str, minimum: int, maximum: int) -> int:
    if maximum <= minimum:
        return minimum
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return minimum + int.from_bytes(digest[:8], "big") % (maximum - minimum + 1)


def deterministic_probability(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64 - 1)


def now_in(timezone: ZoneInfo) -> datetime:
    return datetime.now(timezone)


def parse_datetime(value: str, timezone: ZoneInfo) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone)
    return parsed.astimezone(timezone)


def parse_schedule_date_range(value: str, reference: date) -> tuple[date, date]:
    endpoints = [item.strip() for item in str(value).split("..")]
    if len(endpoints) not in (1, 2) or any(not item for item in endpoints):
        raise ValueError("日期应为 YYYY-MM-DD、MM-DD、DD，或使用 .. 连接的日期区间")

    def parts(endpoint: str) -> list[int]:
        raw_parts = endpoint.split("-")
        if not 1 <= len(raw_parts) <= 3 or any(
            not item.isdigit() for item in raw_parts
        ):
            raise ValueError("日期应为 YYYY-MM-DD、MM-DD、DD，或使用 .. 连接的日期区间")
        return [int(item) for item in raw_parts]

    start_parts = parts(endpoints[0])
    try:
        if len(start_parts) == 3:
            start = date(*start_parts)
        elif len(start_parts) == 2:
            start = date(reference.year, *start_parts)
        else:
            start = date(reference.year, reference.month, start_parts[0])
    except ValueError as exc:
        raise ValueError(f"无效的开始日期：{endpoints[0]}") from exc

    if len(endpoints) == 1:
        return start, start

    end_parts = parts(endpoints[1])
    try:
        if len(end_parts) == 3:
            end = date(*end_parts)
        elif len(end_parts) == 2:
            end = date(start.year, *end_parts)
            if end < start:
                end = date(start.year + 1, *end_parts)
        else:
            end = date(start.year, start.month, end_parts[0])
            if end < start:
                next_year = start.year + (1 if start.month == 12 else 0)
                next_month = 1 if start.month == 12 else start.month + 1
                end = date(next_year, next_month, end_parts[0])
    except ValueError as exc:
        raise ValueError(f"无效的结束日期：{endpoints[1]}") from exc
    if end < start:
        raise ValueError("结束日期不能早于开始日期")
    return start, end


def timeline_item_at(plan: DailyPlan, moment: datetime) -> TimelineItem | None:
    minute = moment.hour * 60 + moment.minute
    for item in plan.timeline:
        if minute_of_day(item.start) <= minute < minute_of_day(item.end):
            return item
    return None


def next_available_at(plan: DailyPlan, moment: datetime) -> datetime | None:
    minute = moment.hour * 60 + moment.minute
    for item in plan.timeline:
        if minute_of_day(item.start) <= minute:
            continue
        if item.state != "sleep" and item.availability in {"normal", "high"}:
            hour, minute_value = map(int, item.start.split(":"))
            return moment.replace(
                hour=hour, minute=minute_value, second=0, microsecond=0
            )
    return None


def format_plan(plan: DailyPlan, moment: datetime | None = None) -> str:
    if not plan.has_schedule and not plan.has_outfit:
        return f"📅 {plan.date}\n今日没有日程和穿搭。"
    if not plan.has_schedule:
        return format_outfit(plan)
    current = timeline_item_at(plan, moment) if moment else None
    outfit = plan.outfit
    lines = [
        f"📅 {plan.date} · {plan.theme}",
        f"💭 心情：{plan.mood}",
        f"🌤️ 天气：{plan.weather.prompt_text if plan.weather else '未记录'}",
    ]
    if outfit:
        outfit_items = "；".join(
            f"{OUTFIT_CATEGORY_LABELS[item.category]}：{item.name}"
            for item in outfit.items
        )
        lines.append(
            f"👗 穿搭：{outfit.summary}"
            + (f"（{outfit_items}）" if outfit_items else "")
        )
    if current:
        lines.append(
            f"📍 当前：{current.activity}"
            + (f"（{current.location}）" if current.location else "")
        )
    lines.append("📝 日程：")
    lines.extend(
        f"- {item.start}-{item.end} {item.activity}"
        + (f" @ {item.location}" if item.location else "")
        for item in plan.timeline
    )
    return "\n".join(lines)


def format_timeline(
    plan: DailyPlan,
    moment: datetime | None = None,
    long_term_day: dict[str, object] | None = None,
) -> str:
    current = timeline_item_at(plan, moment) if moment else None
    stage = long_term_day.get("stage") if long_term_day else None
    active_periods = long_term_day.get("active_periods", []) if long_term_day else []
    holidays = long_term_day.get("holidays", []) if long_term_day else []
    lines = [
        f"📅 {plan.date} 虚拟日程",
        f"💡 今日主题：{plan.theme}",
        f"💭 心情状态：{plan.mood}",
        f"🌤️ 今日天气：{plan.weather.prompt_text if plan.weather else '未记录'}",
    ]
    if isinstance(stage, dict):
        lines.append(
            f"🗓️ 当前大时间段：{stage['name']}（{stage['start_date']} 至 {stage['end_date']}）"
        )
    else:
        lines.append("🗓️ 当前大时间段：暂无当前阶段")
    for period in active_periods:
        constraints = "；".join(period.get("constraints", []))
        lines.append(
            f"⚠️ 特殊时间段：{period['name']}（{period['start_date']} 至 {period['end_date']}）"
            + (f" · {constraints}" if constraints else "")
        )
    if holidays:
        lines.append("🎉 今日节日：" + "、".join(item["name"] for item in holidays))
    if current:
        location = f" @ {current.location}" if current.location else ""
        lines.append(
            f"📍 当前时段：{current.start}-{current.end} {current.activity}{location}"
        )
    lines.append("📝 24 小时时间轴：")
    lines.extend(
        f"- {item.start}-{item.end} {item.activity}"
        + (f" @ {item.location}" if item.location else "")
        for item in plan.timeline
    )
    return "\n".join(lines)


def format_outfit(plan: DailyPlan) -> str:
    outfit = plan.outfit
    if outfit is None:
        return f"📅 {plan.date}\n今日没有穿搭。"
    outfit_items = "；".join(
        f"{OUTFIT_CATEGORY_LABELS[item.category]}：{item.name}"
        for item in outfit.items
    )
    lines = [
        f"👗 {plan.date} 今日穿搭",
        f"🎨 穿搭风格：{outfit.style}",
        f"✨ 造型概述：{outfit.summary}",
    ]
    if plan.has_schedule:
        lines[2:2] = [
            f"💡 今日主题：{plan.theme}",
            f"💭 今日心情：{plan.mood}",
            f"🌤️ 今日天气：{plan.weather.prompt_text if plan.weather else '未记录'}",
        ]
    if outfit_items:
        lines.append(f"🧥 穿搭明细：{outfit_items}")
    return "\n".join(lines)


def prune_date_keys(
    values: dict[str, object], keep_days: int, today: date
) -> dict[str, object]:
    threshold = today - timedelta(days=max(1, keep_days))
    result = {}
    for key, value in values.items():
        date_part = key.split("::", 1)[0]
        try:
            if date.fromisoformat(date_part) >= threshold:
                result[key] = value
        except ValueError:
            result[key] = value
    return result
