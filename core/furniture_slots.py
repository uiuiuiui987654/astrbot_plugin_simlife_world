from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SLOTS_PATH = Path(__file__).with_name("furniture_slots.json")


def load_slots() -> list[dict[str, Any]]:
    try:
        payload = json.loads(SLOTS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    slots = payload.get("slots") if isinstance(payload, dict) else payload
    if not isinstance(slots, list):
        return []
    return [slot for slot in slots if isinstance(slot, dict) and slot.get("id")]


def find_slot(slot_id: str) -> dict[str, Any] | None:
    key = str(slot_id or "").strip()
    if not key:
        return None
    return next((slot for slot in load_slots() if slot.get("id") == key), None)


def slot_fits(slot: dict[str, Any], goods: dict[str, Any]) -> bool:
    if not slot or not goods or not goods.get("installable"):
        return False
    wanted = {str(tag) for tag in (goods.get("slot_tags") or []) if str(tag)}
    have = {str(tag) for tag in (slot.get("tags") or []) if str(tag)}
    return bool(wanted & have)


def occupied_slot_ids(data_dir: Path, persona: str) -> dict[str, dict[str, Any]]:
    from . import money

    occupied: dict[str, dict[str, Any]] = {}
    for item in money.possessions(data_dir, persona):
        slot_id = str(item.get("slot_id") or "").strip()
        if slot_id:
            occupied[slot_id] = item
    return occupied


def first_free_slot(
    data_dir: Path,
    persona: str,
    goods: dict[str, Any],
    room: str = "",
) -> dict[str, Any] | None:
    room_name = str(room or "").strip()
    occupied = occupied_slot_ids(data_dir, persona)
    for slot in load_slots():
        if room_name and str(slot.get("room") or "") != room_name:
            continue
        if str(slot.get("id") or "") in occupied:
            continue
        if slot_fits(slot, goods):
            return slot
    return None


def describe_slots(
    data_dir: Path,
    persona: str,
    *,
    goods: dict[str, Any] | None = None,
    room: str = "",
) -> list[dict[str, Any]]:
    room_name = str(room or "").strip()
    occupied = occupied_slot_ids(data_dir, persona)
    result: list[dict[str, Any]] = []
    for slot in load_slots():
        if room_name and str(slot.get("room") or "") != room_name:
            continue
        entry = dict(slot)
        occupant = occupied.get(str(slot.get("id") or ""))
        entry["occupied"] = bool(occupant)
        entry["occupied_by"] = str((occupant or {}).get("name") or "")
        entry["fits"] = bool(goods is not None and slot_fits(slot, goods))
        result.append(entry)
    return result
