"""What the character "knows" about her own day, injected into LLM requests.

``SmartContextInjector`` picks sections by keyword: the current state is always
available (when the base module is on), the schedule / long-term plan / outfit
only when the user's message asks about them. ``build_state_snapshot`` is a
side-effect-free summary for other plugins.
"""

from __future__ import annotations

import unicodedata
from datetime import date, datetime, timedelta
from typing import Any

from . import life_state
from .environment import environment_context
from .models import OUTFIT_CATEGORY_LABELS, DailyPlan, TimelineItem, minute_of_day
from .utils import timeline_item_at
from .wardrobe import appearance_context, appearance_for

INTIMATES = frozenset({"underwear", "underpants"})
FULL_QUERY_HINT = "用户明确请求完整信息：必须优先调用 {tool}，不要凭当前摘要补全未查询的数据。"


def _minute(now: datetime) -> int:
    return now.hour * 60 + now.minute


def _segment_at(plan: DailyPlan, now: datetime) -> TimelineItem | None:
    """Same-day lookup (start <= now < end); unlike ``timeline_item_at`` it ignores overnight wrap."""
    minute = _minute(now)
    return next((item for item in plan.timeline if minute_of_day(item.start) <= minute < minute_of_day(item.end)), None)


def _segment_after(plan: DailyPlan, now: datetime) -> TimelineItem | None:
    return next((item for item in plan.timeline if minute_of_day(item.start) > _minute(now)), None)


def _segment_before(plan: DailyPlan, current: TimelineItem) -> TimelineItem | None:
    position = next((index for index, item in enumerate(plan.timeline) if item == current), None)
    return plan.timeline[position - 1] if position else None


def _simplify(text: str) -> str:
    """Case-folded text without whitespace or punctuation, for keyword matching."""
    folded = unicodedata.normalize("NFKC", text).casefold()
    return "".join(char for char in folded if not char.isspace() and not unicodedata.category(char).startswith("P"))


def _clamped_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default


class SmartContextInjector:
    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self.settings = settings or {}

    @property
    def enabled(self) -> bool:
        return bool(self.settings.get("enable", False))

    # ------------------------------------------------------------------ settings

    def _max_chars(self) -> int:
        return _clamped_int(self.settings.get("max_chars", 1600), 400, 8000, 1600)

    def _milestone_days(self) -> int:
        return _clamped_int(self.settings.get("long_term_milestone_days", 7), 0, 90, 7)

    def _matches(self, normalized_text: str, values: Any) -> bool:
        if not isinstance(values, list):
            return False
        keywords = (_simplify(str(value)) for value in values)
        return any(keyword and keyword in normalized_text for keyword in keywords)

    @staticmethod
    def _normalize(value: str) -> str:
        return _simplify(value)

    @staticmethod
    def _current_item(plan: DailyPlan, now: datetime) -> TimelineItem | None:
        return _segment_at(plan, now)

    @staticmethod
    def _next_item(plan: DailyPlan, now: datetime) -> TimelineItem | None:
        return _segment_after(plan, now)

    @staticmethod
    def _previous_item(plan: DailyPlan, current: TimelineItem) -> TimelineItem | None:
        return _segment_before(plan, current)

    # ------------------------------------------------------------------ sections

    def _body_line(self, plan, now, furniture_states, history_plans, health_summary) -> str:
        if health_summary:
            return f"\n身体状态：{health_summary}"
        try:
            needs = life_state.compute(plan, now, furniture_states=furniture_states, history_plans=history_plans)
        except (TypeError, ValueError):
            return ""
        return f"\n身体状态：{needs['summary']}" if needs.get("summary") else ""

    def _base_section(
        self,
        plan: DailyPlan,
        now: datetime,
        current: TimelineItem,
        *,
        furniture_context: str = "",
        furniture_states: dict[str, Any] | None = None,
        history_plans: list[Any] | None = None,
        health_summary: str = "",
    ) -> str:
        surroundings = environment_context(
            current.location, now, plan.weather, current.activity, current.state, timeline=plan.timeline, outfit=plan.outfit
        )
        return "".join(
            [
                f"时间：{now.strftime('%Y-%m-%d %H:%M')}\n",
                f"天气：{plan.weather.prompt_text if plan.weather else '未记录'}\n",
                f"当前活动：{current.activity}\n",
                f"地点：{current.location or '未说明'}\n",
                surroundings + "\n",
                f"状态：{current.state}，可打扰度：{current.availability}\n",
                self._body_line(plan, now, furniture_states, history_plans, health_summary),
                f"\n家具状态：{furniture_context}" if furniture_context else "",
                "\n普通回复必须与当前状态保持一致。",
            ]
        )

    def _schedule_section(self, plan: DailyPlan, now: datetime, current: TimelineItem, **context: Any) -> str:
        lines = [
            self._base_section(plan, now, current, **context),
            f"今日主题：{plan.theme}；心情：{plan.mood}。",
            f"当前时段：{current.start}-{current.end}。",
        ]
        for label, item in (("上个时段", _segment_before(plan, current)), ("下个时段", _segment_after(plan, now))):
            if item:
                lines.append(f"{label}：{item.start}-{item.end} {item.activity}。")
        return "\n".join(lines)

    def _outfit_section(
        self, plan: DailyPlan, *, include_underwear: bool, underwear_only: bool = False, current=None, now=None
    ) -> str:
        if plan.outfit is None:
            return ""
        shown = [
            piece
            for piece in plan.outfit.items
            if not (underwear_only and piece.category not in INTIMATES)
            and not (not include_underwear and piece.category in INTIMATES)
        ]
        if not shown:
            return ""
        listing = "；".join(
            f"{OUTFIT_CATEGORY_LABELS[piece.category]}：{piece.name}" + (f"（{piece.details}）" if piece.details else "")
            for piece in shown
        )
        if underwear_only:
            return "贴身穿搭信息：" + listing
        heading = f"今日穿搭：{plan.outfit.summary}（当前就按这套穿，睡衣/就寝时段除外）。"
        if current and now:
            worn = appearance_context(
                current.location, current.activity, current.state, now, timeline=plan.timeline, outfit=plan.outfit
            )
            heading = worn + "\n" + heading
        return heading + listing

    def _long_term_sections(self, long_term, persona_id: str, target: date) -> list[str]:
        day = long_term.expand_day(persona_id, target)
        if not day:
            latest = long_term.latest_stage(persona_id)
            if not latest:
                return ["大时间表：当前没有已批准阶段。"]
            return [
                f"最近阶段已于 {latest['end_date']} 结束：{latest['name']}。后续阶段正在生成中，"
                "不要虚构已过期的固定课程、会议或截止日期。"
            ]
        stage = day["stage"]
        header = f"当前大时间表阶段：{stage['name']}（{stage['kind']}，{stage['start_date']} 至 {stage['end_date']}）。"
        if stage.get("summary"):
            header += f"摘要：{stage['summary']}。"
        if day["constraints"]:
            header += f"约束：{'；'.join(day['constraints'])}。"
        sections = [header]
        if day["fixed_events"]:
            events = "；".join(f"{event['start']}-{event['end']} {event['title']}" for event in day["fixed_events"])
            sections.append(f"今日固定事件：{events}。")
        if day["active_periods"]:
            sections.append("当前特殊时期：" + "；".join(period["name"] for period in day["active_periods"]) + "。")
        horizon = target + timedelta(days=self._milestone_days())
        upcoming = [item for item in stage.get("milestones", []) if target <= date.fromisoformat(item["date"]) <= horizon]
        if upcoming:
            sections.append("近期里程碑：" + "；".join(f"{item['date']} {item['title']}" for item in upcoming) + "。")
        return sections

    @staticmethod
    def _join_with_limit(sections: list[str], limit: int) -> str:
        body = "\n".join(section for section in sections if section)
        if not body:
            return ""
        opening, closing = "<character_state>\n", "\n</character_state>"
        text = opening + body
        if len(text) + len(closing) > limit:
            text = text[: max(0, limit - len(closing) - 1)] + "…"
        return text + closing

    # ------------------------------------------------------------------ public

    def build(
        self,
        plan: DailyPlan,
        now: datetime,
        long_term,
        user_text: str,
        *,
        furniture_context: str = "",
        furniture_states: dict[str, Any] | None = None,
        history_plans: list[Any] | None = None,
        health_summary: str = "",
    ) -> str:
        return self.build_details(
            plan,
            now,
            long_term,
            user_text,
            furniture_context=furniture_context,
            furniture_states=furniture_states,
            history_plans=history_plans,
            health_summary=health_summary,
        )[0]

    def build_proactive_context(
        self,
        plan: DailyPlan,
        now: datetime,
        long_term,
        *,
        furniture_context: str = "",
        furniture_states: dict[str, Any] | None = None,
        history_plans: list[Any] | None = None,
        health_summary: str = "",
    ) -> str:
        """State block for proactive messages: always the schedule plus the long-term plan."""
        current = _segment_at(plan, now)
        if not current:
            return ""
        schedule = self._schedule_section(
            plan,
            now,
            current,
            furniture_context=furniture_context,
            furniture_states=furniture_states,
            history_plans=history_plans,
            health_summary=health_summary,
        )
        return self._join_with_limit([schedule, *self._long_term_sections(long_term, plan.persona_id, now.date())], self._max_chars())

    def build_details(
        self,
        plan: DailyPlan,
        now: datetime,
        long_term,
        user_text: str,
        participant_context: str = "",
        *,
        furniture_context: str = "",
        furniture_states: dict[str, Any] | None = None,
        history_plans: list[Any] | None = None,
        health_summary: str = "",
    ) -> tuple[str, tuple[str, ...], int]:
        """``(injection, modules used, character limit)`` for one chat message."""
        limit = self._max_chars()
        current = _segment_at(plan, now)
        text = _simplify(user_text)
        asked = {
            topic: self._matches(text, self.settings.get(f"{topic}_keywords"))
            for topic in ("outfit", "underwear", "schedule", "long_term", "full_schedule", "full_long_term")
        }
        context = dict(
            furniture_context=furniture_context,
            furniture_states=furniture_states,
            history_plans=history_plans,
            health_summary=health_summary,
        )
        sections: list[str] = []
        modules: list[str] = []

        def add(module: str, *content: str) -> None:
            modules.append(module)
            sections.extend(content)

        if participant_context:
            add("participants", participant_context)
        base_on = bool(self.settings.get("base_module_enable", False))
        if base_on and current:
            add("base", *([] if asked["schedule"] else [self._base_section(plan, now, current, **context)]))
        if asked["full_schedule"] and plan.has_schedule:
            add("full_schedule_query", FULL_QUERY_HINT.format(tool="get_virtual_daily_schedule"))
        if asked["full_long_term"]:
            add("full_long_term_query", FULL_QUERY_HINT.format(tool="get_long_term_timeline"))
        if asked["schedule"] and current:
            add("schedule", self._schedule_section(plan, now, current, **context))
        if asked["long_term"]:
            add("long_term", *self._long_term_sections(long_term, plan.persona_id, now.date()))
        if plan.has_outfit and (asked["outfit"] or asked["underwear"]):
            if asked["outfit"]:
                add("outfit")
                if asked["underwear"]:
                    modules.append("underwear")
                sections.append(self._outfit_section(plan, include_underwear=asked["underwear"], current=current, now=now))
            else:
                add("underwear", self._outfit_section(plan, include_underwear=True, underwear_only=True, current=current, now=now))
        if current and not base_on and not asked["schedule"] and self.settings.get("environment_enable", False):
            surroundings = environment_context(
                current.location, now, plan.weather, current.activity, current.state, timeline=plan.timeline, outfit=plan.outfit
            )
            add("environment", surroundings + self._body_line(plan, now, furniture_states, history_plans, health_summary)
                + (f"\n家具状态：{furniture_context}" if furniture_context else ""))
        return self._join_with_limit(sections, limit), tuple(modules), limit


# ------------------------------------------------------------------ snapshot for other plugins


def _segment_view(item: TimelineItem, *, full: bool = False) -> dict[str, Any]:
    view = {"start": item.start, "end": item.end, "activity": item.activity, "location": item.location}
    if full:
        view = {"id": item.id, **view, "state": item.state, "availability": item.availability}
    return view


def _finished_before(plan: DailyPlan, now: datetime, current: TimelineItem | None) -> TimelineItem | None:
    if current is not None:
        position = next((index for index, item in enumerate(plan.timeline) if item is current), None)
        return plan.timeline[position - 1] if position else None
    return next((item for item in reversed(plan.timeline) if minute_of_day(item.end) <= _minute(now)), None)


def build_state_snapshot(plan: DailyPlan, now: datetime) -> dict[str, Any]:
    """JSON-safe summary of what she is doing now, for other plugins (never raises on a partial plan)."""
    current = timeline_item_at(plan, now)
    upcoming = _segment_after(plan, now)
    earlier = _finished_before(plan, now, current)
    outfit = plan.outfit
    return {
        "date": plan.date,
        "theme": plan.theme,
        "mood": plan.mood,
        "weather": plan.weather.to_dict() if plan.weather is not None else None,
        "current": _segment_view(current, full=True) if current is not None else None,
        "next": _segment_view(upcoming) if upcoming is not None else None,
        "previous": _segment_view(earlier) if earlier is not None else None,
        "outfit": None
        if outfit is None
        else {
            "style": outfit.style,
            "summary": outfit.summary,
            "items": [{"category": piece.category, "name": piece.name, "details": piece.details} for piece in outfit.items],
        },
        "appearance": appearance_for(current.location, current.activity, current.state, now, timeline=plan.timeline)
        if current
        else None,
        "timeline_count": len(plan.timeline),
    }
