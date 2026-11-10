"""Per-request values shared by the dispatcher and the route handlers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class RouteContext:
    endpoint: str
    method: str
    now: datetime
    persona: str | None
    params: dict
    payload: dict
    # filled in by the POST dispatcher once the shared checks have run
    action: Any = None
    actual: Any = None
    current: Any = None
    item: Any = None
    item_id: Any = None
