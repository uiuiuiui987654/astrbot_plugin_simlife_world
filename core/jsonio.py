"""Crash- and thread-safe JSON persistence helpers.

Every state file of the plugin is written through :func:`atomic_write_json`:

* the payload is serialised exactly as before (UTF-8, ``ensure_ascii=False``,
  ``indent=2``), so the on-disk format does not change;
* it is written to a *unique* temporary file next to the target, flushed and
  fsync'ed, then swapped in with :func:`os.replace` — a crash or power cut leaves
  either the old or the new file, never a truncated one, and two writers no
  longer clobber a shared ``*.tmp`` file;
* on Windows ``os.replace`` fails while another thread/process has the target
  open; that case is retried briefly.

Read-modify-write sequences (load → change → save) that may run concurrently —
command handlers and the web view both run state mutators in worker threads via
``asyncio.to_thread`` — are serialised with :data:`STATE_LOCK` through the
:func:`synchronized` decorator. It is one re-entrant lock for all state files, so
nested mutators (money → goods → …) can never deadlock on lock ordering.
"""

from __future__ import annotations

import functools
import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, TypeVar

STATE_LOCK = threading.RLock()

_F = TypeVar("_F", bound=Callable[..., Any])

_REPLACE_RETRIES = 10
_REPLACE_DELAY = 0.05


def synchronized(function: _F) -> _F:
    """Run ``function`` while holding the global state lock."""

    @functools.wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with STATE_LOCK:
            return function(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def atomic_write_text(path: Path | str, text: str, *, encoding: str = "utf-8") -> None:
    """Atomically replace ``path`` with ``text``."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(text)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        for attempt in range(_REPLACE_RETRIES):
            try:
                os.replace(temporary, target)
                break
            except PermissionError:
                # Windows: the target is briefly open in another thread/process.
                if attempt == _REPLACE_RETRIES - 1:
                    raise
                time.sleep(_REPLACE_DELAY)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def atomic_write_json(path: Path | str, payload: Any, *, indent: int | None = 2) -> None:
    """Serialise ``payload`` like the plugin always did and write it atomically."""
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=indent))
