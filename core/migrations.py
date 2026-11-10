"""Versioned state files and their upgrade path.

Every JSON state file in the plugin data directory carries a top-level
``schema_version``. ``SCHEMAS`` lists, per file, the version the current code
writes and the functions that upgrade an older payload one step at a time.

``migrate_all`` runs once at startup, before anything reads the files:

* files that are already current are left untouched (not even rewritten);
* older files are copied to ``backups/`` and then upgraded step by step;
* files written by a *newer* plugin version are never touched — the plugin
  logs a warning instead of silently downgrading or corrupting them;
* the outcome is stored in ``data_manifest.json`` and shown by
  ``/虚拟人生 自检``.

Adding a format change
----------------------
1. bump ``current`` for the file below and in the module that writes it;
2. register ``steps[old_version] = function(payload) -> payload`` that turns
   an ``old_version`` payload into ``old_version + 1``;
3. add a test with a real old payload in ``tests/test_migrations.py``.
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .jsonio import atomic_write_json, synchronized

logger = logging.getLogger("astrbot")

MANIFEST_FILE = "data_manifest.json"
BACKUP_DIR = "backups"
MAX_BACKUPS_PER_FILE = 5

Step = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class Schema:
    current: int
    # version assumed for a payload written before the file had a version field
    assume_missing: int = 1
    steps: dict[int, Step] = field(default_factory=dict)


# file name (relative to the data dir) -> schema
SCHEMAS: dict[str, Schema] = {
    "plans.json": Schema(current=3, assume_missing=3),
    "sessions.json": Schema(current=1),
    "long_term_timelines.json": Schema(current=1),
    "money.json": Schema(current=1),
    "deliveries.json": Schema(current=1),
    "garage.json": Schema(current=1),
    "affection.json": Schema(current=1),
    "diary.json": Schema(current=1),
    "mood_history.json": Schema(current=1),
    "books_state.json": Schema(current=1),
    "camera_events.json": Schema(current=1),
    "home_decor.json": Schema(current=1),
    "item_effects.json": Schema(current=1),
    "world_events.json": Schema(current=1),
    "health_journal.json": Schema(current=1),
    "home_item_states.json": Schema(current=1),
    "home_item_wishes.json": Schema(current=1),
    "home_pending_actions.json": Schema(current=1),
    "food_state.json": Schema(current=1),
    "fridge_inventory.json": Schema(current=2, assume_missing=2),
    "trips.json": Schema(current=1),
    "chat_schedule_state.json": Schema(current=1),
    "platform_checks.json": Schema(current=1),
    "interactions/history.json": Schema(current=1),
}


@dataclass
class FileReport:
    name: str
    status: str  # current | upgraded | newer | unreadable | missing
    version: int | None = None
    from_version: int | None = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in {
                "status": self.status,
                "version": self.version,
                "from_version": self.from_version,
                "detail": self.detail,
            }.items()
            if value not in (None, "")
        }


def _version(payload: dict[str, Any], schema: Schema) -> int | None:
    raw = payload.get("schema_version")
    if raw is None:
        return schema.assume_missing
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _backup(data_dir: Path, name: str, version: int, now: datetime) -> Path:
    source = data_dir / name
    folder = data_dir / BACKUP_DIR
    folder.mkdir(parents=True, exist_ok=True)
    stem = name.replace("/", "__")
    target = folder / f"{stem}.v{version}.{now:%Y%m%d%H%M%S}.json"
    shutil.copy2(source, target)
    old = sorted(folder.glob(f"{stem}.v*.json"), key=lambda path: path.name)
    for path in old[: max(0, len(old) - MAX_BACKUPS_PER_FILE)]:
        try:
            path.unlink()
        except OSError:
            logger.debug("[虚拟人生] 清理旧备份失败 %s", path, exc_info=True)
    return target


def migrate_file(data_dir: Path, name: str, schema: Schema, *, now: datetime | None = None) -> FileReport:
    path = Path(data_dir) / name
    if not path.exists():
        return FileReport(name, "missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return FileReport(name, "unreadable", detail=type(exc).__name__)
    if not isinstance(payload, dict):
        return FileReport(name, "unreadable", detail="不是 JSON 对象")
    version = _version(payload, schema)
    if version is None:
        return FileReport(name, "unreadable", detail="schema_version 不是数字")
    if version > schema.current:
        logger.warning(
            "[虚拟人生] %s 的数据版本 v%s 比当前插件支持的 v%s 新，已保持原样；请升级插件。",
            name,
            version,
            schema.current,
        )
        return FileReport(name, "newer", version=version, detail=f"插件支持到 v{schema.current}")
    if version == schema.current and "schema_version" in payload:
        return FileReport(name, "current", version=version)

    moment = now or datetime.now()
    original = version
    _backup(Path(data_dir), name, original, moment)
    upgraded = payload
    while version < schema.current:
        step = schema.steps.get(version)
        if step is not None:
            upgraded = step(dict(upgraded))
            if not isinstance(upgraded, dict):
                raise TypeError(f"{name} 迁移 v{version} 返回的不是对象")
        version += 1
    upgraded["schema_version"] = schema.current
    atomic_write_json(path, upgraded)
    logger.info("[虚拟人生] 已把 %s 从 v%s 升级到 v%s（原文件已备份）", name, original, schema.current)
    return FileReport(name, "upgraded", version=schema.current, from_version=original)


@synchronized
def migrate_all(
    data_dir: Path,
    *,
    plugin_version: str = "",
    schemas: dict[str, Schema] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Upgrade every known state file and write ``data_manifest.json``."""
    moment = now or datetime.now()
    reports: dict[str, FileReport] = {}
    for name, schema in (schemas or SCHEMAS).items():
        try:
            reports[name] = migrate_file(Path(data_dir), name, schema, now=moment)
        except Exception as exc:  # one broken file must not block the others
            logger.warning("[虚拟人生] 迁移 %s 失败，已保持原样: %s", name, exc, exc_info=True)
            reports[name] = FileReport(name, "unreadable", detail=f"迁移失败：{type(exc).__name__}")
    manifest = {
        "schema_version": 1,
        "plugin_version": plugin_version,
        "checked_at": moment.isoformat(timespec="seconds"),
        "files": {name: report.to_dict() for name, report in reports.items() if report.status != "missing"},
    }
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    atomic_write_json(Path(data_dir) / MANIFEST_FILE, manifest)
    return manifest


def load_manifest(data_dir: Path) -> dict[str, Any]:
    try:
        payload = json.loads((Path(data_dir) / MANIFEST_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def summary(manifest: dict[str, Any]) -> str:
    files = manifest.get("files") or {}
    if not files:
        return "数据版本：尚未检查（插件启动时自动检查）"
    counts: dict[str, list[str]] = {}
    for name, info in files.items():
        counts.setdefault(str(info.get("status") or "?"), []).append(name)
    parts = [f"{len(counts.get('current', [])) + len(counts.get('upgraded', []))}/{len(files)} 个文件为最新格式"]
    if counts.get("upgraded"):
        parts.append("本次升级：" + "、".join(counts["upgraded"]))
    if counts.get("newer"):
        parts.append("⚠️ 来自更新版插件、未改动：" + "、".join(counts["newer"]))
    if counts.get("unreadable"):
        parts.append("⚠️ 无法读取：" + "、".join(counts["unreadable"]))
    return "数据版本：" + "；".join(parts)
