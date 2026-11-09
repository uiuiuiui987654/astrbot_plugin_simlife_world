"""Small durable queue of camera/photo events for the next AI turn.

The observer window takes photos through ``core.camera_photo``.  That path does
not otherwise leave a trace in the chat, so the next user message would see no
evidence that the photo happened.  This queue lets the chat prompt tell the
character that the camera was used, without storing or re-sending image bytes.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

LOCK = threading.RLock()
EVENTS_FILE = "camera_events.json"
MAX_AGE_HOURS = 12
MAX_EVENTS_PER_PERSONA = 12


def _path(data_dir: Path) -> Path:
    return Path(data_dir) / EVENTS_FILE


def _load(data_dir: Path) -> dict[str, Any]:
    path = _path(data_dir)
    if not path.exists():
        return {"schema_version": 1, "personas": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "personas": {}}
    if not isinstance(payload, dict):
        return {"schema_version": 1, "personas": {}}
    payload.setdefault("personas", {})
    return payload


def _save(data_dir: Path, payload: dict[str, Any]) -> None:
    path = _path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def _parse_time(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value or ""))
    except (TypeError, ValueError):
        return None


def _prune(events: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    cutoff = now - timedelta(hours=MAX_AGE_HOURS)
    kept: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        moment = _parse_time(event.get("at"))
        if moment is None or moment < cutoff:
            continue
        kept.append(event)
    return kept[-MAX_EVENTS_PER_PERSONA:]


def record(
    data_dir: Path,
    persona: str,
    target: str,
    caption: str,
    *,
    item_name: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Append one successful camera event for ``persona``."""
    moment = now or datetime.now()
    event = {
        "id": "camera_" + uuid.uuid4().hex[:10],
        "at": moment.isoformat(timespec="seconds"),
        "target": str(target or "room")[:20],
        "caption": str(caption or "")[:300],
        "item_name": str(item_name or "")[:80],
    }
    with LOCK:
        payload = _load(data_dir)
        personas = payload.setdefault("personas", {})
        events = personas.get(str(persona))
        if not isinstance(events, list):
            events = []
        events.append(event)
        personas[str(persona)] = _prune(events, moment)
        _save(data_dir, payload)
    return event


def take_pending(
    data_dir: Path,
    persona: str,
    *,
    now: datetime | None = None,
    limit: int = 2,
) -> list[dict[str, Any]]:
    """Remove and return the most recent pending camera events."""
    moment = now or datetime.now()
    with LOCK:
        payload = _load(data_dir)
        personas = payload.setdefault("personas", {})
        events = personas.get(str(persona))
        if not isinstance(events, list) or not events:
            return []
        events = _prune(events, moment)
        selected = events[-max(1, int(limit)) :]
        remaining = events[: len(events) - len(selected)]
        if remaining:
            personas[str(persona)] = remaining
        else:
            personas.pop(str(persona), None)
        _save(data_dir, payload)
    return [dict(event) for event in selected]


def peek(data_dir: Path, persona: str) -> list[dict[str, Any]]:
    with LOCK:
        payload = _load(data_dir)
        events = (payload.get("personas") or {}).get(str(persona))
        return [dict(event) for event in events if isinstance(event, dict)] if isinstance(events, list) else []
