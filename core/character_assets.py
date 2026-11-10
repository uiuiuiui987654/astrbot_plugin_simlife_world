"""Locally replaceable character artwork.

The bundled PNG files remain the fallback.  Uploaded files are stored by the
AstrBot plugin settings page under the plugin data directory.  On startup (or
plugin reload) the newest valid PNG for each character slot is copied into the
view's static asset directory, so both the 2D and 3D views can display it
without needing an authenticated API request for every image.
"""

from __future__ import annotations

import hashlib
import struct
import time
from pathlib import Path
from typing import Any, Iterable

from astrbot.api import logger

SLOT_KEYS = ("daily", "sleepwear", "avatar")
LEGACY_SLEEPWEAR_SLOTS = ("sleepwear_whale", "sleepwear_set")
CONFIG_KEY = "character_settings"
MAX_BYTES = 12 * 1024 * 1024
MIN_SIDE = 64
MAX_SIDE = 8192


def _iter_values(value: Any) -> Iterable[Any]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, dict):
        for key in ("path", "file", "value", "url", "filename", "name"):
            if key in value:
                return _iter_values(value[key])
        return ()
    if isinstance(value, (list, tuple, set)):
        out = []
        for item in value:
            out.extend(_iter_values(item))
        return out
    return ()


def _slot_values(config: Any) -> dict[str, Any]:
    if not isinstance(config, dict):
        return {}
    settings = config.get(CONFIG_KEY)
    return settings if isinstance(settings, dict) else {}


def _resolve_source(data_dir: Path, raw: str) -> Path | None:
    raw = str(raw or "").strip()
    if not raw:
        return None
    candidate = Path(raw)
    if candidate.is_absolute():
        source = candidate.resolve(strict=False)
    else:
        source = (data_dir / candidate).resolve(strict=False)
    try:
        source.relative_to(data_dir.resolve(strict=False))
    except ValueError:
        return None
    if source.is_file():
        return source
    # Some AstrBot file config versions store only the uploaded filename.
    name = source.name
    if name and name == raw.replace("\\", "/").rsplit("/", 1)[-1]:
        uploads = data_dir / "files"
        matches = sorted(
            uploads.rglob(name), key=lambda p: p.stat().st_mtime, reverse=True
        ) if uploads.is_dir() else []
        if matches:
            return matches[0]
    return None


def _png_size(source: Path) -> tuple[int, int] | None:
    try:
        if source.stat().st_size > MAX_BYTES:
            return None
        with source.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    if header[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", header[16:24])
    if not (MIN_SIDE <= width <= MAX_SIDE and MIN_SIDE <= height <= MAX_SIDE):
        return None
    return width, height


def _copy_to_view(source: Path, target_dir: Path, slot: str) -> tuple[str, str] | None:
    try:
        payload = source.read_bytes()
    except OSError:
        return None
    digest = hashlib.sha1(payload).hexdigest()[:12]
    filename = f"{slot}-{digest}.png"
    target = target_dir / filename
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        if not target.is_file():
            target.write_bytes(payload)
    except OSError as exc:
        logger.warning("[模拟人生] 角色图片写入失败 %s: %s", target, exc)
        return None
    # Use a per-load token so a browser that cached a transient 404 cannot keep
    # showing a broken image after the plugin has reloaded with valid artwork.
    return filename, f"assets/character/{filename}?v={digest}-{time.time_ns()}"


def _cleanup_slot(target_dir: Path, slot: str, keep: set[str]) -> None:
    if not target_dir.is_dir():
        return
    for old in target_dir.glob(f"{slot}-*.png"):
        if old.name in keep:
            continue
        try:
            old.unlink()
        except OSError:
            pass


def sync_character_assets(
    config: Any,
    data_dir: Path,
    view_assets_dir: Path,
) -> dict[str, list[str]]:
    """Copy all configured PNGs into the view and return slot -> URL list."""
    values = _slot_values(config)
    target_dir = Path(view_assets_dir) / "character"
    mapping: dict[str, list[str]] = {}
    for slot in SLOT_KEYS:
        urls: list[str] = []
        filenames: set[str] = set()
        raw_values = list(_iter_values(values.get(slot)))
        if slot == "sleepwear":
            # Older configs split sleepwear into two slots. Merge both upload
            # lists into the single multi-photo sleepwear slot.
            for legacy_slot in LEGACY_SLEEPWEAR_SLOTS:
                raw_values.extend(_iter_values(values.get(legacy_slot)))
        for raw in raw_values:
            candidate = _resolve_source(Path(data_dir), str(raw))
            if candidate is None:
                continue
            if _png_size(candidate) is None:
                logger.warning(
                    "[模拟人生] 角色图片无效或尺寸不符合要求，已忽略：%s", candidate
                )
                continue
            copied = _copy_to_view(candidate, target_dir, slot)
            if copied is None:
                continue
            filename, url = copied
            if filename in filenames:
                continue
            filenames.add(filename)
            urls.append(url)
        _cleanup_slot(target_dir, slot, filenames)
        if slot == "sleepwear":
            for legacy_slot in LEGACY_SLEEPWEAR_SLOTS:
                _cleanup_slot(target_dir, legacy_slot, set())
        if urls:
            mapping[slot] = urls
    if "daily" in mapping and "avatar" not in mapping:
        mapping["avatar"] = list(mapping["daily"])
    return mapping


def clear_synced_assets(view_assets_dir: Path) -> None:
    target_dir = Path(view_assets_dir) / "character"
    if not target_dir.is_dir():
        return
    slots = (*SLOT_KEYS, *LEGACY_SLEEPWEAR_SLOTS)
    for slot in slots:
        for old in target_dir.glob(f"{slot}-*.png"):
            try:
                old.unlink()
            except OSError:
                pass
