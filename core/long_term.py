"""The long-term timeline ("大时间表"): semesters, projects and other multi-week stages.

A stage carries weekly fixed events, one-off special dates, special periods with
extra constraints and milestones. Stages are generated as a draft, approved by an
admin, then expanded day by day to steer the daily schedule.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .holiday_calendar import ChinaHolidayCalendar
from .models import minute_of_day
from .storage import JsonRepository

STAGE_KINDS = {"academic", "project", "custom"}
DRAFT_MODES = {"append", "replace_all"}
SCHEMA_VERSION = 1
UPCOMING_HOLIDAY_DAYS = 7


# ---------------------------------------------------------------------------- validation


def normalize_priority(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("priority must be an integer from 0 to 100, not a boolean")
    if isinstance(value, str):
        try:
            value = int(value.strip())
        except ValueError as exc:
            raise ValueError("priority must be an integer from 0 to 100") from exc
    if not isinstance(value, int):
        raise ValueError("priority must be an integer from 0 to 100")
    if not 0 <= value <= 100:
        raise ValueError("priority must be between 0 and 100")
    return value


def _text(raw: dict, key: str, default: str = "") -> str:
    return str(raw.get(key, default)).strip()


def _strings(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]


def _items(values: object) -> list:
    return values if isinstance(values, list) else []


def _day(raw: dict, key: str) -> date:
    return date.fromisoformat(str(raw.get(key, "")))


def _days_of(stage: dict, start_key: str = "start_date", end_key: str = "end_date") -> tuple[date, date]:
    return date.fromisoformat(stage[start_key]), date.fromisoformat(stage[end_key])


def _fixed_event(raw: dict[str, Any]) -> dict[str, Any]:
    raw = dict(raw)
    event = {
        **raw,
        "title": _text(raw, "title"),
        "start": _text(raw, "start"),
        "end": _text(raw, "end"),
        "location": _text(raw, "location"),
        "participants": _strings(raw.get("participants", [])),
    }
    if not event["title"]:
        raise ValueError("固定事件 title 不能为空")
    try:
        begins, ends = minute_of_day(event["start"]), minute_of_day(event["end"])
    except ValueError as exc:
        raise ValueError(f"fixed event {event['title']!r} requires non-empty start and end in HH:MM") from exc
    if begins >= ends:
        raise ValueError(f"固定事件时间无效: {event['title']}")
    event["required"] = bool(raw.get("required", True))
    return event


def _weekly_rule(raw: dict[str, Any]) -> dict[str, Any]:
    event = _fixed_event(raw)
    weekdays = sorted({int(day) for day in raw.get("weekdays", [])})
    if not weekdays or not all(1 <= day <= 7 for day in weekdays):
        raise ValueError(f"周规则 weekdays 无效: {event['title']}")
    return {**event, "weekdays": weekdays}


def _special_date(raw: dict[str, Any], start: date, end: date) -> dict[str, Any]:
    event = _fixed_event(raw)
    on = _day(raw, "date")
    if not start <= on <= end:
        raise ValueError(f"特殊日期超出阶段范围: {on}")
    return {**event, "date": on.isoformat()}


def _special_period(raw: dict[str, Any], start: date, end: date) -> dict[str, Any]:
    first, last = _day(raw, "start_date"), _day(raw, "end_date")
    if not start <= first <= last <= end:
        raise ValueError("特殊时期日期范围无效")
    return {
        "name": _text(raw, "name", "特殊时期"),
        "start_date": first.isoformat(),
        "end_date": last.isoformat(),
        "constraints": _strings(raw.get("constraints", [])),
    }


def _milestone(raw: dict[str, Any], start: date, end: date) -> dict[str, Any]:
    on = _day(raw, "date")
    if not start <= on <= end:
        raise ValueError(f"里程碑超出阶段范围: {on}")
    title = _text(raw, "title")
    if not title:
        raise ValueError("里程碑 title 不能为空")
    return {"date": on.isoformat(), "title": title, "lead_days": max(0, int(raw.get("lead_days", 0)))}


def validate_stage(value: dict[str, Any], persona_id: str, *, stage_id: str | None = None) -> dict[str, Any]:
    """Normalised copy of one stage; raises ``ValueError`` describing the first problem."""
    value = dict(value)
    stage = {
        **value,
        "id": str(stage_id or value.get("id", "")).strip(),
        "persona_id": persona_id,
        "name": _text(value, "name"),
        "kind": _text(value, "kind", "custom"),
        "summary": _text(value, "summary"),
    }
    if not stage["id"] or not stage["name"]:
        raise ValueError("长期时间表阶段必须包含 id 和 name")
    if stage["kind"] not in STAGE_KINDS:
        raise ValueError("kind 必须是 academic、project 或 custom")
    start, end = _day(value, "start_date"), _day(value, "end_date")
    if start > end:
        raise ValueError("start_date 不能晚于 end_date")
    stage["start_date"], stage["end_date"] = start.isoformat(), end.isoformat()
    stage["priority"] = normalize_priority(value.get("priority", 0))
    stage["constraints"] = _strings(value.get("constraints", []))
    stage["weekly_rules"] = [_weekly_rule(raw) for raw in _items(value.get("weekly_rules", []))]
    stage["special_dates"] = [_special_date(raw, start, end) for raw in _items(value.get("special_dates", []))]
    stage["special_periods"] = [_special_period(raw, start, end) for raw in _items(value.get("special_periods", []))]
    stage["milestones"] = [_milestone(raw, start, end) for raw in _items(value.get("milestones", []))]
    return stage


def validate_stage_bundle(value: dict[str, Any], persona_id: str, *, required_start: date | None = None) -> list[dict[str, Any]]:
    """A generated batch: non-empty, unique ids, back to back with no gaps or overlaps."""
    raw_stages = value.get("stages") if isinstance(value, dict) else None
    if not isinstance(raw_stages, list) or not raw_stages:
        raise ValueError("大时间表必须包含非空 stages 列表")
    stages = sorted(
        (validate_stage(raw, persona_id) for raw in raw_stages),
        key=lambda stage: (stage["start_date"], stage["end_date"], stage["id"]),
    )
    if len({stage["id"] for stage in stages}) != len(stages):
        raise ValueError("大时间表阶段 ID 必须唯一")
    if required_start and date.fromisoformat(stages[0]["start_date"]) != required_start:
        raise ValueError(f"首个阶段必须从 {required_start.isoformat()} 开始")
    for earlier, later in zip(stages, stages[1:]):
        if date.fromisoformat(later["start_date"]) != date.fromisoformat(earlier["end_date"]) + timedelta(days=1):
            raise ValueError("同一批生成的阶段必须首尾连续，不得重叠或留空")
    return stages


def _clash(one: dict[str, Any], other: dict[str, Any]) -> bool:
    return minute_of_day(one["start"]) < minute_of_day(other["end"]) and minute_of_day(other["start"]) < minute_of_day(one["end"])


# ---------------------------------------------------------------------------- store


class LongTermTimelineStore:
    def __init__(self, data_dir: Path):
        self.repo = JsonRepository(data_dir / "long_term_timelines.json", {"schema_version": SCHEMA_VERSION, "stages": []})
        self.holidays = ChinaHolidayCalendar()
        self.stages: list[dict[str, Any]] = []
        self.drafts: dict[str, dict[str, Any]] = {}
        self.notification_targets: dict[str, str] = {}

    # ---- persistence

    async def load(self) -> None:
        data = await self.repo.load()
        self.stages = [dict(stage) for stage in data.get("stages", []) if isinstance(stage, dict)]
        self.drafts = {str(pid): dict(draft) for pid, draft in data.get("drafts", {}).items() if isinstance(draft, dict)}
        self.notification_targets = {
            str(pid): str(umo) for pid, umo in data.get("notification_targets", {}).items() if str(umo).strip()
        }

    async def save(self) -> None:
        await self.repo.save(
            {
                "schema_version": SCHEMA_VERSION,
                "stages": self.stages,
                "drafts": self.drafts,
                "notification_targets": self.notification_targets,
            }
        )

    # ---- drafts

    async def set_draft(
        self,
        persona_id: str,
        stages: list[dict[str, Any]],
        *,
        source: str,
        admin_umo: str,
        created_at: str,
        requirements: str = "",
        mode: str = "append",
    ) -> dict[str, Any]:
        if mode not in DRAFT_MODES:
            raise ValueError("草稿 mode 必须是 append 或 replace_all")
        self.drafts[persona_id] = dict(
            persona_id=persona_id,
            stages=stages,
            source=source,
            admin_umo=admin_umo,
            created_at=created_at,
            requirements=requirements,
            mode=mode,
        )
        await self.save()
        return dict(self.drafts[persona_id])

    def get_draft(self, persona_id: str) -> dict[str, Any] | None:
        draft = self.drafts.get(persona_id)
        return dict(draft) if draft else None

    async def reject_draft(self, persona_id: str) -> bool:
        if self.drafts.pop(persona_id, None) is None:
            return False
        await self.save()
        return True

    async def approve_draft(self, persona_id: str, admin_umo: str) -> list[dict[str, Any]]:
        """Adopt the pending draft; same-id stages are replaced (or all of them for ``replace_all``)."""
        draft = self.drafts.get(persona_id)
        if not draft:
            raise ValueError("当前人格没有待批准草稿")
        approved = [dict(stage) for stage in draft["stages"]]
        replace_all = draft.get("mode") == "replace_all"
        incoming = {stage["id"] for stage in approved}
        self.stages = [
            stage
            for stage in self.stages
            if stage.get("persona_id") != persona_id or (not replace_all and stage.get("id") not in incoming)
        ] + approved
        del self.drafts[persona_id]
        self.notification_targets[persona_id] = admin_umo
        await self.save()
        return approved

    async def add_auto_renewal(self, persona_id: str, stages: list[dict[str, Any]]) -> None:
        known = {stage["id"] for stage in self.stages if stage.get("persona_id") == persona_id}
        self.stages += [stage for stage in stages if stage["id"] not in known]
        await self.save()

    def notification_target(self, persona_id: str) -> str | None:
        return self.notification_targets.get(persona_id)

    # ---- queries

    def _own(self, persona_id: str) -> list[dict[str, Any]]:
        return [stage for stage in self.stages if stage.get("persona_id") == persona_id]

    def list_for_persona(self, persona_id: str) -> list[dict[str, Any]]:
        return sorted(
            (dict(stage) for stage in self._own(persona_id)),
            key=lambda stage: (stage["start_date"], -int(stage.get("priority", 0)), stage["id"]),
        )

    def latest_stage(self, persona_id: str) -> dict[str, Any] | None:
        stages = self.list_for_persona(persona_id)
        return dict(max(stages, key=lambda stage: (stage["end_date"], stage["priority"]))) if stages else None

    def has_stage_starting_after(self, persona_id: str, target: date) -> bool:
        return any(date.fromisoformat(stage["start_date"]) > target for stage in self._own(persona_id))

    def find(self, persona_id: str, stage_id: str) -> dict[str, Any] | None:
        return next((dict(stage) for stage in self._own(persona_id) if stage.get("id") == stage_id), None)

    def active_stage(self, persona_id: str, target: date) -> dict[str, Any] | None:
        """The stage covering ``target``: highest priority, then the shortest, then the oldest."""
        covering = []
        for position, stage in enumerate(self.stages):
            if stage.get("persona_id") != persona_id:
                continue
            start, end = _days_of(stage)
            if start <= target <= end:
                covering.append((-int(stage.get("priority", 0)), (end - start).days, position, stage))
        return dict(min(covering, key=lambda entry: entry[:3])[3]) if covering else None

    def resolve_stage(
        self, persona_id: str, target: date, query: str = ""
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """``(stage, [])`` when one stage is meant, ``(None, candidates)`` when ambiguous or unknown."""
        stages = self.list_for_persona(persona_id)
        wanted = query.strip().strip("\"'").casefold()
        if not wanted:
            return self._default_stage(persona_id, target, stages), []

        def field(stage: dict, key: str) -> str:
            return str(stage.get(key, "")).casefold()

        by_id = [stage for stage in stages if field(stage, "id") == wanted]
        if by_id:
            return by_id[0], []
        by_name = [stage for stage in stages if field(stage, "name") == wanted]
        if by_name:
            return (by_name[0], []) if len(by_name) == 1 else (None, by_name)
        partial = [stage for stage in stages if wanted in field(stage, "id") or wanted in field(stage, "name")]
        return (partial[0], []) if len(partial) == 1 else (None, partial)

    def _default_stage(self, persona_id: str, target: date, stages: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Current stage, else the next one, else the most recent past one."""
        current = self.active_stage(persona_id, target)
        if current:
            return current
        upcoming = [stage for stage in stages if date.fromisoformat(stage["start_date"]) > target]
        if upcoming:
            return min(upcoming, key=lambda stage: (stage["start_date"], stage["end_date"]))
        finished = [stage for stage in stages if date.fromisoformat(stage["end_date"]) < target]
        return max(finished, key=lambda stage: (stage["end_date"], stage["start_date"])) if finished else None

    # ---- one day

    def expand_day(self, persona_id: str, target: date) -> dict[str, Any] | None:
        """What the active stage means for ``target``: fixed events, periods, constraints, milestones."""
        stage = self.active_stage(persona_id, target)
        if not stage:
            return None
        special = [
            dict(event)
            for event in stage.get("special_dates", [])
            if event.get("date") == target.isoformat() and event.get("required", True)
        ]
        weekly = [
            dict(rule)
            for rule in stage.get("weekly_rules", [])
            if target.isoweekday() in rule.get("weekdays", []) and rule.get("required", True)
        ]
        # A one-off event on this date overrides any weekly event it overlaps.
        weekly = [rule for rule in weekly if not any(_clash(rule, event) for event in special)]
        events = sorted(weekly + special, key=lambda event: event["start"])
        for index, event in enumerate(events):
            if any(_clash(event, later) for later in events[index + 1 :]):
                raise ValueError(f"长期时间表固定事件冲突: {event['title']}")

        periods = [dict(period) for period in stage.get("special_periods", []) if _days_of(period)[0] <= target <= _days_of(period)[1]]
        constraints = list(stage.get("constraints", []))
        for period in periods:
            constraints += period.get("constraints", [])
        milestones = [
            dict(milestone)
            for milestone in stage.get("milestones", [])
            if date.fromisoformat(milestone["date"]) - timedelta(days=int(milestone.get("lead_days", 0)))
            <= target
            <= date.fromisoformat(milestone["date"])
        ]
        return {
            "stage": stage,
            "fixed_events": events,
            "active_periods": periods,
            "constraints": list(dict.fromkeys(constraints)),
            "milestones": milestones,
            "holidays": self.holidays.on(target),
        }

    def with_holidays(self, stage: dict[str, Any]) -> dict[str, Any]:
        return {**stage, "holidays": self.holidays.between(*_days_of(stage))}

    def format_day_context(self, persona_id: str, target: date, *, fallback_to_latest: bool = False) -> str:
        """Prompt block for daily planning."""
        day = self.expand_day(persona_id, target)
        if not day:
            latest = self.latest_stage(persona_id) if fallback_to_latest else None
            return self._ended_context(latest) if latest else "长期时间表：当前日期没有生效阶段。"
        stage = day["stage"]
        upcoming = self.holidays.upcoming(target, UPCOMING_HOLIDAY_DAYS)

        def bullets(lines: list[str]) -> list[str]:
            return lines or ["- 无"]

        return "\n".join(
            [
                "<long_term_timeline>",
                f"阶段：{stage['name']}（{stage['kind']}，{stage['start_date']} 至 {stage['end_date']}）",
                f"说明：{stage.get('summary') or '无'}",
                f"今日节日：{'、'.join(item['name'] for item in day['holidays']) or '无'}",
                "未来 7 天节日：" + ("；".join(f"{item['date']} {item['name']}" for item in upcoming) or "无"),
                "今日必须保留的固定事件：",
                *bullets(
                    [
                        f"- {event['start']}-{event['end']} {event['title']}"
                        + (f" @ {event['location']}" if event.get("location") else "")
                        for event in day["fixed_events"]
                    ]
                ),
                "阶段约束：" + ("；".join(day["constraints"]) if day["constraints"] else "无"),
                "临近里程碑：",
                *bullets([f"- {item['date']} {item['title']}" for item in day["milestones"]]),
                "生成当天日程时必须保留固定事件，并围绕阶段约束和里程碑安排其余活动。",
                "</long_term_timeline>",
            ]
        )

    @staticmethod
    def _ended_context(latest: dict[str, Any]) -> str:
        return (
            "<long_term_timeline>\n"
            f"最近阶段已于 {latest['end_date']} 结束：{latest['name']}（{latest['kind']}）。\n"
            f"阶段说明：{latest.get('summary') or '无'}\n"
            "后续阶段正在自动生成中；在生成成功前，可延续该阶段的人物背景和一般约束，"
            "但不要虚构已经过期的固定课程、会议或截止日期。\n"
            "一般约束：" + ("；".join(latest.get("constraints", [])) or "无") + "\n"
            "</long_term_timeline>"
        )
