"""Split a proactive message into several chat bubbles, with typing pauses.

Configured by ``segmented_reply_settings``: split by a list of words (keeping
the word) or by a regex, only for messages up to ``words_count_threshold``
characters, optionally removing a cleanup pattern from every bubble.
"""

from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass
from typing import Any

from astrbot.api import logger


@dataclass(slots=True, frozen=True)
class SegmentResult:
    segments: list[str]
    mode: str
    source_length: int
    threshold: int
    skipped_reason: str = ""


def _to_threshold(value: Any) -> int | None:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None


def _to_words(value: Any) -> list[str]:
    try:
        items = [value] if isinstance(value, str) else list(value)
    except TypeError:
        return []
    words: list[str] = []
    for item in items:
        word = "\n" if str(item) == r"\n" else str(item)
        if word and word not in words:
            words.append(word)
    return words


def _words_pattern(words: list[str]) -> re.Pattern[str] | None:
    if not words:
        return None
    # longest separators first so "。。" wins over "。"
    alternatives = "|".join(sorted(map(re.escape, words), key=len, reverse=True))
    return re.compile(f".*?(?:{alternatives})|.+$", re.DOTALL)


def _compile(value: Any, flags: int, warning: str) -> re.Pattern[str] | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return re.compile(value, flags)
    except re.error as exc:
        logger.warning(warning, exc)
        return None


def _interval_range(value: Any) -> tuple[float, float] | None:
    try:
        low, high = (float(part.strip()) for part in str(value).split(","))
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(part) and part >= 0 for part in (low, high)):
        return None
    return min(low, high), max(low, high)


def _log_base(value: Any) -> float | None:
    try:
        base = float(value)
    except (TypeError, ValueError):
        return None
    return base if math.isfinite(base) and base > 1 else None


class ProactiveMessageSegmenter:
    def __init__(self, settings: dict[str, Any]):
        self.enabled = bool(settings.get("enable"))
        self.threshold = _to_threshold(settings.get("words_count_threshold"))
        self.mode = str(settings.get("split_mode") or "").strip().lower()
        self.regex = _compile(
            settings.get("regex"),
            re.DOTALL | re.MULTILINE,
            "[模拟人生] 拆分正则写错了，这次不拆：%s",
        )
        self.split_words = _to_words(settings.get("split_words"))
        self.words_pattern = _words_pattern(self.split_words)
        cleanup = str(settings.get("content_cleanup_rule") or "") if settings.get("enable_content_cleanup") else ""
        self.cleanup_pattern = _compile(cleanup, 0, "[模拟人生] 清理正则写错了，这次不清理：%s")
        self.interval_method = str(settings.get("interval_method") or "").strip().lower()
        self.random_interval = _interval_range(settings.get("interval"))
        self.log_base = _log_base(settings.get("log_base"))

    def _skip(self, text: str, reason: str) -> SegmentResult:
        return SegmentResult([text], self.mode, len(text), self.threshold, reason)

    def split(self, text: str) -> SegmentResult:
        if not self.enabled:
            return self._skip(text, "disabled")
        if self.threshold is None:
            return self._skip(text, "bad threshold")
        if len(text) > self.threshold:
            return self._skip(text, "too long to split")
        patterns = {"words": (self.words_pattern, "no split words"), "regex": (self.regex, "broken regex")}
        if self.mode not in patterns:
            return self._skip(text, "unknown split mode")
        pattern, missing = patterns[self.mode]
        if pattern is None:
            return self._skip(text, missing)
        pieces = [match.group(0) for match in pattern.finditer(text)]
        if self.cleanup_pattern is not None:
            pieces = [self.cleanup_pattern.sub("", piece) for piece in pieces]
        pieces = [piece for piece in pieces if piece.strip()]
        if not pieces:
            return self._skip(text, "nothing left")
        return SegmentResult(pieces, self.mode, len(text), self.threshold)

    def interval_for(self, segment: str) -> float:
        """Seconds to wait before sending ``segment``."""
        if self.interval_method == "random":
            return random.uniform(*self.random_interval) if self.random_interval else 0.0
        if self.interval_method != "log" or self.log_base is None:
            return 0.0
        if segment.isascii():
            size = len(segment.split())
        else:
            size = sum(1 for character in segment if character.isalnum())
        shortest = math.log(size + 1, self.log_base)
        return random.uniform(shortest, shortest + 0.5)
