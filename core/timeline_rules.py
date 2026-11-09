"""日程时间线的结构规则。"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .models import TimelineItem, minute_of_day

MULTISTOP_MARKERS = ("顺路", "途中", "路过")
MIN_MULTISTOP_SPLIT_MINUTES = 12


def _clock(minutes: int) -> str:
    minutes = max(0, min(24 * 60, int(minutes)))
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _unique_id(base: str, used: set[str], suffix: str) -> str:
    candidate = f"{base}~{suffix}"
    extra = 1
    while candidate in used:
        extra += 1
        candidate = f"{base}~{suffix}{extra}"
    used.add(candidate)
    return candidate


def split_multistop_transit(timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """把「步行回家，顺路在杂货铺买东西」拆成 在路上/店铺/在路上。

    只处理 state=transit 且 activity 含「顺路/途中/路过」，并保留原来的 id 给
    中间停留段，避免已有主动窗口失去引用。
    """
    if not isinstance(timeline, list):
        return timeline
    used = {
        str(item.get("id") or "")
        for item in timeline
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }
    result: list[dict[str, Any]] = []
    for raw in timeline:
        if not isinstance(raw, dict):
            result.append(raw)
            continue
        activity = str(raw.get("activity") or "").strip()
        state = str(raw.get("state") or "").strip()
        if state != "transit":
            result.append(raw)
            continue
        marker = next((item for item in MULTISTOP_MARKERS if item in activity), "")
        if not marker:
            result.append(raw)
            continue
        before, _, after = activity.partition(marker)
        before = before.strip(" ，,。;；")
        after = after.strip(" ，,。;；")
        if not before or not after:
            result.append(raw)
            continue
        try:
            start = minute_of_day(str(raw.get("start") or ""))
            end = minute_of_day(str(raw.get("end") or ""))
        except ValueError:
            result.append(raw)
            continue
        total = end - start
        if total < MIN_MULTISTOP_SPLIT_MINUTES:
            result.append(raw)
            continue
        leg = max(3, min(8, total // 4))
        if total - leg * 2 < 4:
            leg = max(2, (total - 4) // 2)
        stop = total - leg * 2
        if stop < 2:
            result.append(raw)
            continue

        base_id = str(raw.get("id") or "item").strip() or "item"
        first_id = _unique_id(base_id, used, "a")
        last_id = _unique_id(base_id, used, "b")

        first = dict(raw)
        first.update(
            id=first_id,
            start=_clock(start),
            end=_clock(start + leg),
            activity=before,
            location="路上",
            state="transit",
            availability="low",
        )
        middle = dict(raw)
        middle.update(
            start=_clock(start + leg),
            end=_clock(start + leg + stop),
            activity=f"{marker}{after}",
            state="available",
            availability="normal",
        )
        last = dict(raw)
        last.update(
            id=last_id,
            start=_clock(start + leg + stop),
            end=_clock(end),
            activity=before,
            location="路上",
            state="transit",
            availability="low",
        )
        result.extend([first, middle, last])
    return result


def split_plan_timeline(
    timeline: tuple[TimelineItem, ...],
) -> tuple[TimelineItem, ...]:
    """对已加载的 DailyPlan 时间线做多站行程规范化。"""
    raw: list[dict[str, Any]] = []
    for item in timeline:
        value = asdict(item)
        value["participant_ids"] = list(item.participant_ids)
        raw.append(value)
    parts = split_multistop_transit(raw)
    if len(parts) == len(raw):
        return timeline
    return tuple(TimelineItem.from_dict(item) for item in parts)
