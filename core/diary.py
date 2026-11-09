from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

LOCK = threading.RLock()
MAX_ENTRIES = 80


def _path(data_dir: Path) -> Path:
    return Path(data_dir) / "diary.json"


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


def list_entries(
    data_dir: Path, persona: str, limit: int = 14
) -> list[dict[str, Any]]:
    with LOCK:
        content = _load(data_dir)
        entries = (
            content.get("personas", {}).get(str(persona), {}).get("entries")
            or []
        )
    return list(entries)[-max(1, int(limit or 14)) :]


def has_entry(data_dir: Path, persona: str, day: str, source: str) -> bool:
    for entry in list_entries(data_dir, persona, limit=MAX_ENTRIES):
        if str(entry.get("date") or "") == str(day):
            if str(entry.get("source") or "") == str(source):
                return True
    return False


def add_entry(
    data_dir: Path,
    persona: str,
    day: str,
    title: str,
    summary: str,
    *,
    source: str = "auto",
    now: datetime | None = None,
) -> dict[str, Any]:
    moment = now or datetime.now()
    entries = list_entries(data_dir, persona, limit=MAX_ENTRIES)
    entry = {
        "date": str(day or moment.date().isoformat()),
        "title": str(title or "这天")[:80],
        "summary": str(summary or "")[:1200],
        "source": str(source or "auto")[:20],
        "created_at": moment.isoformat(timespec="seconds"),
    }
    with LOCK:
        content = _load(data_dir)
        personas = content.setdefault("personas", {})
        state = personas.setdefault(str(persona), {"entries": []})
        existing = state.setdefault("entries", [])
        replaced = False
        if source == "auto":
            for index, item in enumerate(existing):
                if (
                    str(item.get("date") or "") == entry["date"]
                    and str(item.get("source") or "") == "auto"
                ):
                    existing[index] = entry
                    replaced = True
                    break
        if not replaced:
            existing.append(entry)
        state["entries"] = existing[-MAX_ENTRIES:]
        _save(data_dir, content)
    return entry


def format_entries(entries: list[dict[str, Any]], limit: int = 8) -> str:
    if not entries:
        return "还没有写日记。"
    lines = []
    for entry in entries[-limit:]:
        lines.append(
            f"{entry.get('date')}  {entry.get('title')}\n"
            f"{entry.get('summary')}"
        )
    return "\n\n".join(lines)
