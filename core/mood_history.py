from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

LOCK = threading.RLock()
MAX_ENTRIES = 180
MIN_WRITE_GAP = timedelta(minutes=10)


def _path(data_dir: Path) -> Path:
    return Path(data_dir) / "mood_history.json"


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


def record(
    data_dir: Path,
    persona: str,
    needs: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    if not isinstance(needs, dict) or not needs:
        return {"ok": False, "error": "缺少状态"}
    moment = now or datetime.now()
    day = moment.date().isoformat()
    values = {}
    for key in ("mood", "energy", "satiety", "hydration", "health"):
        value = needs.get(key)
        if isinstance(value, (int, float)):
            values[key] = round(float(value), 1)
    if not values:
        return {"ok": False, "error": "状态里没有可记录数值"}
    with LOCK:
        content = _load(data_dir)
        personas = content.setdefault("personas", {})
        entries = personas.setdefault(str(persona), [])
        if entries:
            last = entries[-1]
            try:
                last_at = datetime.fromisoformat(
                    str(last.get("at") or "")
                )
            except ValueError:
                last_at = None
            if (
                str(last.get("date") or "") == day
                and last_at is not None
                and moment - last_at < MIN_WRITE_GAP
            ):
                return {"ok": True, "skipped": True, "entry": last}
        entry = {
            "date": day,
            "at": moment.isoformat(timespec="seconds"),
            **values,
        }
        if entries and str(entries[-1].get("date") or "") == day:
            entries[-1] = entry
        else:
            entries.append(entry)
        personas[str(persona)] = entries[-MAX_ENTRIES:]
        _save(data_dir, content)
    return {"ok": True, "entry": entry}


def list_entries(
    data_dir: Path, persona: str, limit: int = 30
) -> list[dict[str, Any]]:
    with LOCK:
        content = _load(data_dir)
        entries = content.get("personas", {}).get(str(persona), [])
    return list(entries)[-max(1, int(limit or 30)) :]


def between(
    data_dir: Path,
    persona: str,
    start: str,
    end: str,
) -> list[dict[str, Any]]:
    return [
        entry
        for entry in list_entries(data_dir, persona, limit=MAX_ENTRIES)
        if start <= str(entry.get("date") or "") <= end
    ]
