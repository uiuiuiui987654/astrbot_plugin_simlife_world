"""Cross-platform message delivery helpers and the per-platform self-test.

The plugin sends three kinds of output:

* plain text through ``context.send_message`` (proactive messages, interaction
  replies) — every adapter supports this;
* images through ``context.send_message`` (selfies) — adapters differ in which
  image sources they accept (base64 / URL / local file);
* images as a command reply through ``event.image_result`` (schedule images).

``send_image`` tries the image source variants in order so a platform that
rejects one form still gets the picture. ``/模拟人生 平台测试`` runs all three
paths in the current chat and stores the outcome in ``platform_checks.json``
so README's support table can be filled from real results.
"""

from __future__ import annotations

import base64
import json
import logging
import struct
import uuid
import zlib
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from .jsonio import atomic_write_json, synchronized

logger = logging.getLogger("astrbot")

CHECKS_FILE = "platform_checks.json"
SPOOL_DIR = "outgoing_images"
MAX_SPOOL_FILES = 30

PLATFORM_LABELS = {
    "aiocqhttp": "QQ（OneBot / aiocqhttp）",
    "qq_official": "QQ 官方机器人",
    "telegram": "Telegram",
    "wecom": "企业微信",
    "lark": "飞书",
    "dingtalk": "钉钉",
    "kook": "KOOK",
    "discord": "Discord",
    "webchat": "AstrBot 网页聊天",
}

CHECK_LABELS = {
    "text": "主动发文字",
    "image_file": "主动发图片（本地文件）",
    "image_base64": "主动发图片（base64）",
    "reply_image": "指令回复图片",
}


def platform_label(name: str) -> str:
    return PLATFORM_LABELS.get(str(name or ""), str(name or "未知平台"))


def tiny_png(size: int = 32, rgb: tuple[int, int, int] = (176, 158, 214)) -> bytes:
    """A valid solid-colour PNG without Pillow."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    row = b"\x00" + bytes(rgb) * size
    raw = row * size
    return b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)),
            chunk(b"IDAT", zlib.compress(raw, 9)),
            chunk(b"IEND", b""),
        )
    )


def spool_image(data_dir: Path, payload: bytes, suffix: str = ".png") -> Path:
    """Write an outgoing image to a small rotating folder and return its path."""
    directory = Path(data_dir) / SPOOL_DIR
    directory.mkdir(parents=True, exist_ok=True)
    files = sorted(directory.glob("*"), key=lambda path: path.stat().st_mtime)
    for old in files[: max(0, len(files) - MAX_SPOOL_FILES + 1)]:
        try:
            old.unlink()
        except OSError:
            logger.debug("[模拟人生] 清理旧图片失败 %s", old, exc_info=True)
    path = directory / f"{datetime.now():%Y%m%d%H%M%S}-{uuid.uuid4().hex[:6]}{suffix}"
    path.write_bytes(payload)
    return path


def image_variants(image: str, data_dir: Path | None) -> list[tuple[str, str]]:
    """Ordered ``(kind, value)`` sources to try for one image.

    ``kind`` is ``base64`` / ``url`` / ``file``. A base64 image is also spooled
    to a local file as a fallback, because some adapters only accept files.
    """
    text = str(image or "").strip()
    if not text:
        return []
    if text.startswith("data:image") and "," in text:
        encoded = text.split(",", 1)[1]
        variants = [("base64", encoded)]
        if data_dir is not None:
            try:
                variants.append(("file", str(spool_image(data_dir, base64.b64decode(encoded)))))
            except (ValueError, OSError):
                logger.debug("[模拟人生] base64 图片落盘失败", exc_info=True)
        return variants
    if text.startswith(("http://", "https://")):
        return [("url", text)]
    return [("file", text)]


async def send_image(
    send: Callable[[Any], Awaitable[bool]],
    image_cls: Any,
    image: str,
    *,
    data_dir: Path | None = None,
) -> tuple[bool, str]:
    """Try each image source until the platform accepts one.

    Args:
        send: ``async (component) -> bool`` that delivers one Image component.
        image_cls: AstrBot's ``Image`` message component class.
        image: data URL, http(s) URL or local path.
        data_dir: where base64 images may be spooled as files.

    Returns:
        ``(sent, kind)`` with the variant that worked, or ``(False, last_error)``.
    """
    builders = {"base64": image_cls.fromBase64, "url": image_cls.fromURL, "file": image_cls.fromFileSystem}
    last_error = "没有可发送的图片"
    for kind, value in image_variants(image, data_dir):
        try:
            if await send(builders[kind](value)):
                return True, kind
            last_error = f"{kind}: 平台返回发送失败"
        except Exception as exc:  # adapters raise many different errors
            logger.warning("[模拟人生] 以 %s 方式发送图片失败: %s", kind, exc)
            last_error = f"{kind}: {type(exc).__name__}"
    return False, last_error


def _load(data_dir: Path) -> dict[str, Any]:
    try:
        payload = json.loads((Path(data_dir) / CHECKS_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "platforms": {}}
    if not isinstance(payload, dict) or not isinstance(payload.get("platforms"), dict):
        return {"schema_version": 1, "platforms": {}}
    return payload


def load_checks(data_dir: Path) -> dict[str, dict[str, Any]]:
    return dict(_load(data_dir)["platforms"])


@synchronized
def record_check(
    data_dir: Path,
    platform: str,
    results: dict[str, str],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Store the latest self-test outcome per platform.

    ``results`` maps a check key (see ``CHECK_LABELS``) to ``ok`` / ``sent``
    (handed to the adapter, delivery not confirmed) / ``fail: …``.
    """
    payload = _load(data_dir)
    entry = {
        "platform": str(platform or "unknown"),
        "checked_at": (now or datetime.now()).isoformat(timespec="seconds"),
        "results": {str(key): str(value)[:120] for key, value in results.items()},
    }
    payload["platforms"][entry["platform"]] = entry
    atomic_write_json(Path(data_dir) / CHECKS_FILE, payload)
    return entry


def format_checks(checks: dict[str, dict[str, Any]]) -> str:
    if not checks:
        return "还没有平台测试记录。在要验证的平台上发送 /模拟人生 平台测试。"
    legend = "✅ 成功　📨 已交给平台（请确认是否收到）　❌ 失败　· 未测"
    lines = []
    for name, entry in sorted(checks.items()):
        results = entry.get("results") or {}
        parts = []
        for key, label in CHECK_LABELS.items():
            value = str(results.get(key) or "未测")
            mark = {"ok": "✅", "sent": "📨"}.get(value) or ("❌" if value.startswith("fail") else "·")
            parts.append(f"{mark}{label}")
        lines.append(f"{platform_label(name)}（{str(entry.get('checked_at') or '')[:16]}）：" + " ".join(parts))
    return "\n".join([*lines, legend])
