from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from .jsonio import STATE_LOCK, atomic_write_json

LOCK = STATE_LOCK  # shared re-entrant lock for all state files (see jsonio)
DEFAULT_TRIP_MINUTES = 90
TRIP_FUEL_COST = 12.0
REFUEL_COST = 60.0
REFUEL_TO = 100.0
DESTINATIONS = (
    "海边",
    "公园",
    "咖啡馆",
    "书店",
    "美术馆",
    "电影院",
    "商场",
    "办公室",
    "老街",
    "食堂",
    "植物园",
    "河岸步道",
    "湖畔",
    "露营地",
    "游乐园",
    "花店",
    "面包店",
    "图书馆",
    "超市",
    "山上",
    "江边",
    "夜市",
)
DEFAULT_VEHICLE = {
    "id": "car_white",
    "name": "白色小车",
    "plate": "沪A·M320",
    "fuel": 68,
    "status": "parked",
    "driver": "",
    "destination": "",
    "started_at": "",
    "eta": "",
    "trip_id": "",
}
DEFAULT_VEHICLES = [
    DEFAULT_VEHICLE,
    {
        "id": "car_jeep",
        "name": "吉普",
        "plate": "沪A·J4X4",
        "fuel": 82,
        "status": "parked",
        "driver": "",
        "destination": "",
        "started_at": "",
        "eta": "",
        "trip_id": "",
    },
    {
        "id": "car_sports",
        "name": "跑车",
        "plate": "沪A·GT886",
        "fuel": 74,
        "status": "parked",
        "driver": "",
        "destination": "",
        "started_at": "",
        "eta": "",
        "trip_id": "",
    },
]


def _path(data_dir: Path) -> Path:
    return Path(data_dir) / "garage.json"


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


def _parse_time(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value or ""))
    except (TypeError, ValueError):
        return None


def _ensure_persona(content: dict[str, Any], persona: str) -> dict[str, Any]:
    personas = content.setdefault("personas", {})
    state = personas.setdefault(
        str(persona), {"vehicles": [], "trips": []}
    )
    if not isinstance(state.get("vehicles"), list):
        state["vehicles"] = []
    if not isinstance(state.get("trips"), list):
        state["trips"] = []
    if not state["vehicles"]:
        state["vehicles"] = [dict(item) for item in DEFAULT_VEHICLES]
    else:
        existing = {
            str(item.get("id") or "")
            for item in state["vehicles"]
            if isinstance(item, dict)
        }
        for default in DEFAULT_VEHICLES:
            if str(default.get("id") or "") not in existing:
                state["vehicles"].append(dict(default))
    return state


def _select_vehicle(
    state: dict[str, Any], vehicle_id: str = ""
) -> dict[str, Any] | None:
    vehicles = [
        item
        for item in state.get("vehicles") or []
        if isinstance(item, dict)
    ]
    wanted = str(vehicle_id or "").strip()
    if wanted:
        for vehicle in vehicles:
            if str(vehicle.get("id") or "") == wanted:
                return vehicle
        for vehicle in vehicles:
            if str(vehicle.get("name") or "") == wanted:
                return vehicle
        return None
    return vehicles[0] if vehicles else None


def _trip_for_vehicle(
    state: dict[str, Any], vehicle: dict[str, Any]
) -> dict[str, Any] | None:
    trip_id = str(vehicle.get("trip_id") or "")
    if not trip_id:
        return None
    for item in reversed(state.get("trips") or []):
        if isinstance(item, dict) and str(item.get("id") or "") == trip_id:
            return dict(item)
    return None


def _finish(state: dict[str, Any], now: datetime) -> bool:
    changed = False
    for vehicle in state.get("vehicles") or []:
        if not isinstance(vehicle, dict) or vehicle.get("status") != "out":
            continue
        eta = _parse_time(vehicle.get("eta"))
        if eta is None or eta > now:
            continue
        trip_id = str(vehicle.get("trip_id") or "")
        vehicle.update(
            {
                "status": "parked",
                "driver": "",
                "destination": "",
                "started_at": "",
                "eta": "",
                "trip_id": "",
            }
        )
        for trip in state.get("trips") or []:
            if isinstance(trip, dict) and str(trip.get("id") or "") == trip_id:
                trip["status"] = "returned"
                trip["returned_at"] = now.isoformat(timespec="seconds")
        changed = True
    if changed:
        state["trips"] = list(state.get("trips") or [])[-30:]
    return changed


def snapshot(
    data_dir: Path,
    persona: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    moment = now or datetime.now()
    with LOCK:
        content = _load(data_dir)
        existing = (content.get("personas") or {}).get(str(persona)) or {}
        before_count = len(existing.get("vehicles") or [])
        state = _ensure_persona(content, persona)
        migrated = len(state.get("vehicles") or []) != before_count
        if migrated or _finish(state, moment):
            _save(data_dir, content)
        vehicles: list[dict[str, Any]] = []
        for entry in state.get("vehicles") or []:
            if not isinstance(entry, dict):
                continue
            item = dict(entry)
            item["trip"] = _trip_for_vehicle(state, entry)
            vehicles.append(item)
        vehicle = vehicles[0] if vehicles else {}
        trip = vehicle.get("trip") if vehicle else None
        return {
            "vehicle": dict(vehicle),
            "vehicles": vehicles,
            "trip": trip,
            "destinations": list(DESTINATIONS),
            "trip_fuel_cost": TRIP_FUEL_COST,
            "refuel_cost": REFUEL_COST,
            "history": [
                dict(item)
                for item in (state.get("trips") or [])[-10:][::-1]
                if isinstance(item, dict)
            ],
        }


def start(
    data_dir: Path,
    persona: str,
    destination: str,
    driver: str,
    *,
    now: datetime | None = None,
    minutes: int = DEFAULT_TRIP_MINUTES,
    vehicle_id: str = "",
) -> dict[str, Any]:
    moment = now or datetime.now()
    destination = str(destination or "").strip()[:20]
    if not destination:
        return {"ok": False, "error": "先选一个目的地"}
    driver = "master" if str(driver or "") == "master" else "self"
    with LOCK:
        content = _load(data_dir)
        state = _ensure_persona(content, persona)
        _finish(state, moment)
        vehicle = _select_vehicle(state, vehicle_id)
        if vehicle is None:
            return {"ok": False, "error": "没有这辆车"}
        vehicle_name = str(vehicle.get("name") or "车")
        if vehicle.get("status") == "out":
            return {"ok": False, "error": f"{vehicle_name}已经开出去了"}
        fuel = float(vehicle.get("fuel") or 0.0)
        if fuel < TRIP_FUEL_COST:
            return {"ok": False, "error": f"{vehicle_name}油不够了，先去车库加油"}
        vehicle["fuel"] = round(max(0.0, fuel - TRIP_FUEL_COST), 1)
        trip_id = "trip_" + uuid.uuid4().hex[:10]
        eta = moment + timedelta(minutes=max(30, min(int(minutes or 90), 240)))
        vehicle.update(
            {
                "status": "out",
                "driver": driver,
                "destination": destination,
                "started_at": moment.isoformat(timespec="seconds"),
                "eta": eta.isoformat(timespec="seconds"),
                "trip_id": trip_id,
            }
        )
        state["trips"].append(
            {
                "id": trip_id,
                "persona": str(persona),
                "vehicle_id": str(vehicle.get("id") or ""),
                "vehicle_name": vehicle_name,
                "destination": destination,
                "driver": driver,
                "started_at": moment.isoformat(timespec="seconds"),
                "eta": eta.isoformat(timespec="seconds"),
                "status": "out",
                "noted": False,
            }
        )
        state["trips"] = state["trips"][-30:]
        _save(data_dir, content)
        return {
            "ok": True,
            "vehicle": dict(vehicle),
            "trip": dict(state["trips"][-1]),
            "destinations": list(DESTINATIONS),
        }


def return_home(
    data_dir: Path,
    persona: str,
    *,
    now: datetime | None = None,
    vehicle_id: str = "",
) -> dict[str, Any]:
    moment = now or datetime.now()
    with LOCK:
        content = _load(data_dir)
        state = _ensure_persona(content, persona)
        vehicle = _select_vehicle(state, vehicle_id)
        if vehicle is None:
            return {"ok": False, "error": "没有这辆车"}
        vehicle_name = str(vehicle.get("name") or "车")
        if vehicle.get("status") != "out":
            return {"ok": False, "error": f"{vehicle_name}已经在车库了"}
        trip_id = str(vehicle.get("trip_id") or "")
        returned_trip = None
        for trip in state.get("trips") or []:
            if isinstance(trip, dict) and str(trip.get("id") or "") == trip_id:
                trip["status"] = "returned"
                trip["returned_at"] = moment.isoformat(timespec="seconds")
                returned_trip = dict(trip)
        vehicle.update(
            {
                "status": "parked",
                "driver": "",
                "destination": "",
                "started_at": "",
                "eta": "",
                "trip_id": "",
            }
        )
        _save(data_dir, content)
        return {"ok": True, "vehicle": dict(vehicle), "trip": returned_trip}


def refuel(
    data_dir: Path,
    persona: str,
    *,
    now: datetime | None = None,
    vehicle_id: str = "",
) -> dict[str, Any]:
    moment = now or datetime.now()
    with LOCK:
        content = _load(data_dir)
        state = _ensure_persona(content, persona)
        _finish(state, moment)
        vehicle = _select_vehicle(state, vehicle_id)
        if vehicle is None:
            return {"ok": False, "error": "没有这辆车"}
        vehicle_name = str(vehicle.get("name") or "车")
        if vehicle.get("status") == "out":
            return {"ok": False, "error": f"{vehicle_name}不在车库，暂时加不了油"}
        vehicle["fuel"] = REFUEL_TO
        _save(data_dir, content)
        return {
            "ok": True,
            "vehicle": dict(vehicle),
            "cost": REFUEL_COST,
        }


def recent_returns(
    data_dir: Path,
    persona: str,
    *,
    now: datetime | None = None,
    hours: int = 36,
) -> list[dict[str, Any]]:
    moment = now or datetime.now()
    cutoff = moment - timedelta(hours=max(1, int(hours or 36)))
    with LOCK:
        state = _ensure_persona(_load(data_dir), persona)
    result = []
    for trip in state.get("trips") or []:
        if not isinstance(trip, dict) or trip.get("status") != "returned":
            continue
        if trip.get("noted"):
            continue
        returned_at = _parse_time(trip.get("returned_at"))
        if returned_at is not None and returned_at >= cutoff:
            result.append(dict(trip))
    return result


def mark_noted(
    data_dir: Path,
    persona: str,
    trip_id: str,
) -> None:
    with LOCK:
        content = _load(data_dir)
        state = _ensure_persona(content, persona)
        changed = False
        for trip in state.get("trips") or []:
            if isinstance(trip, dict) and str(trip.get("id") or "") == str(trip_id):
                trip["noted"] = True
                changed = True
                break
        if changed:
            _save(data_dir, content)


def context(
    data_dir: Path,
    persona: str,
    *,
    now: datetime | None = None,
) -> str:
    snapshot_value = snapshot(data_dir, persona, now=now)
    vehicles = snapshot_value.get("vehicles") or []
    out = [item for item in vehicles if item.get("status") == "out" and item.get("trip")]
    if out:
        parts = []
        for vehicle in out:
            trip = vehicle.get("trip") or {}
            driver = "主人开车" if trip.get("driver") == "master" else "她自己在开"
            eta = str(trip.get("eta") or "")
            eta_text = eta[11:16] if len(eta) >= 16 else eta
            parts.append(
                f"{vehicle.get('name') or '车'}不在，{driver}带她去了"
                f"{trip.get('destination')}，预计 {eta_text} 回来"
            )
        return "；".join(parts) + "。"
    names = [str(item.get("name") or "车") for item in vehicles]
    parked = "、".join(names) if names else "白色小车"
    return f"车库停着{parked}，车况正常。"
