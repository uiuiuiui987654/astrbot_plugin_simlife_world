from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from . import money

LOCK = threading.RLock()


def _path(data_dir: Path) -> Path:
    return Path(data_dir) / "deliveries.json"


def _load(data_dir: Path) -> dict[str, Any]:
    path = _path(data_dir)
    if not path.exists():
        return {"schema_version": 1, "orders": []}
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "orders": []}
    if not isinstance(content, dict):
        return {"schema_version": 1, "orders": []}
    if not isinstance(content.get("orders"), list):
        content["orders"] = []
    if not isinstance(content.get("delivered"), list):
        content["delivered"] = []
    return content


def _save(data_dir: Path, content: dict[str, Any]) -> None:
    path = _path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def place_order(
    data_dir: Path,
    persona: str,
    goods: dict[str, Any],
    quantity: int,
    amount: float,
    *,
    now: datetime | None = None,
    minutes: int = 3,
) -> dict[str, Any]:
    moment = now or datetime.now()
    deliver_at = moment + timedelta(minutes=max(0, int(minutes or 0)))
    order = {
        "id": "order-" + uuid.uuid4().hex[:10],
        "persona": str(persona),
        "goods": {
            "id": str(goods.get("id") or ""),
            "name": str(goods.get("name") or "商品"),
            "category": str(goods.get("category") or ""),
            "price": round(float(goods.get("price") or 0.0), 2),
            "book_id": str(goods.get("book_id") or ""),
        },
        "quantity": max(1, int(quantity or 1)),
        "amount": round(float(amount or 0.0), 2),
        "ordered_at": moment.isoformat(timespec="seconds"),
        "deliver_at": deliver_at.isoformat(timespec="seconds"),
    }
    with LOCK:
        content = _load(data_dir)
        content["orders"].append(order)
        _save(data_dir, content)
    return order


def list_orders(data_dir: Path, persona: str) -> list[dict[str, Any]]:
    with LOCK:
        orders = _load(data_dir).get("orders") or []
    return [
        order
        for order in orders
        if str(order.get("persona") or "") == str(persona)
    ]


def deliver_due(
    data_dir: Path,
    persona: str,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    moment = now or datetime.now()
    delivered: list[dict[str, Any]] = []
    with LOCK:
        content = _load(data_dir)
        remaining = []
        for order in content.get("orders") or []:
            if str(order.get("persona") or "") != str(persona):
                remaining.append(order)
                continue
            try:
                due = datetime.fromisoformat(str(order.get("deliver_at") or ""))
            except ValueError:
                due = moment
            if due > moment:
                remaining.append(order)
                continue
            goods = order.get("goods") or {}
            count = max(1, int(order.get("quantity") or 1))
            for _ in range(count):
                money.add_possession(
                    data_dir,
                    persona,
                    {
                        "id": goods.get("id"),
                        "name": goods.get("name"),
                        "category": goods.get("category"),
                        "price": goods.get("price"),
                        "book_id": goods.get("book_id"),
                    },
                    source="delivery",
                    at=moment,
                )
            delivered.append(order)
            delivered_entry = dict(order)
            delivered_entry["delivered_at"] = moment.isoformat(
                timespec="seconds"
            )
            content.setdefault("delivered", []).append(delivered_entry)
        content["orders"] = remaining
        content["delivered"] = content.get("delivered", [])[-60:]
        _save(data_dir, content)
    return delivered


def recent_delivered(
    data_dir: Path,
    persona: str,
    *,
    now: datetime | None = None,
    hours: int = 6,
) -> list[dict[str, Any]]:
    moment = now or datetime.now()
    cutoff = moment - timedelta(hours=max(1, int(hours or 6)))
    with LOCK:
        entries = _load(data_dir).get("delivered") or []
    result = []
    for entry in entries:
        if str(entry.get("persona") or "") != str(persona):
            continue
        try:
            delivered_at = datetime.fromisoformat(
                str(entry.get("delivered_at") or "")
            )
        except ValueError:
            continue
        if delivered_at >= cutoff:
            result.append(entry)
    return result


def pending_summary(data_dir: Path, persona: str) -> str:
    orders = list_orders(data_dir, persona)
    if not orders:
        return ""
    lines = []
    for order in orders[-5:]:
        goods = order.get("goods") or {}
        lines.append(
            f"{goods.get('name') or '商品'} ×{order.get('quantity') or 1}"
            f"（预计 {str(order.get('deliver_at') or '')[11:16]} 送到）"
        )
    return "；".join(lines)
