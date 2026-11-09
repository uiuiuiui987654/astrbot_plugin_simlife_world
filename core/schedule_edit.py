"""把即时互动补写进当天日程，并保持时间线连续。

观察窗里点「一起吃个饭」生成菜品后，如果只回一句就结束，日程里仍然写着
「窝在沙发上看纪录片」，后续主动消息、智能注入和下一次互动都会对不上。
这里把互动区间插进当天时间线：当前时段被切成「前段 + 互动 + 后段」，
并同步调整引用了被拆时段主动窗口，保证 ``DailyPlan`` 的连续性校验通过。
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timedelta

from .models import DailyPlan, ProactiveWindow, TimelineItem, minute_of_day

MIN_DURATION = 5
MAX_DURATION = 240


def _clock(minutes: int) -> str:
    minutes = max(0, min(24 * 60, int(minutes)))
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def insert_activity(
    plan: DailyPlan,
    moment: datetime,
    duration_minutes: int = 30,
    activity: str = "",
    location: str = "",
    *,
    state: str = "available",
    availability: str = "normal",
    defer_transit: bool = True,
) -> DailyPlan:
    """从 ``moment`` 起插入一段活动，返回校验通过的新计划。

    Raises:
        ValueError: 当天没有日程，或插入后时间线不连续。
    """
    text = str(activity or "").strip()
    if not text:
        raise ValueError("activity 不能为空")
    if not plan.has_schedule:
        raise ValueError("当天没有日程可插入")
    try:
        duration = int(duration_minutes)
    except (TypeError, ValueError):
        duration = 30
    duration = max(MIN_DURATION, min(MAX_DURATION, duration))
    start = moment.hour * 60 + moment.minute
    end = min(24 * 60, start + duration)
    if end - start < MIN_DURATION:
        start = max(0, end - MIN_DURATION)

    def _is_transit(item: TimelineItem) -> bool:
        return str(item.state or "") == "transit" or "路上" in str(
            item.location or ""
        )

    # 如果插入点落在通勤/回家路上，先让她走完这一程，再插入活动。
    # 否则会出现「在家吃完饭，再拎着菜走回家」这种倒置日程。
    # 车库出发会显式关闭这个延后，好把正在走的步行段并进车程。
    for _ in range(8 if defer_transit else 0):
        first_overlap = next(
            (
                item
                for item in plan.timeline
                if minute_of_day(item.start) < end
                and minute_of_day(item.end) > start
            ),
            None,
        )
        if first_overlap is None or not _is_transit(first_overlap):
            break
        shifted = minute_of_day(first_overlap.end)
        if shifted <= start or shifted >= 24 * 60:
            break
        start = shifted
        end = min(24 * 60, start + duration)
        if end - start < MIN_DURATION:
            start = max(0, end - MIN_DURATION)
    if start >= 24 * 60:
        raise ValueError("互动活动没有可插入的时间")

    items = list(plan.timeline)
    kept: list[TimelineItem] = []
    overlap: list[TimelineItem] = []
    tail: list[TimelineItem] = []
    for item in items:
        item_start = minute_of_day(item.start)
        item_end = minute_of_day(item.end)
        if item_end <= start:
            kept.append(item)
        elif item_start >= end:
            tail.append(item)
        else:
            overlap.append(item)

    taken = {item.id for item in items}
    prefix: TimelineItem | None = None
    suffix: TimelineItem | None = None
    if overlap:
        first, last = overlap[0], overlap[-1]
        if minute_of_day(first.start) < start:
            prefix = replace(first, end=_clock(start))
        if minute_of_day(last.end) > end:
            base = f"{last.id}~b"
            suffix_id = base
            extra = 1
            while suffix_id in taken:
                extra += 1
                suffix_id = f"{base}{extra}"
            suffix = replace(last, id=suffix_id, start=_clock(end))

    segment_id = f"it-{uuid.uuid4().hex[:8]}"
    while segment_id in taken:
        segment_id = f"it-{uuid.uuid4().hex[:8]}"
    segment = TimelineItem(
        id=segment_id,
        start=_clock(start),
        end=_clock(end),
        activity=text,
        location=str(location or "").strip(),
        state=state,
        availability=availability,
    )

    overlap_ids = {item.id for item in overlap}
    windows: list[ProactiveWindow] = []
    for window in plan.proactive_windows:
        at = minute_of_day(window.at)
        if start <= at < end:
            # 落在互动区间里的主动窗口作废：她正在吃饭。
            continue
        if suffix is not None and window.source_item_id in overlap_ids and at >= end:
            window = replace(window, source_item_id=suffix.id)
        windows.append(window)

    timeline = list(kept)
    if prefix is not None:
        timeline.append(prefix)
    timeline.append(segment)
    if suffix is not None:
        timeline.append(suffix)
    timeline.extend(tail)

    if not timeline or timeline[0].start != "00:00" or timeline[-1].end != "24:00":
        raise ValueError("插入后时间线不完整")

    return replace(plan, timeline=tuple(timeline), proactive_windows=tuple(windows))


def insert_garage_trip(
    plan: DailyPlan,
    trip: dict,
    moment: datetime,
    *,
    activity: str = "",
) -> DailyPlan:
    """把一次车库出发写成当天时间线里的行车/兜风时段。"""
    destination = str((trip or {}).get("destination") or "").strip()
    if not destination:
        raise ValueError("目的地不能为空")
    try:
        started = datetime.fromisoformat(str(trip.get("started_at")))
    except (TypeError, ValueError):
        started = moment
    # 如果出发时正卡在一段步行出门的路上，把这段步行一起并进车程，
    # 避免日程里留下「步行去杂货铺 → 开车去超市」这种重复出门。
    started_minute = started.hour * 60 + started.minute
    absorbed_walk = False
    for item in plan.timeline:
        try:
            item_start = minute_of_day(item.start)
            item_end = minute_of_day(item.end)
        except (TypeError, ValueError):
            continue
        if (
            item_start <= started_minute < item_end
            and str(item.state or "") == "transit"
            and "步行" in str(item.activity or "")
        ):
            started = started.replace(
                hour=item_start // 60,
                minute=item_start % 60,
                second=0,
                microsecond=0,
            )
            absorbed_walk = True
            break
    try:
        eta = datetime.fromisoformat(str(trip.get("eta")))
    except (TypeError, ValueError):
        eta = started + timedelta(minutes=90)
    minutes = max(
        5,
        min(240, int(round((eta - started).total_seconds() / 60))),
    )
    driver = str(trip.get("driver") or "self")
    text = str(activity or "").strip()
    if not text:
        text = f"开车去{destination}" + (
            "（主人开）" if driver == "master" else ""
        )
    return insert_activity(
        plan,
        started,
        minutes,
        text,
        destination,
        state="transit",
        availability="low",
        defer_transit=not absorbed_walk,
    )


def insert_garage_return(
    plan: DailyPlan,
    trip: dict,
    moment: datetime,
) -> DailyPlan:
    """把兜风回家写成一小段日程，避免车库与时间线对不上。"""
    destination = str((trip or {}).get("destination") or "").strip()
    activity = f"从{destination}兜风回来" if destination else "兜风回来"
    return insert_activity(
        plan,
        moment,
        15,
        activity,
        "车库",
        state="available",
        availability="normal",
    )
