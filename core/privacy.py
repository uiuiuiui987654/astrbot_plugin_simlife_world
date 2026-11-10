"""Secrets and personal identifiers: where they come from, and how backups hide them.

* ``resolve_secret`` lets a config field point at an environment variable
  (``env:NAME`` or ``${NAME}``) instead of holding the secret in plain text,
  with an optional fallback variable when the field is empty.
* ``sanitize_backup`` produces a backup that is safe to attach to an issue:
  chat/session identifiers (AstrBot's ``platform:MessageType:id`` origins) are
  replaced, and files that only make sense on this machine are left out.
"""

from __future__ import annotations

import copy
import os
import re
from typing import Any

ENV_REFERENCE = re.compile(r"^(?:env:(?P<a>[A-Za-z_][A-Za-z0-9_]*)|\$\{(?P<b>[A-Za-z_][A-Za-z0-9_]*)\})$")

# AstrBot unified message origin, e.g. "aiocqhttp:FriendMessage:123456"
ORIGIN = re.compile(r"[A-Za-z0-9_.-]+:(?:FriendMessage|GroupMessage|OtherMessage|PrivateMessage):[^\s\"',;]+")
REDACTED = "<已隐藏的会话>"

# per-machine files: session ids, platform self-tests, data-format manifest
EXCLUDED_FROM_SAFE_BACKUP = frozenset(
    {"sessions.json", "platform_checks.json", "data_manifest.json"}
)


def resolve_secret(value: Any, *, fallback_env: str = "") -> str:
    """Return the secret a config field refers to.

    ``"env:IMAGE_KEY"`` / ``"${IMAGE_KEY}"`` read that environment variable;
    any other non-empty value is used as is; an empty value falls back to
    ``fallback_env`` when given.
    """
    text = str(value or "").strip()
    match = ENV_REFERENCE.match(text)
    if match:
        return os.environ.get(match.group("a") or match.group("b") or "", "").strip()
    if text:
        return text
    if fallback_env:
        return os.environ.get(fallback_env, "").strip()
    return ""


def describe_secret_source(value: Any, *, fallback_env: str = "") -> str:
    """Human readable origin of a secret, never the secret itself."""
    text = str(value or "").strip()
    match = ENV_REFERENCE.match(text)
    if match:
        name = match.group("a") or match.group("b")
        return f"环境变量 {name}（{'已设置' if os.environ.get(name) else '未设置'}）"
    if text:
        return "插件配置（明文）"
    if fallback_env and os.environ.get(fallback_env):
        return f"环境变量 {fallback_env}"
    return "未设置"


def _redact(value: Any) -> Any:
    if isinstance(value, str):
        return ORIGIN.sub(REDACTED, value)
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            clean_key = ORIGIN.sub(REDACTED, str(key))
            if clean_key in result:  # several hidden origins collapse into one key
                index = 2
                while f"{clean_key}#{index}" in result:
                    index += 1
                clean_key = f"{clean_key}#{index}"
            result[clean_key] = _redact(item)
        return result
    return value


def sanitize_backup(files: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ``(safe_files, report)`` for a ``{file name: JSON}`` backup."""
    safe: dict[str, Any] = {}
    excluded: list[str] = []
    for name, content in files.items():
        if name in EXCLUDED_FROM_SAFE_BACKUP:
            excluded.append(name)
            continue
        safe[name] = _redact(copy.deepcopy(content))
    return safe, {"excluded": sorted(excluded), "redacted_origins": True}
