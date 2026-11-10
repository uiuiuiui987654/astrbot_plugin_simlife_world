from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from .jsonio import STATE_LOCK, atomic_write_json

LOCK = STATE_LOCK  # shared re-entrant lock for all state files (see jsonio)
DEFAULT_TTL_MINUTES = 120
KEY_LIMITS = {
    "energy": 100,
    "satiety": 100,
    "hydration": 100,
    "hygiene": 100,
    "mood": 100,
    "willingness": 100,
    "health": 100,
}


def _path(data_dir: Path) -> Path:
    return Path(data_dir) / "item_effects.json"


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
    atomic_write_json(path, content)


def add(
    data_dir: Path,
    persona: str,
    effects: dict[str, float],
    *,
    label: str = "",
    now: datetime | None = None,
    ttl_minutes: int = DEFAULT_TTL_MINUTES,
) -> dict[str, Any]:
    moment = now or datetime.now()
    cleaned = {
        key: round(float(value), 2)
        for key, value in (effects or {}).items()
        if key in KEY_LIMITS and float(value or 0) != 0
    }
    if not cleaned:
        return {"ok": False, "error": "没有实际效果"}
    expires = moment + timedelta(minutes=max(5, int(ttl_minutes or DEFAULT_TTL_MINUTES)))
    with LOCK:
        content = _load(data_dir)
        personas = content.setdefault("personas", {})
        state = personas.setdefault(str(persona), {"active": []})
        active = state.setdefault("active", [])
        active.append(
            {
                "label": str(label or "")[:60],
                "effects": cleaned,
                "started_at": moment.isoformat(timespec="seconds"),
                "expires_at": expires.isoformat(timespec="seconds"),
            }
        )
        state["active"] = active[-20:]
        _save(data_dir, content)
    return {"ok": True, "effects": cleaned, "expires_at": expires.isoformat(timespec="seconds")}


def _active_effects(
    state: dict[str, Any], now: datetime
) -> tuple[dict[str, float], bool]:
    total: dict[str, float] = {}
    kept = []
    changed = False
    for entry in state.get("active") or []:
        expires_text = str(entry.get("expires_at") or "")
        try:
            expires = datetime.fromisoformat(expires_text)
        except ValueError:
            changed = True
            continue
        if expires <= now:
            changed = True
            continue
        kept.append(entry)
        for key, value in (entry.get("effects") or {}).items():
            if key in KEY_LIMITS:
                total[key] = total.get(key, 0.0) + float(value or 0.0)
    state["active"] = kept
    return total, changed


def apply(
    data_dir: Path,
    persona: str,
    needs: dict[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    if not isinstance(needs, dict) or not needs:
        return needs
    moment = now or datetime.now()
    with LOCK:
        content = _load(data_dir)
        state = content.setdefault("personas", {}).setdefault(
            str(persona), {"active": []}
        )
        effects, changed = _active_effects(state, moment)
        if changed:
            _save(data_dir, content)
    if not effects:
        return needs
    adjusted = dict(needs)
    for key, value in effects.items():
        current = adjusted.get(key)
        if not isinstance(current, (int, float)):
            continue
        limit = KEY_LIMITS.get(key, 100)
        adjusted[key] = round(min(limit, max(0, float(current) + value)), 1)
    return adjusted
