"""Small persistent journal for sickness onset, duration and recovery.

The physiological layer is deterministic and stateless.  This journal keeps
the one piece of information that cannot be derived from the current schedule:
when a sickness actually started, how many days it has lasted and whether the
character is still in a recovery period.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
from .jsonio import atomic_write_json, synchronized

SCHEMA_VERSION = 1


def journal_path(data_dir: Path) -> Path:
    return Path(data_dir) / "health_journal.json"


def _load(data_dir: Path) -> dict[str, Any]:
    try:
        payload = json.loads(journal_path(data_dir).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": SCHEMA_VERSION, "personas": {}}
    if not isinstance(payload, dict):
        return {"schema_version": SCHEMA_VERSION, "personas": {}}
    personas = payload.get("personas")
    if not isinstance(personas, dict):
        personas = {}
    return {"schema_version": SCHEMA_VERSION, "personas": personas}


def _save(data_dir: Path, payload: dict[str, Any]) -> None:
    path = journal_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, payload)


def _parse_day(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


SYMPTOM_RECOVERY_WORDS = (
    ("睡不好", ("睡", "休息", "躺", "午睡", "小憩")),
    ("胃口", ("粥", "汤", "清淡", "吃")),
    ("着凉", ("澡", "淋浴", "洗", "热", "茶")),
    ("没力气", ("睡", "休息", "躺")),
    ("提不起精神", ("休息", "茶", "散步", "晒")),
    ("发烧", ("睡", "休息", "躺", "水", "粥", "汤")),
)


SYMPTOM_HARM_WORDS = (
    ("睡不好", ("熬夜", "通宵", "咖啡", "酒")),
    ("胃口", ("辣", "火锅", "烧烤", "冰", "冷饮", "酒")),
    ("着凉", ("吹风", "淋雨", "冷饮", "冰", "跑步")),
    ("没力气", ("跑步", "健身", "运动", "熬夜")),
    ("提不起精神", ("熬夜", "通宵")),
    ("发烧", ("跑步", "健身", "运动", "熬夜", "吹风", "冷饮")),
)


def _has_recovery_actions(needs: dict[str, Any]) -> bool:
    actions = needs.get("recovery_actions")
    return isinstance(actions, list) and bool(actions)


def _has_harmful_actions(needs: dict[str, Any]) -> bool:
    harmful = needs.get("harmful_actions")
    return isinstance(harmful, list) and bool(harmful)


def _targeted_harm(needs: dict[str, Any]) -> bool:
    harmful = needs.get("harmful_actions")
    symptoms = needs.get("symptoms")
    if not isinstance(harmful, list) or not isinstance(symptoms, list):
        return False
    harmful_text = " ".join(str(action) for action in harmful)
    for symptom in symptoms:
        text = str(symptom)
        for marker, words in SYMPTOM_HARM_WORDS:
            if marker not in text:
                continue
            if any(word in harmful_text for word in words):
                return True
    return False


def _targeted_recovery(needs: dict[str, Any]) -> bool:
    """Whether recent care actually matches the current symptoms."""
    actions = needs.get("recovery_actions")
    symptoms = needs.get("symptoms")
    if not isinstance(actions, list) or not isinstance(symptoms, list):
        return False
    action_text = " ".join(str(action) for action in actions)
    for symptom in symptoms:
        text = str(symptom)
        for marker, words in SYMPTOM_RECOVERY_WORDS:
            if marker not in text:
                continue
            if any(word in action_text for word in words):
                return True
    return False


def _recovery_required(needs: dict[str, Any]) -> int:
    health = _int(needs.get("health"), 100)
    debt = _int(needs.get("sleep_debt_minutes"), 0)
    severity = str(needs.get("illness_severity") or "")
    has_actions = _has_recovery_actions(needs)
    targeted = _targeted_recovery(needs)
    harmful = _has_harmful_actions(needs)
    target_harm = _targeted_harm(needs)
    if target_harm:
        return 3
    if harmful:
        return 3 if health < 55 else 2
    if severity == "severe" or health < 40 or debt >= 240:
        return 3
    if bool(needs.get("fever")):
        return 3
    if bool(needs.get("heat_illness")):
        return 2
    if bool(needs.get("heavy_food_today")):
        return 3
    if bool(needs.get("light_diet_today")) and health >= 45 and debt < 180:
        return 1
    if targeted and health >= 45 and debt < 180:
        return 1
    if has_actions and health >= 45 and debt < 180:
        return 2
    if health >= 55 and debt < 120:
        return 1
    return 2


def _recent_illness_days(episodes: Any, today: date) -> int:
    if not isinstance(episodes, list):
        return 0
    total = 0
    for episode in episodes:
        if not isinstance(episode, dict):
            continue
        recovered = _parse_day(episode.get("recovered"))
        if recovered is None:
            continue
        age = (today - recovered).days
        if 0 <= age <= 30:
            total += max(0, _int(episode.get("days"), 0))
    return total


def persona_state(
    data_dir: Path,
    persona: str,
    *,
    today: date | None = None,
) -> dict[str, Any]:
    """Read-only journal view with derived 30-day illness load."""
    if not persona:
        return {}
    payload = _load(data_dir)
    entry = payload["personas"].get(str(persona))
    if not isinstance(entry, dict):
        return {}
    result = dict(entry)
    episodes = result.get("episodes")
    recent = _recent_illness_days(episodes, today or date.today())
    result["recent_illness_days"] = recent
    result["weak_constitution"] = recent >= 7
    return result


@synchronized
def update(
    data_dir: Path,
    persona: str,
    needs: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    """Update the sickness journal and return an enriched copy of ``needs``."""
    if not persona or not isinstance(needs, dict):
        return needs
    today = now.date()
    payload = _load(data_dir)
    personas = payload["personas"]
    entry = personas.get(persona)
    if not isinstance(entry, dict):
        entry = {}
    original = dict(entry)
    status = str(entry.get("status") or "healthy")
    pure_sick = bool(needs.get("sick"))
    pure_recovering = bool(needs.get("recovering"))
    onset = _parse_day(entry.get("onset"))
    sick_days = int(entry.get("sick_days") or 0)
    recovered_at = _parse_day(entry.get("recovered_at"))
    recovery_required = max(1, _int(entry.get("recovery_required_days"), 2))
    fever_recovery = bool(entry.get("fever_recovery"))
    heat_recovery = bool(entry.get("heat_recovery"))
    episodes = original.get("episodes")
    episodes = list(episodes) if isinstance(episodes, list) else []

    if pure_sick:
        if status != "sick" or onset is None:
            onset = today
            status = "sick"
            sick_days = 1
        else:
            sick_days = max(1, (today - onset).days + 1)
        recovered_at = None
        recovery_required = 0
        fever_recovery = bool(needs.get("fever"))
        heat_recovery = bool(needs.get("heat_illness"))
    elif status == "sick":
        status = "recovering"
        recovered_at = today
        sick_days = max(1, sick_days)
        recovery_required = _recovery_required(needs)
        fever_recovery = bool(needs.get("fever") or fever_recovery)
        heat_recovery = bool(needs.get("heat_illness") or heat_recovery)
        if onset is not None:
            episode = {
                "onset": onset.isoformat(),
                "recovered": today.isoformat(),
                "days": sick_days,
            }
            if not any(
                isinstance(item, dict)
                and item.get("onset") == episode["onset"]
                and item.get("recovered") == episode["recovered"]
                for item in episodes
            ):
                episodes.append(episode)
                episodes = episodes[-10:]
    elif status == "recovering":
        required = recovery_required
        has_actions = _has_recovery_actions(needs)
        targeted = _targeted_recovery(needs)
        if _targeted_harm(needs):
            required = 3
        elif _has_harmful_actions(needs):
            required = max(required, 2)
        elif (
            targeted
            and _int(needs.get("health"), 100) >= 50
            and _int(needs.get("sleep_debt_minutes"), 0) < 180
        ):
            required = 1
        elif (
            bool(needs.get("light_diet_today"))
            and _int(needs.get("health"), 100) >= 50
            and _int(needs.get("sleep_debt_minutes"), 0) < 180
        ):
            required = 1
        elif (
            _int(needs.get("health"), 100) >= 70
            and _int(needs.get("sleep_debt_minutes"), 0) < 90
            and _int(needs.get("satiety"), 100) >= 50
            and _int(needs.get("hygiene"), 100) >= 50
        ):
            required = 1
        elif (
            _int(needs.get("health"), 100) < 50
            or _int(needs.get("sleep_debt_minutes"), 0) >= 180
        ):
            required = max(required, 3)
        recovery_required = max(1, required)
        if recovered_at is not None and (today - recovered_at).days >= recovery_required:
            status = "healthy"
            recovered_at = None
            recovery_required = 0
            fever_recovery = False
    elif pure_recovering:
        # A pure self-reported recovery state without a recorded sickness is
        # allowed to remain soft; it does not create a fake sick day count.
        status = "recovering"
        recovered_at = today
        sick_days = max(1, sick_days)
        recovery_required = _recovery_required(needs)
        fever_recovery = bool(needs.get("fever"))
        heat_recovery = bool(needs.get("heat_illness"))

    if status == "healthy":
        recovery_required = 0
        fever_recovery = False
        heat_recovery = False
    elif status == "recovering" and fever_recovery:
        recovery_required = max(3, recovery_required)
    elif status == "recovering" and heat_recovery:
        recovery_required = max(2, recovery_required)
    if (
        status == "recovering"
        and _int(needs.get("hydration"), 100) < 30
    ):
        recovery_required = max(2, recovery_required)
    if (
        status == "recovering"
        and not fever_recovery
        and not heat_recovery
        and bool(needs.get("weekly_meal_regular"))
        and recovery_required > 1
    ):
        recovery_required -= 1
    if (
        status == "recovering"
        and not fever_recovery
        and not heat_recovery
        and bool(needs.get("regular_exercise"))
        and recovery_required > 1
    ):
        recovery_required -= 1
    if (
        status == "recovering"
        and not fever_recovery
        and not heat_recovery
        and bool(needs.get("recovery_light_movement"))
        and not bool(needs.get("regular_exercise"))
        and recovery_required > 1
    ):
        recovery_required -= 1
    if (
        status == "recovering"
        and not fever_recovery
        and not heat_recovery
        and bool(needs.get("good_sleep_streak"))
        and recovery_required > 1
    ):
        recovery_required -= 1
    if (
        status == "recovering"
        and not fever_recovery
        and not heat_recovery
        and bool(needs.get("socially_satisfied"))
        and recovery_required > 1
    ):
        recovery_required -= 1

    recent_illness_days = _recent_illness_days(episodes, today)
    weak_constitution = recent_illness_days >= 7
    if status == "recovering" and recent_illness_days >= 7:
        recovery_required = max(
            recovery_required, 4 if recent_illness_days >= 14 else 3
        )

    recovery_log = original.get("recovery_log")
    recovery_log = list(recovery_log) if isinstance(recovery_log, list) else []
    if status in ("sick", "recovering"):
        actions = needs.get("recovery_actions")
        harmful = needs.get("harmful_actions")
        actions = actions if isinstance(actions, list) else []
        harmful = harmful if isinstance(harmful, list) else []
        if actions or harmful:
            entry_log = {
                "date": today.isoformat(),
                "actions": [str(value) for value in actions[:4]],
                "harmful": [str(value) for value in harmful[:4]],
                "targeted": _targeted_recovery(needs),
                "targeted_harm": _targeted_harm(needs),
            }
            recovery_log = [
                item
                for item in recovery_log
                if not (isinstance(item, dict) and item.get("date") == today.isoformat())
            ]
            recovery_log.append(entry_log)
            recovery_log = recovery_log[-7:]

    entry = {
        "status": status,
        "onset": onset.isoformat() if onset and status == "sick" else str(original.get("onset") or ""),
        "sick_days": sick_days if status in ("sick", "recovering") else 0,
        "recovered_at": recovered_at.isoformat() if recovered_at else "",
        "recovery_required_days": recovery_required,
        "recovery_log": recovery_log,
        "episodes": episodes,
        "fever_recovery": fever_recovery,
        "heat_recovery": heat_recovery,
        "updated_at": today.isoformat(),
    }
    if entry != original:
        personas[persona] = entry
        _save(data_dir, payload)

    enriched = dict(needs)
    if status == "sick":
        enriched["sick"] = True
        enriched["recovering"] = False
        enriched["sick_days"] = sick_days
        enriched["health_status"] = "sick"
        if sick_days > 1:
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + f"；病程第 {sick_days} 天"
            )
    elif status == "recovering":
        elapsed = (
            max(0, (today - recovered_at).days) if recovered_at is not None else 0
        )
        days_left = max(0, recovery_required - elapsed)
        enriched["sick"] = False
        enriched["recovering"] = True
        enriched["sick_days"] = sick_days
        enriched["recovery_days_left"] = days_left
        enriched["recovery_required_days"] = recovery_required
        enriched["health_status"] = "recovering"
        enriched["fever_recovery"] = fever_recovery
        enriched["heat_recovery"] = heat_recovery
        if heat_recovery:
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；中暑刚缓过来，还怕晒"
            )
        if fever_recovery:
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；刚退烧，胃口还没完全恢复"
            )
        if bool(needs.get("heavy_food_today")):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；今天吃了重口，恢复慢一点"
            )
        if bool(needs.get("light_diet_today")):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；今天吃得清淡，恢复顺一点"
            )
        if _int(needs.get("hydration"), 100) < 30:
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；水喝得太少，恢复慢一点"
            )
        if _targeted_harm(needs):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；今天做的事不太适合养病，恢复慢一点"
            )
        elif _has_harmful_actions(needs):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；今天没照顾好自己，恢复慢一点"
            )
        if (
            bool(needs.get("weekly_meal_regular"))
            and not fever_recovery
            and not heat_recovery
        ):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；这周饮食规律，恢复快一点"
            )
        if (
            bool(needs.get("regular_exercise"))
            and not fever_recovery
            and not heat_recovery
        ):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；最近有规律运动，恢复快一点"
            )
        if (
            bool(needs.get("recovery_light_movement"))
            and not bool(needs.get("regular_exercise"))
            and not fever_recovery
            and not heat_recovery
        ):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；今天慢慢走了走，恢复快一点"
            )
        if (
            bool(needs.get("good_sleep_streak"))
            and not fever_recovery
            and not heat_recovery
        ):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；最近睡得早，恢复快一点"
            )
        if (
            bool(needs.get("socially_satisfied"))
            and not fever_recovery
            and not heat_recovery
        ):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；最近有人陪着说说话，恢复快一点"
            )
        enriched["recent_illness_days"] = recent_illness_days
        if recent_illness_days >= 7:
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；最近反复生病，恢复期会拉长"
            )
        if _targeted_harm(needs):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；最近有做不适合当前症状的事，恢复会变慢"
            )
        elif _has_harmful_actions(needs):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；最近有在勉强自己，恢复会变慢"
            )
        elif _targeted_recovery(needs):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；最近有按症状照顾自己"
            )
        elif _has_recovery_actions(needs):
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；最近有好好休息"
            )
        if sick_days > 1:
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + f"；恢复中（病程第 {sick_days} 天，预计还需 {days_left} 天）"
            )
        elif days_left:
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + f"；预计还需 {days_left} 天恢复"
            )
    else:
        enriched["sick"] = False
        enriched["recovering"] = False
        enriched["sick_days"] = 0
        enriched["recovery_days_left"] = 0
        enriched["recovery_required_days"] = 0
        enriched["health_status"] = "healthy"
        enriched["fever_recovery"] = False
        enriched["heat_recovery"] = False
    enriched["recovery_log"] = recovery_log
    enriched["episodes"] = episodes
    enriched["recent_illness_days"] = recent_illness_days
    enriched["weak_constitution"] = weak_constitution
    if weak_constitution:
        enriched["summary"] = (
            str(enriched.get("summary") or "")
            + f"；最近30天生病 {recent_illness_days} 天，身体底子有点虚"
        )
    if status in ("sick", "recovering") and recovery_log:
        latest = recovery_log[-1] if isinstance(recovery_log[-1], dict) else {}
        actions = latest.get("actions") or []
        harmful = latest.get("harmful") or []
        parts = [str(value) for value in actions[:2]]
        parts.extend(str(value) for value in harmful[:2])
        if parts:
            enriched["summary"] = (
                str(enriched.get("summary") or "")
                + "；最近养病记录：" + "、".join(parts)
            )
    return enriched
