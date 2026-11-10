"""Renders schedule / outfit / long-term cards to PNG via AstrBot's HTML renderer.

Everything here builds the data dict for ``templates/schedule.html``; the
template switches on ``view``. Stage cards are cached by content hash, the
day's timeline and outfit are rendered fresh each time.
"""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .models import OUTFIT_CATEGORY_LABELS, DailyPlan, minute_of_day
from .utils import timeline_item_at
from .wardrobe import DAILY, SLEEPWEAR, appearance_for

RenderHtml = Callable[..., Awaitable[str]]

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = PLUGIN_ROOT / "templates" / "schedule.html"
ASSETS = PLUGIN_ROOT / "assets"
BASE_FONTS = '"PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif'
WIDTH_RANGE = (720, 2000)

STATE_LABELS = dict(sleep="睡眠", busy="忙碌", focus="专注", transit="通勤", available="空闲", social="社交")
AVAILABILITY_LABELS = dict(blocked="不便联系", low="较少联系", normal="正常联系", high="适合联系")
KIND_LABELS = dict(academic="校历", project="工期", custom="自定义")
SOURCE_LABELS = dict(
    natural="自然语言生成",
    json="结构化数据导入",
    revision="按修改意见生成",
    regenerate="完整重生成",
    auto_renewal="自动续期",
)
WEEKDAY_LABELS = {number: f"周{name}" for number, name in enumerate("一二三四五六日", start=1)}
OUTFIT_CATEGORY_ICONS = dict(
    hairstyle="✦",
    headwear="♕",
    underwear="◈",
    underpants="◇",
    top="▱",
    bottom="▽",
    dress="♢",
    legwear="║",
    outerwear="◇",
    shoes="◒",
    accessory="✧",
    bag="▣",
    makeup="✿",
    fragrance="❋",
    other="◆",
)


def _kind(kind: str) -> str:
    return KIND_LABELS.get(kind, kind)


def _joined(values: Any) -> str:
    return "、".join(values or [])


def _persona_key(persona_id: str) -> str:
    return hashlib.sha1(persona_id.encode("utf-8")).hexdigest()[:12]


def _character(plan: DailyPlan, now: datetime) -> dict[str, str] | None:
    """The illustration to show: sleepwear only when today's schedule says she's in bed."""
    current = timeline_item_at(plan, now) if plan.date == now.date().isoformat() else None
    look = (
        appearance_for(current.location, current.activity, current.state, now, timeline=plan.timeline)
        if current
        else DAILY
    )
    if look["src"] not in (DAILY["src"], SLEEPWEAR["src"]):
        return None
    try:
        picture = (ASSETS / look["src"].rsplit("/", 1)[-1]).read_bytes()
    except OSError:
        return None
    return {"name": look["name"], "src": "data:image/png;base64," + base64.b64encode(picture).decode("ascii")}


def _timeline_rows(plan: DailyPlan, now: datetime, same_day: bool) -> list[dict[str, Any]]:
    minute = now.hour * 60 + now.minute
    rows = []
    for item in plan.timeline:
        start, end = minute_of_day(item.start), minute_of_day(item.end)
        rows.append(
            {
                "start": item.start,
                "end": item.end,
                "activity": item.activity,
                "location": item.location,
                "state": item.state,
                "state_label": STATE_LABELS.get(item.state, item.state),
                "availability_label": AVAILABILITY_LABELS.get(item.availability, item.availability),
                "duration": end - start,
                "current": same_day and start <= minute < end,
            }
        )
    return rows


def _long_term_blocks(day: dict[str, Any] | None) -> dict[str, Any]:
    day = day or {}
    stage = day.get("stage")
    return {
        "current_stage": {
            "name": stage["name"],
            "kind_label": _kind(stage["kind"]),
            "start_date": stage["start_date"],
            "end_date": stage["end_date"],
            "summary": stage.get("summary", ""),
        }
        if isinstance(stage, dict)
        else None,
        "active_periods": [
            {
                "name": period["name"],
                "start_date": period["start_date"],
                "end_date": period["end_date"],
                "constraints_text": "；".join(period.get("constraints", [])),
            }
            for period in day.get("active_periods", [])
        ],
        "today_holidays": [
            {"name": holiday["name"], "kind_label": "传统节日" if holiday.get("kind") == "traditional" else "法定节日"}
            for holiday in day.get("holidays", [])
        ],
    }


class ScheduleImageRenderer:
    def __init__(
        self,
        data_dir: Path,
        render_html: RenderHtml,
        settings: dict[str, Any] | None = None,
        *,
        template_path: Path | None = None,
    ) -> None:
        self.render_html = render_html
        self.settings = settings or {}
        self.cache_dir = data_dir / "image_cache"
        self.template_path = template_path or DEFAULT_TEMPLATE
        self.template = self.template_path.read_text(encoding="utf-8")

    @property
    def enabled(self) -> bool:
        return bool(self.settings.get("image_render_enabled", True))

    # ------------------------------------------------------------------ cache

    def _remove(self, paths) -> None:
        for path in paths:
            try:
                path.unlink()
            except OSError:
                continue

    async def cleanup(self, *, max_age_days: int = 7) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cutoff = time.time() - max_age_days * 86400

        def stale(path: Path) -> bool:
            try:
                return path.stat().st_mtime < cutoff
            except OSError:
                return False

        self._remove(path for path in self.cache_dir.glob("*.png") if stale(path))

    def invalidate_persona(self, persona_id: str) -> None:
        self._remove(self.cache_dir.glob(f"{_persona_key(persona_id)}-*.png"))

    # ------------------------------------------------------------------ cards

    async def render_timeline(self, plan: DailyPlan, now: datetime, long_term_day: dict[str, Any] | None = None) -> str:
        same_day = plan.date == now.date().isoformat()
        current = timeline_item_at(plan, now) if same_day else None
        payload = {
            "title": f"{plan.date} 虚拟日程",
            "subtitle": plan.persona_id,
            "status_label": f"当前时段 {current.start}–{current.end}" if current else "非今日计划",
            "theme_text": plan.theme,
            "mood": plan.mood,
            "weather": plan.weather.label if plan.weather else "",
            "character": _character(plan, now),
            **_long_term_blocks(long_term_day),
            "items": _timeline_rows(plan, now, same_day),
            "windows": [
                {"at": window.at, "intent": window.intent, "audience": window.audience} for window in plan.proactive_windows
            ],
            "generated_at": now.strftime("%Y-%m-%d %H:%M"),
        }
        return await self._render("timeline", plan.persona_id, payload, file_tag="timeline", cache=False)

    async def render_daily(self, plan: DailyPlan, now: datetime) -> str:
        return await self.render_timeline(plan, now)

    async def render_outfit(self, plan: DailyPlan, now: datetime) -> str:
        outfit = plan.outfit
        if outfit is None:
            raise ValueError("this plan has no outfit")
        payload = {
            "title": f"{plan.date} 今日穿搭",
            "subtitle": plan.persona_id,
            "theme_text": plan.theme,
            "mood": plan.mood,
            "weather": plan.weather.label if plan.weather else "",
            "has_schedule": plan.has_schedule,
            "character": _character(plan, now),
            "outfit_style": outfit.style,
            "outfit_summary": outfit.summary,
            "outfit_items": [
                {
                    "category": piece.category,
                    "label": OUTFIT_CATEGORY_LABELS[piece.category],
                    "icon": OUTFIT_CATEGORY_ICONS[piece.category],
                    "name": piece.name,
                    "details": piece.details,
                }
                for piece in outfit.items
            ],
            "generated_at": now.strftime("%Y-%m-%d %H:%M"),
        }
        return await self._render("outfit", plan.persona_id, payload, file_tag="outfit", cache=False)

    async def render_stage_list(self, stages: list[dict[str, Any]], persona_id: str) -> str:
        """Gantt-style overview; bar positions are percentages of the whole span."""
        spans = [(date.fromisoformat(stage["start_date"]), date.fromisoformat(stage["end_date"])) for stage in stages]
        first, last = min(start for start, _ in spans), max(end for _, end in spans)
        total = max(1, (last - first).days + 1)
        rows = [
            {
                "id": stage["id"],
                "name": stage["name"],
                "kind": stage["kind"],
                "kind_label": _kind(stage["kind"]),
                "start_date": stage["start_date"],
                "end_date": stage["end_date"],
                "priority": stage["priority"],
                "summary": stage.get("summary", ""),
                "left": round((start - first).days / total * 100, 3),
                "width": round(((end - start).days + 1) / total * 100, 3),
            }
            for stage, (start, end) in zip(stages, spans)
        ]
        payload = {
            "title": "已批准大时间表",
            "subtitle": f"{persona_id} · 共 {len(rows)} 个阶段",
            "range": f"{first.isoformat()} 至 {last.isoformat()}",
            "stages": rows,
        }
        return await self._render("stage_list", persona_id, payload, file_tag="list", cache=True)

    async def render_stage(
        self,
        stage: dict[str, Any],
        persona_id: str,
        *,
        status: str = "approved",
        draft_metadata: dict[str, Any] | None = None,
    ) -> str:
        weekly = [
            {
                **rule,
                "weekday_text": "、".join(WEEKDAY_LABELS.get(day, str(day)) for day in rule.get("weekdays", [])),
                "participants_text": _joined(rule.get("participants", [])),
            }
            for rule in stage.get("weekly_rules", [])
        ]
        special = [{**event, "participants_text": _joined(event.get("participants", []))} for event in stage.get("special_dates", [])]
        metadata = None
        if draft_metadata:
            source = str(draft_metadata.get("source", ""))
            metadata = {
                "source": SOURCE_LABELS.get(source, source),
                "created_at": str(draft_metadata.get("created_at", "")),
                "requirements": str(draft_metadata.get("requirements", "")),
            }
        payload = {
            "title": stage["name"],
            "subtitle": f"{persona_id} · {_kind(stage['kind'])}",
            "status": status,
            "status_label": "待批准草稿" if status == "draft" else "已批准",
            "stage": {**stage, "kind_label": _kind(stage["kind"]), "weekly_rules": weekly, "special_dates": special},
            "draft_metadata": metadata,
        }
        return await self._render("stage", persona_id, payload, file_tag=f"stage-{status}", cache=True)

    # ------------------------------------------------------------------ rendering

    def _look(self) -> dict[str, Any]:
        theme = str(self.settings.get("image_theme", "dark")).strip().lower()
        try:
            width = int(self.settings.get("image_width", 1200))
        except (TypeError, ValueError):
            width = 1200
        font = "".join(char for char in str(self.settings.get("image_font", "")).strip() if char not in ";{}")
        return {
            "theme": theme if theme in ("dark", "light") else "dark",
            "width": min(WIDTH_RANGE[1], max(WIDTH_RANGE[0], width)),
            "font_stack": (f'"{font}", ' if font else "") + BASE_FONTS,
        }

    def _base_data(self, view: str, persona_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"view": view, "persona_id": persona_id, "character": None, **self._look(), **payload}

    async def _render(self, view: str, persona_id: str, payload: dict[str, Any], *, file_tag: str, cache: bool) -> str:
        """Render to ``image_cache/<persona>-<tag>-<hash|uuid>.png``; cached cards are reused."""
        data = self._base_data(view, persona_id, payload)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if cache:
            fingerprint = self.template + "\n" + json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            suffix = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:20]
        else:
            suffix = uuid.uuid4().hex
        target = self.cache_dir / f"{_persona_key(persona_id)}-{file_tag}-{suffix}.png"
        if cache and target.exists():
            return str(target)
        produced = Path(
            await self.render_html(self.template, data, return_url=False, options={"full_page": True, "type": "png"})
        )
        if not produced.exists():
            raise RuntimeError(f"the renderer reported {produced}, but no file is there")
        shutil.copyfile(produced, target)
        try:
            if produced.resolve() != target.resolve():
                produced.unlink()
        except OSError:
            pass
        return str(target)

    _persona_key = staticmethod(_persona_key)
    _character_data = staticmethod(_character)
