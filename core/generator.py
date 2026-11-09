from __future__ import annotations

import hashlib
import json
import random
from dataclasses import replace
from datetime import date, datetime, timedelta
from datetime import time as dt_time
from pathlib import Path

import holidays
from astrbot.api import logger

from .environment import building_prompt
from .food import FoodSystem
from .long_term import validate_stage_bundle
from .models import (
    DailyPlan,
    Outfit,
    ProactiveWindow,
    TimelineItem,
    minute_of_day,
    season_for_date,
    weather_for_date,
)
from .persona import PersonaContext
from .travel import TravelService, Trip
from .timeline_rules import split_multistop_transit
from .utils import extract_json_object
from .wardrobe import wardrobe_prompt
from . import health_journal, life_state, transport


MEAL_WORDS = (
    "早餐",
    "早饭",
    "早点",
    "午餐",
    "午饭",
    "中饭",
    "晚餐",
    "晚饭",
    "夜宵",
    "吃",
    "饭",
    "餐",
    "粥",
    "面",
    "米线",
    "饺子",
    "包子",
    "三明治",
    "吐司",
    "面包",
    "蛋",
    "肉",
    "鱼",
    "汤",
    "菜",
    "咖啡",
    "奶茶",
    "水果",
    "零食",
    "外卖",
    "食堂",
    "小吃",
)
REST_WORDS = ("休息", "午睡", "小憩", "躺", "放松", "发呆", "放空", "闭目")
HOME_LOCATION_WORDS = (
    "家",
    "楼",
    "室",
    "厅",
    "房",
    "厨",
    "浴",
    "阳台",
    "露台",
    "玄关",
    "楼梯",
    "衣帽间",
    "影音",
    "画室",
    "车库",
)


def _timeline_value(item, key: str, default=""):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def validate_timeline_realism(
    timeline,
    *,
    sleep_debt_minutes: int = 0,
    energy: int = 100,
    willingness: int = 100,
    health: int = 100,
    sick: bool = False,
    recovering: bool = False,
    illness_severity: str = "",
    weak_constitution: bool = False,
    bad_weather: bool = False,
    severe_weather: bool = False,
    winter: bool = False,
    extreme_cold: bool = False,
    fever: bool = False,
    hangover: bool = False,
    hangover_severe: bool = False,
    fever_recovery: bool = False,
    heat_illness: bool = False,
) -> None:
    """Reject schedules that cannot support a plausible waking day.

    This is deliberately structural rather than aesthetic: the model still
    controls the day, but every generated plan must cover 24 hours, include a
    real night's sleep, at least two food moments, and some after-noon rest.
    A high sleep debt additionally requires a recovery-oriented day.
    """
    items = [
        item
        for item in (timeline or [])
        if str(_timeline_value(item, "activity") or "").strip()
    ]
    if not items:
        raise ValueError("timeline 不能为空")
    items = sorted(
        items,
        key=lambda item: (
            minute_of_day(str(_timeline_value(item, "start") or "00:00")),
            minute_of_day(str(_timeline_value(item, "end") or "00:00")),
        ),
    )
    previous_end = 0
    sleep_minutes = 0
    meals = 0
    rests = 0
    intense_exercise = 0
    heavy_exercise = 0
    outside_blocks = 0
    transit_minutes = 0
    social_blocks = 0
    recovery_items = 0
    heavy_food = 0
    midday_outdoor = 0
    for item in items:
        start_text = str(_timeline_value(item, "start") or "")
        end_text = str(_timeline_value(item, "end") or "")
        try:
            start = minute_of_day(start_text)
            end = minute_of_day(end_text)
        except ValueError as exc:
            raise ValueError(f"时间格式不合法：{start_text}-{end_text}") from exc
        if start > previous_end:
            raise ValueError(
                f"timeline 在 {previous_end // 60:02d}:{previous_end % 60:02d}"
                f"-{start_text} 之间留有空档"
            )
        if start < previous_end:
            raise ValueError(f"timeline 在 {start_text} 处发生重叠")
        if end <= start:
            raise ValueError(f"时间区间不合法：{start_text}-{end_text}")
        previous_end = end
        activity = str(_timeline_value(item, "activity") or "")
        state = str(_timeline_value(item, "state") or "")
        location = str(_timeline_value(item, "location") or "")
        if state == "sleep":
            sleep_minutes += end - start
        if state == "transit":
            transit_minutes += end - start
        elif location and not any(word in location for word in HOME_LOCATION_WORDS):
            outside_blocks += 1
        outdoors = state == "transit" or (
            bool(location)
            and not any(word in location for word in HOME_LOCATION_WORDS)
        )
        if outdoors and start < 16 * 60 and end > 10 * 60:
            midday_outdoor += 1
        if state == "social" or any(
            word in activity for word in ("聚会", "约朋友", "见朋友", "社交", "一起吃饭")
        ):
            social_blocks += 1
        if any(word in activity for word in MEAL_WORDS):
            meals += 1
        if any(
            word in activity
            for word in ("喝水", "温水", "热水", "喝汤", "粥", "清淡", "姜茶", "热茶", "绿豆汤", "淡盐水", "西瓜")
        ):
            recovery_items += 1
        if any(
            word in activity
            for word in ("辣", "火锅", "烧烤", "炸", "酒", "啤酒", "白酒", "红酒")
        ):
            heavy_food += 1
        if start >= 12 * 60 and (
            state in ("sleep", "rest") or any(word in activity for word in REST_WORDS)
        ):
            rests += 1
        if any(
            word in activity
            for word in ("跑步", "慢跑", "健身", "力量训练", "爬山", "徒步", "游泳", "高强度")
        ):
            intense_exercise += 1
        if any(
            word in activity
            for word in ("健身", "力量训练", "爬山", "高强度", "长跑", "篮球")
        ):
            heavy_exercise += 1
    if previous_end < 24 * 60:
        raise ValueError(
            f"timeline 只覆盖到 {previous_end // 60:02d}:{previous_end % 60:02d}，必须覆盖 00:00-24:00"
        )
    if sleep_minutes < 300:
        raise ValueError(f"睡眠只有 {sleep_minutes} 分钟，至少需要 5 小时")
    if meals < 2:
        raise ValueError("timeline 里至少要有两次明确的吃饭/食物活动")
    if rests < 1:
        raise ValueError("午间之后至少要有一次休息、午睡或放空安排")
    if sleep_debt_minutes >= 180:
        if sleep_minutes < 420:
            raise ValueError(
                f"睡眠债已有 {sleep_debt_minutes} 分钟，今天至少要睡 7 小时，"
                f"当前只有 {sleep_minutes} 分钟"
            )
        if intense_exercise > 2:
            raise ValueError("睡眠债较高时，高强度运动最多安排 2 次")
        if outside_blocks > 3:
            raise ValueError("睡眠债较高时，外出安排不要超过 3 段")
        if transit_minutes > 150:
            raise ValueError("睡眠债较高时，通勤/交通总时长不要超过 2.5 小时")
    if sleep_debt_minutes >= 300:
        if sleep_minutes < 450:
            raise ValueError(
                f"睡眠债已有 {sleep_debt_minutes} 分钟，今天至少需要 7.5 小时睡眠"
            )
        if intense_exercise > 1:
            raise ValueError("睡眠债超过 5 小时时，高强度运动最多安排 1 次")
        if outside_blocks > 2:
            raise ValueError("睡眠债超过 5 小时时，外出安排不要超过 2 段")
        if transit_minutes > 90:
            raise ValueError("睡眠债超过 5 小时时，通勤/交通总时长不要超过 1.5 小时")
    if energy < 25 and intense_exercise > 2:
        raise ValueError("精力过低时，高强度运动不要超过 2 次")
    if willingness < 25:
        if outside_blocks > 2:
            raise ValueError("当前意愿偏低时，外出安排不要超过 2 段")
        if social_blocks > 1:
            raise ValueError("当前意愿偏低时，社交活动不要超过 1 次")
        if intense_exercise > 1:
            raise ValueError("当前意愿偏低时，高强度运动不要超过 1 次")
    if willingness < 15:
        if outside_blocks > 1:
            raise ValueError("当前意愿很低时，外出安排不要超过 1 段")
        if social_blocks > 0:
            raise ValueError("当前意愿很低时，尽量不安排社交活动")
    if health < 50:
        if sleep_minutes < 420:
            raise ValueError("身体状态偏低时，今天至少需要 7 小时睡眠")
        if intense_exercise > 1:
            raise ValueError("身体状态偏低时，高强度运动最多安排 1 次")
        if outside_blocks > 2:
            raise ValueError("身体状态偏低时，外出安排不要超过 2 段")
    if health < 35:
        if intense_exercise > 0:
            raise ValueError("身体很不舒服时，不要安排高强度运动")
        if outside_blocks > 1:
            raise ValueError("身体很不舒服时，外出安排不要超过 1 段")
    if sick:
        if sleep_minutes < 450:
            raise ValueError("生病时，今天至少要睡 7.5 小时")
        if intense_exercise > 0:
            raise ValueError("生病时，不要安排高强度运动")
        if outside_blocks > 1:
            raise ValueError("生病时，外出安排不要超过 1 段")
        if social_blocks > 0:
            raise ValueError("生病时，不建议安排社交活动")
    elif recovering:
        if sleep_minutes < 420:
            raise ValueError("恢复期至少需要 7 小时睡眠")
        if intense_exercise > 1:
            raise ValueError("恢复期高强度运动最多安排 1 次")
        if heavy_exercise > 0:
            raise ValueError("恢复期不要安排力量训练、爬山等重体力运动")
        if outside_blocks > 2:
            raise ValueError("恢复期外出安排不要超过 2 段")
        if social_blocks > 1:
            raise ValueError("恢复期社交活动不要超过 1 次")
    if illness_severity == "severe":
        if sleep_minutes < 480:
            raise ValueError("病情较重时，今天至少需要 8 小时睡眠")
        if intense_exercise > 0:
            raise ValueError("病情较重时，不要安排高强度运动")
        if outside_blocks > 0:
            raise ValueError("病情较重时，尽量待在家里休息")
        if social_blocks > 0:
            raise ValueError("病情较重时，不要安排社交活动")
    if weak_constitution:
        if sleep_minutes < 420:
            raise ValueError("最近反复生病、身体底子偏虚时，今天至少需要 7 小时睡眠")
        if intense_exercise > 1:
            raise ValueError("身体底子偏虚时，高强度运动最多安排 1 次")
        if outside_blocks > 2:
            raise ValueError("身体底子偏虚时，外出安排不要超过 2 段")
        if social_blocks > 1:
            raise ValueError("身体底子偏虚时，社交活动不要超过 1 次")
    if bad_weather:
        # Rain/wind is guidance for pacing, not a hard blocker: a slightly
        # over-packed day is better than leaving the whole day without a plan.
        if transit_minutes > 120:
            raise ValueError("坏天气时，通勤/交通总时长不要超过 2 小时")
        if intense_exercise > 1:
            raise ValueError("坏天气时，高强度运动最多安排 1 次")
    if severe_weather and outside_blocks > 1:
        raise ValueError("暴雨/台风/大雪等恶劣天气时，外出安排不要超过 1 段")
    if winter and outside_blocks > 2:
        # Winter clothing/weather is already handled by the prompt; do not
        # reject an otherwise complete day just because it has three outings.
        pass
    if extreme_cold and outside_blocks > 1:
        raise ValueError("最低气温低于 5°C 时，外出安排不要超过 1 段")
    if fever:
        if sleep_minutes < 480:
            raise ValueError("发烧时，今天至少需要 8 小时睡眠")
        if intense_exercise > 0:
            raise ValueError("发烧时，不要安排高强度运动")
        if outside_blocks > 1:
            raise ValueError("发烧时，外出安排不要超过 1 段")
        if social_blocks > 0:
            raise ValueError("发烧时，不要安排社交活动")
        if recovery_items < 1:
            raise ValueError("发烧时，今天至少要安排喝水、热汤或粥")
    if hangover:
        if sleep_minutes < 420:
            raise ValueError("宿醉时，今天至少需要 7 小时睡眠")
        if recovery_items < 1:
            raise ValueError("宿醉时，今天至少要安排喝水、热汤或清淡饮食")
        if outside_blocks > 2:
            raise ValueError("宿醉时，外出安排不要超过 2 段")
        if intense_exercise > 1:
            raise ValueError("宿醉时，高强度运动最多安排 1 次")
    if hangover_severe:
        if sleep_minutes < 480:
            raise ValueError("重度宿醉时，今天至少需要 8 小时睡眠")
        if outside_blocks > 1:
            raise ValueError("重度宿醉时，外出安排不要超过 1 段")
        if social_blocks > 0:
            raise ValueError("重度宿醉时，不要安排社交活动")
    if fever_recovery:
        if sleep_minutes < 420:
            raise ValueError("刚退烧时，今天至少需要 7 小时睡眠")
        if meals < 3:
            raise ValueError("刚退烧时，今天至少要安排三餐")
        if recovery_items < 1:
            raise ValueError("刚退烧时，今天至少要安排喝水、粥或清淡饮食")
        if heavy_food > 0:
            raise ValueError("刚退烧时，不要安排辛辣、油炸、烧烤或酒精")
        if outside_blocks > 2:
            raise ValueError("刚退烧时，外出安排不要超过 2 段")
    if heat_illness:
        if midday_outdoor > 0:
            raise ValueError("中暑恢复期，10:00-16:00 尽量不要安排户外活动")
        if recovery_items < 1:
            raise ValueError("中暑恢复期，今天至少要安排喝水或清淡饮食")
        if outside_blocks > 1:
            raise ValueError("中暑恢复期，外出安排不要超过 1 段")


class DailyPlanGenerator:
    def __init__(self, context, config, data_dir: Path | None = None):
        self.context = context
        self.config = config
        self.data_dir = data_dir
        self.generating: set[str] = set()
        self.food = FoodSystem(data_dir, Path(__file__).with_name("food_catalog.json"))
        self.travel = TravelService(
            data_dir, Path(__file__).with_name("travel_destinations.json")
        )

    def _settings(self) -> dict:
        return self.config.get("schedule_settings", {}) or {}

    def _prompt_settings(self) -> dict:
        return self.config.get("prompt_settings", {}) or {}

    def _pool(self) -> dict:
        return self.config.get("creative_pool", {}) or {}

    def _rhythm_settings(self) -> dict:
        return self.config.get("schedule_rhythm", {}) or {}

    def _food_settings(self) -> dict:
        return self.config.get("food_settings", {}) or {}

    def _travel_settings(self) -> dict:
        return self.config.get("travel_settings", {}) or {}

    def _travel_prompt(
        self, target: date, persona: PersonaContext
    ) -> tuple[str, Trip | None, str]:
        """Return the travel prompt block, the trip and its phase for ``target``.

        The service also plans new trips, so a day far from any trip may still
        come back with a countdown block once a trip has just been scheduled.
        """
        settings = self._travel_settings()
        if not bool(settings.get("enable", True)):
            return "", None, "none"
        try:
            found = self.travel.ensure(
                persona.id,
                target,
                persona.prompt,
                holiday=self._holiday(target),
                settings=settings,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "[Virtual Life] Travel planning failed persona=%s: %s", persona.id, exc
            )
            return "", None, "none"
        if found is None:
            return "", None, "none"
        trip, phase = found
        try:
            block = self.travel.prompt_block(trip, phase, target, settings)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "[Virtual Life] Travel prompt failed persona=%s: %s", persona.id, exc
            )
            return "", None, "none"
        return block, trip, phase

    def _apply_travel(
        self, plan: DailyPlan, trip: Trip | None, phase: str
    ) -> DailyPlan:
        """Normalise timeline locations so away days stay in the destination."""
        if trip is None or phase == "none":
            return plan
        try:
            updated, changes = self.travel.apply(
                plan, trip, phase, self._travel_settings()
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "[Virtual Life] Travel location normalisation failed persona=%s: %s",
                plan.persona_id,
                exc,
            )
            return plan
        if changes:
            logger.info(
                "[Virtual Life] Travel locations normalised persona=%s date=%s city=%s changes=%s",
                plan.persona_id,
                plan.date,
                trip.city,
                len(changes),
            )
        return updated

    def _home_items_path(self) -> Path:
        return Path(__file__).with_name("home_items.json")

    def _load_home_items(self) -> list[dict]:
        try:
            payload = json.loads(self._home_items_path().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        items = payload.get("items", []) if isinstance(payload, dict) else []
        return [item for item in items if isinstance(item, dict)]

    def _outdoor_scenes_path(self) -> Path:
        return Path(__file__).with_name("outdoor_scenes.json")

    def _load_outdoor_scenes(self) -> list[dict]:
        try:
            payload = json.loads(
                self._outdoor_scenes_path().read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return []
        scenes = payload.get("scenes", []) if isinstance(payload, dict) else []
        return [scene for scene in scenes if isinstance(scene, dict)]

    def _home_items_prompt(self) -> str:
        items = self._load_home_items()
        if not items:
            return ""
        grouped: dict[str, list[str]] = {}
        for item in items:
            room = str(item.get("room") or "家").strip()
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            actions = [
                str(action).strip()
                for action in item.get("actions", [])
                if str(action).strip()
            ]
            label = name + ("（" + "、".join(actions) + "）" if actions else "")
            grouped.setdefault(room, []).append(label)
        if not grouped:
            return ""
        lines = [building_prompt(), wardrobe_prompt(), "【家中的可互动物品与设施】"]
        for room, labels in grouped.items():
            floor = next(
                (item.get("floor", 1) for item in items if item.get("room") == room), 1
            )
            lines.append(f"- {floor}楼·{room}：" + "；".join(labels))
        lines.append(
            "生成 timeline 时，请自然地从这些物品和活动里选择当天会用到的内容；"
            "不必全部使用，也不要虚构家里没有的大型设施。物品名可以出现在 activity 中"
            "（例如“用手冲壶做咖啡”“在阳台给绿植浇水”），location 使用「一楼·厨房」或「二楼·画室」等准确楼层与房间；换楼层安排自然的上下楼过渡。"
        )
        return "\n".join(lines)

    def _home_wish_prompt(self, target: date, persona_id: str = "") -> str:
        if self.data_dir is None:
            return ""
        path = Path(self.data_dir) / "home_item_wishes.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ""
        wishes = payload.get("wishes", []) if isinstance(payload, dict) else []
        target_text = target.isoformat()
        selected: list[str] = []
        for wish in wishes:
            if not isinstance(wish, dict):
                continue
            if str(wish.get("date") or "") != target_text:
                continue
            if wish.get("persona") and str(wish["persona"]) != persona_id:
                continue
            room = str(wish.get("room") or "").strip()
            name = str(wish.get("name") or "").strip()
            action = str(wish.get("action") or "").strip()
            if not name:
                continue
            selected.append(f"- {room}·{name}" + (f"：{action}" if action else ""))
        if not selected:
            return ""
        return (
            "【主人今天点名希望参考的家庭活动】\n"
            + "\n".join(selected[:20])
            + "\n如果与当天主题、心情和作息不冲突，请优先把这些活动自然排进 timeline；"
            "不要为了满足清单硬塞。"
        )

    def _previous_life_needs(self, target: date, persona_id: str = "") -> tuple[date, dict] | None:
        """Load the most recent pre-target body state for validation."""
        if self.data_dir is None:
            return None
        try:
            payload = json.loads(
                (Path(self.data_dir) / "plans.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return None
        plans = payload.get("plans", {}) if isinstance(payload, dict) else {}
        if not isinstance(plans, dict):
            return None
        selected: tuple[date, dict] | None = None
        for value in plans.values():
            if not isinstance(value, dict):
                continue
            if persona_id and str(value.get("persona_id") or "") not in ("", persona_id):
                continue
            try:
                plan_day = date.fromisoformat(str(value.get("date") or ""))
            except ValueError:
                continue
            if plan_day >= target:
                continue
            if selected is None or plan_day > selected[0]:
                selected = (plan_day, value)
        if selected is None:
            return None
        plan_day, plan = selected
        history_plans = sorted(
            (
                value
                for value in plans.values()
                if isinstance(value, dict)
                and str(value.get("date") or "") < plan_day.isoformat()
                and (
                    not persona_id
                    or str(value.get("persona_id") or "") in ("", persona_id)
                )
            ),
            key=lambda value: str(value.get("date") or ""),
        )[-3:]
        try:
            journal_state = self._health_journal_state(target, persona_id)
            needs = life_state.compute(
                plan,
                datetime.combine(plan_day, dt_time(23, 59)),
                history_plans=history_plans,
                weak_constitution=bool(journal_state.get("weak_constitution")),
                recent_illness_days=int(
                    journal_state.get("recent_illness_days") or 0
                ),
            )
        except (TypeError, ValueError):
            return None
        return plan_day, needs

    def _previous_night_alcohol_severity(self, target: date, persona_id: str = "") -> str:
        if self.data_dir is None:
            return ""
        try:
            payload = json.loads(
                (Path(self.data_dir) / "plans.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return ""
        plans = payload.get("plans", {}) if isinstance(payload, dict) else {}
        if not isinstance(plans, dict):
            return ""
        previous_day = (target - timedelta(days=1)).isoformat()
        for value in plans.values():
            if not isinstance(value, dict):
                continue
            if str(value.get("date") or "") != previous_day:
                continue
            if persona_id and str(value.get("persona_id") or "") not in ("", persona_id):
                continue
            minutes = 0
            text = ""
            for item in value.get("timeline") or []:
                if not isinstance(item, dict):
                    continue
                activity = str(item.get("activity") or "")
                if not any(
                    word in activity
                    for word in ("喝酒", "酒吧", "微醺", "啤酒", "红酒", "白酒")
                ):
                    continue
                try:
                    start = minute_of_day(str(item.get("start") or "00:00"))
                    end = minute_of_day(str(item.get("end") or "00:00"))
                    minutes += max(0, end - start)
                except ValueError:
                    pass
                text += " " + activity
            if minutes <= 0:
                return ""
            if (
                minutes >= 120
                or "酒吧" in text
                or "喝多" in text
                or any(
                    word in text
                    for word in ("白酒", "红酒", "威士忌", "伏特加", "烈酒")
                )
            ):
                return "severe"
            return "mild"
        return ""

    def _previous_night_alcohol(self, target: date, persona_id: str = "") -> bool:
        return bool(self._previous_night_alcohol_severity(target, persona_id))

    def _weather_outfit_prompt(self, target: date) -> str:
        try:
            weather = weather_for_date(target)
        except (TypeError, ValueError):
            return ""
        text = str(getattr(weather, "prompt_text", None) or weather or "")
        try:
            low = int(getattr(weather, "temperature_low", 15))
            high = int(getattr(weather, "temperature_high", 22))
        except (TypeError, ValueError):
            low, high = 15, 22
        lines: list[str] = []
        if any(word in text for word in ("雨", "雪")):
            lines.append("带伞或防水外套，鞋底防滑，别让裙摆拖地。")
        if low < 10:
            lines.append("天气偏冷，主套装外加厚外套/针织开衫/围巾，不要光腿。")
        elif low < 15:
            lines.append("早晚偏凉，带一件薄外套，方便增减。")
        if high >= 28:
            lines.append("中午偏热，选轻薄透气材质，注意防晒。")
        if high - low >= 10:
            lines.append("温差较大，采用叠穿，早晚加外套、中午可脱。")
        if not lines:
            return ""
        return "【天气穿搭】" + "".join(lines)

    def _life_state_prompt(self, target: date, persona_id: str = "") -> str:
        """Give the schedule model yesterday's end-of-day body state.

        The model still decides the day, but a very tired / hungry / grimy
        character should not be planned as if she had a full battery.
        """
        if self.data_dir is None:
            return ""
        try:
            payload = json.loads(
                (Path(self.data_dir) / "plans.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return ""
        plans = payload.get("plans", {}) if isinstance(payload, dict) else {}
        if not isinstance(plans, dict):
            return ""
        selected: tuple[date, dict] | None = None
        for value in plans.values():
            if not isinstance(value, dict):
                continue
            if persona_id and str(value.get("persona_id") or "") not in ("", persona_id):
                continue
            try:
                plan_day = date.fromisoformat(str(value.get("date") or ""))
            except ValueError:
                continue
            if plan_day >= target:
                continue
            if selected is None or plan_day > selected[0]:
                selected = (plan_day, value)
        if selected is None:
            return ""
        plan_day, plan = selected
        history_plans = sorted(
            (
                value
                for value in plans.values()
                if isinstance(value, dict)
                and str(value.get("date") or "") < plan_day.isoformat()
                and (
                    not persona_id
                    or str(value.get("persona_id") or "") in ("", persona_id)
                )
            ),
            key=lambda value: str(value.get("date") or ""),
        )[-3:]
        try:
            needs = life_state.compute(
                plan,
                datetime.combine(plan_day, dt_time(23, 59)),
                history_plans=history_plans,
            )
        except (TypeError, ValueError):
            return ""
        summary = str(needs.get("summary") or "").strip()
        if not summary:
            return ""
        debt = int(needs.get("sleep_debt_minutes") or 0)
        energy = int(needs.get("energy") if needs.get("energy") is not None else 100)
        willingness = int(
            needs.get("willingness") if needs.get("willingness") is not None else 100
        )
        health = int(needs.get("health") if needs.get("health") is not None else 100)
        sick = bool(needs.get("sick"))
        recovery = ""
        if debt >= 240:
            recovery = (
                "\n【恢复优先】睡眠债已经超过 4 小时：今天应明显降低强度，"
                "减少不必要的外出和长途移动，避免高强度运动，安排补觉或更长休息，并提前入睡。"
            )
        elif debt >= 120:
            recovery = (
                "\n【轻度恢复】睡眠债超过 2 小时：今天适当减少高强度活动、长时间专注和不必要的外出，"
                "安排一段补觉或放空，晚上不要太晚睡。"
            )
        elif energy < 35:
            recovery = (
                "\n【精力偏低】今天不要把高强度活动排得太满，留出恢复和休息的余量。"
            )
        if willingness < 30:
            recovery += (
                "\n【意愿偏低】今天尽量减少社交、外出和需要勉强自己的安排，"
                "多留一点独处和恢复时间，但不要把所有事都取消。"
            )
        elif willingness < 50:
            recovery += (
                "\n【意愿一般】今天社交和外出保持适度，不要连续安排太多费神的活动。"
            )
        if health < 55:
            recovery += (
                "\n【身体状态偏低】今天减少高强度活动和不必要的外出，"
                "保证睡眠和三餐，多安排温和的休息。"
            )
        if sick:
            recovery += (
                "\n【生病恢复】今天以休息为主：取消高强度运动和社交，"
                "减少外出，保证至少 7.5 小时睡眠，安排清淡饮食和室内放松。"
            )
            if bool(needs.get("fever")):
                recovery += (
                    "\n【发烧】今天额头有点烫，尽量卧床、多喝水、吃粥或汤，"
                    "不要出门吹风，也不要运动或社交，保证 8 小时睡眠。"
                )
            symptoms = needs.get("symptoms") or []
            if symptoms:
                recovery += "目前症状：" + "、".join(
                    str(value) for value in symptoms[:3]
                ) + "。"
        elif bool(needs.get("recovering")):
            recovery += (
                "\n【恢复期】身体还在恢复，今天保持低强度，少安排社交和外出，"
                "保证睡眠和三餐，不要急着恢复满负荷。"
            )
        journal_state = self._health_journal_state(target, persona_id)
        if journal_state.get("weak_constitution"):
            recent_days = int(journal_state.get("recent_illness_days") or 0)
            recovery += (
                f"\n【体虚】最近30天已经生病约 {recent_days} 天，身体底子偏虚。"
                "今天降低强度，保证 7 小时以上睡眠，高强度运动最多 1 次，"
                "外出和社交都控制少一些。"
            )
        if journal_state.get("fever_recovery"):
            recovery += (
                "\n【退烧恢复】刚退过烧，胃口和体力还没完全恢复。"
                "今天饮食清淡、多喝水，不要立刻高强度工作或运动，"
                "保证睡眠，给自己留一点缓冲。"
            )
        if self._previous_night_alcohol(target, persona_id):
            severe = self._previous_night_alcohol_severity(target, persona_id) == "severe"
            recovery += (
                "\n【宿醉】昨晚喝了酒，今天头可能有点沉。保证 7 小时睡眠，"
                "安排喝水、热汤或清淡饮食，不要立刻高强度运动，外出也少一点。"
            )
            if severe:
                recovery += (
                    "昨晚喝得有点多，今天尽量 8 小时睡眠、只安排 1 段外出，"
                    "不要社交，先补水吃清淡的。"
                )
        if bool(needs.get("heat_illness")) or self._health_journal_state(
            target, persona_id
        ).get("heat_recovery"):
            recovery += (
                "\n【中暑恢复】昨天暴晒后有点中暑，今天避开 10:00-16:00 的户外，"
                "多喝水、待在阴凉处，不要中午出门运动。"
            )
        outfit_weather = self._weather_outfit_prompt(target)
        if outfit_weather:
            recovery += "\n" + outfit_weather
        return (
            f"【前一天结束时的生理状态（{plan_day.isoformat()}）】\n"
            f"{summary}\n"
            "生成今天的时间线时，请让这些状态自然影响安排："
            "精力低就优先保证睡眠和休息、减少高强度活动；"
            "饱腹低就把三餐和加餐排足；清洁低就安排洗漱或泡澡；"
            "心情低就安排放松、喜欢的事或温和的社交。"
            "不要机械加塞，也不要直接复述这些数值。"
            + recovery
        )

    def _health_journal_state(
        self,
        target: date,
        persona_id: str = "",
    ) -> dict:
        if self.data_dir is None or not persona_id:
            return {}
        try:
            return health_journal.persona_state(
                Path(self.data_dir), persona_id, today=target
            )
        except (OSError, TypeError, ValueError):
            return {}

    def _outdoor_options_prompt(self) -> str:
        scenes = self._load_outdoor_scenes()
        if not scenes:
            return ""
        lines = ["【外出场景选项】"]
        for scene in scenes:
            name = str(scene.get("name") or "").strip()
            if not name:
                continue
            raw_activities = scene.get("activities", [])
            activities = (
                [
                    str(action).strip()
                    for action in raw_activities
                    if str(action).strip()
                ]
                if isinstance(raw_activities, list)
                else []
            )
            lines.append(
                "- "
                + name
                + ("（" + "、".join(activities) + "）" if activities else "")
            )
            if scene.get("description"):
                lines.append("  环境：" + str(scene["description"]))
            if scene.get("weather_notes"):
                lines.append("  天气与时间：" + str(scene["weather_notes"]))
        if len(lines) <= 1:
            return ""
        lines.append(
            "【今日选项排序】\n"
            "生成 timeline 前，先在内部把「家中的可互动物品与设施」和上面的「外出场景选项」放在一起排序：\n"
            "- 结合人格偏好、当天主题、心情、精力、时间段、天气感、最近是否去过、活动新鲜度和重复成本打分；\n"
            "- 家中活动优先选择排序靠前的 2-4 项，外出活动优先选择 1-2 项，再补充吃饭、通勤和必要休息；\n"
            "- 如果主人今天点名希望参考的家庭活动在列，把它放在家庭活动排序的最前面；\n"
            "- 避免连续多天重复同一地点或同一活动；排序只用于内部决策，不要输出排序过程或额外字段。\n"
            "各场景的 location 请直接使用场景名或其中提到的具体地点，方便观察窗识别。"
        )
        return "\n".join(lines)

    def _transport_prompt(self) -> str:
        settings = self.config.get("transport_settings", {}) or {}
        if not bool(settings.get("enable", True)):
            return ""
        return transport.transport_prompt()

    def _schedule_rhythm_prompt(self, target: date) -> str:
        settings = self._rhythm_settings()
        if not bool(settings.get("enable", True)):
            return ""

        def text(key: str, default: str) -> str:
            value = settings.get(key, default)
            return str(value).strip() if value not in (None, "") else default

        def number(key: str, default: int) -> int:
            try:
                return int(settings.get(key, default))
            except (TypeError, ValueError):
                return default

        wake = text("wake_time", "07:00")
        sleep = text("sleep_time", "23:30")
        breakfast = text("breakfast_window", "07:00-09:00")
        lunch = text("lunch_window", "11:30-13:30")
        dinner = text("dinner_window", "17:30-19:30")
        min_act = number("min_activity_minutes", 20)
        max_act = number("max_activity_minutes", 180)
        min_items = number("timeline_min_items", 8)
        max_items = number("timeline_max_items", 16)
        out_min = number("outdoor_min_per_day", 0)
        out_max = number("outdoor_max_per_day", 2)
        home_min = number("home_item_min_per_day", 2)
        home_max = number("home_item_max_per_day", 4)
        transition = number("transition_minutes", 15)
        wind_down = number("wind_down_minutes", 45)

        if min_act > max_act:
            min_act, max_act = max_act, min_act
        if min_items > max_items:
            min_items, max_items = max_items, min_items
        if out_min > out_max:
            out_min, out_max = out_max, out_min
        if home_min > home_max:
            home_min, home_max = home_max, home_min

        min_act = max(5, min_act)
        max_act = max(min_act, max_act)
        min_items = max(1, min_items)
        max_items = max(min_items, max_items)
        out_min = max(0, out_min)
        out_max = max(out_min, out_max)
        home_min = max(0, home_min)
        home_max = max(home_min, home_max)
        transition = max(0, transition)
        wind_down = max(0, wind_down)

        season = season_for_date(target)
        weather = weather_for_date(target)
        weekend = target.weekday() >= 5

        lines = [
            "【日程精细度规则】",
            f"- 季节：{season}；今日天气：{weather.prompt_text}。活动和穿搭要符合季节与天气；"
            "雨天、大风或寒冷时优先室内场景，晴朗可安排公园或海边，闷热时减少长时间户外。",
        ]
        weather_text = str(getattr(weather, "prompt_text", "") or "")
        if any(word in weather_text for word in ("雨", "雪", "雷", "大风", "寒")):
            lines.append(
                "- 今天天气不好，外出活动最多 2 段（往返 transit 不计入），其余安排在家里或室内。"
            )
        lines.extend([
            f"- 参考作息：起床 {wake}，入睡 {sleep}；00:00 到起床、入睡到 24:00 必须是 sleep。"
            + ("周末可晚起 30-60 分钟。" if weekend else "工作日按参考作息起床。")
            + "若人格需要熬夜，必须在 activity 中体现，并保留足够的恢复时间。",
            f"- 三餐窗口：早餐 {breakfast}，午餐 {lunch}，晚餐 {dinner}；"
            "每餐 20-60 分钟，activity 要写清吃什么、在哪里吃。",
            f"- timeline 保持 {min_items}-{max_items} 项；清醒活动单项 {min_act}-{max_act} 分钟。"
            f"超过 {max_act} 分钟的专注或外出，拆成活动 + 短休息/转场。",
            f"- 每天安排 {out_min}-{out_max} 次外出；外出地点必须来自【外出场景选项】，"
            f"离开和返回时安排约 {transition} 分钟的 transit。",
            "- 如果外出途中顺路去杂货铺、便利店、快递站等，必须拆成三段分别写："
            "「在路上」→「店铺/站点」→「在路上」；不要把「步行回家，顺路买东西」"
            "写成同一个 timeline 项。",
            f"- 每天使用 {home_min}-{home_max} 件不同的家中物品；"
            "不要连续多天只用床、书桌或手机。",
            f"- 13:00-15:00 安排一段低强度休息或午睡；睡前留出约 {wind_down} 分钟做洗漱、"
            "阅读、听音乐等低刺激活动。",
            "- state/availability 与活动一致：sleep→blocked；工作/学习→busy 或 focus；"
            "社交/外出社交→social；通勤→transit；自由活动→available。",
            "- 避免连续两项完全相同；避免一天内多次往返同一个远距离地点；"
            "活动名称要具体到动作、物品或地点，不要只写“休息”“娱乐”“工作”。",
            "- 主题为宅家日时外出取 0-1 次；探索日取 1-2 次；工作日以办公室、书房和专注块为主；"
            "自我提升日多安排学习、阅读、运动。",
        ])
        return "\n".join(lines)

    def _food_catalog_path(self) -> Path:
        return Path(__file__).with_name("food_catalog.json")

    def _load_food_catalog(self) -> dict:
        try:
            payload = json.loads(self._food_catalog_path().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _food_detail_prompt(self, target: date) -> str:
        settings = self._food_settings()
        if not bool(settings.get("enable", True)):
            return ""
        catalog = self._load_food_catalog()
        meals = catalog.get("meals", {})
        if not isinstance(meals, dict) or not meals:
            return ""

        def number(key: str, default: int) -> int:
            try:
                return int(settings.get(key, default))
            except (TypeError, ValueError):
                return default

        home_min = max(0, number("home_cooked_min_per_day", 1))
        home_max = max(home_min, number("home_cooked_max_per_day", 2))
        takeout_max = max(0, number("takeout_max_per_day", 1))
        grocery_min = max(0, number("grocery_shopping_min_per_week", 1))
        grocery_max = max(grocery_min, number("grocery_shopping_max_per_week", 3))
        variety_days = max(1, number("dish_variety_days", 3))
        include_ingredients = bool(settings.get("include_ingredients", True))
        include_method = bool(settings.get("include_cooking_method", True))
        include_shopping = bool(settings.get("include_shopping_list", True))

        lines = ["【饮食与做饭细节】"]
        for meal_name, dishes in meals.items():
            if not isinstance(dishes, list):
                continue
            labels: list[str] = []
            for dish in dishes:
                if not isinstance(dish, dict):
                    continue
                name = str(dish.get("name") or "").strip()
                if not name:
                    continue
                details: list[str] = []
                raw_ingredients = dish.get("ingredients", [])
                ingredients = (
                    [str(item).strip() for item in raw_ingredients if str(item).strip()]
                    if isinstance(raw_ingredients, list)
                    else []
                )
                if include_ingredients and ingredients:
                    details.append("食材：" + "、".join(ingredients))
                method = str(dish.get("method") or "").strip()
                if include_method and method:
                    details.append("做法：" + method)
                labels.append(
                    name + ("（" + "；".join(details) + "）" if details else "")
                )
            if labels:
                lines.append(f"- {meal_name}可选：" + "、".join(labels))

        lines.extend(
            [
                f"- 每天安排 {home_min}-{home_max} 顿在家做饭；外卖或食堂最多 {takeout_max} 顿，"
                "其余可以用简单早餐、加餐或剩菜解决。",
                "- 每顿正餐必须写出具体菜名；做饭的 activity 写成“做XX（食材：…；做法：…）”，"
                "吃饭写成“吃XX”，不要只写“做饭”“吃饭”。",
                f"- 参考最近 {variety_days} 天的历史日程，避免重复同一道菜；"
                "同类菜可以换食材、换做法或换主食。",
            ]
        )
        if include_shopping:
            lines.extend(
                [
                    f"- 每周安排 {grocery_min}-{grocery_max} 次食材采购；需要补货时去超市、杂货铺或菜市场，"
                    "activity 要写清买什么，location 使用对应场景名。",
                    "- 优先使用冰箱里已有的食材；采购清单要有蔬菜、肉蛋水产、主食、乳品豆制品或调味杂货。",
                ]
            )
        lines.append(
            "- 从人格设定读取饮食偏好和忌口；没有偏好时均衡搭配蛋白质、蔬菜和主食，"
            "不要连续多天只吃面包、泡面或外卖。"
        )
        return "\n".join(lines)

    def _fridge_inventory_path(self) -> Path | None:
        if self.data_dir is None:
            return None
        return Path(self.data_dir) / "fridge_inventory.json"

    def _load_fridge_inventory(self) -> list[dict]:
        path = self._fridge_inventory_path()
        if path is None:
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        ingredients = (
            payload.get("ingredients", []) if isinstance(payload, dict) else []
        )
        return [item for item in ingredients if isinstance(item, dict)]

    def _fridge_prompt(self) -> str:
        if not bool(self._food_settings().get("enable", True)):
            return ""
        ingredients = self._load_fridge_inventory()
        if not ingredients:
            return ""
        grouped: dict[str, list[str]] = {}
        for item in ingredients:
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            category = str(item.get("category") or "其他").strip() or "其他"
            quantity = item.get("quantity")
            unit = str(item.get("unit") or "").strip()
            label = name
            if quantity not in (None, ""):
                label += "×" + str(quantity) + (unit or "")
            grouped.setdefault(category, []).append(label)
        if not grouped:
            return ""
        lines = ["【冰箱与储物柜现有食材】"]
        for category, labels in grouped.items():
            lines.append(f"- {category}：" + "、".join(labels))
        lines.extend(
            [
                "【冰箱配菜规则】",
                "- 做饭优先使用上面现有食材，至少搭配 2 种；可以自由组合成新菜，"
                "但必须写出菜名、主要食材和做法。",
                "- 尽量按“主食 + 蛋白质 + 蔬菜”搭配，避免只用一种食材凑一顿。",
                "- 如果某道菜缺 1-2 样食材，把缺少的写进采购清单，并安排去超市、杂货铺或菜市场补货；"
                "不要重复购买冰箱里已有且数量充足的食材。",
                "- 冰箱库存是当前快照；食材用完后改用其他组合或采购，不要凭空变出大量食材。",
            ]
        )
        return "\n".join(lines)

    def _food_prompt(
        self, target: date, persona: PersonaContext, *, away: bool = False
    ) -> tuple[str, dict | None]:
        settings = self._food_settings()
        if not bool(settings.get("enable", True)):
            return "", None
        if away:
            return (
                "【旅行中的饮食】\n"
                "- 今天在外地旅行，三餐都在当地吃：写清城市和菜名"
                "（例如“在京都锦市场吃汤豆腐”），不要安排在家做饭、买菜或点外卖到住处。\n"
                "- 早餐可以从简（便利店、咖啡馆、住处早餐），午餐和晚餐挑当地特色；"
                "最好和行程里的地点对得上。\n"
                "- 采购和备菜留到回家以后，不要为了凑满冰箱临时去菜市场。",
                None,
            )
        if not bool(settings.get("dynamic_menu_enable", True)):
            parts = [self._food_detail_prompt(target), self._fridge_prompt()]
            return "\n\n".join(part for part in parts if part), None
        try:
            menu = self.food.plan_day(
                target,
                persona.id,
                persona.prompt,
                settings,
                self._rhythm_settings(),
            )
            if not menu:
                raise RuntimeError("empty food menu")
            return self.food.format_day_prompt(menu, settings), menu
        except Exception as exc:
            logger.warning(
                "[Virtual Life] Dynamic menu planning failed persona=%s: %s",
                persona.id,
                exc,
            )
            parts = [self._food_detail_prompt(target), self._fridge_prompt()]
            return "\n\n".join(part for part in parts if part), None

    def _apply_food_state(
        self,
        plan: DailyPlan,
        persona: PersonaContext,
        menu: dict | None,
    ) -> None:
        if menu is None:
            return
        try:
            result = self.food.apply_plan(plan, persona.id, menu, self._food_settings())
            if result.get("status") == "applied":
                logger.info(
                    "[Virtual Life] Food updated persona=%s date=%s consumed=%s purchased=%s",
                    persona.id,
                    plan.date,
                    result.get("consumed"),
                    result.get("purchased"),
                )
        except Exception as exc:
            logger.warning(
                "[Virtual Life] Food inventory update failed persona=%s: %s",
                persona.id,
                exc,
            )

    @staticmethod
    def _pick(values: object, fallback: str) -> str:
        candidates = (
            [str(value) for value in values] if isinstance(values, list) else []
        )
        return random.choice(candidates) if candidates else fallback

    def _holiday(self, target: date) -> str:
        try:
            return str(holidays.country_holidays("CN").get(target, "普通日期"))
        except Exception:
            return "普通日期"

    def _window_budget_caps(self) -> tuple[int | None, int | None]:
        """Per-audience proactive window count ceilings derived from daily budget.

        Returns the friend and group caps as optional ints. A cap is None when
        the corresponding session type is disabled (no budget exists). When set,
        the cap mirrors the effective daily budget ceiling: daily_budget_max
        clamped by daily_hard_max.
        """

        def cap_for(settings_key: str) -> int | None:
            settings = self.config.get(settings_key, {}) or {}
            if not settings.get("enable", False):
                return None
            minimum = max(0, int(settings.get("daily_budget_min", 0)))
            maximum = max(minimum, int(settings.get("daily_budget_max", minimum)))
            hard_max = max(0, int(settings.get("daily_hard_max", maximum)))
            return min(maximum, hard_max)

        return cap_for("friend_settings"), cap_for("group_settings")

    async def generate(
        self,
        target: date,
        persona: PersonaContext,
        extra: str = "",
        history_plans: list[DailyPlan] | None = None,
        long_term_context: str = "",
        relationship_context: str = "",
        include_schedule: bool = True,
        include_outfit: bool = True,
        base_plan: DailyPlan | None = None,
    ) -> DailyPlan:
        """Generate a complete plan from the combined schedule and outfit prompts.

        Args:
            target: Date to generate.
            persona: Persona used to guide the plan.
            extra: Optional administrator requirements.
            history_plans: Recent plans used to reduce repetition.
            long_term_context: Optional long-term stage constraints.
            relationship_context: Optional Personal Network relationship context.

        Returns:
            A complete validated plan, or a failed placeholder after all retries.
        """
        pool = self._pool()
        if not include_schedule and not include_outfit:
            if base_plan is not None:
                return base_plan
            revision = hashlib.sha1(
                f"{target.isoformat()}::{persona.id}::empty".encode()
            ).hexdigest()[:12]
            return DailyPlan(
                date=target.isoformat(),
                persona_id=persona.id,
                theme="",
                mood="",
                outfit=None,
                timeline=(),
                revision=revision,
            )
        theme = (
            self._pick(pool.get("themes"), "日常日")
            if include_schedule
            else (base_plan.theme if base_plan else "")
        )
        mood = (
            self._pick(pool.get("moods"), "平静")
            if include_schedule
            else (base_plan.mood if base_plan else "")
        )
        outfit_style = (
            self._pick(pool.get("outfit_styles"), "日常休闲风")
            if include_outfit
            else (base_plan.outfit.style if base_plan and base_plan.outfit else "")
        )
        mode = (
            "完整生成"
            if include_schedule and include_outfit
            else ("生成日程" if include_schedule else "生成穿搭")
        )
        outfit_context, timeline = (
            self._format_plan_context(base_plan) if base_plan else ("", "")
        )
        try:
            return await self._generate_plan(
                target,
                persona,
                mode=mode,
                include_schedule=include_schedule,
                include_outfit=include_outfit,
                theme=theme,
                mood=mood,
                outfit_style=outfit_style,
                base_plan=base_plan,
                history=self._format_history(history_plans or []),
                long_term_context=long_term_context,
                relationship_context=relationship_context,
                outfit_context=outfit_context,
                timeline=timeline,
                requirements=extra,
                update_theme_mood=include_schedule,
            )
        except RuntimeError as exc:
            return DailyPlan(
                date=target.isoformat(),
                persona_id=persona.id,
                theme="生成失败",
                mood="未知",
                outfit=None,
                timeline=(),
                status="failed",
                revision=hashlib.sha1(str(exc).encode("utf-8")).hexdigest()[:12],
            )

    async def rewrite_schedule(
        self,
        plan: DailyPlan,
        persona: PersonaContext,
        *,
        extra: str = "",
        long_term_context: str = "",
        relationship_context: str = "",
    ) -> DailyPlan:
        """Rewrite timeline-related fields while preserving plan identity and outfit.

        Args:
            plan: Existing valid daily plan.
            persona: Persona used to guide the rewritten activities.
            extra: Optional administrator requirements for the timeline.
            long_term_context: Optional long-term stage constraints.
            relationship_context: Optional Personal Network relationship context.

        Returns:
            A validated plan with a new timeline, windows, budget, and revision.

        Raises:
            RuntimeError: If generation is already running or every attempt fails.
        """
        outfit_context, timeline = self._format_plan_context(plan)
        schedule_exists = plan.has_schedule
        pool = self._pool()
        theme = (
            plan.theme if schedule_exists else self._pick(pool.get("themes"), "日常日")
        )
        mood = plan.mood if schedule_exists else self._pick(pool.get("moods"), "平静")
        return await self._generate_plan(
            date.fromisoformat(plan.date),
            persona,
            mode="重写日程",
            include_schedule=True,
            include_outfit=False,
            theme=theme,
            mood=mood,
            outfit_style=plan.outfit.style if plan.outfit else "",
            base_plan=plan,
            long_term_context=long_term_context,
            relationship_context=relationship_context,
            outfit_context=outfit_context,
            timeline=timeline,
            requirements=extra,
            update_theme_mood=not schedule_exists,
        )

    async def rewrite_outfit(
        self,
        plan: DailyPlan,
        persona: PersonaContext,
        *,
        extra: str = "",
    ) -> DailyPlan:
        """Rewrite only the outfit while preserving all schedule-related fields.

        Args:
            plan: Existing valid daily plan.
            persona: Persona used to guide the rewritten outfit.
            extra: Optional administrator requirements for the outfit.

        Returns:
            A validated plan with a new outfit and revision.

        Raises:
            RuntimeError: If generation is already running or every attempt fails.
        """
        raw_styles = self._pool().get("outfit_styles")
        styles = (
            [str(value).strip() for value in raw_styles]
            if isinstance(raw_styles, list)
            else []
        )
        styles = [value for value in styles if value]
        explicitly_requested = next((style for style in styles if style in extra), None)
        current_style = plan.outfit.style if plan.outfit else ""
        alternatives = [style for style in styles if style != current_style]
        outfit_style = explicitly_requested or self._pick(
            alternatives,
            current_style or "日常休闲风",
        )
        outfit_context, timeline = self._format_plan_context(plan)
        return await self._generate_plan(
            date.fromisoformat(plan.date),
            persona,
            mode="重写穿搭",
            include_schedule=False,
            include_outfit=True,
            theme=plan.theme,
            mood=plan.mood,
            outfit_style=outfit_style,
            base_plan=plan,
            outfit_context=outfit_context,
            timeline=timeline,
            requirements=extra,
        )

    async def _generate_plan(
        self,
        target: date,
        persona: PersonaContext,
        *,
        mode: str,
        include_schedule: bool,
        include_outfit: bool,
        theme: str,
        mood: str,
        outfit_style: str,
        base_plan: DailyPlan | None = None,
        history: str = "",
        long_term_context: str = "",
        relationship_context: str = "",
        outfit_context: str = "",
        timeline: str = "",
        requirements: str = "",
        update_theme_mood: bool = False,
    ) -> DailyPlan:
        """Generate and validate a full plan or selected plan components.

        Args:
            target: Date being generated.
            persona: Persona used to guide generation.
            mode: Human-readable operation name exposed to prompt templates.
            include_schedule: Whether schedule prompt and fields are included.
            include_outfit: Whether outfit prompt and field are included.
            theme: Selected or preserved theme.
            mood: Selected or preserved mood.
            outfit_style: Selected or preserved outfit style.
            base_plan: Existing plan used for a partial rewrite.
            history: Formatted recent or current plan context.
            long_term_context: Formatted long-term stage context.
            relationship_context: Formatted Personal Network context.
            outfit_context: Formatted existing outfit context.
            timeline: Formatted existing timeline context.
            requirements: Optional administrator requirements.

        Returns:
            A validated complete or partially replaced plan.

        Raises:
            RuntimeError: If generation is concurrent, misconfigured, or invalid after retries.
        """
        key = f"{target.isoformat()}::{persona.id}"
        if key in self.generating:
            raise RuntimeError("plan generation already running")
        self.generating.add(key)
        try:
            settings = self._settings()
            prompt_settings = self._prompt_settings()
            friend_cap, group_cap = self._window_budget_caps()
            variables = {
                "mode": mode,
                "date": target.isoformat(),
                "weekday": "星期" + "一二三四五六日"[target.weekday()],
                "holiday": self._holiday(target),
                "persona": persona.prompt,
                "theme": theme or "无",
                "mood": mood or "无",
                "outfit_style": outfit_style,
                "history": history or "无",
                "long_term_context": long_term_context or "无",
                "outfit_context": outfit_context or "无",
                "timeline": timeline or "无",
                "current_outfit": outfit_context or "无",
                "requirements": requirements or "无",
            }
            components = []
            food_menu: dict | None = None
            trip: Trip | None = None
            trip_phase = "none"
            if include_schedule:
                components.append("schedule")
            if include_outfit:
                components.append("outfit")
            system_prompts = [
                str(
                    prompt_settings.get(f"{component}_generation_system_prompt", "")
                    or ""
                ).strip()
                for component in components
            ]
            prompt_template_keys = (
                ["complete_generation_prompt_template"]
                if include_schedule and include_outfit
                else [f"{components[0]}_prompt_template"]
            )
            prompt_templates = [
                str(prompt_settings.get(key, "") or "").strip()
                for key in prompt_template_keys
            ]
            if any(not value for value in system_prompts + prompt_templates):
                raise RuntimeError("schedule or outfit generation prompt is empty")
            system_prompt = "\n\n".join(system_prompts)
            base_prompt = "\n\n".join(
                template.format(**variables) for template in prompt_templates
            )
            if include_schedule:
                base_prompt += (
                    "\n\n【日程写作约束】timeline 的 activity 只写她自己的安排和感受，"
                    "不要替主人编造具体行为、点单、选择或说过的话；"
                    "如果需要和主人一起活动，写到安排层面即可，"
                    "例如「和主人一起吃寿司」，不要写「他选的那盘」「他说……」"
                    "这类没有输入依据的细节。"
                )
            if include_schedule and relationship_context:
                base_prompt += (
                    "\n\nUse the following stored relationship data only as factual context. "
                    "When a timeline item clearly involves a listed person, add that "
                    "person's exact id to the optional participant_ids array. Use an "
                    "empty array for solitary activities and never invent IDs.\n"
                    + relationship_context
                )
            if include_schedule and (friend_cap is not None or group_cap is not None):
                limits = []
                if friend_cap is not None:
                    limits.append(
                        f"面向好友（audience 为 private 或 both）的 proactive_windows "
                        f"数量不得超过 {friend_cap} 个"
                    )
                if group_cap is not None:
                    limits.append(
                        f"面向群聊（audience 为 group 或 both）的 proactive_windows "
                        f"数量不得超过 {group_cap} 个"
                    )
                base_prompt += (
                    "\n\n主动消息预算约束：proactive_windows 数量必须与每日主动消息预算一致。"
                    + "；".join(limits)
                    + "。audience 为 both 的窗口同时计入好友与群聊。"
                )

            if include_schedule:
                home_items_prompt = self._home_items_prompt()
                if home_items_prompt:
                    base_prompt += "\n\n" + home_items_prompt
                home_wish_prompt = self._home_wish_prompt(target, persona.id)
                if home_wish_prompt:
                    base_prompt += "\n\n" + home_wish_prompt
                outdoor_prompt = self._outdoor_options_prompt()
                if outdoor_prompt:
                    base_prompt += "\n\n" + outdoor_prompt
                rhythm_prompt = self._schedule_rhythm_prompt(target)
                if rhythm_prompt:
                    base_prompt += "\n\n" + rhythm_prompt
                transport_prompt = self._transport_prompt()
                if transport_prompt:
                    base_prompt += "\n\n" + transport_prompt
                life_state_prompt = self._life_state_prompt(target, persona.id)
                if life_state_prompt:
                    base_prompt += "\n\n" + life_state_prompt
                travel_prompt, trip, trip_phase = self._travel_prompt(target, persona)
                if travel_prompt:
                    base_prompt += "\n\n" + travel_prompt
                away = trip is not None and trip_phase in {
                    "depart",
                    "away",
                    "return",
                }
                food_prompt, food_menu = self._food_prompt(target, persona, away=away)
                if food_prompt:
                    base_prompt += "\n\n" + food_prompt

            attempts = max(1, int(settings.get("generation_retries", 2)) + 1)
            retry_template = str(
                prompt_settings.get("generation_retry_prompt_template", "") or ""
            ).strip()
            if attempts > 1 and not retry_template:
                raise RuntimeError("generation retry prompt template is empty")
            last_error = ""
            retry_feedback = ""
            for attempt in range(attempts):
                prompt = base_prompt + retry_feedback
                raw = ""
                try:
                    raw = await self._call_llm_with_system(
                        prompt,
                        f"daily_{'_'.join(components)}_{persona.id}_{target.isoformat()}",
                        system_prompt,
                    )
                    payload = extract_json_object(raw)
                    raw_timeline: list[dict] = []
                    raw_windows: list[dict] = []
                    bonus: dict = {}
                    if include_schedule:
                        for required in (
                            "timeline",
                            "proactive_windows",
                            "budget_bonus",
                        ):
                            if required not in payload:
                                raise ValueError(f"missing schedule field: {required}")
                        raw_timeline = payload["timeline"]
                        raw_windows = payload["proactive_windows"]
                        bonus = payload["budget_bonus"]
                        if not isinstance(raw_timeline, list) or not all(
                            isinstance(item, dict) for item in raw_timeline
                        ):
                            raise ValueError("timeline must be an array of objects")
                        if not isinstance(raw_windows, list) or not all(
                            isinstance(item, dict) for item in raw_windows
                        ):
                            raise ValueError(
                                "proactive_windows must be an array of objects"
                            )
                        raw_timeline = split_multistop_transit(raw_timeline)
                        friend_count = sum(
                            1
                            for item in raw_windows
                            if str(item.get("audience", "both")) in {"both", "private"}
                        )
                        group_count = sum(
                            1
                            for item in raw_windows
                            if str(item.get("audience", "both")) in {"both", "group"}
                        )
                        if friend_cap is not None and friend_count > friend_cap:
                            raise ValueError(
                                f"proactive_windows 面向好友数量 {friend_count} "
                                f"超过预算上限 {friend_cap}"
                            )
                        if group_cap is not None and group_count > group_cap:
                            raise ValueError(
                                f"proactive_windows 面向群聊数量 {group_count} "
                                f"超过预算上限 {group_cap}"
                            )
                        if not isinstance(bonus, dict):
                            raise ValueError("budget_bonus must be an object")
                    outfit: dict | None = None
                    parsed_outfit: Outfit | None = None
                    if include_outfit:
                        outfit = payload.get("outfit")
                        if (
                            not include_schedule
                            and not isinstance(outfit, dict)
                            and isinstance(payload.get("items"), list)
                        ):
                            outfit = payload
                        if not isinstance(outfit, dict):
                            raise ValueError("missing structured outfit")
                        outfit["style"] = outfit_style
                        parsed_outfit = Outfit.from_dict(outfit)
                        parsed_outfit.validate_complete()
                    revision = hashlib.sha1(
                        f"{base_plan.revision if base_plan else ''}\n{mode}\n{raw}".encode()
                    ).hexdigest()[:12]
                    parsed_timeline = tuple(
                        TimelineItem.from_dict(item) for item in raw_timeline
                    )
                    parsed_windows = tuple(
                        ProactiveWindow.from_dict(item) for item in raw_windows
                    )
                    if include_schedule:
                        previous_life = self._previous_life_needs(target, persona.id)
                        previous_needs = previous_life[1] if previous_life else {}
                        journal_state = self._health_journal_state(target, persona.id)
                        weather_today = weather_for_date(target)
                        weather_text = str(
                            getattr(weather_today, "prompt_text", None)
                            or weather_today
                            or ""
                        )
                        bad_weather = any(
                            word in weather_text
                            for word in (
                                "雨",
                                "雪",
                                "雷",
                                "大風",
                                "大风",
                                "寒",
                                "霜",
                                "冰",
                                "雾",
                            )
                        )
                        severe_weather = any(
                            word in weather_text
                            for word in ("暴", "台风", "大雪", "雷")
                        )
                        winter = target.month in (12, 1, 2)
                        try:
                            low_temp = int(
                                getattr(weather_today, "temperature_low", 99)
                            )
                        except (TypeError, ValueError):
                            low_temp = 99
                        extreme_cold = low_temp < 5
                        validate_timeline_realism(
                            parsed_timeline,
                            sleep_debt_minutes=int(
                                previous_needs.get("sleep_debt_minutes") or 0
                            ),
                            energy=int(
                                previous_needs.get("energy")
                                if previous_needs.get("energy") is not None
                                else 100
                            ),
                            willingness=int(
                                previous_needs.get("willingness")
                                if previous_needs.get("willingness") is not None
                                else 100
                            ),
                            health=int(
                                previous_needs.get("health")
                                if previous_needs.get("health") is not None
                                else 100
                            ),
                            sick=bool(previous_needs.get("sick")),
                            recovering=bool(previous_needs.get("recovering")),
                            illness_severity=str(
                                previous_needs.get("illness_severity") or ""
                            ),
                            weak_constitution=bool(
                                journal_state.get("weak_constitution")
                            ),
                            bad_weather=bad_weather,
                            severe_weather=severe_weather,
                            winter=winter,
                            extreme_cold=extreme_cold,
                            fever=bool(previous_needs.get("fever")),
                            hangover=self._previous_night_alcohol(target, persona.id),
                            hangover_severe=self._previous_night_alcohol_severity(
                                target, persona.id
                            ) == "severe",
                            fever_recovery=bool(
                                journal_state.get("fever_recovery")
                            ),
                            heat_illness=bool(
                                previous_needs.get("heat_illness")
                                or journal_state.get("heat_recovery")
                            ),
                        )
                    if base_plan is None:
                        plan = DailyPlan(
                            date=target.isoformat(),
                            persona_id=persona.id,
                            theme=theme if include_schedule else "",
                            mood=mood if include_schedule else "",
                            outfit=parsed_outfit if include_outfit else None,
                            timeline=parsed_timeline if include_schedule else (),
                            proactive_windows=(
                                parsed_windows if include_schedule else ()
                            ),
                            private_bonus=(
                                int(bonus.get("private", 0)) if include_schedule else 0
                            ),
                            group_bonus=(
                                int(bonus.get("group", 0)) if include_schedule else 0
                            ),
                            revision=revision,
                        )
                        plan = self._apply_travel(plan, trip, trip_phase)
                        self._apply_food_state(plan, persona, food_menu)
                        return plan

                    rewritten = base_plan
                    if include_schedule:
                        rewritten = replace(
                            rewritten,
                            theme=theme if update_theme_mood else rewritten.theme,
                            mood=mood if update_theme_mood else rewritten.mood,
                            timeline=parsed_timeline,
                            proactive_windows=parsed_windows,
                            private_bonus=int(bonus.get("private", 0)),
                            group_bonus=int(bonus.get("group", 0)),
                        )
                    if include_outfit:
                        rewritten = replace(rewritten, outfit=parsed_outfit)
                    plan = replace(rewritten, revision=revision)
                    plan = self._apply_travel(plan, trip, trip_phase)
                    self._apply_food_state(plan, persona, food_menu)
                    return plan
                except Exception as exc:
                    last_error = str(exc)
                    logger.warning(
                        "[Virtual Life] Plan generation validation failed mode=%s persona=%s attempt=%s: %s",
                        mode,
                        persona.id,
                        attempt + 1,
                        exc,
                    )
                    if raw and "JSON" in last_error:
                        logger.warning(
                            "[Virtual Life] Unparsable model output mode=%s persona=%s "
                            "attempt=%s chars=%s preview=%r",
                            mode,
                            persona.id,
                            attempt + 1,
                            len(raw),
                            self._preview_for_log(raw),
                        )
                    if attempt + 1 < attempts:
                        previous_output = raw or "（模型未返回可用文本）"
                        if len(previous_output) > 12000:
                            previous_output = (
                                previous_output[:6000]
                                + "\n...（中间内容已截断）...\n"
                                + previous_output[-6000:]
                            )
                        try:
                            retry_feedback = "\n\n" + retry_template.format(
                                mode=mode,
                                attempt=attempt + 2,
                                error=last_error,
                                previous_output=previous_output,
                            )
                        except (KeyError, IndexError, ValueError) as template_error:
                            raise RuntimeError(
                                f"invalid generation retry prompt variable: {template_error}"
                            ) from template_error
            raise RuntimeError(last_error or "plan generation failed")
        finally:
            self.generating.discard(key)

    @staticmethod
    def _format_plan_context(plan: DailyPlan) -> tuple[str, str]:
        """Format outfit and timeline context for configurable prompt templates.

        Args:
            plan: Plan whose preserved context should be described.

        Returns:
            Outfit context followed by timeline context.
        """
        outfit_context = ""
        if plan.outfit:
            outfit_items = "；".join(
                f"{item.category}={item.name}"
                + (f"（{item.details}）" if item.details else "")
                for item in plan.outfit.items
            )
            outfit_context = (
                f"{plan.outfit.style}｜{plan.outfit.summary}｜{outfit_items}"
            )
        timeline = "；".join(
            f"{item.start}-{item.end} {item.activity}"
            + (f" @ {item.location}" if item.location else "")
            for item in plan.timeline
        )
        return outfit_context, timeline

    @staticmethod
    def _format_history(plans: list[DailyPlan]) -> str:
        if not plans:
            return "无"
        blocks: list[str] = []
        older_plans = plans[:-1]
        if older_plans:
            blocks.append("较早日程摘要：")
        for plan in older_plans:
            activities = "、".join(
                dict.fromkeys(item.activity for item in plan.timeline)
            )
            outfit_style = plan.outfit.style if plan.outfit else "无"
            blocks.append(
                f"- {plan.date}｜主题：{plan.theme or '无'}｜"
                f"心情：{plan.mood or '无'}｜穿搭风格：{outfit_style}｜"
                f"主要活动：{activities or '无'}"
            )
        latest = plans[-1]
        _, latest_activities = DailyPlanGenerator._format_plan_context(latest)
        latest_style = latest.outfit.style if latest.outfit else "无"
        latest_outfit = latest.outfit.summary if latest.outfit else "无"
        blocks.extend(
            [
                "最近一天详情：",
                f"- {latest.date}｜主题：{latest.theme or '无'}｜"
                f"心情：{latest.mood or '无'}｜穿搭风格：{latest_style}｜"
                f"穿搭：{latest_outfit}｜"
                f"活动：{latest_activities}",
                "新日程可以延续尚未完成的兴趣或状态，但不要照抄相同主题、穿搭和活动组合。",
            ]
        )
        return "\n".join(blocks)

    async def generate_long_term_timeline(
        self,
        persona: PersonaContext,
        *,
        start_date: date,
        previous_stage: dict | None = None,
        requirements: str = "",
    ) -> list[dict]:
        previous_text = "无"
        if previous_stage:
            previous_text = (
                f"{previous_stage['name']}（{previous_stage['kind']}，"
                f"{previous_stage['start_date']} 至 {previous_stage['end_date']}）："
                f"{previous_stage.get('summary') or '无说明'}"
            )
        system_prompt = (
            "You are a strict long-term timeline planner. Return exactly one JSON object and no Markdown or explanation.\n"
            "The top-level object must contain a stages array with 1 to 3 stages. Never output null for required fields.\n"
            "Stage rules:\n"
            "- Every stage must contain id, name, kind, start_date, end_date, priority, summary, weekly_rules, "
            "special_dates, special_periods, milestones, and constraints.\n"
            "- id and name must be non-empty strings; ids must be unique. kind must be academic, project, or custom.\n"
            "- start_date and end_date must use YYYY-MM-DD. The first stage must start on the requested date; each later "
            "stage must start on the day after the previous stage ends. Stages must not overlap or leave gaps.\n"
            "- priority must be a JSON integer from 0 to 100. Never use text values such as high, medium, or low.\n"
            "- summary must be a string. constraints must be an array of strings; use [] when empty.\n"
            "Recurring event rules for weekly_rules:\n"
            "- Each item must contain weekdays, start, end, title, location, participants, and required.\n"
            "- weekdays must be a non-empty JSON array of unique integers from 1 to 7: 1=Monday, 2=Tuesday, "
            "3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday. Never use weekday names, strings, 0, null, or [].\n"
            "- start and end must be non-empty HH:MM strings and start must be earlier than end. title must be non-empty.\n"
            "- location must be a string, participants must be an array of strings, and required must be a JSON boolean.\n"
            "Special date rules for special_dates:\n"
            "- Each item uses the same event fields as weekly_rules except weekdays, plus date in YYYY-MM-DD.\n"
            "- date must fall within its stage. start and end must be non-empty HH:MM strings with start earlier than end.\n"
            "Special period rules for special_periods:\n"
            "- Each item must contain a non-empty name, start_date, end_date, and constraints array.\n"
            "- Both dates must fall within the stage and start_date must not be later than end_date.\n"
            "Milestone rules for milestones:\n"
            "- Each item must contain date, a non-empty title, and lead_days as a non-negative JSON integer.\n"
            "- The milestone date must fall within its stage.\n"
            "Use [] instead of placeholder objects when a list has no valid items. Before responding, self-check every field, "
            "type, enum, date range, weekday, time, and stage boundary against all rules above."
        )
        prompt = (
            f"起始日期：{start_date.isoformat()}\n"
            f"人格设定：\n{persona.prompt}\n\n"
            f"前一阶段：{previous_text}\n"
            f"管理员要求：{requirements or '无'}\n\n"
            "请根据人格自行判断适合的阶段类型和合理持续时间。学生角色可生成学期、假期、考试周等校历；"
            "上班族角色可生成项目周期、冲刺期、发布期等工期；其他角色使用 custom。"
        )
        raw = await self._call_llm_with_system(
            prompt,
            f"long_term_{persona.id}_{start_date.isoformat()}",
            system_prompt,
        )
        return validate_stage_bundle(
            extract_json_object(raw), persona.id, required_start=start_date
        )

    async def generate_new_character(
        self,
        persona: PersonaContext,
    ) -> dict:
        """Generate a new virtual character to appear in today's schedule.

        Args:
            persona: Persona context used to shape the character's background.

        Returns:
            A dict with keys: name, bio, personality, preferences, facts, relationship_type, relationship_description.
            relationship_type is a noun like "同学"/"朋友"/"同事", relationship_description is a short sentence.

        Raises:
            RuntimeError: If the LLM call fails or output is invalid.
        """
        system_prompt = (
            "你是一个虚构人物生成器。只返回一个可被 JSON.parse 直接解析的 JSON 对象，"
            "禁止 Markdown、代码块、解释或额外文字。\n"
            "对象必须包含以下字段：\n"
            "- name: 非空字符串，人物姓名\n"
            "- bio: 字符串，人物身份、职业、家庭背景和相识经历，100字以内\n"
            "- personality: 字符串，相对稳定的性格及行为方式，50字以内\n"
            "- preferences: 字符串，稳定喜好、忌讳和活动倾向，50字以内\n"
            "- facts: 字符串，生日、住址和重要人生事实等其他长期信息，50字以内\n"
            "- relationship_type: 非空字符串，与人格的关系类型（身份名词，如 同学、朋友、同事、邻居），不超过6字\n"
            "- relationship_description: 非空字符串，关系简述，不超过30字\n"
            "禁止输出 null、空对象或缺少任何字段的对象。"
        )
        prompt = (
            f"人格设定：\n{persona.prompt}\n\n"
            "请根据人格设定，生成一个与人格今天有可能在日程中相遇的全新虚构人物。"
            "人物应与人格的生活圈子相符，背景、性格和关系类型要自然合理。"
        )
        raw = await self._call_llm_with_system(
            prompt,
            f"new_character_{persona.id}",
            system_prompt,
        )
        payload = extract_json_object(raw)
        for required in ("name", "relationship_type", "relationship_description"):
            if (
                not isinstance(payload.get(required), str)
                or not payload[required].strip()
            ):
                raise RuntimeError(f"new character missing required field: {required}")
        return {
            "name": str(payload["name"]).strip(),
            "bio": str(payload.get("bio", "")).strip(),
            "personality": str(payload.get("personality", "")).strip(),
            "preferences": str(payload.get("preferences", "")).strip(),
            "facts": str(payload.get("facts", "")).strip(),
            "relationship_type": str(payload["relationship_type"]).strip(),
            "relationship_description": str(
                payload["relationship_description"]
            ).strip(),
        }

    @staticmethod
    def _preview_for_log(raw: str, limit: int = 240) -> str:
        """Return a bounded head/tail preview of an invalid completion."""
        text = str(raw).strip()
        if len(text) <= limit * 2 + 30:
            return text
        return f"{text[:limit]} … {text[-limit:]}"

    async def complete(self, prompt: str, system_prompt: str, session_id: str) -> str:
        """Run a one-off generation with the configured schedule provider.

        Used by the observation window's instant interactions, which need a
        short reply without touching the daily plan.
        """
        return await self._call_llm_with_system(prompt, session_id, system_prompt)

    async def _call_llm_with_system(
        self, prompt: str, session_id: str, system_prompt: str
    ) -> str:
        provider_id = str(self._settings().get("schedule_llm_provider") or "").strip()
        provider = self.context.get_provider_by_id(provider_id) if provider_id else None
        provider = provider or self.context.get_using_provider()
        if not provider:
            raise RuntimeError("no LLM provider available")
        response = await provider.text_chat(
            prompt=prompt, session_id=session_id, system_prompt=system_prompt
        )
        for key in ("completion_text", "completion", "text", "content"):
            value = getattr(response, key, None)
            if isinstance(value, str) and value.strip():
                return value.strip()
        raise RuntimeError("LLM returned empty completion")
