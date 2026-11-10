"""Stable jitter for proactive-message windows."""

from __future__ import annotations

from .models import DailyPlan, ProactiveWindow, minute_of_day
from .utils import deterministic_int


def proactive_window_offset_minutes(plan: DailyPlan, window: ProactiveWindow, jitter_minutes: int) -> int:
    """Shift ``window`` by up to ±``jitter_minutes`` (max 60) inside its source segment.

    The shift is derived from the plan and window ids, so re-scheduling the same
    day always lands on the same minute.
    """
    spread = min(60, max(0, int(jitter_minutes)))
    segment = next((item for item in plan.timeline if item.id == window.source_item_id), None)
    if not spread or segment is None:
        return 0
    at = minute_of_day(window.at)
    low = max(-spread, minute_of_day(segment.start) - at)
    high = min(spread, minute_of_day(segment.end) - at - 1)
    if low > high:
        return 0
    return deterministic_int(f"proactive-window::{plan.persona_id}::{plan.date}::{window.id}", low, high)
