from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, replace
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


ORDINARY_DAY = "普通日期"
DEFAULT_STYLE = "日常休闲风"
NONE_TEXT = "无"
WEEKDAY_NAMES = "一二三四五六日"
AWAY_PHASES = {"depart", "away", "return"}
SCHEDULE_FIELDS = ("timeline", "proactive_windows", "budget_bonus")
WINDOW_AUDIENCES = (("好友", {"both", "private"}), ("群聊", {"both", "group"}))
RETRY_ECHO_LIMIT = 12000
BAD_WEATHER_WORDS = ("雨", "雪", "雷", "大風", "大风", "寒", "霜", "冰", "雾")
SEVERE_WEATHER_WORDS = ("暴", "台风", "大雪", "雷")

OWNER_DETAIL_RULE = (
    "【日程写作约束】timeline 的 activity 只写她自己的安排和感受，"
    "不要替主人编造具体行为、点单、选择或说过的话；"
    "如果需要和主人一起活动，写到安排层面即可，"
    "例如「和主人一起吃寿司」，不要写「他选的那盘」「他说……」"
    "这类没有输入依据的细节。"
)
PARTICIPANT_RULE = (
    "下面是她认识的人（来自人际关系数据），只当作事实参考。某个时间段明显是和其中某人一起度过时，"
    "把那人的 id 原样填进这一项的 participant_ids；一个人待着的时段填空数组。不要编造 id。\n"
)

LONG_TERM_SYSTEM_PROMPT = """你在为一个角色规划接下来几周到几个月的长期安排。只输出一个 JSON 对象，不要 Markdown，也不要任何解释。

顶层只有一个 stages 数组，放 1 到 3 个阶段。必填字段一律不能是 null。

每个阶段的字段：id、name、kind、start_date、end_date、priority、summary、weekly_rules、special_dates、special_periods、milestones、constraints。
- id、name 是非空字符串，各阶段 id 互不相同；kind 取 academic / project / custom 之一。
- start_date、end_date 写成 YYYY-MM-DD。第一个阶段从要求的日期开始，之后每个阶段都从前一个结束的第二天开始，不重叠、不留空档。
- priority 是 0 到 100 的 JSON 整数，不能写 high、medium、low 这类文字。
- summary 是字符串；constraints 是字符串数组，没有就写 []。

weekly_rules（每周重复的事）每项：weekdays、start、end、title、location、participants、required。
- weekdays 是不重复的 1 到 7 的整数组成的非空数组（1 是周一，7 是周日），不要写星期名称、字符串、0、null 或 []。
- start、end 是 HH:MM，都不能为空，start 早于 end；title 不能为空。
- location 是字符串，participants 是字符串数组，required 是 true 或 false。

special_dates（某一天的特别安排）每项：字段和 weekly_rules 相同但没有 weekdays，另加 YYYY-MM-DD 的 date；date 落在本阶段内，时间规则同上。

special_periods（阶段里的一段特殊时期）每项有非空 name、start_date、end_date 和 constraints 数组，两个日期都在本阶段内，且开始不晚于结束。

milestones（里程碑）每项：date、非空 title、lead_days（提前几天提醒，不小于 0 的 JSON 整数）；date 落在本阶段内。

列表里没有内容就写 []，不要放占位对象。输出前逐项检查字段、类型、取值、日期范围、星期、时间和阶段衔接是否都符合以上要求。"""

LONG_TERM_TASK = (
    "请按人格设定判断适合什么样的阶段、各持续多久：学生一般是学期、假期、考试周；"
    "上班族一般是项目周期、冲刺、上线；其他身份用 custom。"
)

CHARACTER_FIELDS = ("name", "bio", "personality", "preferences", "facts", "relationship_type", "relationship_description")
CHARACTER_REQUIRED = ("name", "relationship_type", "relationship_description")
NEW_CHARACTER_SYSTEM_PROMPT = """请虚构一个人物。只输出一个能被 JSON.parse 直接解析的 JSON 对象，不要 Markdown、代码块或说明文字。

字段：
- name：名字，不能为空
- bio：身份、职业、家庭情况，以及和她是怎么认识的（100 字以内）
- personality：比较稳定的性格和做事方式（50 字以内）
- preferences：长期的喜好、忌讳和爱做的事（50 字以内）
- facts：生日、住处等其他长期信息（50 字以内）
- relationship_type：和她是什么关系，用一个身份词，例如同学、朋友、同事、邻居（6 字以内，不能为空）
- relationship_description：一句话说明这段关系（30 字以内，不能为空）

每个字段都要有，不要写 null 或空对象。"""

NEW_CHARACTER_TASK = "按上面的人格设定，编一个她今天可能在日常里碰到的新人物：要和她的生活圈子对得上，背景、性格和关系都要说得通。"

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
        options = [str(value) for value in values] if isinstance(values, list) else []
        return random.choice(options) if options else fallback

    def _holiday(self, target: date) -> str:
        try:
            return str(holidays.country_holidays("CN").get(target, ORDINARY_DAY))
        except Exception:
            logger.debug("[虚拟人生] 节假日查询失败，按普通日期处理", exc_info=True)
            return ORDINARY_DAY

    def _window_budget_caps(self) -> tuple[int | None, int | None]:
        """Most proactive windows a day may hold for (friends, groups); ``None`` when that side is off.

        Mirrors the daily budget ceiling: ``daily_budget_max`` clipped by ``daily_hard_max``.
        """

        def ceiling(section: str) -> int | None:
            settings = self.config.get(section, {}) or {}
            if not settings.get("enable", False):
                return None
            low = max(0, int(settings.get("daily_budget_min", 0)))
            high = max(low, int(settings.get("daily_budget_max", low)))
            return min(high, max(0, int(settings.get("daily_hard_max", high))))

        return ceiling("friend_settings"), ceiling("group_settings")

    # ------------------------------------------------------------------ public entry points

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
        """Plan ``target`` (schedule and/or outfit); a ``status="failed"`` placeholder when every attempt fails."""
        if not (include_schedule or include_outfit):
            return base_plan or DailyPlan(
                date=target.isoformat(),
                persona_id=persona.id,
                theme="",
                mood="",
                outfit=None,
                timeline=(),
                revision=_short_hash(f"{target.isoformat()}::{persona.id}::empty"),
            )
        pool = self._pool()
        kept = base_plan
        theme = self._pick(pool.get("themes"), "日常日") if include_schedule else (kept.theme if kept else "")
        mood = self._pick(pool.get("moods"), "平静") if include_schedule else (kept.mood if kept else "")
        if include_outfit:
            style = self._pick(pool.get("outfit_styles"), DEFAULT_STYLE)
        else:
            style = kept.outfit.style if kept and kept.outfit else ""
        mode = {(True, True): "完整生成", (True, False): "生成日程", (False, True): "生成穿搭"}[(include_schedule, include_outfit)]
        outfit_context, timeline = self._format_plan_context(kept) if kept else ("", "")
        try:
            return await self._generate_plan(
                target,
                persona,
                mode=mode,
                include_schedule=include_schedule,
                include_outfit=include_outfit,
                theme=theme,
                mood=mood,
                outfit_style=style,
                base_plan=kept,
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
                revision=_short_hash(str(exc)),
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
        """New timeline / windows / budget for an existing plan; the outfit stays.

        Theme and mood are kept unless the plan had no schedule yet. Raises ``RuntimeError`` on failure.
        """
        had_schedule = plan.has_schedule
        pool = self._pool()
        outfit_context, timeline = self._format_plan_context(plan)
        return await self._generate_plan(
            date.fromisoformat(plan.date),
            persona,
            mode="重写日程",
            include_schedule=True,
            include_outfit=False,
            theme=plan.theme if had_schedule else self._pick(pool.get("themes"), "日常日"),
            mood=plan.mood if had_schedule else self._pick(pool.get("moods"), "平静"),
            outfit_style=plan.outfit.style if plan.outfit else "",
            base_plan=plan,
            long_term_context=long_term_context,
            relationship_context=relationship_context,
            outfit_context=outfit_context,
            timeline=timeline,
            requirements=extra,
            update_theme_mood=not had_schedule,
        )

    async def rewrite_outfit(self, plan: DailyPlan, persona: PersonaContext, *, extra: str = "") -> DailyPlan:
        """New outfit for an existing plan; the schedule stays. Raises ``RuntimeError`` on failure.

        A style named in ``extra`` wins; otherwise a different style from the pool is picked.
        """
        raw_styles = self._pool().get("outfit_styles")
        styles = [text for text in (str(value).strip() for value in raw_styles) if text] if isinstance(raw_styles, list) else []
        current = plan.outfit.style if plan.outfit else ""
        asked_for = next((style for style in styles if style in extra), None)
        style = asked_for or self._pick([style for style in styles if style != current], current or DEFAULT_STYLE)
        outfit_context, timeline = self._format_plan_context(plan)
        return await self._generate_plan(
            date.fromisoformat(plan.date),
            persona,
            mode="重写穿搭",
            include_schedule=False,
            include_outfit=True,
            theme=plan.theme,
            mood=plan.mood,
            outfit_style=style,
            base_plan=plan,
            outfit_context=outfit_context,
            timeline=timeline,
            requirements=extra,
        )

    # ------------------------------------------------------------------ the generation loop

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
        """Prompt → LLM → validate, retrying with the error fed back. Raises ``RuntimeError`` when it gives up."""
        job_key = f"{target.isoformat()}::{persona.id}"
        if job_key in self.generating:
            raise RuntimeError("this day is already being generated")
        self.generating.add(job_key)
        try:
            job = _Job(
                target=target,
                persona=persona,
                mode=mode,
                schedule=include_schedule,
                outfit=include_outfit,
                theme=theme,
                mood=mood,
                style=outfit_style,
                base=base_plan,
                update_theme_mood=update_theme_mood,
                caps=self._window_budget_caps(),
            )
            components = [name for name, wanted in (("schedule", job.schedule), ("outfit", job.outfit)) if wanted]
            prompts = self._prompt_settings()

            def setting(key: str) -> str:
                return str(prompts.get(key, "") or "").strip()

            systems = [setting(f"{name}_generation_system_prompt") for name in components]
            template = setting("complete_generation_prompt_template" if len(components) == 2 else f"{components[0]}_prompt_template")
            if not template or not all(systems):
                raise RuntimeError("a generation prompt in the settings is empty")
            prompt = template.format(
                mode=mode,
                date=target.isoformat(),
                weekday="星期" + WEEKDAY_NAMES[target.weekday()],
                holiday=self._holiday(target),
                persona=persona.prompt,
                theme=theme or NONE_TEXT,
                mood=mood or NONE_TEXT,
                outfit_style=outfit_style,
                history=history or NONE_TEXT,
                long_term_context=long_term_context or NONE_TEXT,
                outfit_context=outfit_context or NONE_TEXT,
                timeline=timeline or NONE_TEXT,
                current_outfit=outfit_context or NONE_TEXT,
                requirements=requirements or NONE_TEXT,
            )
            if job.schedule:
                prompt += self._schedule_prompt_extras(job, relationship_context)

            attempts = max(1, int(self._settings().get("generation_retries", 2)) + 1)
            retry_template = setting("generation_retry_prompt_template")
            if attempts > 1 and not retry_template:
                raise RuntimeError("the retry prompt in the settings is empty")
            session = f"daily_{'_'.join(components)}_{persona.id}_{target.isoformat()}"
            feedback = error = ""
            for attempt in range(1, attempts + 1):
                raw = ""
                try:
                    raw = await self._call_llm_with_system(prompt + feedback, session, "\n\n".join(systems))
                    return self._accept(job, raw)
                except Exception as exc:
                    error = str(exc)
                    logger.warning("[虚拟人生] 日程生成第 %s 次校验未通过 mode=%s persona=%s: %s", attempt, mode, persona.id, exc)
                    if raw and "JSON" in error:
                        logger.warning(
                            "[虚拟人生] 模型输出无法解析 mode=%s persona=%s attempt=%s 长度=%s 预览=%r",
                            mode,
                            persona.id,
                            attempt,
                            len(raw),
                            self._preview_for_log(raw),
                        )
                    if attempt < attempts:
                        feedback = _retry_feedback(retry_template, mode, attempt + 1, error, raw)
            raise RuntimeError(error or "could not generate a valid plan")
        finally:
            self.generating.discard(job_key)

    def _schedule_prompt_extras(self, job: _Job, relationship_context: str) -> str:
        """Everything appended to a schedule prompt: rules, budget caps and the life-sim context blocks.

        Also decides the day's trip and menu, which ``_accept`` applies to the finished plan.
        """
        target, persona = job.target, job.persona
        blocks = [OWNER_DETAIL_RULE]
        if relationship_context:
            blocks.append(PARTICIPANT_RULE + relationship_context)
        friend_cap, group_cap = job.caps
        limits = [
            f"给{who}的窗口（audience 为 {kinds}）最多 {cap} 个"
            for who, kinds, cap in (("好友", "private 或 both", friend_cap), ("群聊", "group 或 both", group_cap))
            if cap is not None
        ]
        if limits:
            blocks.append(
                "主动消息额度：proactive_windows 的数量要符合每天的额度——"
                + "；".join(limits)
                + "。audience 为 both 的窗口两边都要算上。"
            )
        blocks += [
            self._home_items_prompt(),
            self._home_wish_prompt(target, persona.id),
            self._outdoor_options_prompt(),
            self._schedule_rhythm_prompt(target),
            self._transport_prompt(),
            self._life_state_prompt(target, persona.id),
        ]
        travel_text, job.trip, job.trip_phase = self._travel_prompt(target, persona)
        blocks.append(travel_text)
        travelling = job.trip is not None and job.trip_phase in AWAY_PHASES
        food_text, job.menu = self._food_prompt(target, persona, away=travelling)
        blocks.append(food_text)
        return "".join("\n\n" + block for block in blocks if block)

    def _accept(self, job: _Job, raw: str) -> DailyPlan:
        """Validate one model answer and build the plan from it; any problem raises."""
        payload = extract_json_object(raw)
        timeline, windows, bonus = _read_schedule(payload, job.caps) if job.schedule else ([], [], {})
        outfit = _read_outfit(payload, job.style, alone=not job.schedule) if job.outfit else None
        revision = _short_hash(f"{job.base.revision if job.base else ''}\n{job.mode}\n{raw}")
        items = tuple(TimelineItem.from_dict(item) for item in timeline)
        planned_windows = tuple(ProactiveWindow.from_dict(item) for item in windows)
        if job.schedule:
            self._check_realism(job.target, job.persona.id, items)

        if job.base is None:
            plan = DailyPlan(
                date=job.target.isoformat(),
                persona_id=job.persona.id,
                theme=job.theme if job.schedule else "",
                mood=job.mood if job.schedule else "",
                outfit=outfit,
                timeline=items,
                proactive_windows=planned_windows,
                private_bonus=int(bonus.get("private", 0)) if job.schedule else 0,
                group_bonus=int(bonus.get("group", 0)) if job.schedule else 0,
                revision=revision,
            )
        else:
            plan = job.base
            if job.schedule:
                plan = replace(
                    plan,
                    theme=job.theme if job.update_theme_mood else plan.theme,
                    mood=job.mood if job.update_theme_mood else plan.mood,
                    timeline=items,
                    proactive_windows=planned_windows,
                    private_bonus=int(bonus.get("private", 0)),
                    group_bonus=int(bonus.get("group", 0)),
                )
            if job.outfit:
                plan = replace(plan, outfit=outfit)
            plan = replace(plan, revision=revision)
        plan = self._apply_travel(plan, job.trip, job.trip_phase)
        self._apply_food_state(plan, job.persona, job.menu)
        return plan

    def _check_realism(self, target: date, persona_id: str, items: tuple[TimelineItem, ...]) -> None:
        """Reject timelines that ignore yesterday's body state, illness or today's weather."""
        before = self._previous_life_needs(target, persona_id)
        needs = before[1] if before else {}
        journal = self._health_journal_state(target, persona_id)
        weather = weather_for_date(target)
        weather_text = str(getattr(weather, "prompt_text", None) or weather or "")
        try:
            coldest = int(getattr(weather, "temperature_low", 99))
        except (TypeError, ValueError):
            coldest = 99

        def level(key: str) -> int:
            value = needs.get(key)
            return int(value if value is not None else 100)

        validate_timeline_realism(
            items,
            sleep_debt_minutes=int(needs.get("sleep_debt_minutes") or 0),
            energy=level("energy"),
            willingness=level("willingness"),
            health=level("health"),
            sick=bool(needs.get("sick")),
            recovering=bool(needs.get("recovering")),
            illness_severity=str(needs.get("illness_severity") or ""),
            weak_constitution=bool(journal.get("weak_constitution")),
            bad_weather=any(word in weather_text for word in BAD_WEATHER_WORDS),
            severe_weather=any(word in weather_text for word in SEVERE_WEATHER_WORDS),
            winter=target.month in (12, 1, 2),
            extreme_cold=coldest < 5,
            fever=bool(needs.get("fever")),
            hangover=self._previous_night_alcohol(target, persona_id),
            hangover_severe=self._previous_night_alcohol_severity(target, persona_id) == "severe",
            fever_recovery=bool(journal.get("fever_recovery")),
            heat_illness=bool(needs.get("heat_illness") or journal.get("heat_recovery")),
        )

    # ------------------------------------------------------------------ context text

    @staticmethod
    def _format_plan_context(plan: DailyPlan) -> tuple[str, str]:
        """``(outfit, timeline)`` one-line summaries used by the prompt templates."""
        outfit = ""
        if plan.outfit:
            pieces = "；".join(
                f"{piece.category}={piece.name}" + (f"（{piece.details}）" if piece.details else "") for piece in plan.outfit.items
            )
            outfit = f"{plan.outfit.style}｜{plan.outfit.summary}｜{pieces}"
        slots = "；".join(
            f"{item.start}-{item.end} {item.activity}" + (f" @ {item.location}" if item.location else "") for item in plan.timeline
        )
        return outfit, slots

    @staticmethod
    def _format_history(plans: list[DailyPlan]) -> str:
        """Recent days for the prompt: older ones as one-liners, the last one in detail."""
        if not plans:
            return NONE_TEXT
        *older, latest = plans
        lines = ["较早日程摘要："] if older else []
        for plan in older:
            activities = "、".join(dict.fromkeys(item.activity for item in plan.timeline)) or NONE_TEXT
            lines.append(
                f"- {plan.date}｜主题：{plan.theme or NONE_TEXT}｜心情：{plan.mood or NONE_TEXT}｜"
                f"穿搭风格：{plan.outfit.style if plan.outfit else NONE_TEXT}｜主要活动：{activities}"
            )
        outfit = latest.outfit
        lines += [
            "最近一天详情：",
            f"- {latest.date}｜主题：{latest.theme or NONE_TEXT}｜心情：{latest.mood or NONE_TEXT}｜"
            f"穿搭风格：{outfit.style if outfit else NONE_TEXT}｜穿搭：{outfit.summary if outfit else NONE_TEXT}｜"
            f"活动：{DailyPlanGenerator._format_plan_context(latest)[1]}",
            "可以接着做之前没做完的事、延续之前的状态，但别把同样的主题、穿搭和活动组合再来一遍。",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------ other generations

    async def generate_long_term_timeline(
        self,
        persona: PersonaContext,
        *,
        start_date: date,
        previous_stage: dict | None = None,
        requirements: str = "",
    ) -> list[dict]:
        """1–3 consecutive long-term stages starting on ``start_date`` (validated)."""
        previous = (
            f"{previous_stage['name']}（{previous_stage['kind']}，{previous_stage['start_date']} 至 "
            f"{previous_stage['end_date']}）：{previous_stage.get('summary') or '无说明'}"
            if previous_stage
            else NONE_TEXT
        )
        prompt = (
            f"起始日期：{start_date.isoformat()}\n人格设定：\n{persona.prompt}\n\n"
            f"前一阶段：{previous}\n管理员要求：{requirements or NONE_TEXT}\n\n{LONG_TERM_TASK}"
        )
        raw = await self._call_llm_with_system(
            prompt, f"long_term_{persona.id}_{start_date.isoformat()}", LONG_TERM_SYSTEM_PROMPT
        )
        return validate_stage_bundle(extract_json_object(raw), persona.id, required_start=start_date)

    async def generate_new_character(self, persona: PersonaContext) -> dict:
        """A new acquaintance she might meet today (name, bio, personality, … relationship_*).

        Raises ``RuntimeError`` when a required field is missing.
        """
        raw = await self._call_llm_with_system(
            f"人格设定：\n{persona.prompt}\n\n{NEW_CHARACTER_TASK}", f"new_character_{persona.id}", NEW_CHARACTER_SYSTEM_PROMPT
        )
        payload = extract_json_object(raw)
        for field in CHARACTER_REQUIRED:
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                raise RuntimeError(f"the new character lacks {field}")
        return {field: str(payload.get(field, "")).strip() for field in CHARACTER_FIELDS}

    # ------------------------------------------------------------------ LLM access

    @staticmethod
    def _preview_for_log(raw: str, limit: int = 240) -> str:
        """Head and tail of an unusable completion, for the log."""
        text = str(raw).strip()
        return text if len(text) <= limit * 2 + 30 else f"{text[:limit]} … {text[-limit:]}"

    async def complete(self, prompt: str, system_prompt: str, session_id: str) -> str:
        """One-off completion with the schedule provider (used by the panel's quick interactions)."""
        return await self._call_llm_with_system(prompt, session_id, system_prompt)

    async def _call_llm_with_system(self, prompt: str, session_id: str, system_prompt: str) -> str:
        provider_id = str(self._settings().get("schedule_llm_provider") or "").strip()
        provider = (self.context.get_provider_by_id(provider_id) if provider_id else None) or self.context.get_using_provider()
        if not provider:
            raise RuntimeError("no chat model is configured")
        response = await provider.text_chat(prompt=prompt, session_id=session_id, system_prompt=system_prompt)
        for name in ("completion_text", "completion", "text", "content"):
            text = getattr(response, name, None)
            if isinstance(text, str) and text.strip():
                return text.strip()
        raise RuntimeError("the model returned nothing")


# ---------------------------------------------------------------------------- generation helpers


@dataclass
class _Job:
    """One plan generation: what to produce and the context decided along the way."""

    target: date
    persona: PersonaContext
    mode: str
    schedule: bool
    outfit: bool
    theme: str
    mood: str
    style: str
    base: DailyPlan | None
    update_theme_mood: bool
    caps: tuple[int | None, int | None]
    trip: Trip | None = None
    trip_phase: str = "none"
    menu: dict | None = None


def _short_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _object_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, dict) for item in value)


def _read_schedule(payload: dict, caps: tuple[int | None, int | None]) -> tuple[list[dict], list[dict], dict]:
    """``(timeline, windows, budget_bonus)`` from a schedule answer, enforcing the window budget."""
    for field in SCHEDULE_FIELDS:
        if field not in payload:
            raise ValueError(f"the schedule part lacks {field}")
    timeline, windows, bonus = (payload[field] for field in SCHEDULE_FIELDS)
    if not _object_list(timeline):
        raise ValueError("timeline has to be a list of objects")
    if not _object_list(windows):
        raise ValueError("proactive_windows has to be a list of objects")
    timeline = split_multistop_transit(timeline)
    for (who, audiences), cap in zip(WINDOW_AUDIENCES, caps):
        count = sum(1 for window in windows if str(window.get("audience", "both")) in audiences)
        if cap is not None and count > cap:
            raise ValueError(f"给{who}的主动窗口有 {count} 个，超过了额度 {cap}")
    if not isinstance(bonus, dict):
        raise ValueError("budget_bonus has to be an object")
    return timeline, windows, bonus


def _read_outfit(payload: dict, style: str, *, alone: bool) -> Outfit:
    """The outfit from an answer; an outfit-only answer may be the outfit object itself."""
    outfit = payload.get("outfit")
    if alone and not isinstance(outfit, dict) and isinstance(payload.get("items"), list):
        outfit = payload
    if not isinstance(outfit, dict):
        raise ValueError("no outfit object found (expected {\"outfit\": {...}})")
    outfit["style"] = style
    parsed = Outfit.from_dict(outfit)
    parsed.validate_complete()
    return parsed


def _retry_feedback(template: str, mode: str, attempt: int, error: str, raw: str) -> str:
    """The retry note showing the model its previous answer (middle cut when very long)."""
    previous = raw or "（上次没有返回任何内容）"
    if len(previous) > RETRY_ECHO_LIMIT:
        half = RETRY_ECHO_LIMIT // 2
        previous = previous[:half] + "\n……（中间太长，略去）……\n" + previous[-half:]
    try:
        return "\n\n" + template.format(mode=mode, attempt=attempt, error=error, previous_output=previous)
    except (KeyError, IndexError, ValueError) as exc:
        raise RuntimeError(f"the retry prompt uses an unknown variable: {exc}") from exc
