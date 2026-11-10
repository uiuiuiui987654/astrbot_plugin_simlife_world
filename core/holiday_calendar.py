"""Chinese public holidays (``holidays``) and traditional festivals (``lunar_python``)."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from functools import lru_cache
from typing import Any

import holidays

logger = logging.getLogger("astrbot")

try:
    from lunar_python import Solar
except ImportError:  # pragma: no cover - AstrBot installs requirements.txt
    Solar = None

FESTIVALS = frozenset({"除夕", "春节", "元宵节", "端午节", "七夕节", "中秋节", "重阳节", "腊八节"})
RENAMES = {"农历除夕": "除夕"}


@lru_cache(maxsize=16)
def _public_holidays(year: int) -> dict[date, str]:
    try:
        return dict(holidays.country_holidays("CN", years=[year], language="zh_CN"))
    except Exception:
        logger.debug("[模拟人生] 读取 %s 年法定节假日失败", year, exc_info=True)
        return {}


def _public_names(day: date) -> list[str]:
    raw = str(_public_holidays(day.year).get(day, ""))
    names = (RENAMES.get(part.strip(), part.strip()) for part in raw.split("; "))
    return [name for name in names if name and not name.startswith("休息日")]


def _festival_names(day: date) -> list[str]:
    if Solar is None:
        return []
    try:
        festivals = Solar.fromYmd(day.year, day.month, day.day).getLunar().getFestivals()
    except Exception:
        logger.debug("[模拟人生] 计算 %s 的农历节日失败", day, exc_info=True)
        return []
    return [name for name in festivals if name in FESTIVALS]


class ChinaHolidayCalendar:
    def on(self, target: date) -> list[dict[str, Any]]:
        """Holidays on ``target``: public ones first, then traditional festivals, no duplicates."""
        found: dict[str, str] = {}
        for name in _public_names(target):
            found.setdefault(name, "public")
        for name in _festival_names(target):
            found.setdefault(name, "traditional")
        return [{"date": target.isoformat(), "name": name, "kind": kind} for name, kind in found.items()]

    def between(self, start: date, end: date) -> list[dict[str, Any]]:
        days = (end - start).days
        return [item for offset in range(days + 1) for item in self.on(start + timedelta(days=offset))]

    def upcoming(self, target: date, days: int = 7) -> list[dict[str, Any]]:
        return self.between(target + timedelta(days=1), target + timedelta(days=max(0, days)))
