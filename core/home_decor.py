from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

LOCK = threading.RLock()


def _path(data_dir: Path) -> Path:
    return Path(data_dir) / "home_decor.json"


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


def _entries(content: dict[str, Any], persona: str) -> dict[str, Any]:
    personas = content.setdefault("personas", {})
    entries = personas.setdefault(str(persona), {})
    if not isinstance(entries, dict):
        entries = {}
        personas[str(persona)] = entries
    return entries


def overrides(data_dir: Path, persona: str) -> dict[str, dict[str, Any]]:
    with LOCK:
        return dict(_entries(_load(data_dir), persona))


def place(
    data_dir: Path,
    persona: str,
    item_id: str,
    room: str,
    x: Any,
    y: Any,
    *,
    facing: str = "S",
) -> dict[str, Any]:
    item_key = str(item_id or "").strip()
    room_name = str(room or "").strip()[:10]
    if not item_key or not room_name:
        return {"ok": False, "error": "要指定家具和房间"}
    try:
        nx = round(max(0.05, min(0.95, float(x))), 3)
        ny = round(max(0.05, min(0.95, float(y))), 3)
    except (TypeError, ValueError):
        return {"ok": False, "error": "摆放位置无效"}
    with LOCK:
        content = _load(data_dir)
        entries = _entries(content, persona)
        entries[item_key] = {
            "item_id": item_key,
            "room": room_name,
            "place": {
                "x": nx,
                "y": ny,
                "facing": str(facing or "S")[:1],
            },
            "stored": False,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        _save(data_dir, content)
    return {"ok": True, "item_id": item_key, "room": room_name, "place": entries[item_key]["place"]}


def store(data_dir: Path, persona: str, item_id: str) -> dict[str, Any]:
    item_key = str(item_id or "").strip()
    if not item_key:
        return {"ok": False, "error": "没有选中家具"}
    with LOCK:
        content = _load(data_dir)
        entries = _entries(content, persona)
        current = dict(entries.get(item_key) or {})
        current["item_id"] = item_key
        current["stored"] = True
        current["updated_at"] = datetime.now().isoformat(timespec="seconds")
        entries[item_key] = current
        _save(data_dir, content)
    return {"ok": True, "item_id": item_key, "stored": True}


def reset(data_dir: Path, persona: str, item_id: str = "") -> dict[str, Any]:
    with LOCK:
        content = _load(data_dir)
        entries = _entries(content, persona)
        if item_id:
            entries.pop(str(item_id).strip(), None)
        else:
            entries.clear()
        _save(data_dir, content)
    return {"ok": True}


def apply_items(
    items: list[dict[str, Any]],
    data_dir: Path,
    persona: str,
) -> list[dict[str, Any]]:
    """Apply custom positions and hide stored base furniture."""
    if not persona:
        return items
    entries = overrides(data_dir, persona)
    result: list[dict[str, Any]] = []
    for raw in items:
        item = dict(raw)
        item_id = str(item.get("id") or "")
        entry = entries.get(item_id)
        if isinstance(entry, dict):
            if entry.get("stored"):
                continue
            room = str(entry.get("room") or "").strip()
            place = entry.get("place")
            if room:
                item["room"] = room
            if isinstance(place, dict):
                item["custom_place"] = True
                item["place"] = {
                    "x": place.get("x"),
                    "y": place.get("y"),
                    "facing": place.get("facing") or "S",
                }
        result.append(item)
    return result


def describe(
    items: list[dict[str, Any]],
    data_dir: Path,
    persona: str,
) -> list[dict[str, Any]]:
    entries = overrides(data_dir, persona)
    result: list[dict[str, Any]] = []
    for raw in items:
        item = dict(raw)
        item_id = str(item.get("id") or "")
        entry = entries.get(item_id) if item_id else None
        item["stored"] = bool(entry and entry.get("stored"))
        item["custom_place"] = bool(entry and entry.get("place"))
        if entry:
            item["override_room"] = str(entry.get("room") or "")
            item["override_place"] = entry.get("place")
        result.append(item)
    return result
