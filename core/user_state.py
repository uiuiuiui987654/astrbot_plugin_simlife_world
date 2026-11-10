"""主人在观察窗里的状态：目前用于「我上床睡了」。

观察窗的床头/床点「我上床睡了」后，插件记下这个状态，之后的普通聊天、
智能注入和主动消息都会知道主人在睡觉，回复变轻、主动消息暂停。
状态最多保留 12 小时；主人醒来说话或按「我醒了」会自动清除。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from .jsonio import atomic_write_json

SLEEP_TTL_HOURS = 12


class UserStateStore:
    def __init__(self, data_dir: Path | str | None) -> None:
        self.data_dir = Path(data_dir) if data_dir else None
        self.path = self.data_dir / "user_state.json" if self.data_dir else None

    def load(self) -> dict[str, Any]:
        if self.path is None or not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def save(self, state: dict[str, Any]) -> None:
        if self.path is None:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(self.path, state)
        except OSError:
            pass

    def sleeping_since(self, now: datetime | None = None) -> datetime | None:
        state = self.load()
        if str(state.get("mode") or "") != "sleep":
            return None
        raw = str(state.get("since") or "").strip()
        if not raw:
            return None
        try:
            since = datetime.fromisoformat(raw)
        except ValueError:
            return None
        current = now or datetime.now()
        if (since.tzinfo is None) != (current.tzinfo is None):
            since = since.replace(tzinfo=None)
            current = current.replace(tzinfo=None)
        if since > current:
            return None
        if current - since > timedelta(hours=SLEEP_TTL_HOURS):
            return None
        return since

    def is_sleeping(self, now: datetime | None = None) -> bool:
        return self.sleeping_since(now) is not None

    def place(self) -> str:
        return str(self.load().get("place") or "床上")

    def set_sleeping(
        self,
        now: datetime | None = None,
        *,
        place: str = "卧室的床上",
        source: str = "window",
    ) -> dict[str, Any]:
        moment = now or datetime.now()
        state = {
            "mode": "sleep",
            "since": moment.isoformat(timespec="seconds"),
            "place": str(place or "卧室的床上"),
            "source": str(source or "window"),
        }
        self.save(state)
        return state

    def clear(self) -> None:
        state = self.load()
        if not state:
            return
        state.pop("mode", None)
        state["cleared_at"] = datetime.now().isoformat(timespec="seconds")
        self.save(state)

    def snapshot(self, now: datetime | None = None) -> dict[str, Any]:
        """给面板用的状态快照。"""
        since = self.sleeping_since(now)
        if since is None:
            return {"sleeping": False}
        return {
            "sleeping": True,
            "since": since.isoformat(timespec="seconds"),
            "place": self.place(),
        }

    def describe(self, now: datetime | None = None) -> str:
        since = self.sleeping_since(now)
        if since is None:
            return ""
        return (
            f"【主人状态】主人已经在{self.place()}睡觉了（{since.strftime('%H:%M')} 上床）。"
            "现在不适合拉着他聊天：回复要轻、短，可以道晚安或让他早点闭眼，别主动展开新话题。"
        )
