from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

LOCK = threading.RLock()
MAX_SCORE = 1000
DAILY_CAP = 20
LEVELS = (
    (0, "陌生"),
    (100, "眼熟"),
    (250, "熟悉"),
    (450, "亲近"),
    (650, "依赖"),
    (850, "很重要"),
)
ANNIVERSARY_DAYS = (7, 30, 100, 180, 365, 730)


def next_anniversary(days: int) -> int | None:
    for value in ANNIVERSARY_DAYS:
        if days < value:
            return value
    return None


def _path(data_dir: Path) -> Path:
    return Path(data_dir) / "affection.json"


def _load(data_dir: Path) -> dict[str, Any]:
    path = _path(data_dir)
    if not path.exists():
        return {"schema_version": 1, "personas": {}}
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "personas": {}}
    if not isinstance(content, dict):
        return {"schema_version": 1, "personas": {}}
    content.setdefault("personas", {})
    return content


def _save(data_dir: Path, content: dict[str, Any]) -> None:
    path = _path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def _level(score: int) -> tuple[str, int | None]:
    current = LEVELS[0][1]
    next_score = None
    for threshold, label in LEVELS:
        if score >= threshold:
            current = label
        elif next_score is None:
            next_score = threshold
    return current, next_score


def snapshot(
    data_dir: Path, persona: str, *, now: datetime | None = None
) -> dict[str, Any]:
    moment = now or datetime.now()
    with LOCK:
        content = _load(data_dir)
        state = content.get("personas", {}).get(str(persona), {})
    score = max(0, min(MAX_SCORE, int(state.get("score") or 0)))
    level, next_score = _level(score)
    first_seen = str(state.get("first_seen") or moment.date().isoformat())
    try:
        days_known = (
            moment.date() - datetime.fromisoformat(first_seen).date()
        ).days + 1
    except ValueError:
        days_known = 1
    daily_used = (
        int(state.get("added_today") or 0)
        if str(state.get("date") or "") == moment.date().isoformat()
        else 0
    )
    return {
        "persona": str(persona),
        "score": score,
        "level": level,
        "next_score": next_score,
        "days_known": max(1, days_known),
        "first_seen": first_seen,
        "is_anniversary": days_known in ANNIVERSARY_DAYS,
        "next_anniversary": next_anniversary(days_known),
        "nickname": str(state.get("nickname") or "主人"),
        "daily_points": max(0, daily_used),
        "daily_cap": DAILY_CAP,
        "daily_remaining": max(0, DAILY_CAP - daily_used),
        "milestones": list(state.get("milestones") or [])[-20:],
        "events": list(state.get("events") or [])[-20:],
    }


def set_nickname(
    data_dir: Path,
    persona: str,
    nickname: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    value = str(nickname or "").strip()[:12]
    if not value:
        return {"ok": False, "error": "称呼不能为空"}
    moment = now or datetime.now()
    with LOCK:
        content = _load(data_dir)
        personas = content.setdefault("personas", {})
        state = personas.setdefault(
            str(persona),
            {
                "score": 0,
                "added_today": 0,
                "date": moment.date().isoformat(),
                "first_seen": moment.date().isoformat(),
                "events": [],
                "milestones": [],
            },
        )
        state["nickname"] = value
        _save(data_dir, content)
    return {"ok": True, "nickname": value}


def add(
    data_dir: Path,
    persona: str,
    points: int,
    reason: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    moment = now or datetime.now()
    day = moment.date().isoformat()
    value = int(points or 0)
    if value <= 0:
        return snapshot(data_dir, persona)
    with LOCK:
        content = _load(data_dir)
        personas = content.setdefault("personas", {})
        state = personas.setdefault(
            str(persona),
            {
                "score": 0,
                "added_today": 0,
                "date": day,
                "first_seen": day,
                "events": [],
                "milestones": [],
            },
        )
        state.setdefault("first_seen", day)
        state.setdefault("milestones", [])
        if str(state.get("date") or "") != day:
            state["date"] = day
            state["added_today"] = 0
        remaining = max(0, DAILY_CAP - int(state.get("added_today") or 0))
        applied = min(value, remaining)
        if applied > 0:
            old_score = int(state.get("score") or 0)
            old_level, _ = _level(old_score)
            state["score"] = max(
                0, min(MAX_SCORE, old_score + applied)
            )
            state["added_today"] = int(state.get("added_today") or 0) + applied
            new_level, _ = _level(int(state["score"]))
            if new_level != old_level:
                milestones = state.get("milestones") or []
                milestones.append(
                    {
                        "at": moment.isoformat(timespec="seconds"),
                        "level": new_level,
                        "score": int(state["score"]),
                    }
                )
                state["milestones"] = milestones[-20:]
            events = state.get("events") or []
            events.append(
                {
                    "at": moment.isoformat(timespec="seconds"),
                    "points": applied,
                    "reason": str(reason or "")[:80],
                }
            )
            state["events"] = events[-60:]
            _save(data_dir, content)
    return snapshot(data_dir, persona, now=moment)


def format_status(data_dir: Path, persona: str) -> str:
    info = snapshot(data_dir, persona)
    lines = [
        f"好感度：{info['score']} / {MAX_SCORE} · {info['level']}",
        f"认识第 {info['days_known']} 天。",
        f"称呼：{info.get('nickname') or '主人'}。",
    ]
    if info.get("is_anniversary"):
        lines.append(f"今天是认识第 {info['days_known']} 天纪念日。")
    elif info.get("next_anniversary"):
        lines.append(
            f"下一个纪念日：认识第 {info['next_anniversary']} 天。"
        )
    if info.get("next_score"):
        lines.append(f"距离下一阶段：{max(0, info['next_score'] - info['score'])} 点")
    milestones = info.get("milestones") or []
    if milestones:
        latest = milestones[-1]
        lines.append(f"最近关系变化：进入「{latest.get('level')}」")
    events = info.get("events") or []
    for event in events[-3:]:
        lines.append(f"+{event.get('points')} · {event.get('reason')}")
    return "\n".join(lines)
