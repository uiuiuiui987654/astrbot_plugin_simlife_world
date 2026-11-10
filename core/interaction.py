"""Immediate interactions driven by the observation window.

The window writes a small request file when the owner clicks the dining table
(or types a line of chat); the plugin picks it up, asks the model for a short
in-character reply, sends it to QQ when configured, and writes a response file
the window polls for the speech bubble.

Files (under ``<plugin data>/interactions``)::

    requests/<id>.json    written by the window, consumed by the plugin
    responses/<id>.json   written by the plugin, read by the window
    history.json          last interactions, newest last
"""

from __future__ import annotations

import difflib
import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from astrbot.api import logger

from .human_style import DIALOGUE_FLOW_RULE, HUMAN_CHAT_RULE
from .jsonio import atomic_write_json

MAX_CHAT_CHARS = 200
MAX_SPEECH_CHARS = 160
HISTORY_LIMIT = 60
STALE_MINUTES = 15
HANDLED_TTL_MINUTES = 60 * 24 * 7
REQUEST_KINDS = {"dish", "chat"}

DEFAULT_SETTINGS: dict[str, Any] = {
    "enable": True,
    "poll_seconds": 2,
    "sync_to_qq": True,
    "sync_umo": "",
    "allow_user_chat": True,
    "max_reply_chars": 120,
    "consume_ingredients": True,
    "history_minutes": 120,
    "history_messages": 8,
    "history_chars": 1000,
    "record_to_conversation": True,
    "repeat_guard": True,
    "insert_activity_enable": True,
    "insert_activity_minutes": 30,
    "insert_activity_ai_decide": True,
    "insert_activity_max_minutes": 120,
}

# 历史消息里 AstrBot 注入的时间戳，例如：
# <system_reminder>... Current datetime: 2026-11-01 23:20 (CST), Weekday: Sunday</system_reminder>
REMINDER_RE = re.compile(r"<system_reminder>.*?</system_reminder>", re.S)
DATETIME_RE = re.compile(r"Current datetime:\s*(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})")
ACTION_NOTE_RE = re.compile(
    r"^\s*[（(][^）)\n]{0,24}(?:接过|递过|拿起|端着|收下|接住)[^）)\n]{0,24}[）)]\s*"
)

# 每做一道菜，按单位大致消耗多少；数量不会超过冰箱里剩余的量。
CONSUME_BY_UNIT: dict[str, float] = {
    "克": 150.0,
    "g": 150.0,
    "毫升": 100.0,
    "ml": 100.0,
    "片": 2.0,
    "朵": 3.0,
    "个": 1.0,
    "颗": 1.0,
    "根": 1.0,
    "块": 1.0,
    "条": 1.0,
    "把": 1.0,
    "头": 1.0,
    "罐": 1.0,
    "盒": 1.0,
    "袋": 1.0,
}

# 模型偶尔会用别的叫法，先归一化再去冰箱里找。
INGREDIENT_ALIASES: dict[str, str] = {
    "西红柿": "番茄",
    "圣女果": "番茄",
    "马铃薯": "土豆",
    "洋芋": "土豆",
    "蛋": "鸡蛋",
    "土鸡蛋": "鸡蛋",
    "小葱": "葱",
    "香葱": "葱",
    "大葱": "葱",
    "蒜头": "蒜",
    "大蒜": "蒜",
    "五花肉": "猪肉",
    "猪里脊": "猪肉",
    "猪排": "猪肉",
    "牛腩块": "牛腩",
    "牛肉片": "牛肉",
    "鸡胸肉": "鸡胸",
    "鸡腿肉": "鸡腿",
    "虾": "虾仁",
    "鲜虾": "虾仁",
    "虾米": "虾仁",
    "鲈鱼片": "鲈鱼",
    "午餐肉罐头": "午餐肉",
    "火腿片": "火腿",
    "香肠片": "香肠",
}


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "开", "是"}


def _as_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, payload)


def _clean(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit]


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number:  # NaN
        return default
    return number


def _normalize_ingredient(name: str) -> str:
    text = _clean(name, 16)
    return INGREDIENT_ALIASES.get(text, text)


def _message_text(item: dict[str, Any]) -> str:
    """把一条历史消息压成纯文本，顺手去掉 AstrBot 注入的系统提醒。"""
    content = item.get("content")
    parts: list[str] = []
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, list):
        for part in content:
            if isinstance(part, str):
                parts.append(part)
                continue
            if not isinstance(part, dict):
                continue
            if part.get("type") not in (None, "text"):
                continue
            text = str(part.get("text") or "")
            if text:
                parts.append(text)
    text = REMINDER_RE.sub(" ", " ".join(parts))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:200]


def _message_time(item: dict[str, Any]) -> datetime | None:
    """从 system_reminder 里解析消息时间；没有就返回 None。"""
    raw = json.dumps(item, ensure_ascii=False)
    match = DATETIME_RE.search(raw)
    if not match:
        return None
    try:
        return datetime.strptime(f"{match.group(1)} {match.group(2)}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None


PROACTIVE_NOTE_RE = re.compile(r"^(?:（这条是你自己主动发的）|（你主动发起的消息）|\[系统任务[:：])")


def _is_proactive_note(text: str) -> bool:
    """主动消息写进历史时留下的说明行（不是对方真的说过的话）。"""
    return bool(PROACTIVE_NOTE_RE.match(str(text or "").strip()))


def _normalized_chars(text: str) -> str:
    """去掉空白和标点，只留可比较的文字。"""
    return re.sub(r"[\s\W_]+", "", str(text or ""))


def _longest_common_substring(a: str, b: str) -> int:
    """最长公共子串长度，用来抓「换个词复述同一句」的复读。"""
    if not a or not b:
        return 0
    best = 0
    previous = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        current = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                current[j] = previous[j - 1] + 1
                if current[j] > best:
                    best = current[j]
        previous = current
    return best


def _bigram_overlap(a: str, b: str) -> float:
    """两段文字的双字重合率（以较短的一方为分母）。"""
    if len(a) < 2 or len(b) < 2:
        return 0.0
    first = {a[i : i + 2] for i in range(len(a) - 1)}
    second = {b[i : i + 2] for i in range(len(b) - 1)}
    if not first or not second:
        return 0.0
    return len(first & second) / min(len(first), len(second))


def is_repetitive(speech: str, recent: list[str], *, threshold: float = 0.5) -> bool:
    """新回复是否在复读最近说过的话（共享长片段 / 双字重合 / 编辑相似度）。"""
    current = _normalized_chars(speech)
    if len(current) < 4:
        return False
    for line in recent or []:
        other = _normalized_chars(line)
        if len(other) < 4:
            continue
        if _longest_common_substring(current, other) >= 4:
            return True
        if _bigram_overlap(current, other) >= 0.45:
            return True
        if difflib.SequenceMatcher(None, current, other).ratio() >= threshold:
            return True
    return False


def _match_inventory(inventory: list[Any], name: str) -> dict[str, Any] | None:
    """Find the fridge entry that best matches a dish ingredient name."""
    target = _normalize_ingredient(name)
    if not target:
        return None
    entries = [item for item in inventory if isinstance(item, dict)]
    for item in entries:
        if _normalize_ingredient(str(item.get("name") or "")) == target:
            return item
    for item in entries:
        stored = _normalize_ingredient(str(item.get("name") or ""))
        if len(stored) >= 2 and len(target) >= 2 and (
            stored in target or target in stored
        ):
            return item
    return None


class InteractionService:
    """Request/response store plus prompt and reply helpers."""

    def __init__(self, data_dir: Path | None):
        self.data_dir = Path(data_dir) if data_dir else None

    # ---------------------------------------------------------------- settings

    @staticmethod
    def settings(raw: dict[str, Any] | None) -> dict[str, Any]:
        merged = dict(DEFAULT_SETTINGS)
        if isinstance(raw, dict):
            merged.update({k: v for k, v in raw.items() if v is not None})
        merged["enable"] = _as_bool(merged.get("enable"), True)
        merged["sync_to_qq"] = _as_bool(merged.get("sync_to_qq"), True)
        merged["allow_user_chat"] = _as_bool(merged.get("allow_user_chat"), True)
        merged["consume_ingredients"] = _as_bool(
            merged.get("consume_ingredients"), True
        )
        merged["poll_seconds"] = _as_int(merged.get("poll_seconds"), 2, 1, 30)
        merged["max_reply_chars"] = _as_int(
            merged.get("max_reply_chars"), 120, 20, 400
        )
        merged["history_minutes"] = _as_int(
            merged.get("history_minutes"), 120, 0, 1440
        )
        merged["history_messages"] = _as_int(
            merged.get("history_messages"), 8, 0, 40
        )
        merged["history_chars"] = _as_int(merged.get("history_chars"), 1000, 0, 4000)
        merged["record_to_conversation"] = _as_bool(
            merged.get("record_to_conversation"), True
        )
        merged["repeat_guard"] = _as_bool(merged.get("repeat_guard"), True)
        merged["insert_activity_enable"] = _as_bool(
            merged.get("insert_activity_enable"), True
        )
        merged["insert_activity_minutes"] = _as_int(
            merged.get("insert_activity_minutes"), 30, 5, 240
        )
        merged["insert_activity_ai_decide"] = _as_bool(
            merged.get("insert_activity_ai_decide"), True
        )
        merged["insert_activity_max_minutes"] = _as_int(
            merged.get("insert_activity_max_minutes"), 120, 5, 240
        )
        merged["sync_umo"] = str(merged.get("sync_umo") or "").strip()
        return merged

    # ------------------------------------------------------------------ paths

    def root(self) -> Path | None:
        if self.data_dir is None:
            return None
        return self.data_dir / "interactions"

    def requests_dir(self) -> Path | None:
        root = self.root()
        return root / "requests" if root else None

    def responses_dir(self) -> Path | None:
        root = self.root()
        return root / "responses" if root else None

    def history_path(self) -> Path | None:
        root = self.root()
        return root / "history.json" if root else None

    def _handled_path(self, request_id: str) -> Path | None:
        root = self.root()
        if root is None:
            return None
        safe = re.sub(r"[^A-Za-z0-9_.-]", "", request_id) or "unknown"
        return root / "handled" / f"{safe}.done"

    def _is_handled(self, request_id: str) -> bool:
        path = self._handled_path(request_id)
        if path is None or not path.exists():
            return False
        try:
            if time.time() - path.stat().st_mtime > HANDLED_TTL_MINUTES * 60:
                path.unlink(missing_ok=True)
                return False
        except OSError:
            return False
        return True

    def _mark_handled(self, request_id: str) -> None:
        path = self._handled_path(request_id)
        if path is None or not request_id:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(time.time()), encoding="utf-8")
        except OSError:
            logger.warning("[模拟人生] 无法记录已处理互动 id=%s", request_id)

    def _sent_path(self, request_id: str) -> Path | None:
        root = self.root()
        if root is None:
            return None
        safe = re.sub(r"[^A-Za-z0-9_.-]", "", request_id) or "unknown"
        return root / "sent" / f"{safe}.sent"

    def claim_sent(self, request_id: str) -> bool:
        """发送 QQ 前抢占一次，保证同一个互动只发一条。"""
        path = self._sent_path(request_id)
        if path is None:
            return False
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        except OSError:
            logger.warning("[模拟人生] 无法创建互动发送标记 id=%s", request_id)
            return True
        os.close(descriptor)
        return True

    def release_sent(self, request_id: str) -> None:
        path = self._sent_path(request_id)
        if path is not None:
            path.unlink(missing_ok=True)

    # --------------------------------------------------------------- requests

    def pending(self, limit: int = 3) -> list[dict[str, Any]]:
        """Return unhandled requests, oldest first."""
        directory = self.requests_dir()
        if directory is None or not directory.is_dir():
            return []
        cutoff = datetime.now() - timedelta(minutes=STALE_MINUTES)
        items: list[tuple[float, dict[str, Any]]] = []
        seen_ids: set[str] = set()
        for path in directory.glob("*.json"):
            payload = _read_json(path, None)
            if not isinstance(payload, dict):
                continue
            request_id = str(payload.get("id") or "").strip()
            if not request_id:
                continue
            if self._is_handled(request_id):
                logger.warning(
                    "[模拟人生] 丢弃已处理过的重复互动请求 id=%s file=%s",
                    request_id,
                    path.name,
                )
                path.unlink(missing_ok=True)
                continue
            if request_id in seen_ids:
                # 同一请求被重复写入（例如窗口重试）时只处理一次。
                logger.warning(
                    "[模拟人生] 丢弃重复互动请求文件 id=%s file=%s",
                    request_id,
                    path.name,
                )
                path.unlink(missing_ok=True)
                continue
            seen_ids.add(request_id)
            created = _parse_time(payload.get("created_at"))
            if created is not None and created < cutoff:
                # stale window request: drop so it cannot pop up hours later
                path.unlink(missing_ok=True)
                continue
            if self.response_path(request_id).exists():
                path.unlink(missing_ok=True)
                continue
            try:
                stamp = path.stat().st_mtime
            except OSError:
                stamp = 0.0
            items.append((stamp, payload))
        items.sort(key=lambda item: item[0])
        return [payload for _stamp, payload in items[: max(1, limit)]]

    def response_path(self, request_id: str) -> Path:
        directory = self.responses_dir()
        safe = re.sub(r"[^A-Za-z0-9_.-]", "", request_id) or "unknown"
        if directory is None:
            return Path(f"{safe}.json")
        return directory / f"{safe}.json"

    def _claim_lock_path(self, request_id: str) -> Path | None:
        directory = self.requests_dir()
        if directory is None:
            return None
        safe = re.sub(r"[^A-Za-z0-9_.-]", "", request_id) or "unknown"
        return directory / ".processing" / f"{safe}.lock"

    def claim(self, request: dict[str, Any]) -> bool:
        """原子认领一个请求，避免重复轮询、重载或双实例重复处理。"""
        directory = self.requests_dir()
        request_id = str(request.get("id") or "").strip()
        if directory is None or not request_id:
            return False
        if self._is_handled(request_id):
            logger.info(
                "[模拟人生] 互动已处理过，忽略重复认领 id=%s", request_id
            )
            return False
        processing = directory / ".processing"
        processing.mkdir(parents=True, exist_ok=True)
        lock = self._claim_lock_path(request_id)
        if lock is None:
            return False
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > STALE_MINUTES * 120:
                    lock.unlink(missing_ok=True)
                    descriptor = os.open(
                        lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                    )
                else:
                    return False
            except (FileNotFoundError, OSError):
                return False
        os.close(descriptor)
        try:
            for path in directory.glob("*.json"):
                payload = _read_json(path, None)
                if (
                    not isinstance(payload, dict)
                    or str(payload.get("id")) != request_id
                ):
                    continue
                target = processing / path.name
                try:
                    path.replace(target)
                except FileNotFoundError:
                    continue
                return target.exists()
            lock.unlink(missing_ok=True)
            return False
        except Exception:
            lock.unlink(missing_ok=True)
            raise

    def finish(self, request: dict[str, Any]) -> None:
        """Remove a handled request file so it is not processed twice."""
        directory = self.requests_dir()
        request_id = str(request.get("id") or "").strip()
        if directory is None or not request_id:
            return
        search_dirs = [directory, directory / ".processing"]
        for search in search_dirs:
            for path in search.glob("*.json"):
                payload = _read_json(path, None)
                if isinstance(payload, dict) and str(payload.get("id")) == request_id:
                    path.unlink(missing_ok=True)
        lock = self._claim_lock_path(request_id)
        if lock is not None:
            lock.unlink(missing_ok=True)
        self._mark_handled(request_id)

    def write_response(
        self,
        request: dict[str, Any],
        result: dict[str, Any],
        *,
        qq: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_id = str(request.get("id") or "").strip()
        payload = {
            "id": request_id,
            "ok": True,
            "kind": str(request.get("kind") or "chat"),
            "speech": _clean(result.get("speech"), MAX_SPEECH_CHARS),
            "detail": _clean(result.get("detail"), 400),
            "dish": result.get("dish") or None,
            "used": result.get("used") or [],
            "missing": result.get("missing") or [],
            "mood": _clean(result.get("mood"), 20),
            "qq": qq or {"sent": False, "umo": "", "error": ""},
            "handled_at": datetime.now().isoformat(timespec="seconds"),
        }
        path = self.response_path(request_id)
        _write_json(path, payload)
        self.finish(request)
        self.record(request, payload)
        return payload

    # ---------------------------------------------------------------- history

    def record(self, request: dict[str, Any], response: dict[str, Any]) -> None:
        path = self.history_path()
        if path is None:
            return
        payload = _read_json(path, {"schema_version": 1, "items": []})
        items = payload.get("items") if isinstance(payload, dict) else []
        if not isinstance(items, list):
            items = []
        response_id = str(response.get("id") or "")
        if response_id and any(
            isinstance(item, dict) and str(item.get("id") or "") == response_id
            for item in items
        ):
            # 同一请求被重复处理时只保留一次历史。
            return
        items.append(
            {
                "id": response.get("id"),
                "kind": response.get("kind"),
                "item_name": _clean(request.get("item_name"), 40),
                "action": _clean(request.get("action"), 40),
                "speech": response.get("speech"),
                "dish": response.get("dish"),
                "used": response.get("used") or [],
                "missing": response.get("missing") or [],
                "mood": response.get("mood"),
                "at": response.get("handled_at"),
                "qq": bool((response.get("qq") or {}).get("sent")),
            }
        )
        _write_json(
            path,
            {
                "schema_version": 1,
                "items": items[-HISTORY_LIMIT:],
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            },
        )

    def recent(self, limit: int = 5) -> list[dict[str, Any]]:
        path = self.history_path()
        if path is None:
            return []
        payload = _read_json(path, {"items": []})
        items = payload.get("items") if isinstance(payload, dict) else []
        if not isinstance(items, list):
            return []
        return items[-max(1, limit) :]

    def recent_gifts(
        self, limit: int = 3, *, hours: int = 48
    ) -> list[dict[str, Any]]:
        """Return recent gift records inside the hours window, oldest first."""
        cutoff = datetime.now() - timedelta(hours=max(1, int(hours)))
        picks: list[dict[str, Any]] = []
        for item in reversed(self.recent(24)):
            if not isinstance(item, dict):
                continue
            if str(item.get("action") or "") != "give":
                continue
            if not str(item.get("item_name") or "").strip():
                continue
            at = _parse_time(item.get("at"))
            if at is not None and at < cutoff:
                continue
            picks.append(item)
            if len(picks) >= max(1, limit):
                break
        picks.reverse()
        return picks

    # ------------------------------------------------------------- 聊天历史

    def format_history(
        self,
        history: Any,
        *,
        now: datetime | None = None,
        settings: dict[str, Any] | None = None,
    ) -> str:
        """把最近几轮对话渲染成提示词片段。

        只保留 ``history_minutes`` 分钟内的消息；assistant 消息没有时间戳，
        会跟随它前面那条 user 消息的时间。往回取够 ``history_messages`` 条或
        ``history_chars`` 个字符就停，避免把很久以前的话题带进来。
        """
        config = self.settings(settings)
        if not isinstance(history, list) or not history:
            return ""
        limit = config["history_messages"]
        if limit <= 0:
            return ""
        moment = now or datetime.now()
        if moment.tzinfo is not None:
            moment = moment.replace(tzinfo=None)
        cutoff = (
            moment - timedelta(minutes=config["history_minutes"])
            if config["history_minutes"] > 0
            else None
        )
        entries: list[tuple[datetime | None, str, str, bool]] = []
        seen_at: datetime | None = None
        pending_proactive = False
        for item in history:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "")
            text = _message_text(item)
            stamped = _message_time(item)
            if stamped is not None:
                seen_at = stamped
            if role == "user" and _is_proactive_note(text):
                pending_proactive = True
                continue
            if role not in {"user", "assistant"} or not text:
                continue
            entries.append((stamped or seen_at, role, text, pending_proactive))
            if role == "assistant":
                pending_proactive = False
        if cutoff is not None:
            entries = [
                entry for entry in entries if entry[0] is None or entry[0] >= cutoff
            ]
        picked: list[str] = []
        used = 0
        for _stamp, role, text, proactive in reversed(entries):
            if role == "user":
                speaker = "主人"
            elif proactive:
                speaker = "你（主动发起）"
            else:
                speaker = "你"
            line = f"{speaker}：{text}"
            if picked and used + len(line) > config["history_chars"]:
                break
            picked.append(line)
            used += len(line)
            if len(picked) >= limit:
                break
        picked.reverse()
        return "\n".join(picked)

    # ------------------------------------------------------------------ 冰箱

    def fridge_path(self) -> Path | None:
        if self.data_dir is None:
            return None
        return self.data_dir / "fridge_inventory.json"

    def consume_dish(
        self, dish: dict[str, Any] | None, settings: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Deduct the dish ingredients from ``fridge_inventory.json``.

        Returns ``{"used": [...], "missing": [...]}``; unknown ingredients are
        reported instead of invented, and no quantity ever goes negative.
        """
        result: dict[str, Any] = {"used": [], "missing": []}
        config = self.settings(settings)
        path = self.fridge_path()
        if (
            not config["consume_ingredients"]
            or path is None
            or not isinstance(dish, dict)
        ):
            return result
        raw_ingredients = dish.get("ingredients")
        if not isinstance(raw_ingredients, list):
            return result
        names = [_clean(item, 16) for item in raw_ingredients if _clean(item, 16)]
        if not names:
            return result
        payload = _read_json(path, None)
        if not isinstance(payload, dict):
            return result
        inventory = payload.get("ingredients")
        if not isinstance(inventory, list):
            return result
        changed = False
        for name in names:
            item = _match_inventory(inventory, name)
            if item is None:
                result["missing"].append(name)
                continue
            quantity = _to_float(item.get("quantity"))
            unit = str(item.get("unit") or "").strip()
            amount = min(quantity, CONSUME_BY_UNIT.get(unit, 1.0))
            amount = round(amount, 2)
            if amount <= 0:
                result["missing"].append(name)
                continue
            left = round(quantity - amount, 2)
            item["quantity"] = left
            changed = True
            result["used"].append(
                {
                    "name": str(item.get("name") or name),
                    "amount": amount,
                    "unit": unit,
                    "left": max(0.0, left),
                }
            )
        if changed:
            payload["ingredients"] = [
                item
                for item in inventory
                if isinstance(item, dict) and _to_float(item.get("quantity")) > 0.05
            ]
            payload["updated_at"] = datetime.now().date().isoformat()
            _write_json(path, payload)
        return result

    # ----------------------------------------------------------------- prompt

    def build_prompt(
        self,
        request: dict[str, Any],
        *,
        persona_prompt: str,
        persona_name: str = "",
        location: str = "",
        activity: str = "",
        now_text: str = "",
        ingredients: list[str] | None = None,
        history: str = "",
        avoid_lines: list[str] | None = None,
        recent_gifts: list[dict[str, Any]] | None = None,
        away: bool = False,
        user_sleeping: bool = False,
        settings: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        config = self.settings(settings)
        limit = config["max_reply_chars"]
        avoid = [str(line).strip() for line in (avoid_lines or []) if str(line).strip()]
        furniture_context = str(request.get("furniture_context") or "").strip()
        needs = request.get("needs") if isinstance(request.get("needs"), dict) else {}
        needs_summary = str(needs.get("summary") or "").strip()
        needs_details = str(needs.get("details") or "").strip()
        system = (
            (persona_prompt or "你是一个有自己生活的普通人。").strip()
            + "\n\n你正在通过家里的观察窗和主人即时互动。"
            + (f"你现在在{location}，正在{activity}。" if location or activity else "")
            + (f"\n现在是{now_text}。" if now_text else "")
            + f"\n请用第一人称、口语化地回应，1-2 句，不超过 {limit} 字；"
            "不要解释设定，不要用列表，不要写动作描写以外的旁白。"
            + (
                "\n下面会给你最近几轮聊天记录：要接着那几轮往下说，"
                "别重复自我介绍，也别主动提更早的话题。"
                if history
                else ""
            )
            + (
                "\n如果对话里标着「你（主动发起）」，那是你自己主动说的话，接着它说就行。"
                if history and "主动发起" in history
                else ""
            )
            + (
                "\n另外会列出你最近已经说过的话：这次必须换个说法，"
                "不要重复同一件家务、同一个动作、同一个数字、同一个比喻，"
                "也不要换个词把刚才的场景再描述一遍；如果现在还在做同一件事，"
                "就说它的新进展（快结束了、刚换了个动作），别复述刚才的细节。"
                if avoid
                else ""
            )
            + (
                "\n注意：你现在不在家，而是在外面；家里的东西你碰不到，"
                "不要写家里正在发生的事，也不要答应回家做饭、收拾之类的请求，"
                "说话要符合你人正在外面的状态。"
                if away
                else ""
            )
            + (
                "\n主人已经上床睡觉了：你的回应要轻、短，别拉着他继续聊天，"
                "可以道晚安、催他闭眼，不要主动开新话题。"
                if user_sleeping
                else ""
            )
            + (
                "\n你清楚家里家具和电器的当前状态；回应时不要和这些状态矛盾，"
                "如果主人刚开/关了东西，可以自然地接一句。"
                if furniture_context
                else ""
            )
            + (
                "\n当前日程只是你自己的安排，不代表主人真的做过什么。"
                "不要根据日程替主人编造点单、选择、动作或说过的话；"
                "只有主人在聊天里明确表达过的内容才算事实。"
                "拿不准时就顺着主人刚说的话回应，不要补全你不知道的细节。"
            )
            + (
                "\n你现在的身体状态会影响语气和精力：累、饿、困、刚洗过澡之类的感受要自然带出来，"
                "但不要每次都像报数值一样复述。"
                "如果精力、意愿偏低，或者身体不太舒服，可以自然地拒绝出门、运动或太费力的邀请，"
                "不必勉强答应；拒绝时保持角色口吻，不要把身体数值直接说出来。"
                "如果正在生病，语气可以更虚弱一些，优先休息，不要逞强。"
                if needs_summary
                else ""
            )
            + HUMAN_CHAT_RULE
            + DIALOGUE_FLOW_RULE
        )
        history_block = (
            f"【你们最近在聊的（只接这几轮，更早的事不要提）】\n{history}\n\n"
            if history
            else ""
        )
        avoid_block = (
            "【你最近已经说过的话（这次不要重复这些内容、场景细节和句式）】\n"
            + "\n".join(f"- {line}" for line in avoid[:4])
            + "\n\n"
            if avoid
            else ""
        )
        furniture_block = (
            "【家里和家具的当前状态（回应时不要和这些状态矛盾）】\n"
            + furniture_context
            + "\n\n"
            if furniture_context
            else ""
        )
        needs_block = (
            "【你现在的身体状态（自然带进语气，不需要报数值）】\n"
            + needs_summary
            + (f"\n感受：{needs_details}" if needs_details else "")
            + "\n\n"
            if needs_summary
            else ""
        )
        weather = request.get("weather") if isinstance(request.get("weather"), dict) else {}
        weather_condition = str(weather.get("condition") or "").strip()
        weather_block = ""
        if weather_condition:
            weather_parts = [weather_condition]
            low = weather.get("temperature_low")
            high = weather.get("temperature_high")
            if isinstance(low, (int, float)) and isinstance(high, (int, float)):
                weather_parts.append(f"{low}~{high}°C")
            description = str(weather.get("description") or "").strip()
            if description:
                weather_parts.append(description)
            weather_block = "【当前天气】" + "，".join(weather_parts) + "\n\n"
        mood = _clean(request.get("mood"), 20)
        mood_block = f"【你今天的总体心情】{mood}\n\n" if mood else ""
        appearance = (
            request.get("appearance")
            if isinstance(request.get("appearance"), dict)
            else {}
        )
        clothes_block = ""
        clothes_name = str(appearance.get("name") or "").strip()
        clothes_description = str(appearance.get("description") or "").strip()
        if clothes_name or clothes_description:
            clothes_text = "【你当前穿着】"
            clothes_text += clothes_name or "日常服装"
            if clothes_description:
                clothes_text += f"（{clothes_description}）"
            clothes_block = clothes_text + "\n\n"
        current = request.get("current") if isinstance(request.get("current"), dict) else {}
        next_items = request.get("next") if isinstance(request.get("next"), list) else []
        schedule_lines = []
        if current:
            start = str(current.get("start") or "").strip()
            end = str(current.get("end") or "").strip()
            activity = str(current.get("activity") or "").strip()
            location = str(current.get("location") or "").strip()
            if activity or location:
                schedule_lines.append(
                    f"{start}-{end} {activity or '当前活动'}"
                    + (f"（{location}）" if location else "")
                )
        for item in next_items[:2]:
            if not isinstance(item, dict):
                continue
            start = str(item.get("start") or "").strip()
            end = str(item.get("end") or "").strip()
            activity = str(item.get("activity") or "").strip()
            location = str(item.get("location") or "").strip()
            if activity or location:
                schedule_lines.append(
                    f"{start}-{end} {activity or '接下来的活动'}"
                    + (f"（{location}）" if location else "")
                )
        schedule_block = (
            "【你的日程】\n" + "\n".join(schedule_lines) + "\n\n"
            if schedule_lines
            else ""
        )
        current_activity = str((current or {}).get("activity") or "").strip()
        busy_keywords = (
            "工作",
            "会议",
            "上课",
            "面试",
            "赶工",
            "加班",
            "做饭",
            "烹饪",
            "打扫",
            "洗澡",
            "运动",
            "跑步",
            "健身",
            "瑜伽",
        )
        busy_block = ""
        if current_activity and any(
            word in current_activity for word in busy_keywords
        ):
            busy_block = (
                f"【你正在忙】{current_activity}。回应要短一些，先处理手上的事；"
                "如果主人递东西，可以接一下并简短回应，不要展开长聊。\n\n"
            )
        gift_history_lines = []
        for item in (recent_gifts or [])[:3]:
            if not isinstance(item, dict):
                continue
            gift_name = _clean(item.get("item_name"), 20)
            gift_at = _clean(item.get("at"), 20)
            if gift_name:
                gift_history_lines.append(
                    f"- {gift_name}" + (f"（{gift_at[:16].replace('T', ' ')}）" if gift_at else "")
                )
        gift_history_block = (
            "【你最近收到的东西】\n" + "\n".join(gift_history_lines) + "\n\n"
            if gift_history_lines
            else ""
        )
        kind = str(request.get("kind") or "chat")
        if kind == "dish":
            item_name = _clean(request.get("item_name"), 20) or "餐桌"
            room = _clean(request.get("room"), 10) or "厨房"
            fridge = "、".join(ingredients[:14]) if ingredients else "冰箱里东西不多"
            user = (
                history_block
                + avoid_block
                + needs_block
                + weather_block
                + mood_block
                + clothes_block
                + schedule_block
                + furniture_block
                + f"主人走到{room}的{item_name}旁边，想让你随手做点吃的。\n"
                f"冰箱里现有：{fridge}。\n"
                "请挑一道你现在真的想做的家常菜，尽量用手边食材，写清菜名、主要食材和一句话做法。\n"
                '只输出 JSON，不要多余文字：'
                '{"speech":"对主人说的话（1-2 句，口语）",'
                '"dish":{"name":"菜名","ingredients":["食材1","食材2"],"method":"一句话做法"},'
                '"mood":"一个词的当前心情"}'
            )
            return system, user
        if kind == "game":
            game_name = _clean(request.get("game_name"), 24) or "小游戏"
            game_result = _clean(request.get("game_result"), 16)
            game_score = _clean(request.get("game_score"), 40)
            outcome = {
                "win": "主人赢了，你输了",
                "lose": "主人输了，你赢了",
                "draw": "平局",
            }.get(game_result, "刚刚结束一局")
            score_text = f"，比分 {game_score}" if game_score else ""
            user = (
                history_block
                + avoid_block
                + needs_block
                + weather_block
                + mood_block
                + clothes_block
                + schedule_block
                + furniture_block
                + f"【观察窗游戏结果】主人刚和你玩了{game_name}，{outcome}{score_text}。\n"
                "请以月月的身份，用她自己的口吻自然说一句赛后反应，"
                "不要复述固定台词，不要把主人写成你，也不要写成系统公告。\n"
                '只输出 JSON，不要多余文字：'
                '{"speech":"你的赛后反应（1-2 句，口语）","mood":"一个词的当前心情"}'
            )
            return system, user
        text = _clean(request.get("text"), MAX_CHAT_CHARS) or "在吗？"
        give_item = ""
        if str(request.get("action") or "") == "give":
            give_item = _clean(request.get("item_name"), 20).strip()
        give_block = ""
        if give_item:
            gift_source = _clean(request.get("gift_source"), 120).strip()
            give_block = (
                f"【观察窗动作】主人正把{give_item}递给你。这是动作，不是普通聊天；"
                "自然接住并回应，不要问“给我什么”。\n"
            )
            if gift_source:
                give_block += f"主人刚才说的是：{gift_source}\n"
        user = (
            history_block
            + avoid_block
            + needs_block
            + weather_block
            + mood_block
            + clothes_block
            + schedule_block
            + busy_block
            + gift_history_block
            + furniture_block
            + give_block
            + (
                f"主人把{give_item}递给你，说：{text}\n"
                if give_item
                else f"主人对你说：{text}\n"
            )
            + "接着上面的对话自然回一句；如果这是新话题，就顺着说，不要硬扯回旧话题。"
            "可以顺口提一下你现在在做什么，但要说新的进展，不要重复最近说过的动作细节。\n"
            '只输出 JSON，不要多余文字：'
            '{"speech":"你的回复（1-2 句）","mood":"一个词的当前心情"}'
        )
        return system, user


    # ----------------------------------------------------- 日程插入判定

    def build_schedule_decision_prompt(
        self,
        request: dict[str, Any],
        result: dict[str, Any],
        *,
        persona_prompt: str,
        current_activity: str = "",
        current_location: str = "",
        now_text: str = "",
    ) -> tuple[str, str]:
        """让模型判断这次互动要不要写进当天日程。"""
        kind = str(request.get("kind") or "chat")
        action = str(request.get("action") or "")
        dish = str((result.get("dish") or {}).get("name") or "").strip()
        item_name = _clean(request.get("item_name"), 20)
        room = _clean(request.get("room"), 10)
        speech = _clean(result.get("speech"), 120)
        text = _clean(request.get("text"), MAX_CHAT_CHARS)
        if kind == "dish":
            happened = (
                f"主人在观察窗走到{room or '家'}{'的' + item_name if item_name else ''}旁边，"
                f"让你做点吃的，你做的是「{dish or '家常菜'}」。你回他：{speech}"
            )
        elif kind == "game":
            game_name = _clean(request.get("game_name"), 24) or "小游戏"
            game_result = _clean(request.get("game_result"), 16)
            outcome = {
                "win": "主人赢了，你输了",
                "lose": "主人输了，你赢了",
                "draw": "平局",
            }.get(game_result, "刚刚结束")
            happened = (
                f"主人在观察窗和你玩了{game_name}，{outcome}。你回：{speech}"
            )
        elif action == "give":
            happened = (
                f"主人在观察窗把{item_name or '东西'}递给你，对你说「{text}」。"
                f"你回：{speech}"
            )
        elif item_name:
            happened = (
                f"主人在观察窗点了{room or '家'}的{item_name}，对你说「{text}」。你回：{speech}"
            )
        else:
            happened = f"主人在观察窗对你说「{text}」。你回：{speech}"
        system = (
            (persona_prompt or "你是一个有自己生活的普通人。").strip()
            + "\n\n你正在判断刚才这件小事要不要写进今天的日程。"
            "日程决定你接下来一段时间在做什么，所以只有真的改变安排的事才值得写进去。"
        )
        user = (
            f"当前时间：{now_text or '现在'}。\n"
            f"你现在的日程：{current_activity or '自由活动'}（{current_location or '未说明'}）。\n"
            f"刚发生的事：{happened}\n\n"
            "判断标准：\n"
            "- 会改变你接下来一段时间在做什么（一起吃饭、做饭、被叫去帮忙、出门、陪对方做点什么，"
            "通常要持续 5 分钟以上）→ insert 为 true；\n"
            "- 只是闲聊一句、随手碰一下、看一眼东西，说完就完 → insert 为 false。\n"
            "如果插入，写一条第一人称的简短活动，给出时长（5-90 分钟）和地点。\n"
            '只输出 JSON，不要多余文字：'
            '{"insert":true,"activity":"陪主人一起吃番茄牛肉炒蛋","minutes":25,"location":"餐厅","reason":"一句话理由"}'
        )
        return system, user

    @staticmethod
    def parse_schedule_decision(
        raw: str, *, default_minutes: int = 30
    ) -> dict[str, Any]:
        """解析「要不要写进日程」的 JSON；无法解析时返回空字典。"""
        match = re.search(r"\{.*\}", str(raw or ""), re.S)
        if not match:
            return {}
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict) or "insert" not in data:
            return {}
        flag = data.get("insert")
        if isinstance(flag, str):
            flag = flag.strip().lower() in {"true", "yes", "1", "on"}
        else:
            flag = bool(flag)
        return {
            "insert": flag,
            "activity": _clean(data.get("activity"), 40),
            "minutes": _as_int(data.get("minutes"), default_minutes, 5, 120),
            "location": _clean(data.get("location"), 12),
            "reason": _clean(data.get("reason"), 60),
        }

    # ------------------------------------------------------------- 反重复判断

    @staticmethod
    def recent_assistant_texts(history: Any, limit: int = 4) -> list[str]:
        """从会话历史里取最近几条「你说过的话」，按时间从新到旧。"""
        if not isinstance(history, list) or limit <= 0:
            return []
        lines: list[str] = []
        for item in reversed(history):
            if not isinstance(item, dict) or item.get("role") != "assistant":
                continue
            text = _message_text(item)
            if text:
                lines.append(text)
            if len(lines) >= limit:
                break
        return lines

    @staticmethod
    def is_repetitive(
        speech: str,
        recent: list[str],
        *,
        threshold: float = 0.5,
    ) -> bool:
        """判断新回复是否在复读最近说过的话。"""
        return is_repetitive(speech, recent, threshold=threshold)


    # ------------------------------------------------------------------ reply

    def parse_reply(self, raw: str, settings: dict[str, Any] | None = None) -> dict[str, Any]:
        config = self.settings(settings)
        text = str(raw or "").strip()
        payload: dict[str, Any] = {}
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                payload = parsed
        speech = _clean(
            payload.get("speech") or payload.get("reply") or text,
            config["max_reply_chars"] + 40,
        )
        speech = ACTION_NOTE_RE.sub("", speech).strip()
        if not speech:
            speech = "嗯，我在呢。"
        dish = payload.get("dish")
        normalized: dict[str, Any] = {
            "speech": speech,
            "detail": _clean(payload.get("detail"), 400),
            "mood": _clean(payload.get("mood"), 20),
            "dish": None,
        }
        if isinstance(dish, dict):
            name = _clean(dish.get("name"), 24)
            if name:
                ingredients = dish.get("ingredients")
                normalized["dish"] = {
                    "name": name,
                    "ingredients": [
                        _clean(item, 16)
                        for item in (ingredients if isinstance(ingredients, list) else [])
                        if _clean(item, 16)
                    ][:8],
                    "method": _clean(dish.get("method"), 80),
                }
        return normalized

    def qq_text(self, request: dict[str, Any], result: dict[str, Any]) -> str:
        """只发「菜品 + 回复」，做法、食材、库存变化都不进消息。"""
        speech = str(result.get("speech") or "").strip()
        dish = result.get("dish") or {}
        if dish.get("name"):
            return f"🍽️ {dish['name']}\n{speech}" if speech else f"🍽️ {dish['name']}"
        action = str(request.get("action") or "").strip()
        item_name = str(request.get("item_name") or "").strip()
        if action == "give" and item_name:
            return speech
        return speech


def _parse_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None
