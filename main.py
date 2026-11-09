from __future__ import annotations

import asyncio
import hashlib
import json
import random
import re
import shutil
import sys
from pathlib import Path
import uuid
from datetime import date, datetime, time, timedelta
from dataclasses import replace
from typing import Any
from zoneinfo import ZoneInfo

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.message_components import Image, Plain, Record, Reply
from astrbot.api.star import Context, Star, StarTools
from astrbot.core.agent.message import TextPart
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.provider.entities import LLMResponse, ProviderRequest
from astrbot.core.star.filter.command import CommandFilter, GreedyStr
from astrbot.core.star.filter.command_group import CommandGroupFilter
from astrbot.core.star.filter.regex import RegexFilter
from astrbot.core.utils.session_lock import session_lock_manager

from .core.context_injection import SmartContextInjector, build_state_snapshot
from .core.human_style import (
    CURRENT_STATE_RULE,
    DIALOGUE_FLOW_RULE,
    FUTURE_OUTFIT_RULE,
    HUMAN_CHAT_RULE,
    IMAGE_FACT_RULE,
    REMOTE_CHAT_RULE,
    SELFIE_CHAT_RULE,
)
from .core import chat_schedule as chat_schedule_events
from .core import character_assets
from .core import timeline_rules, wardrobe
from .core import (
    affection,
    books,
    camera_events,
    camera_photo,
    delivery,
    diary,
    furniture_state,
    garage,
    goods,
    health_journal,
    item_effects,
    life_state,
    money,
    mood_history,
    view_state,
    weekly,
    world_events,
)
from .core.generator import DailyPlanGenerator
from .core.image_renderer import ScheduleImageRenderer
from .core.interaction import InteractionService
from .core.long_term import LongTermTimelineStore, validate_stage_bundle
from .core.message_generator import ProactiveMessageGenerator
from .core.message_segmenter import ProactiveMessageSegmenter
from .core.models import (
    DailyPlan,
    ProactiveWindow,
    ScheduleRequirement,
)
from .core.persona import PersonaContext, PersonaResolver
from .core.proactive import ProactivePolicy, session_kind
from .core.reply_delay import (
    QueuedMessage,
    ReplyDelayCoordinator,
    ReplyDelayPolicy,
    format_delay_context,
    format_queued_messages,
)
from .core.runtime import SchedulerRuntime
from .core.schedule_edit import insert_activity, insert_garage_trip
from .core.storage import PluginStorage
from .core.user_state import UserStateStore
from .core.utils import (
    deterministic_int,
    deterministic_probability,
    format_outfit,
    format_plan,
    format_timeline,
    next_available_at,
    now_in,
    parse_datetime,
    parse_schedule_date_range,
    prune_date_keys,
    timeline_item_at,
)
from .core.view_api import VirtualLifeViewAPI
from .core.window_schedule import proactive_window_offset_minutes



GROUP_PRIVACY_TERMS = (
    "日程",
    "今日计划",
    "今天计划",
    "穿搭",
    "家具",
    "客厅",
    "卧室",
    "厨房",
    "阳台",
    "书房",
    "浴室",
    "健身房",
    "公司",
    "单位",
    "上班",
    "下班",
    "出门",
    "回家",
    "在家",
    "家里",
    "家中",
    "宅家",
)

GROUP_OUTPUT_TERMS = (
    "日程",
    "今日计划",
    "今天计划",
    "穿搭",
    "家具",
    "客厅",
    "卧室",
    "厨房",
    "阳台",
    "书房",
    "浴室",
    "健身房",
    "在家",
    "家里",
    "家中",
    "公司",
    "单位",
    "上班",
    "下班",
    "出门",
    "回家",
)

GIVE_INTENT_PATTERNS = (
    re.compile(
        r"(?:我要|我|想|准备)?(?:拿|送|递|带)"
        r"(?P<item>[^，。,.!?！？\s]{0,12}?)给(?:他|她|月月|你)"
    ),
    re.compile(
        r"给(?:他|她|月月|你)(?:拿|送|递|带)"
        r"(?P<item>[^，。,.!?！？\s]{0,12})"
    ),
)

# 月月主动请求主人递东西：「顺手递我一下」「帮我拿条浴巾」。
GIVE_REQUEST_PATTERNS = (
    re.compile(
        r"(?:顺手|帮我|帮忙|劳驾|麻烦)?(?:把|将)?"
        r"(?:递给|拿给|送给|带给|递|拿|送|带)(?:给)?我"
        r"(?:一下|下|过来|来|嘛|吧)?"
    ),
    re.compile(
        r"(?:帮我|帮忙|给我|替我)"
        r"(?:递给|拿给|送给|带给|递|拿|送|带)"
        r"(?:一下|下|点|个|条|件|杯|瓶|盒|袋|份|张|本|双|支)?"
        r"(?P<item>[^，。,.!?！？\s]{1,12})"
    ),
)

GIVE_REQUEST_NEGATED_RE = re.compile(
    r"(?:不用|别|不必|不需要|不是|没让你)[^，。,.!?！？]{0,6}"
    r"(?:递给|拿给|送给|带给|递|拿|送|带)(?:给)?我"
)

GIFT_ITEM_PREFIX_RE = re.compile(
    r"^(?:一下|下|点|个|条|件|杯|瓶|盒|袋|份|碗|盘|罐|串|块|颗|张|本|双|支)+"
)


def _clean_gift_item(value: str) -> str:
    item = str(value or "").strip().lstrip("了着过点个些把将请")
    item = GIFT_ITEM_PREFIX_RE.sub("", item)
    item = item.strip("，。,.!?！？、 ")
    item = item.rstrip("吧啊呀哦嘛呢啦呗")
    return item


def _requested_gift_label(
    text: str,
    known_items: list[str] | None = None,
) -> str | None:
    """识别月月请求递东西的回复，返回观察窗按钮文案。"""
    raw = str(text or "").strip()
    if not raw or GIVE_REQUEST_NEGATED_RE.search(raw):
        return None
    match = None
    for pattern in GIVE_REQUEST_PATTERNS:
        match = pattern.search(raw)
        if match:
            break
    if not match:
        return None

    for name in sorted(
        {str(item).strip() for item in (known_items or []) if str(item).strip()},
        key=len,
        reverse=True,
    ):
        if name in raw:
            return f"把{name}递给月月"

    item = _clean_gift_item(str(match.groupdict().get("item") or ""))
    if item:
        return f"把{item}递给月月"

    prefix = raw[: match.start()]
    for segment in reversed(re.split(r"[，,。.!?！？；;\s]+", prefix)):
        segment = _clean_gift_item(segment)
        segment = re.split(r"(?:在|放|就|正|刚|已经)", segment)[0].strip()
        segment = _clean_gift_item(segment)
        if segment and segment not in ("我", "你", "他", "她", "月月", "这边", "那边"):
            return f"把{segment}递给月月"

    after = _clean_gift_item(raw[match.end() :])
    if after:
        return f"把{after[:12]}递给月月"
    return "把东西递给月月"

GROUP_PRIVACY_RULE = (
    "【群聊隐私硬性规则】当前是群聊。禁止提及、暗示或解释自己的虚拟日程、"
    "今日计划、具体地点、房间、穿搭、家具和位置变化；也不要提自己正在上班、"
    "下班、出门或回家。只允许自然流露当前生理与心情。不要解释这条规则。"
)


def _group_message_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


_GROUP_PLAN_STOPWORDS = {
    "一个", "一些", "一下", "一起", "一点", "没有", "已经", "现在", "今天",
    "明天", "昨天", "早上", "上午", "中午", "下午", "晚上", "时候", "什么",
    "怎么", "这个", "那个", "这些", "那些", "自己", "我们", "你们", "他们",
    "她们", "别人", "东西", "事情", "地方", "这边", "那边", "这里", "那里",
    "出来", "起来", "下来", "过来", "回来", "上去", "下去", "进去", "出去",
    "开始", "准备", "然后", "因为", "所以", "但是", "而且", "如果", "虽然",
    "可以", "需要", "觉得", "知道", "看到", "听到", "感觉", "有点", "比较",
    "非常", "特别", "一直", "还是", "就是", "不是", "真的", "其实", "应该",
    "可能", "大概", "简单", "慢慢", "轻轻", "顺手", "随手", "收拾", "整理",
    "活动", "安排", "计划", "工作", "生活", "休息", "睡觉", "起床", "吃饭",
    "喝水", "洗澡", "刷牙", "洗脸", "穿衣", "换衣", "出门", "回家", "在家",
    "路上", "房间", "时间", "天气", "心情", "身体", "状态", "样子", "声音",
    "味道", "颜色", "衣服", "鞋子", "袜子", "裤子", "裙子", "外套", "帽子",
    "头发", "眼睛", "嘴巴", "手指", "肩膀", "脖子", "肚子", "肠胃", "精神",
    "力气", "习惯", "节奏", "氛围",
}


def _group_plan_terms(plan) -> set[str]:
    """从当日计划提取群聊需要屏蔽的具体事项词。"""
    from collections import Counter

    texts: list[str] = []
    for item in getattr(plan, "timeline", None) or []:
        texts.append(str(getattr(item, "activity", "") or ""))
        texts.append(str(getattr(item, "location", "") or ""))
    outfit = getattr(plan, "outfit", None)
    if outfit is not None:
        outfit_texts = [
            str(getattr(outfit, "summary", "") or ""),
            str(getattr(outfit, "style", "") or ""),
        ]
        for outfit_item in getattr(outfit, "items", None) or []:
            outfit_texts.append(str(getattr(outfit_item, "name", "") or ""))
            outfit_texts.append(str(getattr(outfit_item, "details", "") or ""))
        for text in outfit_texts:
            if text.strip():
                texts.extend([text, text])
    counts: Counter[str] = Counter()
    for text in texts:
        for run in re.findall(r"[\u4e00-\u9fff]+", text):
            for size in (2, 3, 4):
                for index in range(0, max(0, len(run) - size + 1)):
                    token = run[index : index + size]
                    if token in _GROUP_PLAN_STOPWORDS:
                        continue
                    counts[token] += 1
    return {token for token, count in counts.items() if count >= 2}



def _plugin_version() -> str:
    try:
        text = Path(__file__).with_name("metadata.yaml").read_text(encoding="utf-8")
        match = re.search(r"(?m)^version:\s*(\S+)", text)
        return match.group(1).strip() if match else "未知"
    except Exception:
        return "未知"


PLUGIN_ID = "astrbot_plugin_simlife_world"
LEGACY_PLUGIN_ID = "astrbot_plugin_virtual_life"


def _migrate_legacy_data(data_dir: Path) -> None:
    """Copy data from the pre-rename plugin id when the new data dir is empty."""
    try:
        legacy_dir = StarTools.get_data_dir(LEGACY_PLUGIN_ID)
        if legacy_dir == data_dir or not legacy_dir.is_dir():
            return
        if any(data_dir.iterdir()):
            return
        shutil.copytree(legacy_dir, data_dir, dirs_exist_ok=True)
        logger.info(
            "[虚拟人生] 已从旧插件标识迁移数据目录 %s -> %s",
            legacy_dir,
            data_dir,
        )
    except Exception as exc:
        logger.warning("[虚拟人生] 旧插件数据迁移失败: %s", exc)


def _frontend_ui_version() -> str:
    try:
        text = Path(__file__).with_name("views").joinpath(
            "life", "index.html"
        ).read_text(encoding="utf-8")
        match = re.search(r"app\.js\?v=([^\"'&<>]+)", text)
        return match.group(1).strip() if match else "未知"
    except Exception:
        return "未知"


class ProactiveVirtualDailyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.context = context
        self.config = config
        self.data_dir = StarTools.get_data_dir("astrbot_plugin_simlife_world")
        _migrate_legacy_data(self.data_dir)
        self.storage = PluginStorage(self.data_dir)
        self.personas = PersonaResolver(context)
        self.plan_generator = DailyPlanGenerator(context, config, self.data_dir)
        self.travel = self.plan_generator.travel
        self.interactions = InteractionService(self.data_dir)
        self.user_states = UserStateStore(self.data_dir)
        self._interaction_lock = asyncio.Lock()
        self._interaction_task: asyncio.Task | None = None
        self._decision_task: asyncio.Task | None = None
        self.message_generator = ProactiveMessageGenerator(context, config)
        delivery_settings = self.config.get("delivery_settings", {}) or {}
        self.message_segmenter = ProactiveMessageSegmenter(
            delivery_settings.get("segmented_reply_settings", {}) or {},
        )
        self.long_term = LongTermTimelineStore(self.data_dir)
        self.smart_context_injector = SmartContextInjector(
            self.config.get("smart_context_injection", {}) or {},
        )
        self.reply_delay_policy = ReplyDelayPolicy(
            self.config.get("reply_delay_settings", {}) or {},
        )
        self.reply_delay_coordinator = ReplyDelayCoordinator()
        self.image_renderer = ScheduleImageRenderer(
            self.data_dir,
            self.html_render,
            self.config.get("image_settings", {}) or {},
        )
        self.timezone = self._resolve_timezone()
        self.view_api = VirtualLifeViewAPI(self)
        self.view_api.register()
        self.policy = ProactivePolicy(config, self.storage, self.timezone)
        self.runtime = SchedulerRuntime(self.timezone)
        self.refresh_lock = asyncio.Lock()
        self.delivery_locks: dict[str, asyncio.Lock] = {}
        self._schedule_available_umos: set[str] = set()
        self._conversation_generations: dict[str, int] = {}
        self._conversation_activity_at: dict[str, datetime] = {}
        self._active_agent_counts: dict[str, int] = {}
        self._agent_release_tasks: set[asyncio.Task] = set()
        self._window_retry_counts: dict[tuple[str, str, str], int] = {}
        self.renewal_attempts: dict[str, int] = {}
        self._personal_network_unavailable_logged = False
        # 聊天里的确定活动 / 菜谱变化自动补写进当天日程。
        self.chat_schedule_state = chat_schedule_events.ChatScheduleState(
            self.data_dir / "chat_schedule_state.json"
        )
        self._chat_schedule_tasks: set[asyncio.Task] = set()
        self._chat_schedule_lock = asyncio.Lock()

    def _resolve_timezone(self) -> ZoneInfo:
        try:
            name = str(self.context.get_config().get("timezone") or "Asia/Shanghai")
            return ZoneInfo(name)
        except Exception:
            return ZoneInfo("Asia/Shanghai")

    @filter.event_message_type(
        filter.EventMessageType.GROUP_MESSAGE, priority=sys.maxsize
    )
    async def block_group_commands(self, event: AstrMessageEvent):
        """群聊里不执行 / 或 ／ 开头的指令。

        AstrBot 的唤醒检查会先把唤前缀（通常是 /）从 event.message_str 中剥离，
        所以必须同时检查未经修改的 message_obj.message_str，否则群聊指令会漏过。
        """
        settings = self.config.get("group_settings", {}) or {}
        if bool(settings.get("allow_commands", False)):
            return
        text = str(getattr(event, "message_str", "") or "").strip()
        raw_text = str(
            getattr(getattr(event, "message_obj", None), "message_str", "") or ""
        ).strip()
        if text.startswith(("/", "／")) or raw_text.startswith(("/", "／")):
            logger.debug(
                "[虚拟人生] 群聊指令已拦截 text=%s raw=%s",
                text[:40],
                raw_text[:40],
            )
            event.stop_event()

    async def initialize(self) -> None:
        await self._cancel_stale_loops()
        await self.storage.load()
        await self._normalize_loaded_timelines()
        await self.long_term.load()
        await self.image_renderer.cleanup()
        view_assets_dir = Path(__file__).resolve().parent / "views" / "life" / "assets"
        try:
            custom_characters = await asyncio.to_thread(
                character_assets.sync_character_assets,
                self.config,
                self.data_dir,
                view_assets_dir,
            )
            wardrobe.set_custom_character_sources(
                custom_characters,
                rotation_seconds=int(
                    (self.config.get("character_settings", {}) or {}).get(
                        "rotation_seconds", 86400
                    )
                    or 86400
                ),
            )
            if custom_characters:
                logger.info(
                    "[虚拟人生] 已加载自定义角色立绘 %s 个槽位 / %s 张图片",
                    len(custom_characters),
                    sum(len(value) for value in custom_characters.values()),
                )
        except Exception as exc:
            logger.warning("[虚拟人生] 自定义角色立绘加载失败：%s", exc)
            wardrobe.set_custom_character_sources(None)
        schedule_settings = self.config.get("schedule_settings", {}) or {}
        generate_time = str(schedule_settings.get("generate_time", "07:00"))
        self.runtime.start(generate_time, self._daily_refresh)
        await self._refresh_all(force=False)
        # Start unconditionally so toggling "即时互动" in the panel works without a reload.
        self._interaction_task = asyncio.create_task(self._interaction_loop())
        self._decision_task = asyncio.create_task(self._decision_loop())
        logger.info("[虚拟人生] 插件已启动，时区=%s", self.timezone.key)

    async def _cancel_stale_loops(self) -> None:
        """热重载可能留下旧实例的后台循环，启动时按协程归属清理。"""
        current = asyncio.current_task()
        stale: list[asyncio.Task] = []
        for task in asyncio.all_tasks():
            if task is current or task.done():
                continue
            coro = task.get_coro()
            qualname = getattr(coro, "__qualname__", "")
            if not qualname.endswith(("_interaction_loop", "_decision_loop")):
                continue
            task.cancel()
            stale.append(task)
        if stale:
            await asyncio.gather(*stale, return_exceptions=True)
            logger.info("[虚拟人生] 清理旧实例遗留循环 %s 个", len(stale))

    async def _normalize_loaded_timelines(self) -> None:
        """启动时修正历史数据：多站行程、旧版强制女仆装、旧摆位坐标。"""
        changed = 0
        if money.backfill_placements(self.data_dir):
            changed += 1
        for key, plan in list(self.storage.plans.items()):
            updated = timeline_rules.split_plan_timeline(plan.timeline)
            migrated_outfit = wardrobe.migrate_legacy_forced_outfit(plan.outfit)
            if updated == plan.timeline and migrated_outfit is plan.outfit:
                continue
            self.storage.plans[key] = replace(
                plan,
                timeline=updated,
                outfit=migrated_outfit,
            )
            changed += 1
        if changed:
            await self.storage.save_plans()
            logger.info("[虚拟人生] 启动时规范化历史日程/穿搭 %s 条", changed)

    async def terminate(self) -> None:
        self.context.registered_web_apis[:] = [
            api
            for api in self.context.registered_web_apis
            if getattr(api[1], "__self__", None) is not self.view_api
        ]
        self.runtime.stop()
        if self._interaction_task is not None:
            self._interaction_task.cancel()
            await asyncio.gather(self._interaction_task, return_exceptions=True)
            self._interaction_task = None
        if self._decision_task is not None:
            self._decision_task.cancel()
            await asyncio.gather(self._decision_task, return_exceptions=True)
            self._decision_task = None
        await self._cancel_stale_loops()
        chat_schedule_tasks = tuple(self._chat_schedule_tasks)
        for task in chat_schedule_tasks:
            task.cancel()
        if chat_schedule_tasks:
            await asyncio.gather(*chat_schedule_tasks, return_exceptions=True)
        self.reply_delay_coordinator.clear()
        release_tasks = tuple(self._agent_release_tasks)
        for task in release_tasks:
            task.cancel()
        if release_tasks:
            await asyncio.gather(*release_tasks, return_exceptions=True)
        await self.storage.save_plans()
        await self.storage.save_sessions()

    @staticmethod
    def _umo_hash(umo: str) -> str:
        return hashlib.sha1(umo.encode("utf-8")).hexdigest()[:12]

    def _now(self) -> datetime:
        return now_in(self.timezone)

    def _daily_generation_flags(self) -> tuple[bool, bool]:
        settings = self.config.get("schedule_settings", {}) or {}
        return (
            bool(settings.get("daily_schedule_generation_enable", True)),
            bool(settings.get("daily_outfit_generation_enable", True)),
        )

    def _mark_conversation_activity(
        self, umo: str, moment: datetime | None = None
    ) -> int:
        generation = self._conversation_generations.get(umo, 0) + 1
        self._conversation_generations[umo] = generation
        self._conversation_activity_at[umo] = moment or self._now()
        return generation

    def _conversation_generation(self, umo: str) -> int:
        return self._conversation_generations.get(umo, 0)

    def _agent_is_active(self, umo: str) -> bool:
        return self._active_agent_counts.get(umo, 0) > 0

    def _proactive_context_is_current(self, umo: str, generation: int) -> bool:
        return (
            not self._agent_is_active(umo)
            and self._conversation_generation(umo) == generation
        )

    def _window_is_idle_enough(self, umo: str, now: datetime) -> bool:
        activity_at = self._conversation_activity_at.get(umo)
        if activity_at is None:
            return True
        delivery = self.config.get("delivery_settings", {}) or {}
        minimum = max(0, int(delivery.get("minimum_idle_for_window_minutes", 20)))
        return (now - activity_at).total_seconds() >= minimum * 60

    async def _release_agent_after_history_save(self, umo: str) -> None:
        history_saved = False
        try:
            async with session_lock_manager.acquire_lock(umo):
                history_saved = True
        finally:
            count = self._active_agent_counts.get(umo, 0)
            if count <= 1:
                self._active_agent_counts.pop(umo, None)
                if history_saved:
                    self._mark_conversation_activity(umo)
                    self._schedule_idle(umo)
            else:
                self._active_agent_counts[umo] = count - 1

    def _personal_network_plugin(self):
        settings = self.config.get("personal_network_integration", {}) or {}
        if not settings.get("enable", False):
            return None
        getter = getattr(self.context, "get_registered_star", None)
        metadata = (
            getter("astrbot_plugin_personal_network") if callable(getter) else None
        )
        plugin = (
            metadata.star_cls
            if metadata and metadata.activated and metadata.star_cls
            else None
        )
        required_methods = {
            "get_context_for_plugin",
            "record_life_event_from_plugin",
        }
        if plugin is None or any(
            not hasattr(plugin, method) for method in required_methods
        ):
            if not self._personal_network_unavailable_logged:
                logger.warning(
                    "[Virtual Life] Personal Network integration is enabled but a compatible plugin is unavailable."
                )
                self._personal_network_unavailable_logged = True
            return None
        self._personal_network_unavailable_logged = False
        return plugin

    def _personal_network_status(self) -> str:
        settings = self.config.get("personal_network_integration", {}) or {}
        if not settings.get("enable", False):
            return "未启用"
        try:
            available = bool(self._personal_network_plugin())
        except Exception:
            available = False
        return "已连接" if available else "已启用但插件不可用"

    async def _generate_new_character(self, persona: PersonaContext) -> str:
        """Possibly generate a new virtual character and write it to Personal Network.

        Returns a non-empty hint string to append to schedule requirements when a
        character is successfully created, or an empty string otherwise.
        """
        settings = self.config.get("personal_network_integration", {}) or {}
        try:
            probability = max(
                0.0, min(1.0, float(settings.get("new_character_probability", 0.0)))
            )
        except (TypeError, ValueError):
            probability = 0.0
        if probability <= 0.0:
            return ""
        import random as _random

        if _random.random() >= probability:
            return ""
        plugin = self._personal_network_plugin()
        if plugin is None or not hasattr(plugin, "upsert_batch_for_plugin"):
            return ""
        try:
            char = await self.plan_generator.generate_new_character(persona)
        except Exception:
            logger.exception(
                "[Virtual Life] New character generation failed persona=%s", persona.id
            )
            return ""
        ref = "new_char"
        try:
            result = await plugin.upsert_batch_for_plugin(
                persona.id,
                characters=[
                    {
                        "ref": ref,
                        "name": char["name"],
                        "bio": char["bio"],
                        "personality": char["personality"],
                        "preferences": char["preferences"],
                        "facts": char["facts"],
                    }
                ],
                relationships=[
                    {
                        "source": "persona",
                        "target": ref,
                        "type": char["relationship_type"],
                        "strength": 30,
                        "status": "active",
                        "description": char["relationship_description"],
                    }
                ],
                source="astrbot_plugin_simlife_world",
            )
            if not result.get("updated"):
                logger.warning(
                    "[Virtual Life] New character write rejected persona=%s: %s",
                    persona.id,
                    result.get("reason", "unknown"),
                )
                return ""
            char_uuid = result.get("refs", {}).get(ref, "")
            logger.info(
                "[Virtual Life] New character written to Personal Network persona=%s name=%s uuid=%s",
                persona.id,
                char["name"],
                char_uuid,
            )
        except Exception:
            logger.exception(
                "[Virtual Life] Failed to write new character to Personal Network persona=%s",
                persona.id,
            )
            return ""
        return (
            f"今天日程中应安排与 {char['name']}（{char['relationship_type']}）的相遇或互动。"
            f"关系说明：{char['relationship_description']}。"
            f"人物简介：{char['bio']}。"
            "请在时间线中自然地加入这次会面，并在对应 timeline 项目的 participant_ids 中填入该人物的 ID（从关系数据中获取）。"
        )

    async def _personal_network_participants_context(
        self, persona_id: str, participant_ids: tuple[str, ...]
    ) -> str:
        """Return a brief context string for the given participant UUIDs.

        Fetches the full network snapshot and filters by the provided IDs,
        returning a formatted string suitable for injection into the LLM prompt.
        Returns an empty string on any failure or if the feature is disabled.
        """
        if not participant_ids:
            return ""
        settings = self.config.get("personal_network_integration", {}) or {}
        if not settings.get("inject_current_participants", True):
            return ""
        plugin = self._personal_network_plugin()
        if plugin is None or not hasattr(plugin, "get_network_for_plugin"):
            return ""
        try:
            data = await plugin.get_network_for_plugin(persona_id)
        except Exception:
            logger.exception(
                "[Virtual Life] Failed to fetch network for participant injection persona=%s",
                persona_id,
            )
            return ""
        id_set = set(participant_ids)
        characters = [
            c for c in (data.get("characters") or []) if c.get("id") in id_set
        ]
        if not characters:
            return ""
        lines = ["当前时段参与人物："]
        for c in characters:
            name = c.get("name", "（未知）")
            bio = c.get("bio", "")
            personality = c.get("personality", "")
            parts = [name]
            if bio:
                parts.append(bio)
            if personality:
                parts.append(f"性格：{personality}")
            lines.append("- " + "；".join(parts))
        return "\n".join(lines)

    async def _personal_network_context(self, persona_id: str) -> str:
        plugin = self._personal_network_plugin()
        if plugin is None:
            return ""
        settings = self.config.get("personal_network_integration", {}) or {}
        try:
            max_chars = max(
                500,
                min(12000, int(settings.get("max_context_chars", 4000))),
            )
        except (TypeError, ValueError):
            max_chars = 4000
        try:
            return await plugin.get_context_for_plugin(persona_id, max_chars=max_chars)
        except Exception:
            logger.exception(
                "[Virtual Life] Failed to read Personal Network context: persona=%s",
                persona_id,
            )
            return ""

    async def _record_completed_personal_network_events(
        self, persona_id: str, now: datetime
    ) -> None:
        settings = self.config.get("personal_network_integration", {}) or {}
        if not settings.get("record_completed_events", True):
            return
        plugin = self._personal_network_plugin()
        if plugin is None:
            return
        for plan in self.storage.plans.values():
            if plan.persona_id != persona_id or plan.status != "ok":
                continue
            plan_date = date.fromisoformat(plan.date)
            for item in plan.timeline:
                if not item.participant_ids:
                    continue
                if item.end == "24:00":
                    ended_at = datetime.combine(
                        plan_date + timedelta(days=1), time.min, self.timezone
                    )
                else:
                    ended_at = datetime.combine(
                        plan_date,
                        time.fromisoformat(item.end),
                        self.timezone,
                    )
                if ended_at > now:
                    continue
                summary = item.activity
                if item.location:
                    summary += f"（地点：{item.location}）"
                try:
                    await plugin.record_life_event_from_plugin(
                        persona_id,
                        participant_ids=list(item.participant_ids),
                        event_type="virtual_schedule",
                        summary=summary,
                        occurred_at=ended_at.isoformat(),
                        importance=50,
                        emotional_tone=plan.mood,
                        source="astrbot_plugin_simlife_world",
                        source_key=f"{plan.date}:{item.id}",
                    )
                except ValueError as exc:
                    logger.warning(
                        "[Virtual Life] Skipped Personal Network event: persona=%s item=%s error=%s",
                        persona_id,
                        item.id,
                        exc,
                    )
                except Exception:
                    logger.exception(
                        "[Virtual Life] Failed to record Personal Network event: persona=%s item=%s",
                        persona_id,
                        item.id,
                    )

    async def _daily_refresh(self) -> None:
        await self._refresh_all(force=True)

    async def _refresh_all(self, *, force: bool) -> None:
        async with self.refresh_lock:
            now = self._now()
            self.storage.prune_schedule_requirements(now.date())
            await self._check_long_term_renewals(now.date())
            grouped: dict[str, tuple[PersonaContext, list[str]]] = {}
            for umo in self.policy.enabled_sessions():
                persona = await self.personas.resolve(umo)
                grouped.setdefault(persona.id, (persona, []))[1].append(umo)

            for persona, sessions in grouped.values():
                await self._record_completed_personal_network_events(persona.id, now)
                await self._process_deliveries(persona, now)
                await self._ensure_world_event(persona, now.date())
                await self._record_garage_returns(persona, now)
                await self._settle_work_income(
                    persona, now.date() - timedelta(days=1)
                )
                await self._settle_work_income(
                    persona, now.date(), before=now
                )
                await self._write_daily_diary(
                    persona, now.date() - timedelta(days=1)
                )
                await self._write_weekly_diary(persona, now)
                await self._write_monthly_diary(persona, now)
                await self._write_yearly_diary(persona, now)
                await self._record_anniversary(persona, now)
                plan = await self._ensure_plan(persona, now.date(), force=force)
                for umo in sessions:
                    await self._schedule_session(umo, persona, plan)

            keep_days = int(
                (self.config.get("schedule_settings", {}) or {}).get("history_days", 14)
            )
            self.storage.plans = prune_date_keys(
                self.storage.plans, keep_days, now.date()
            )
            await self.storage.save_plans()
            await self.storage.save_sessions()

    async def _ensure_plan_for_umo(
        self,
        umo: str,
        *,
        force: bool = False,
        extra: str = "",
        preserve_disabled: bool = False,
    ) -> tuple[PersonaContext, DailyPlan]:
        persona = await self.personas.resolve(umo)
        plan = await self._ensure_plan(
            persona,
            self._now().date(),
            force=force,
            extra=extra,
            preserve_disabled=preserve_disabled,
        )
        return persona, plan

    async def _ensure_plan(
        self,
        persona: PersonaContext,
        target: date,
        *,
        force: bool = False,
        extra: str = "",
        preserve_disabled: bool = False,
    ) -> DailyPlan:
        date_str = target.isoformat()
        existing = self.storage.get_plan(date_str, persona.id)
        if existing and not force:
            return existing
        settings = self.config.get("schedule_settings", {}) or {}
        include_schedule, include_outfit = self._daily_generation_flags()
        history_plans = []
        if include_schedule:
            reference_days = max(0, int(settings.get("reference_history_days", 3)))
            history_plans = self.storage.get_recent_plans(
                persona.id, target, reference_days
            )
        long_term_settings = self.config.get("long_term_settings", {}) or {}
        long_term_context = ""
        if include_schedule and long_term_settings.get("enable", True):
            long_term_context = self.long_term.format_day_context(
                persona.id,
                target,
                fallback_to_latest=True,
            )
        schedule_requirements = (
            self.storage.active_schedule_requirements(persona.id, target)
            if include_schedule
            else []
        )
        relationship_context = (
            await self._personal_network_context(persona.id) if include_schedule else ""
        )
        new_character_hint = (
            await self._generate_new_character(persona) if include_schedule else ""
        )
        requirement_sections = []
        if extra.strip():
            requirement_sections.append("本次补充要求：\n" + extra.strip())
        if schedule_requirements:
            requirement_sections.append(
                "预设日程要求：\n"
                + "\n".join(f"- {item.requirement}" for item in schedule_requirements)
            )
        if new_character_hint:
            requirement_sections.append("新人物出现要求：\n" + new_character_hint)
        plan = await self.plan_generator.generate(
            target,
            persona,
            extra="\n\n".join(requirement_sections),
            history_plans=history_plans,
            long_term_context=long_term_context,
            relationship_context=relationship_context,
            include_schedule=include_schedule,
            include_outfit=include_outfit,
            base_plan=existing if preserve_disabled else None,
        )
        plan_key = self.storage.plan_key(date_str, persona.id)
        previous_plan = self.storage.plans.get(plan_key)
        self.storage.plans[plan_key] = plan
        if include_schedule and plan.has_schedule:
            self.storage.consume_schedule_requirements(
                [item.id for item in schedule_requirements], target
            )
        try:
            await self.storage.save_plans()
        except Exception:
            if previous_plan is None:
                self.storage.plans.pop(plan_key, None)
            else:
                self.storage.plans[plan_key] = previous_plan
            for item in schedule_requirements:
                self.storage.schedule_requirements[item.id] = item
            raise
        return plan

    async def _add_schedule_requirement(
        self,
        event: AstrMessageEvent,
        date_range: str,
        requirement: str,
    ) -> str:
        if not event.is_admin():
            return "无权限：仅管理员可以添加日程要求。"
        today = self._now().date()
        requirement = str(requirement).strip()
        try:
            start, end = parse_schedule_date_range(date_range, today)
            if start <= today:
                raise ValueError("只能为今天之后的日期添加日程要求")
            range_days = (end - start).days + 1
            if range_days > 366:
                raise ValueError("日期区间不能超过 366 天")
            if not requirement:
                raise ValueError("日程要求不能为空")
            if len(requirement) > 500:
                raise ValueError("每条日程要求不能超过 500 字")
            persona = await self.personas.resolve(event.unified_msg_origin)
            for offset in range(range_days):
                target = start + timedelta(days=offset)
                existing_plan = self.storage.get_plan(target.isoformat(), persona.id)
                if existing_plan and existing_plan.has_schedule:
                    raise ValueError(
                        f"{target.isoformat()} 已有有效日程，无法添加首次生成要求"
                    )
                if (
                    len(self.storage.active_schedule_requirements(persona.id, target))
                    >= 10
                ):
                    raise ValueError(
                        f"{target.isoformat()} 已有 10 条日程要求，无法继续添加"
                    )
        except ValueError as exc:
            return f"无法添加日程要求：{exc}。"

        item = ScheduleRequirement(
            id=uuid.uuid4().hex[:12],
            persona_id=persona.id,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            requirement=requirement,
            created_at=self._now().isoformat(),
        )
        self.storage.schedule_requirements[item.id] = item
        try:
            await self.storage.save_plans()
        except Exception as exc:
            self.storage.schedule_requirements.pop(item.id, None)
            logger.warning(
                "[Virtual Life] Schedule requirement persistence failed persona=%s: %s",
                persona.id,
                exc,
            )
            return "日程要求保存失败，请检查日志后重试。"
        normalized_range = (
            item.start_date
            if item.start_date == item.end_date
            else f"{item.start_date}..{item.end_date}"
        )
        return f"已为人格 {persona.id} 添加日程要求：{normalized_range}。"

    def _parse_travel_plan_args(
        self, text: str, today: date
    ) -> tuple[str, date | None, int | None]:
        """Split "<destination> [YYYY-MM-DD|MM-DD] [days]" into its parts."""
        tokens = [token for token in str(text or "").split() if token]
        depart: date | None = None
        days: int | None = None
        name_parts: list[str] = []
        for token in tokens:
            parts = token.split("-")
            if (
                depart is None
                and len(parts) in (2, 3)
                and all(part.isdigit() for part in parts)
            ):
                try:
                    depart = parse_schedule_date_range(token, today)[0]
                    continue
                except ValueError:
                    pass
            if days is None and token.isdigit() and 1 <= int(token) <= 30:
                days = int(token)
                continue
            name_parts.append(token)
        name = "".join(name_parts).strip()
        if not name:
            raise ValueError(
                "格式：/虚拟日程 旅行 规划 <目的地> [出发日期] [天数]，"
                "例如「/虚拟日程 旅行 规划 京都 2026-11-20 5」。"
            )
        return name, depart, days

    async def _handle_travel_command(
        self, event: AstrMessageEvent, action: str, argument: str
    ) -> str:
        persona = await self.personas.resolve(event.unified_msg_origin)
        today = self._now().date()
        settings = self.config.get("travel_settings", {}) or {}
        action = str(action or "").strip()
        argument = str(argument or "").strip()
        if action in {"目的地", "列表", "清单"}:
            return self.travel.destination_list_text()
        if action in {"规划", "安排", "计划"}:
            if not event.is_admin():
                return "无权限：只有管理员可以规划旅行。"
            try:
                name, depart, days = self._parse_travel_plan_args(argument, today)
            except ValueError as exc:
                return str(exc)
            trip, error = self.travel.plan(
                persona.id,
                name,
                depart=depart,
                days=days,
                persona_prompt=persona.prompt,
                today=today,
                settings=settings,
            )
            if trip is None:
                return error
            return (
                f"已为人格 {persona.id} 安排旅行：\n"
                + self.travel.describe(trip, today)
                + "\n\n之后生成日程时会按这趟行程写；想改时间就先取消再重新规划。"
            )
        if action in {"取消", "删除"}:
            if not event.is_admin():
                return "无权限：只有管理员可以取消旅行。"
            trip = self.travel.cancel(persona.id, today)
            if trip is None:
                return "现在没有可以取消的旅行。"
            return f"已取消：{trip.city}（{trip.depart} → {trip.back}）。"
        trip = self.travel.current(persona.id, today) or self.travel.upcoming(
            persona.id, today
        )
        if trip is None:
            return (
                "现在没有安排旅行。\n"
                + self.travel.destination_list_text()
                + "\n\n用法：/虚拟日程 旅行 规划 <目的地> [出发日期] [天数]"
            )
        return self.travel.describe(trip, today)

    async def _reschedule_plan_sessions(
        self, persona: PersonaContext, plan: DailyPlan
    ) -> None:
        for umo in self.policy.enabled_sessions():
            resolved = await self.personas.resolve(umo)
            if resolved.id == persona.id:
                await self._schedule_session(umo, resolved, plan)
        await self.storage.save_sessions()

    async def _schedule_session(
        self, umo: str, persona: PersonaContext, plan: DailyPlan
    ) -> None:
        prefix = f"pvd:{self._umo_hash(umo)}:plan:"
        self.runtime.remove_prefix(prefix)
        self.runtime.remove(f"pvd:{self._umo_hash(umo)}:idle")
        if not plan.has_schedule:
            self._schedule_available_umos.discard(umo)
            return
        self._schedule_available_umos.add(umo)
        now = self._now()
        state = self.policy.ensure_state(umo, persona.id, plan, now)
        delivery = self.config.get("delivery_settings", {}) or {}
        jitter_minutes = delivery.get("proactive_window_jitter_minutes", 15)
        for window in plan.proactive_windows:
            if not self._window_matches(umo, window):
                continue
            run_at = self._at_time(plan.date, window.at) + timedelta(
                minutes=proactive_window_offset_minutes(plan, window, jitter_minutes),
            )
            if run_at <= now:
                continue
            self.runtime.add_date_job(
                prefix + "window:" + window.id,
                run_at,
                self._run_window,
                umo,
                persona.id,
                plan.revision,
                window.id,
            )
        await self._schedule_sleep_exception(umo, persona, plan, state)
        self._schedule_idle(umo)

    @staticmethod
    def _window_matches(umo: str, window: ProactiveWindow) -> bool:
        kind = "group" if session_kind(umo) == "group" else "private"
        return window.audience in {"both", kind}

    def _at_time(self, date_str: str, hhmm: str) -> datetime:
        hour, minute = map(int, hhmm.split(":"))
        return datetime.combine(
            date.fromisoformat(date_str), time(hour, minute), self.timezone
        )

    async def _schedule_sleep_exception(self, umo, persona, plan, state) -> None:
        if state.sleep_drawn:
            return
        state.sleep_drawn = True
        probability = float(
            (self.config.get("delivery_settings", {}) or {}).get(
                "sleep_exception_probability", 0.08
            )
        )
        state.sleep_selected = deterministic_probability(
            f"sleep::{plan.date}::{umo}"
        ) < max(0.0, min(1.0, probability))
        if not state.sleep_selected:
            return
        sleep_items = [item for item in plan.timeline if item.state == "sleep"]
        if not sleep_items:
            return
        item = max(
            sleep_items,
            key=lambda value: self._duration_minutes(value.start, value.end),
        )
        start = self._at_time(plan.date, item.start)
        end = self._end_time(plan.date, item.end)
        if end <= self._now() or (end - start).total_seconds() < 120:
            return
        earliest = max(start, self._now() + timedelta(seconds=10))
        span = max(1, int((end - earliest).total_seconds() // 60) - 1)
        offset = deterministic_int(f"sleep-time::{plan.date}::{umo}", 0, span)
        run_at = earliest + timedelta(minutes=offset)
        self.runtime.add_date_job(
            f"pvd:{self._umo_hash(umo)}:plan:sleep",
            run_at,
            self._run_sleep,
            umo,
            persona.id,
            plan.revision,
        )

    @staticmethod
    def _duration_minutes(start: str, end: str) -> int:
        def value(raw: str) -> int:
            if raw == "24:00":
                return 1440
            hour, minute = map(int, raw.split(":"))
            return hour * 60 + minute

        return value(end) - value(start)

    def _end_time(self, date_str: str, hhmm: str) -> datetime:
        if hhmm == "24:00":
            return datetime.combine(
                date.fromisoformat(date_str) + timedelta(days=1),
                time.min,
                self.timezone,
            )
        return self._at_time(date_str, hhmm)

    def _schedule_idle(self, umo: str, *, run_at: datetime | None = None) -> None:
        job_id = f"pvd:{self._umo_hash(umo)}:idle"
        self.runtime.remove(job_id)
        if not self.policy.is_enabled(umo) or umo not in self._schedule_available_umos:
            return
        if run_at is None:
            settings = self.policy.settings_for(umo)
            minimum = max(1, int(settings.get("idle_min_minutes", 90)))
            maximum = max(minimum, int(settings.get("idle_max_minutes", minimum)))
            run_at = self._now() + timedelta(minutes=random.randint(minimum, maximum))
        self.runtime.add_date_job(job_id, run_at, self._run_idle, umo)

    async def _run_window(
        self, umo: str, persona_id: str, revision: str, window_id: str
    ) -> None:
        persona, plan = await self._ensure_plan_for_umo(umo)
        if persona.id != persona_id or plan.revision != revision:
            await self._schedule_session(umo, persona, plan)
            return
        window = next(
            (value for value in plan.proactive_windows if value.id == window_id), None
        )
        if not window:
            return
        await self._attempt_window(umo, persona, plan, window, delayed=False)

    async def _run_delayed_window(
        self,
        umo: str,
        persona_id: str,
        revision: str,
        window_id: str,
        scheduled_at: str,
        retry_reason: str = "",
    ) -> None:
        persona, plan = await self._ensure_plan_for_umo(umo)
        if persona.id != persona_id or plan.revision != revision:
            return
        window = next(
            (value for value in plan.proactive_windows if value.id == window_id), None
        )
        if not window:
            return
        await self._attempt_window(
            umo,
            persona,
            plan,
            window,
            delayed=True,
            attempt_key=scheduled_at,
            retry_reason=retry_reason,
        )

    async def _attempt_window(
        self,
        umo: str,
        persona: PersonaContext,
        plan: DailyPlan,
        window: ProactiveWindow,
        *,
        delayed: bool,
        attempt_key: str = "",
        retry_reason: str = "",
    ) -> None:
        intent = window.intent
        if delayed:
            intent = self._delayed_window_intent(window, plan, retry_reason)
        sent, reason = await self._attempt_unsolicited(
            umo,
            persona,
            plan,
            intent,
            "window",
            attempt_key=attempt_key or window.id,
        )
        if sent:
            self._window_retry_counts.pop((umo, plan.revision, window.id), None)
            return
        if not self._should_retry_window(umo, reason):
            return
        key = (umo, plan.revision, window.id)
        count = self._window_retry_counts.get(key, 0)
        delivery = self.config.get("delivery_settings", {}) or {}
        retry_max = max(0, int(delivery.get("window_retry_max", 3)))
        if count >= retry_max:
            return
        run_at = self._window_retry_run_at(umo, plan, reason)
        if run_at is None:
            return
        self._schedule_window_retry(umo, persona, plan, window, run_at, reason)
        if reason != "agent task active":
            self._window_retry_counts[key] = count + 1

    def _delayed_window_intent(
        self,
        window: ProactiveWindow,
        plan: DailyPlan,
        retry_reason: str = "",
    ) -> str:
        source = next(
            (item for item in plan.timeline if item.id == window.source_item_id), None
        )
        base = window.intent
        if not source:
            return base
        if self._now() < self._end_time(plan.date, source.end):
            return base
        reason_hint = {
            "conversation is not idle enough": "当时你正在忙或正在聊天，没找到合适的插话时机",
            "agent task active": "当时你们正在处理一件复杂的事情，不适合突然打断",
            "cooldown active": "当时你们刚刚才聊过，紧接着再开口会显得太突兀",
            "availability probability rejected": "当时对方的状态不太适合被打扰",
            "sleeping": "当时对方正在休息",
        }.get(retry_reason, "当时时机不太合适")
        return (
            f"{base}。你原本打算在「{source.activity}」时段联系对方，但{reason_hint}，"
            "错过了那个时机；现在自然地向对方提起，别让对方察觉这是程序自动安排的。"
        )

    def _should_retry_window(self, umo: str, reason: str) -> bool:
        if reason in {"sleeping", "availability probability rejected"}:
            return True
        delivery = self.config.get("delivery_settings", {}) or {}
        if reason == "conversation is not idle enough":
            return bool(delivery.get("window_retry_when_not_idle", False))
        if reason == "agent task active":
            return bool(delivery.get("window_retry_when_not_idle", False))
        if reason == "cooldown active":
            return bool(delivery.get("window_retry_when_cooldown", False))
        return False

    def _window_retry_run_at(
        self, umo: str, plan: DailyPlan, reason: str
    ) -> datetime | None:
        now = self._now()
        if reason in {"sleeping", "availability probability rejected"}:
            next_time = next_available_at(plan, now)
            if not next_time:
                return None
            run_at = next_time + timedelta(minutes=random.randint(3, 15))
        elif reason == "agent task active":
            run_at = now + timedelta(minutes=30)
        elif reason == "conversation is not idle enough":
            state = self.storage.sessions.get(umo)
            delivery = self.config.get("delivery_settings", {}) or {}
            idle_required = max(
                0, int(delivery.get("minimum_idle_for_window_minutes", 20))
            )
            activity_times = []
            if state and state.last_user_message_at:
                activity_times.append(
                    parse_datetime(state.last_user_message_at, self.timezone)
                )
            if activity_at := self._conversation_activity_at.get(umo):
                activity_times.append(activity_at)
            if not activity_times:
                return None
            target = max(activity_times) + timedelta(minutes=idle_required)
            run_at = max(target, now) + timedelta(minutes=random.randint(1, 5))
        elif reason == "cooldown active":
            state = self.storage.sessions.get(umo)
            if not state or not state.last_proactive_at:
                return None
            settings = self.policy.settings_for(umo)
            cooldown = max(0, int(settings.get("cooldown_minutes", 0)))
            target = parse_datetime(state.last_proactive_at, self.timezone) + timedelta(
                minutes=cooldown
            )
            run_at = max(target, now) + timedelta(minutes=random.randint(1, 5))
        else:
            return None
        if run_at.date() > date.fromisoformat(plan.date):
            return None
        return run_at

    def _schedule_window_retry(
        self,
        umo: str,
        persona: PersonaContext,
        plan: DailyPlan,
        window: ProactiveWindow,
        run_at: datetime | None = None,
        retry_reason: str = "",
    ) -> None:
        if run_at is None:
            next_time = next_available_at(plan, self._now())
            if not next_time:
                return
            run_at = next_time + timedelta(minutes=random.randint(3, 15))
        self.runtime.add_date_job(
            f"pvd:{self._umo_hash(umo)}:plan:window-retry:{window.id}",
            run_at,
            self._run_delayed_window,
            umo,
            persona.id,
            plan.revision,
            window.id,
            run_at.isoformat(),
            retry_reason,
        )

    async def _run_sleep(self, umo: str, persona_id: str, revision: str) -> None:
        persona, plan = await self._ensure_plan_for_umo(umo)
        if persona.id != persona_id or plan.revision != revision:
            return
        await self._attempt_unsolicited(
            umo, persona, plan, "睡梦中醒来、起夜或失眠时忽然想起对方", "sleep"
        )

    async def _run_idle(self, umo: str) -> None:
        persona, plan = await self._ensure_plan_for_umo(umo)
        sent, reason = await self._attempt_unsolicited(
            umo, persona, plan, "会话已经沉默了一段时间，想自然地重新联系", "idle"
        )
        if sent:
            self._schedule_idle(umo)
            return
        if reason in {"sleeping", "availability probability rejected"}:
            next_time = next_available_at(plan, self._now())
            if next_time:
                self._schedule_idle(
                    umo, run_at=next_time + timedelta(minutes=random.randint(3, 15))
                )
        elif reason in {
            "cooldown active",
            "conversation is not idle enough",
            "agent task active",
        }:
            self._schedule_idle(umo, run_at=self._now() + timedelta(minutes=30))

    # ------------------------------------------------------- 发言机会（自主决定）

    def _decision_settings(self) -> dict:
        return self.config.get("delivery_settings", {}) or {}

    async def _decision_loop(self) -> None:
        """固定间隔给角色一次「要不要开口」的机会，由模型自己决定。"""
        settings = self._decision_settings()
        if not bool(settings.get("decision_loop_enable", True)):
            logger.info("[虚拟人生] 发言决策循环未启用")
            return
        interval = max(5, int(settings.get("decision_interval_minutes", 20)))
        logger.info("[虚拟人生] 发言决策循环已启动，间隔=%s 分钟", interval)
        while True:
            try:
                await self._run_decision_opportunities()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("[虚拟人生] 发言决策失败: %s", exc)
            await asyncio.sleep(interval * 60)

    async def _run_decision_opportunities(self) -> None:
        settings = self._decision_settings()
        if not bool(settings.get("decision_loop_enable", True)):
            return
        now = self._now()
        min_silence = max(0, int(settings.get("decision_min_silence_minutes", 8)))
        for umo in self.policy.enabled_sessions():
            try:
                state = self.storage.sessions.get(umo)
                if state and state.last_user_message_at:
                    last = parse_datetime(state.last_user_message_at, self.timezone)
                    if (
                        last is not None
                        and (now - last).total_seconds() / 60 < min_silence
                    ):
                        continue
                persona, plan = await self._ensure_plan_for_umo(umo)
                if plan.status != "ok":
                    continue
                current = timeline_item_at(plan, now)
                if current is not None and current.state == "sleep":
                    continue
                await self._attempt_unsolicited(
                    umo,
                    persona,
                    plan,
                    "忽然想说点什么，也可能只是想想",
                    "decision",
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("[虚拟人生] 发言决策异常 umo=%s: %s", umo, exc)

    async def _attempt_unsolicited(
        self,
        umo: str,
        persona: PersonaContext,
        plan: DailyPlan,
        intent: str,
        trigger: str,
        *,
        attempt_key: str = "",
    ) -> tuple[bool, str]:
        lock = self.delivery_locks.setdefault(umo, asyncio.Lock())
        async with lock:
            if not plan.has_schedule:
                return False, "schedule unavailable"
            if self._agent_is_active(umo):
                logger.info("[虚拟人生] 跳过 %s: 会话正在处理 Agent 任务", umo)
                return False, "agent task active"
            now = self._now()
            if self.user_states.is_sleeping(now):
                logger.info("[虚拟人生] 跳过 %s: 主人在睡觉", umo)
                return False, "user sleeping"
            if trigger == "window" and not self._window_is_idle_enough(umo, now):
                logger.info("[虚拟人生] 跳过 %s: 会话尚未达到窗口沉默时间", umo)
                return False, "conversation is not idle enough"
            state = self.policy.ensure_state(umo, persona.id, plan, now)
            current_item = timeline_item_at(plan, now)
            needs = self._life_needs(plan, now)
            decision = self.policy.evaluate(
                umo=umo,
                state=state,
                current_item=current_item,
                now=now,
                trigger=trigger,
                attempt_key=attempt_key,
                needs=needs,
            )
            if not decision.allowed:
                logger.info("[虚拟人生] 跳过 %s: %s", umo, decision.reason)
                return False, decision.reason
            generation = self._conversation_generation(umo)
            delivered = await self._deliver(
                umo,
                persona,
                plan,
                intent,
                state.unanswered_count,
                generation,
                decide=(trigger == "decision"),
            )
            if not delivered:
                if trigger == "decision":
                    return False, "model chose silence"
                reason = (
                    "agent task active"
                    if self._agent_is_active(umo)
                    else "conversation is not idle enough"
                )
                return False, reason
            self.policy.record_delivery(
                state,
                now,
                count_budget=not (
                    session_kind(umo) == "group" and trigger == "window"
                ),
            )
            await self.storage.save_sessions()
            return True, "sent"

    def _current_room_conflict(self, text: str, current) -> str:
        """Return a home room mentioned by text that is not the current room."""
        if current is None:
            return ""
        location = str(getattr(current, "location", "") or "")
        if not location:
            return ""
        allowed = {word for word in self.HOME_PLACE_WORDS if word in location}
        for word in self.HOME_PLACE_WORDS:
            if word == "家":
                continue
            if word in str(text or "") and word not in allowed:
                return word
        return ""

    async def _deliver(
        self,
        umo: str,
        persona: PersonaContext,
        plan: DailyPlan,
        intent: str,
        unanswered_count: int,
        generation: int,
        decide: bool = False,
    ) -> bool:
        now = self._now()
        is_group = session_kind(umo) == "group"
        current_item = timeline_item_at(plan, now)
        if is_group:
            current_state = "正在过自己的日常"
        else:
            current_state = current_item.activity if current_item else "今日状态暂未明确"
        await self._record_completed_personal_network_events(persona.id, now)
        relationship_context = "" if is_group else await self._personal_network_context(persona.id)
        timeline_context = ""
        delivery = self.config.get("delivery_settings", {}) or {}
        if is_group:
            timeline_context = self._group_life_context(plan, now)
        elif delivery.get("proactive_timeline_context", True):
            furniture_states, furniture_context = self._furniture_activity_context(now)
            health_summary = str(self._life_needs(plan, now).get("summary") or "")
            timeline_context = self.smart_context_injector.build_proactive_context(
                plan,
                now,
                self.long_term,
                furniture_context=furniture_context,
                furniture_states=furniture_states,
                history_plans=self._life_history_plans(plan),
                health_summary=health_summary,
            )
        if not is_group:
            try:
                pending_actions = view_state.load_pending_actions(
                    self.data_dir / "plans.json", persona.id
                )
                if pending_actions:
                    labels = "、".join(
                        str(action.get("label") or "递东西")
                        for action in pending_actions[:2]
                    )
                    timeline_context += (
                        "\n\n【观察窗待处理】主人之前在对话里提到要给月月东西，"
                        f"观察窗里还有「{labels}」按钮。可以在主动消息里自然提醒"
                        "主人去点一下，但不要说得像系统提示。"
                    )
                recent_gifts = self.interactions.recent_gifts(2, hours=48)
                if recent_gifts:
                    gift_names = "、".join(
                        str(item.get("item_name") or "").strip()
                        for item in recent_gifts
                    )
                    timeline_context += (
                        f"\n\n【最近收到的东西】{gift_names}。"
                        "如果和当前主动消息自然相关，可以顺口提一句；"
                        "不要每条都提，也不要像在报清单。"
                    )
            except Exception:
                pass
        group_intent = "想自然地在群里说句话，和群友互动一下"
        recent_proactive: list[str] = []
        reader = getattr(self.message_generator, "recent_proactive_texts", None)
        if (
            not is_group
            and delivery.get("proactive_repeat_guard", True)
            and callable(reader)
        ):
            recent_proactive = await reader(umo, 8)
        text = await self.message_generator.generate(
            umo=umo,
            persona=persona,
            current_time=now,
            current_state=current_state,
            intent=group_intent if is_group else intent,
            unanswered_count=unanswered_count,
            relationship_context=relationship_context,
            timeline_context=timeline_context,
            recent_sent=recent_proactive,
            decide=decide,
            include_history=not is_group,
            group_mode=is_group,
        )
        if decide and not text:
            if is_group:
                try:
                    break_probability = float(
                        delivery.get("group_break_silence_probability", 0.4)
                    )
                except (TypeError, ValueError):
                    break_probability = 0.4
                break_probability = max(0.0, min(1.0, break_probability))
                if break_probability > 0 and random.random() < break_probability:
                    logger.info(
                        "[虚拟人生] 群聊冷场，按概率 %s 改口主动发言 umo=%s",
                        break_probability,
                        umo,
                    )
                    text = await self.message_generator.generate(
                        umo=umo,
                        persona=persona,
                        current_time=now,
                        current_state=current_state,
                        intent=group_intent,
                        unanswered_count=unanswered_count,
                        relationship_context="",
                        timeline_context=timeline_context,
                        recent_sent=[],
                        decide=False,
                        include_history=False,
                        group_mode=True,
                        retry_note=(
                            "群里现在有点安静，别再沉默。自然地说一句短话打破冷场，"
                            "可以分享此刻的一件小事或一个轻吐槽；不要汇报日程、"
                            "不要像公告，也不要硬开一个空泛的话题。"
                        ),
                    )
            if not text:
                logger.info("[虚拟人生] %s 这一次决定不开口", umo)
                return False
        if is_group:
            text = self._filter_group_reply(
                text, extra_terms=_group_plan_terms(plan)
            )
            if not text or text == "……":
                return False
        if not is_group:
            conflict = self._current_room_conflict(text, current_item)
            if conflict:
                logger.info(
                    "[虚拟人生] 主动消息场景不一致，重写一次 umo=%s wrong=%s text=%s",
                    umo,
                    conflict,
                    text,
                )
                retry = await self.message_generator.generate(
                    umo=umo,
                    persona=persona,
                    current_time=now,
                    current_state=current_state,
                    intent=intent,
                    unanswered_count=unanswered_count,
                    relationship_context=relationship_context,
                    timeline_context=timeline_context,
                    recent_sent=recent_proactive,
                    include_history=True,
                    retry_note=(
                        f"你刚才提到了「{conflict}」，但你此刻实际在"
                        f"{getattr(current_item, 'location', '') or '当前地点'}，"
                        f"正在{getattr(current_item, 'activity', '') or current_state}。"
                        "重写这一句，不要提到其他房间、地点或旧场景，只按当前状态说。"
                    ),
                )
                if retry:
                    text = retry
                if self._current_room_conflict(text, current_item):
                    logger.info(
                        "[虚拟人生] 重写后场景仍不一致，放弃本次主动消息 umo=%s",
                        umo,
                    )
                    return False
        if recent_proactive and self.interactions.is_repetitive(text, recent_proactive):
            logger.info(
                "[虚拟人生] 主动消息与最近内容重复，重写一次 umo=%s text=%s", umo, text
            )
            retry = await self.message_generator.generate(
                umo=umo,
                persona=persona,
                current_time=now,
                current_state=current_state,
                intent=group_intent if is_group else intent,
                unanswered_count=unanswered_count,
                relationship_context=relationship_context,
                timeline_context=timeline_context,
                recent_sent=recent_proactive + [text],
                include_history=not is_group,
                retry_note=(
                    "你刚才写的那句和最近说过的话太像了（同一场景/动作/数字）。"
                    "这次必须换一个完全不同的话题或角度，别再提刚才那件事。"
                ),
            )
            if self.interactions.is_repetitive(retry, recent_proactive):
                logger.info("[虚拟人生] 重写后仍然重复，放弃本次主动消息 umo=%s", umo)
                return False
            if is_group:
                retry = self._filter_group_reply(
                    retry, extra_terms=_group_plan_terms(plan)
                )
                if not retry or retry == "……":
                    return False
            text = retry
        if not self._proactive_context_is_current(umo, generation):
            logger.info("[虚拟人生] 丢弃 %s 的主动消息：生成期间会话已发生变化", umo)
            return False
        async with session_lock_manager.acquire_lock(umo):
            if not self._proactive_context_is_current(umo, generation):
                logger.info("[虚拟人生] 丢弃 %s 的主动消息：提交前会话已发生变化", umo)
                return False
            await self._send_text(umo, text)
            await self.message_generator.record_conversation(
                umo=umo,
                persona_id=persona.id,
                intent=intent,
                assistant_text=text,
            )
        return True

    async def _send_text(self, umo: str, text: str) -> None:
        result = self.message_segmenter.split(text)
        logger.info(
            "[虚拟人生] 主动消息分段 umo=%s mode=%s chars=%s parts=%s threshold=%s reason=%s",
            umo,
            result.mode,
            result.source_length,
            len(result.segments),
            result.threshold,
            result.skipped_reason or "segmented",
        )
        for index, segment in enumerate(result.segments):
            sent = await self.context.send_message(umo, MessageChain().message(segment))
            if not sent:
                raise RuntimeError(f"platform unavailable for {umo}")
            if index + 1 < len(result.segments):
                await asyncio.sleep(self.message_segmenter.interval_for(segment))

    async def react_to_camera(
        self, persona_id: str, camera_event: dict
    ) -> bool:
        """Let the character decide whether to say something right after a photo."""
        try:
            now = self._now()
            target_umo = ""
            persona = None
            for umo in self.policy.enabled_sessions():
                if session_kind(umo) == "group":
                    continue
                candidate = await self.personas.resolve(umo)
                if candidate.id == persona_id:
                    target_umo = umo
                    persona = candidate
                    break
            if not target_umo or persona is None:
                return False
            plan = self.storage.get_plan(now.date().isoformat(), persona.id)
            if plan is None or plan.status != "ok" or not plan.has_schedule:
                return False
            target = str(camera_event.get("target") or "")
            caption = str(camera_event.get("caption") or "").strip()
            if target == camera_photo.TARGET_CHARACTER:
                what = "主人刚刚用相机拍了你本人"
            elif target == camera_photo.TARGET_ITEM:
                what = (
                    "主人刚刚用相机拍了家里的「"
                    + str(camera_event.get("item_name") or "家具")
                    + "」"
                )
            else:
                what = "主人刚刚用相机拍了你此刻所在的房间"
            detail = f"（{caption}）" if caption else ""
            intent = (
                f"{what}{detail}。你可以自然地评价这张照片、害羞、吐槽、"
                "反问一句，或者什么都不说；不要像系统提示，也不要复述拍照功能。"
            )
            generation = self._conversation_generations.get(target_umo, 0)
            sent = await self._deliver(
                target_umo,
                persona,
                plan,
                intent,
                0,
                generation,
                decide=True,
            )
            logger.info(
                "[虚拟人生] 拍照后主动反应 persona=%s sent=%s",
                persona_id,
                sent,
            )
            return bool(sent)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[虚拟人生] 拍照后主动反应失败: %s", exc)
            return False

    # ------------------------------------------------------------- interactions

    def _interaction_settings(self) -> dict:
        return self.config.get("interaction_settings", {}) or {}

    async def _interaction_loop(self) -> None:
        config = self.interactions.settings(self._interaction_settings())
        interval = max(1, int(config["poll_seconds"]))
        logger.info("[虚拟人生] 即时互动已启动，轮询间隔=%ss", interval)
        while True:
            try:
                await self._process_interactions()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("[虚拟人生] 即时互动处理失败: %s", exc)
            await asyncio.sleep(interval)

    async def _process_interactions(self) -> None:
        config = self.interactions.settings(self._interaction_settings())
        if not config["enable"]:
            return
        async with self._interaction_lock:
            for request in self.interactions.pending(limit=3):
                if not self.interactions.claim(request):
                    logger.info(
                        "[虚拟人生] 互动请求已被认领或存在重复，跳过 id=%s",
                        request.get("id"),
                    )
                    continue
                try:
                    await self._handle_interaction(request, config)
                except Exception as exc:
                    logger.warning(
                        "[虚拟人生] 互动失败 id=%s: %s", request.get("id"), exc
                    )
                    self.interactions.write_response(
                        request,
                        {"speech": "刚才走神了，没听清……再说一次？"},
                        qq={
                            "sent": False,
                            "umo": "",
                            "error": f"{type(exc).__name__}",
                        },
                    )
                finally:
                    self.interactions.finish(request)

    HOME_PLACE_WORDS = (
        "家",
        "客厅",
        "卧室",
        "厨房",
        "浴室",
        "卫生间",
        "阳台",
        "书房",
        "餐厅",
        "玄关",
        "健身室",
        "健身房",
        "衣帽间",
        "画室",
        "影音室",
        "露台",
        "楼梯厅",
        "洗衣房",
        "储藏室",
        "花园",
        "车库",
        "小屋",
        "公寓",
        "宿舍",
        "出租屋",
    )
    AWAY_PLACE_WORDS = (
        "路上",
        "街",
        "超市",
        "公园",
        "公司",
        "学校",
        "地铁",
        "公交",
        "出差",
        "旅行",
        "机场",
        "车站",
        "酒店",
        "民宿",
        "商场",
        "菜市场",
    )

    def _is_home_place(self, location: str, activity: str = "") -> bool:
        place = str(location or "").strip()
        if not place:
            return True
        if any(word in place for word in self.AWAY_PLACE_WORDS):
            return False
        return any(word in place for word in self.HOME_PLACE_WORDS)

    async def _handle_interaction(self, request: dict, config: dict) -> None:
        persona = await self.personas.resolve(None)
        now = self._now()
        affection_action = str(request.get("affection_action") or "")
        action_thresholds = {
            "headpat": 100,
            "handhold": 250,
            "hug": 450,
            "kiss": 650,
        }
        if affection_action in action_thresholds:
            target_persona = (
                str(request.get("persona") or "").strip() or persona.id
            )
            relation = affection.snapshot(
                self.data_dir, target_persona, now=now
            )
            required = action_thresholds[affection_action]
            if int(relation.get("score") or 0) < required:
                result = {
                    "speech": "现在还不太熟呢，等我们再亲近一点吧。",
                    "detail": "",
                    "mood": "",
                    "dish": None,
                    "rejected": True,
                    "affection_action": affection_action,
                    "score": int(relation.get("score") or 0),
                    "required": required,
                }
                qq = await self._sync_interaction_qq(request, result, config)
                self.interactions.write_response(request, result, qq=qq)
                logger.info(
                    "[虚拟人生] 关系动作被拒绝 action=%s score=%s required=%s",
                    affection_action,
                    relation.get("score"),
                    required,
                )
                return
        plan = self.storage.get_plan(now.date().isoformat(), persona.id)
        current = timeline_item_at(plan, now) if plan is not None else None
        active = request.get("current") or {}
        place_kind = str(active.get("kind") or "").strip()
        place = str(
            active.get("location") or getattr(current, "location", "") or ""
        ).strip()
        activity = str(active.get("activity") or getattr(current, "activity", "") or "")
        away = (
            place_kind not in ("", "home")
            if place_kind
            else not self._is_home_place(place, activity)
        )
        if away and str(request.get("item_id") or "").strip():
            where = place or "外面"
            result = {
                "speech": f"我还在外面呢（{where}），等回家再碰这些吧。",
                "detail": "",
                "mood": "",
                "dish": None,
            }
            qq = await self._sync_interaction_qq(request, result, config)
            self.interactions.write_response(request, result, qq=qq)
            logger.info(
                "[虚拟人生] 互动被拒绝：她不在家 location=%s item=%s",
                where,
                request.get("item_id"),
            )
            return
        user_sleeping = self._detect_user_sleep(request, now)
        if not user_sleeping and self.user_states.is_sleeping(now):
            # 主人在观察窗里点了别的东西（或打字说话），说明已经起来活动了。
            self.user_states.clear()
            logger.info("[虚拟人生] 主人在观察窗活动，清除睡眠状态")
        history_text, history_items = await self._interaction_history(config)
        avoid_lines = (
            self.interactions.recent_assistant_texts(history_items, 4)
            if config.get("repeat_guard", True)
            else []
        )
        recent_gifts = self.interactions.recent_gifts(3, hours=48)
        system, user = self.interactions.build_prompt(
            request,
            persona_prompt=persona.prompt,
            persona_name=persona.id,
            location=str(getattr(current, "location", "") or ""),
            activity=str(getattr(current, "activity", "") or ""),
            now_text=now.strftime("%H:%M"),
            ingredients=self._interaction_ingredients(),
            history=history_text,
            avoid_lines=avoid_lines,
            recent_gifts=recent_gifts,
            away=away,
            user_sleeping=user_sleeping,
            settings=config,
        )
        raw = await self.plan_generator.complete(
            user, system, f"interaction_{request.get('id', 'x')}"
        )
        result = self.interactions.parse_reply(raw, config)
        if avoid_lines and self.interactions.is_repetitive(
            result.get("speech", ""), avoid_lines
        ):
            logger.info(
                "[虚拟人生] 互动回复与前文重复，重写一次 id=%s speech=%s",
                request.get("id"),
                result.get("speech"),
            )
            system, user = self.interactions.build_prompt(
                request,
                persona_prompt=persona.prompt,
                persona_name=persona.id,
                location=str(getattr(current, "location", "") or ""),
                activity=str(getattr(current, "activity", "") or ""),
                now_text=now.strftime("%H:%M"),
                ingredients=self._interaction_ingredients(),
                history=history_text,
                avoid_lines=avoid_lines + [str(result.get("speech") or "")],
                recent_gifts=recent_gifts,
                away=away,
                user_sleeping=user_sleeping,
                settings=config,
            )
            raw_retry = await self.plan_generator.complete(
                user, system, f"interaction_retry_{request.get('id', 'x')}"
            )
            retry = self.interactions.parse_reply(raw_retry, config)
            if not self.interactions.is_repetitive(
                retry.get("speech", ""), avoid_lines
            ):
                result = retry
        if str(request.get("kind") or "") == "dish":
            usage = self.interactions.consume_dish(result.get("dish"), config)
            if usage["used"] or usage["missing"]:
                result["used"] = usage["used"]
                result["missing"] = usage["missing"]
                logger.info(
                    "[虚拟人生] 互动做菜扣减库存 dish=%s used=%s missing=%s",
                    (result.get("dish") or {}).get("name"),
                    [f"{item['name']}x{item['amount']}" for item in usage["used"]],
                    usage["missing"],
                )
        if str(request.get("action") or "") != "give":
            self._maybe_queue_give_request(
                str(result.get("speech") or ""), persona.id, now
            )
        await self._insert_interaction_activity(request, result, config)
        qq = await self._sync_interaction_qq(request, result, config)
        action_points = {
            "headpat": 2,
            "handhold": 3,
            "hug": 4,
            "kiss": 6,
        }
        affection_action = str(request.get("affection_action") or "")
        if affection_action in action_points:
            result["affection_points"] = action_points[affection_action]
        payload = self.interactions.write_response(request, result, qq=qq)
        await self._record_interaction_turn(request, result, config)
        try:
            kind = str(request.get("kind") or "")
            action = str(request.get("action") or "")
            affection_action = str(request.get("affection_action") or "")
            action_points = {
                "headpat": 2,
                "handhold": 3,
                "hug": 4,
                "kiss": 6,
            }
            points = (
                action_points[affection_action]
                if affection_action in action_points
                else 4
                if action == "give"
                else 2
                if kind in ("dish", "game")
                else 1
            )
            affection.add(
                self.data_dir,
                persona.id,
                points,
                f"观察窗互动：{affection_action or kind or action or '聊天'}",
                now=self._now(),
            )
        except Exception as exc:
            logger.debug("[虚拟人生] 增加好感失败: %s", exc)
        logger.info(
            "[虚拟人生] 互动完成 id=%s kind=%s qq=%s speech=%s",
            payload.get("id"),
            payload.get("kind"),
            qq.get("sent"),
            payload.get("speech"),
        )

    async def _record_interaction_turn(
        self, request: dict, result: dict, config: dict
    ) -> None:
        """把这次观察窗互动写回 QQ 会话，下一轮普通聊天才接得上。"""
        if not config.get("record_to_conversation", True):
            return
        umo = self._interaction_umo(config)
        speech = str(result.get("speech") or "").strip()
        if not umo or not speech:
            return
        dish = (result.get("dish") or {}).get("name") or ""
        item_name = str(request.get("item_name") or "").strip()
        action = str(request.get("action") or "").strip()
        kind = str(request.get("kind") or "").strip()
        if kind == "dish":
            user_text = f"（在观察窗里走到{item_name or '餐桌'}旁边，让你做点吃的）"
            if dish:
                user_text += f"最后做的是{dish}"
        elif kind == "game":
            game_name = str(request.get("game_name") or "小游戏").strip()
            user_text = f"（在观察窗里和你玩了一局{game_name}）"
        elif action == "give":
            gift_text = str(request.get("text") or "").strip()
            if gift_text.startswith("（") and "）" in gift_text:
                gift_text = gift_text.split("）", 1)[1].strip()
            user_text = (
                f"（在观察窗里把{item_name or '东西'}递给你）"
                + (gift_text or "喏，给你。")
            )
        else:
            user_text = f"（在观察窗里对你说）{request.get('text') or ''}"
        try:
            manager = self.context.conversation_manager
            conversation_id = await manager.get_curr_conversation_id(umo)
            if not conversation_id:
                return
            await manager.add_message_pair(
                conversation_id,
                {"role": "user", "content": [{"type": "text", "text": user_text}]},
                {"role": "assistant", "content": [{"type": "text", "text": speech}]},
            )
            logger.debug("[虚拟人生] 互动已写入对话历史 umo=%s", umo)
        except Exception as exc:
            logger.warning("[虚拟人生] 写入互动历史失败 umo=%s: %s", umo, exc)

    USER_SLEEP_PATTERN = (
        "晚安", "睡了", "去睡", "睡觉", "上床", "困了", "休息", "闭眼", "躺下"
    )
    USER_WAKE_PATTERN = ("我醒了", "睡醒", "醒了", "起床", "早安", "我起了")

    def _detect_user_sleep(self, request: dict, now: datetime) -> bool:
        """观察窗里点床说「我上床睡了」时，记录主人在睡觉；说醒则清除。"""
        text = str(request.get("text") or "")
        item = str(request.get("item_name") or "")
        item_id = str(request.get("item_id") or "")
        is_bed = item_id == "bed" or "床" in item
        wants_sleep = any(word in text for word in self.USER_SLEEP_PATTERN)
        wants_wake = any(word in text for word in self.USER_WAKE_PATTERN)
        if wants_wake:
            if self.user_states.is_sleeping(now):
                self.user_states.clear()
                logger.info("[虚拟人生] 主人醒了，清除睡眠状态")
            return False
        if is_bed and wants_sleep:
            self.user_states.set_sleeping(now, place="卧室的床上", source="window")
            logger.info("[虚拟人生] 记录主人在床上睡觉 text=%s", text[:40])
            return True
        return False

    def _update_user_state_from_message(self, text: str, now: datetime) -> None:
        message = str(text or "")
        if not message:
            return
        if any(word in message for word in self.USER_WAKE_PATTERN):
            if self.user_states.is_sleeping(now):
                self.user_states.clear()
                logger.info("[虚拟人生] 主人在聊天里说自己醒了，清除睡眠状态")
            return
        sleep_hint = re.search(
            r"(我(要|去|先|准备|该|得)?去?睡|我去睡|准备睡|睡觉了|晚安|困了)",
            message,
        )
        if sleep_hint and not any(word in message for word in ("你睡", "睡得")):
            if not self.user_states.is_sleeping(now):
                self.user_states.set_sleeping(
                    now, place="QQ 聊天里说要去睡", source="chat"
                )
                logger.info("[虚拟人生] 主人在聊天里说要去睡，记录睡眠状态")

    async def _inject_user_state(
        self, event: AstrMessageEvent, req: ProviderRequest
    ) -> None:
        """普通聊天里注入主人睡眠状态，回复才会轻声。"""
        text = self.user_states.describe(self._now())
        if not text:
            return
        req.extra_user_content_parts.append(TextPart(text=text).mark_as_temp())
        logger.info("[虚拟人生] 注入主人睡眠状态 umo=%s", event.unified_msg_origin)

    async def _insert_interaction_activity(
        self, request: dict, result: dict, config: dict
    ) -> None:
        """由角色自己判断这次互动要不要写进当天日程，再决定怎么写。"""
        if not bool(config.get("insert_activity_enable", True)):
            return
        if str(request.get("item_id") or "") == "bed" and any(
            word in str(request.get("text") or "") for word in self.USER_SLEEP_PATTERN
        ):
            logger.info("[虚拟人生] 主人在睡觉，跳过日程插入")
            return
        persona = await self.personas.resolve(None)
        now = self._now()
        date_str = now.date().isoformat()
        plan = self.storage.get_plan(date_str, persona.id)
        if plan is None or not plan.has_schedule:
            return
        current = timeline_item_at(plan, now)
        dish = str((result.get("dish") or {}).get("name") or "").strip()
        item_name = str(request.get("item_name") or "").strip()
        room = str(request.get("room") or "").strip()
        default_minutes = int(config.get("insert_activity_minutes", 30))
        max_minutes = int(config.get("insert_activity_max_minutes", 120))
        location = room or str(getattr(current, "location", "") or "")
        action = str(request.get("action") or "").strip()
        kind = str(request.get("kind") or "").strip()
        if dish:
            default_activity = f"和主人一起吃饭（{dish}）"
        elif kind == "game":
            game_name = str(request.get("game_name") or "小游戏").strip()
            default_activity = f"和主人玩了一局{game_name}"
            default_minutes = min(default_minutes, 10)
        elif action == "give":
            default_activity = f"接过主人递来的{item_name or '东西'}"
            default_minutes = min(default_minutes, 5)
        elif item_name:
            default_activity = f"在{room or '家'}陪主人待一会儿"
        else:
            default_activity = "和主人说说话"

        insert = True
        activity = default_activity
        minutes = default_minutes
        place = location
        reason = "direct"
        if bool(config.get("insert_activity_ai_decide", True)):
            system, user = self.interactions.build_schedule_decision_prompt(
                request,
                result,
                persona_prompt=persona.prompt,
                current_activity=str(getattr(current, "activity", "") or ""),
                current_location=str(getattr(current, "location", "") or ""),
                now_text=now.strftime("%H:%M"),
            )
            try:
                raw = await self.plan_generator.complete(
                    user, system, f"schedule_decision_{request.get('id', 'x')}"
                )
                decision = self.interactions.parse_schedule_decision(
                    raw, default_minutes=default_minutes
                )
            except Exception as exc:
                logger.warning("[虚拟人生] 日程插入判定失败: %s", exc)
                decision = {}
            if decision:
                insert = bool(decision["insert"])
                reason = decision["reason"] or "ai"
                if insert:
                    activity = decision["activity"] or default_activity
                    minutes = max(5, min(max_minutes, int(decision["minutes"])))
                    place = decision["location"] or location
            else:
                # 模型没给出可用判断时：吃饭这类明确事件保守插入，其余跳过。
                insert = bool(dish)
                reason = "fallback"
            logger.info(
                "[虚拟人生] 日程插入判定 insert=%s reason=%s activity=%s minutes=%s",
                insert,
                reason,
                activity,
                minutes,
            )
            if not insert:
                return

        try:
            updated = insert_activity(plan, now, minutes, activity, place)
        except Exception as exc:
            logger.warning("[虚拟人生] 互动活动写入日程失败: %s", exc)
            return
        try:
            key = self.storage.plan_key(date_str, persona.id)
            self.storage.plans[key] = updated
            await self.storage.save_plans()
        except Exception as exc:
            logger.warning("[虚拟人生] 保存互动日程失败: %s", exc)
            return
        logger.info(
            "[虚拟人生] 已把互动写入今日日程 activity=%s location=%s 时长=%s分钟 (reason=%s)",
            activity,
            place or "-",
            minutes,
            reason,
        )

    async def _interaction_history(self, config: dict) -> tuple[str, list]:
        """读取目标会话最近几轮聊天，供即时互动接着往下聊。

        返回 ``(格式化文本, 原始历史列表)``；后者用于反重复判断。
        """
        if int(config.get("history_messages", 0)) <= 0:
            return "", []
        umo = self._interaction_umo(config)
        if not umo:
            return "", []
        try:
            manager = self.context.conversation_manager
            conversation_id = await manager.get_curr_conversation_id(umo)
            if not conversation_id:
                return "", []
            conversation = await manager.get_conversation(umo, conversation_id)
            raw = getattr(conversation, "history", "[]")
            history = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(history, list):
                return "", []
            text = self.interactions.format_history(
                history, now=self._now(), settings=config
            )
            if text:
                logger.debug(
                    "[虚拟人生] 互动参考历史 umo=%s 行数=%s", umo, text.count("\n") + 1
                )
            return text, history
        except Exception as exc:
            logger.warning("[虚拟人生] 读取互动历史失败 umo=%s: %s", umo, exc)
            return "", []

    def _interaction_ingredients(self) -> list[str]:
        path = self.data_dir / "fridge_inventory.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        items = payload.get("ingredients", []) if isinstance(payload, dict) else []
        names: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if name:
                names.append(name)
        return names

    def _interaction_umo(self, config: dict) -> str:
        configured = str(config.get("sync_umo") or "").strip()
        if configured:
            return configured
        for key in ("friend_settings", "group_settings"):
            section = self.config.get(key, {}) or {}
            for value in section.get("session_list", []) or []:
                text = str(value).strip()
                if text:
                    return text
        return ""

    async def _sync_interaction_qq(
        self, request: dict, result: dict, config: dict
    ) -> dict:
        record: dict = {"sent": False, "umo": "", "error": ""}
        if not config["sync_to_qq"]:
            record["error"] = "disabled"
            return record
        umo = self._interaction_umo(config)
        if not umo:
            record["error"] = "no_session"
            return record
        text = self.interactions.qq_text(request, result)
        if not text:
            record["error"] = "empty"
            return record
        request_id = str(request.get("id") or "")
        if not self.interactions.claim_sent(request_id):
            logger.warning(
                "[虚拟人生] 互动已发送过，跳过重复 QQ 消息 id=%s", request_id
            )
            record["error"] = "duplicate"
            return record
        record["umo"] = umo
        try:
            sent = await self.context.send_message(umo, MessageChain().message(text))
        except Exception as exc:
            self.interactions.release_sent(request_id)
            record["error"] = f"{type(exc).__name__}: {exc}"
            logger.warning("[虚拟人生] 互动同步 QQ 失败 umo=%s: %s", umo, exc)
            return record
        if not sent:
            self.interactions.release_sent(request_id)
            record["error"] = "platform unavailable"
            return record
        record["sent"] = True
        return record

    async def _check_long_term_renewals(self, target: date) -> None:
        settings = self.config.get("long_term_settings", {}) or {}
        if not settings.get("enable", True):
            return
        persona_ids = {
            str(stage.get("persona_id", ""))
            for stage in self.long_term.stages
            if stage.get("persona_id")
        }
        for persona_id in persona_ids:
            latest = self.long_term.latest_stage(persona_id)
            if not latest:
                continue
            end = date.fromisoformat(latest["end_date"])
            if target < end or self.long_term.has_stage_starting_after(persona_id, end):
                continue
            await self._run_long_term_renewal(persona_id)

    async def _run_long_term_renewal(self, persona_id: str) -> None:
        latest = self.long_term.latest_stage(persona_id)
        target_umo = self.long_term.notification_target(persona_id)
        if not latest or not target_umo:
            return
        attempts = self.renewal_attempts.get(persona_id, 0) + 1
        self.renewal_attempts[persona_id] = attempts
        settings = self.config.get("long_term_settings", {}) or {}
        try:
            persona = await self.personas.resolve_id(persona_id, target_umo)
            start = date.fromisoformat(latest["end_date"]) + timedelta(days=1)
            stages = await self.plan_generator.generate_long_term_timeline(
                persona,
                start_date=start,
                previous_stage=latest,
                requirements="自动延续当前人物的大时间表，保持经历连续但允许进入新的学期、假期、项目或生活阶段。",
            )
            await self.long_term.add_auto_renewal(persona_id, stages)
            self.image_renderer.invalidate_persona(persona_id)
            self.renewal_attempts.pop(persona_id, None)
            await self._notify_admin(
                target_umo,
                f"人格 {persona_id} 的大时间表已自动续期："
                + "、".join(
                    f"{stage['name']}（{stage['start_date']} 至 {stage['end_date']}）"
                    for stage in stages
                ),
            )
        except Exception as exc:
            await self._notify_admin(
                target_umo,
                f"人格 {persona_id} 的大时间表自动续期失败（第 {attempts} 次）：{exc}",
            )
            maximum = max(1, int(settings.get("renewal_max_attempts", 6)))
            if attempts >= maximum:
                return
            delay = max(1, int(settings.get("renewal_retry_minutes", 60)))
            self.runtime.add_date_job(
                f"pvd:long-term-renewal:{hashlib.sha1(persona_id.encode()).hexdigest()[:12]}",
                self._now() + timedelta(minutes=delay),
                self._run_long_term_renewal,
                persona_id,
            )

    async def _notify_admin(self, umo: str, text: str) -> None:
        try:
            await self.context.send_message(umo, MessageChain().message(text))
        except Exception as exc:
            logger.error("[虚拟人生] 管理员通知发送失败 %s: %s", umo, exc)

    def _scheduled_proactive_entries(
        self, umo: str, plan: DailyPlan
    ) -> list[tuple[datetime, str]]:
        job_times = dict(self.runtime.scheduled_jobs())
        umo_hash = self._umo_hash(umo)
        plan_prefix = f"pvd:{umo_hash}:plan:"
        windows = {window.id: window for window in plan.proactive_windows}
        entries: list[tuple[datetime, str]] = []

        idle_time = job_times.get(f"pvd:{umo_hash}:idle")
        if idle_time:
            entries.append((idle_time, "沉默主动"))

        for job_id, run_at in job_times.items():
            if not job_id.startswith(plan_prefix):
                continue
            suffix = job_id[len(plan_prefix) :]
            if suffix == "sleep":
                entries.append((run_at, "睡眠异常主动"))
            elif suffix.startswith("window-retry:"):
                window_id = suffix.removeprefix("window-retry:")
                window = windows.get(window_id)
                label = f"延迟窗口 [{window_id}]"
                entries.append(
                    (run_at, label + (f" · {window.intent}" if window else ""))
                )
            elif suffix.startswith("window:"):
                window_id = suffix.removeprefix("window:")
                window = windows.get(window_id)
                label = f"日程窗口 [{window_id}]"
                entries.append(
                    (run_at, label + (f" · {window.intent}" if window else ""))
                )

        return sorted(entries, key=lambda item: (item[0], item[1]))

    async def _refresh_persona_daily_plan(self, persona: PersonaContext) -> DailyPlan:
        plan = await self._ensure_plan(
            persona,
            self._now().date(),
            force=True,
            preserve_disabled=True,
        )
        for umo in self.policy.enabled_sessions():
            resolved = await self.personas.resolve(umo)
            if resolved.id == persona.id:
                await self._schedule_session(umo, resolved, plan)
        return plan

    async def _create_long_term_draft(
        self,
        *,
        persona: PersonaContext,
        admin_umo: str,
        requirements: str,
        start_date: date,
        previous_stage: dict | None,
        source: str,
        mode: str,
    ) -> dict:
        stages = await self.plan_generator.generate_long_term_timeline(
            persona,
            start_date=start_date,
            previous_stage=previous_stage,
            requirements=requirements,
        )
        draft = await self.long_term.set_draft(
            persona.id,
            stages,
            source=source,
            admin_umo=admin_umo,
            created_at=self._now().isoformat(),
            requirements=requirements,
            mode=mode,
        )
        self.image_renderer.invalidate_persona(persona.id)
        return draft

    async def _image_view_results(
        self, event: AstrMessageEvent, title: str, fallback: str, jobs
    ) -> list:
        if not self.image_renderer.enabled:
            return [event.plain_result(fallback)]
        try:
            paths = [await job() for job in jobs]
        except Exception:
            logger.exception("[虚拟人生] 图片渲染失败，回退文字输出")
            return [event.plain_result("图片渲染失败，已切换为文字模式。\n" + fallback)]
        return [
            event.plain_result(title),
            *(event.image_result(path) for path in paths),
        ]

    @staticmethod
    def _parse_long_term_json(content: str, persona_id: str) -> list[dict]:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"结构化数据不是合法 JSON：{exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("结构化数据必须是 JSON 对象")
        if "stages" not in payload:
            payload = {"stages": [payload]}
        return validate_stage_bundle(payload, persona_id)

    async def _prepare_reply_delay(
        self,
        event: AstrMessageEvent,
    ) -> None:
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            event.set_extra("virtual_life_reply_delay_excluded", True)
            return
        excluded = event.get_extra("provider_request") is not None
        event.set_extra("virtual_life_reply_delay_excluded", excluded)
        if excluded:
            return
        if not self.reply_delay_policy.enabled:
            return
        try:
            received_at = datetime.fromtimestamp(float(event.created_at), self.timezone)
        except (AttributeError, TypeError, ValueError, OSError):
            received_at = self._now()
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
        except Exception:
            logger.exception("[虚拟人生] 回复延迟跳过：人格解析失败")
            return
        plan = self.storage.get_plan(received_at.date().isoformat(), persona.id)
        if not plan or not plan.has_schedule:
            logger.info(
                "[虚拟人生] 回复延迟跳过：内存中没有有效日程 persona=%s date=%s",
                persona.id,
                received_at.date().isoformat(),
            )
            return
        arrival_item = timeline_item_at(plan, received_at)
        if arrival_item is None:
            return

        active = self.reply_delay_coordinator.is_active(
            event.unified_msg_origin,
            received_at,
        )
        decision = self.reply_delay_policy.decide(
            arrival_item,
            received_at,
            len(event.get_message_str()),
            active_conversation=active,
            needs=self._life_needs(plan, received_at),
        )
        queued = QueuedMessage(
            received_at=received_at,
            sender_id=event.get_sender_id(),
            sender_name=event.get_sender_name(),
            prompt=str(event.get_message_str() or ""),
            image_urls=self._message_media_urls(event, Image),
            audio_urls=self._message_media_urls(event, Record),
            temporary_files=tuple(
                str(path)
                for path in getattr(event, "_temporary_local_files", ())
                if path
            ),
        )
        batch, primary = await self.reply_delay_coordinator.enqueue(
            event.unified_msg_origin,
            queued,
            decision,
            arrival_item,
            extend_seconds=(
                self.reply_delay_policy.merge_window_seconds
                if self.reply_delay_policy.merge_extend
                else 0
            ),
            max_total_seconds=self.reply_delay_policy.max_merge_seconds,
        )
        if batch is None:
            return
        if not primary:
            self._detach_temporary_files(event, queued.temporary_files)
            event.stop_event()
            logger.info(
                "[虚拟人生] 消息已加入回复延迟批次 umo=%s queued=%s deadline=%s",
                event.unified_msg_origin,
                len(batch.messages),
                batch.deadline.isoformat(),
            )
            return

        if decision.delay_seconds > 0 and self.reply_delay_policy.notify_user:
            notification = self.reply_delay_policy.notification(decision)
            if notification:
                try:
                    await self.context.send_message(
                        event.unified_msg_origin,
                        MessageChain().message(notification),
                    )
                except Exception:
                    logger.exception("[虚拟人生] 回复延迟提示发送失败")

        messages = await self.reply_delay_coordinator.settle(batch, self._now())
        settled_at = self._now()
        event.set_extra("virtual_life_reply_delay_batch", batch)
        event.set_extra("virtual_life_reply_delay_messages", messages)
        event.set_extra("virtual_life_reply_delay_persona_id", persona.id)
        event.set_extra("virtual_life_reply_delay_settled_at", settled_at)
        logger.info(
            "[虚拟人生] 回复延迟批次开始结算 umo=%s availability=%s planned=%ss actual=%ss queued=%s",
            event.unified_msg_origin,
            decision.availability,
            decision.delay_seconds,
            max(0, int((settled_at - batch.created_at).total_seconds())),
            len(messages),
        )

    @staticmethod
    def _message_media_urls(
        event: AstrMessageEvent, media_type: type
    ) -> tuple[str, ...]:
        components = []
        for component in event.get_messages():
            components.append(component)
            if isinstance(component, Reply) and component.chain:
                components.extend(component.chain)
        urls = []
        for component in components:
            if not isinstance(component, media_type):
                continue
            value = component.path or component.url or component.file
            if value and str(value) not in urls:
                urls.append(str(value))
        return tuple(urls)

    @staticmethod
    def _detach_temporary_files(
        event: AstrMessageEvent,
        temporary_files: tuple[str, ...],
    ) -> None:
        tracked = getattr(event, "_temporary_local_files", None)
        if not isinstance(tracked, list):
            return
        for path in temporary_files:
            while path in tracked:
                tracked.remove(path)

    def _apply_reply_delay_batch(
        self,
        event: AstrMessageEvent,
        req: ProviderRequest,
    ) -> None:
        batch = event.get_extra("virtual_life_reply_delay_batch")
        messages = event.get_extra("virtual_life_reply_delay_messages")
        settled_at = event.get_extra("virtual_life_reply_delay_settled_at")
        persona_id = event.get_extra("virtual_life_reply_delay_persona_id")
        if not batch or not messages or not isinstance(settled_at, datetime):
            return
        req.prompt = format_queued_messages(
            messages,
            group=session_kind(event.unified_msg_origin) == "group",
        )
        req.image_urls = [url for message in messages for url in message.image_urls]
        req.audio_urls = [url for message in messages for url in message.audio_urls]
        for message in messages:
            for path in message.temporary_files:
                event.track_temporary_local_file(path)
        current_plan = self.storage.get_plan(
            settled_at.date().isoformat(),
            str(persona_id),
        )
        current_item = (
            timeline_item_at(current_plan, settled_at)
            if current_plan and current_plan.has_schedule
            else None
        )
        delay_context = format_delay_context(batch, settled_at, current_item)
        req.extra_user_content_parts.append(TextPart(text=delay_context).mark_as_temp())

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE, priority=999)
    async def on_friend_message(self, event: AstrMessageEvent) -> None:
        await self._handle_incoming(event)

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE, priority=998)
    async def on_group_message(self, event: AstrMessageEvent) -> None:
        await self._handle_incoming(event)

    def _is_conversation_event(self, event: AstrMessageEvent) -> bool:
        if event.get_extra("handlers_parsed_params", None):
            return False
        handlers = event.get_extra("activated_handlers", None) or []
        for handler in handlers:
            for event_filter in getattr(handler, "event_filters", None) or []:
                if isinstance(
                    event_filter, (CommandFilter, CommandGroupFilter, RegexFilter)
                ):
                    return False
        return True

    def _schedule_private_only(self) -> bool:
        settings = self.config.get("schedule_settings", {}) or {}
        return bool(settings.get("private_only", True))

    def _schedule_available_for_umo(self, umo: str) -> bool:
        """日程、日程注入、回复延迟和主动消息只对私聊会话生效。"""
        if not umo:
            return False
        return not self._schedule_private_only() or session_kind(umo) == "friend"

    @staticmethod
    def _give_action_label(text: str) -> str | None:
        raw = str(text or "").strip()
        if not raw:
            return None
        for pattern in GIVE_INTENT_PATTERNS:
            match = pattern.search(raw)
            if not match:
                continue
            item = str(match.group("item") or "").strip().lstrip("了着过点个些")
            item = re.sub(
                r"^(?:盒|杯|瓶|袋|份|碗|盘|罐|串|块|颗)(?=.)", "", item
            )
            item = item.rstrip("吧啊呀哦嘛呢啦呗")
            if not item or item in ("东西", "礼物"):
                return "把东西递给月月"
            return f"把{item}递给月月"
        return None

    def _known_gift_item_names(self, persona_id: str | None = None) -> list[str]:
        """收集家具名和持有物名，用于识别月月请求里要递的东西。"""
        names: set[str] = set()
        try:
            items, _ = view_state.load_home_items(self.data_dir / "plans.json")
            names.update(
                str(item.get("name") or "").strip()
                for item in items
                if str(item.get("name") or "").strip()
            )
        except Exception:
            pass
        if persona_id:
            try:
                snapshot = money.snapshot(self.data_dir, persona_id)
                names.update(
                    str(item.get("name") or "").strip()
                    for item in snapshot.get("possessions") or []
                    if str(item.get("name") or "").strip()
                )
            except Exception:
                pass
        return sorted(names, key=len, reverse=True)

    def _maybe_queue_give_request(
        self,
        text: str,
        persona_id: str,
        now: datetime,
    ) -> dict | None:
        """月月主动请主人递东西时，给观察窗补一个待处理按钮。"""
        label = _requested_gift_label(
            text, self._known_gift_item_names(persona_id)
        )
        if not label:
            return None
        try:
            action = view_state.queue_pending_action(
                self.data_dir / "plans.json",
                persona=persona_id,
                label=label,
                source=f"月月请求：{text[:120]}",
                now=now,
            )
            logger.info(
                "[虚拟人生] 月月请求递东西，已准备观察窗按钮 label=%s", label
            )
            return action
        except Exception as exc:
            logger.warning("[虚拟人生] 准备月月请求按钮失败: %s", exc)
            return None

    async def _maybe_queue_give_action(self, event: AstrMessageEvent, now: datetime) -> None:
        """私聊出现「拿东西给他/她/月月」时，给观察窗准备一个按钮。"""
        if session_kind(event.unified_msg_origin) != "friend":
            return
        if not (self._interaction_settings().get("enable", True)):
            return
        text = str(event.get_message_str() or "").strip()
        label = self._give_action_label(text)
        if not label:
            return
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            view_state.queue_pending_action(
                self.data_dir / "plans.json",
                persona=persona.id,
                label=label,
                source=text,
                now=now,
            )
            logger.info(
                "[虚拟人生] 已准备观察窗递东西按钮 umo=%s label=%s",
                event.unified_msg_origin,
                label,
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 准备递东西按钮失败: %s", exc)

    async def _handle_incoming(self, event: AstrMessageEvent) -> None:
        umo = event.unified_msg_origin
        if not self.policy.is_enabled(umo):
            return
        if not self._is_conversation_event(event):
            logger.debug("[虚拟人生] 命令消息不计入空闲计时 umo=%s", umo)
            return
        now = self._now()
        if session_kind(umo) == "friend":
            # 群聊消息不能改写主人的睡眠状态，否则会影响私聊和日程。
            self._update_user_state_from_message(str(event.get_message_str() or ""), now)
            await self._maybe_queue_give_action(event, now)
        self._mark_conversation_activity(umo, now)
        self.policy.record_incoming(umo, now)
        await self.storage.save_sessions()
        self._schedule_idle(umo)

    @filter.on_agent_begin()
    async def mark_agent_active(self, event: AstrMessageEvent, _run_context) -> None:
        umo = event.unified_msg_origin
        self._active_agent_counts[umo] = self._active_agent_counts.get(umo, 0) + 1
        self._mark_conversation_activity(umo)

    @filter.on_agent_done()
    async def defer_agent_release(
        self,
        event: AstrMessageEvent,
        _run_context,
        _response: LLMResponse | None,
    ) -> None:
        umo = event.unified_msg_origin
        if _response is not None:
            reply_text = str(getattr(_response, "completion_text", "") or "").strip()
            if reply_text and session_kind(umo) == "friend":
                try:
                    persona = await self.personas.resolve(umo)
                    self._maybe_queue_give_request(
                        reply_text, persona.id, self._now()
                    )
                except Exception as exc:
                    logger.debug(
                        "[虚拟人生] 检查月月递东西请求失败: %s", exc
                    )
        task = asyncio.create_task(self._release_agent_after_history_save(umo))
        self._agent_release_tasks.add(task)
        task.add_done_callback(self._agent_release_tasks.discard)

    @filter.on_waiting_llm_request()
    async def queue_reply_delay(self, event: AstrMessageEvent) -> None:
        await self._prepare_reply_delay(event)

    def _group_life_context(self, plan: DailyPlan, now: datetime) -> str:
        """群聊只暴露生理与心情，不带日程、地点、穿搭和家具。"""
        needs = self._life_needs(plan, now)
        labels = needs.get("labels") if isinstance(needs, dict) else {}
        if not isinstance(labels, dict):
            return ""
        parts = []
        for key, title in (
            ("energy", "精力"),
            ("satiety", "饱腹"),
            ("hygiene", "清洁"),
            ("hydration", "水分"),
            ("mood", "心情"),
            ("willingness", "意愿"),
            ("health", "健康"),
        ):
            value = str(labels.get(key) or "").strip()
            if value:
                parts.append(f"{title}{value}")
        if not parts:
            return ""
        text = "【当前生理与心情】" + "；".join(parts)
        illness = str(needs.get("illness_label") or "").strip()
        if illness:
            text += f"；{illness}"
        elif needs.get("sick"):
            text += "；正在生病"
        elif needs.get("recovering"):
            text += "；病后恢复中"
        states = []
        if needs.get("morning_grogginess") and not needs.get(
            "morning_grogginess_relief"
        ):
            states.append("昨晚没睡够，早上有点懵")
        if needs.get("afternoon_dip") and not needs.get("afternoon_dip_relief"):
            states.append("午后有点犯困")
        if needs.get("evening_sleepiness"):
            states.append("这个点有点困了")
        if states:
            text += "；" + "、".join(states)
        try:
            discomfort = int(needs.get("discomfort_count") or 0)
        except (TypeError, ValueError):
            discomfort = 0
        if discomfort > 0:
            text += f"；身体有 {discomfort} 处小不适"
        return (
            text
            + "\n（这是群聊：不要主动提自己的日程、地点、穿搭或家具，"
            "只按当前生理和心情自然说话。）"
        )

    def _sanitize_group_request(
        self, req: ProviderRequest, plan=None, event=None
    ) -> None:
        """群聊请求的硬隔离：去日程工具、去旧日程上下文、加隐私规则。"""
        try:
            terms = set(GROUP_PRIVACY_TERMS)
            if plan is not None:
                terms.update(_group_plan_terms(plan))
            if event is not None:
                event.set_extra("virtual_life_group_terms", terms)
            prompt = str(getattr(req, "system_prompt", "") or "")
            if GROUP_PRIVACY_RULE not in prompt:
                req.system_prompt = (prompt + "\n\n" + GROUP_PRIVACY_RULE).strip()
            tool_set = getattr(req, "func_tool", None)
            if tool_set is not None:
                for name in (
                    "get_virtual_daily_schedule",
                    "get_long_term_timeline",
                    "add_schedule_requirement",
                    "request_money",
                    "spend_money",
                    "set_savings_goal",
                    "request_goal_reward",
                    "browse_goods",
                    "buy_goods",
                    "use_item",
                    "place_item",
                    "read_book",
                    "add_reading_note",
                    "write_diary",
                    "recall_life",
                    "drive_self",
                ):
                    try:
                        tool_set.remove_tool(name)
                    except Exception:
                        pass
            contexts = getattr(req, "contexts", None)
            if isinstance(contexts, list):
                for message in contexts:
                    if not isinstance(message, dict):
                        continue
                    if message.get("role") not in ("assistant", "tool"):
                        continue
                    text = _group_message_text(message.get("content"))
                    if any(term in text for term in terms):
                        message["content"] = "（群聊中已省略旧内容）"
        except Exception as exc:
            logger.debug("[虚拟人生] 群聊请求隔离失败: %s", exc)

    @staticmethod
    def _filter_group_recap(text: str) -> str:
        lines = [
            line
            for line in str(text or "").splitlines()
            if not any(term in line for term in GROUP_PRIVACY_TERMS)
        ]
        return "\n".join(lines).strip()

    @staticmethod
    def _filter_group_reply(text: str, extra_terms=None) -> str:
        terms = set(GROUP_OUTPUT_TERMS)
        if extra_terms:
            terms.update(str(term) for term in extra_terms if str(term).strip())
        parts = re.split(r"(?<=[。！？!?；;\n])", str(text or ""))
        kept = [
            part
            for part in parts
            if part.strip() and not any(term in part for term in terms)
        ]
        cleaned = "".join(kept).strip()
        return cleaned if cleaned else "……"

    @staticmethod
    def _plain_for_compare(text: str) -> str:
        return re.sub(r"[\s\W_]+", "", str(text or ""), flags=re.UNICODE).lower()

    @classmethod
    def _humanize_reply(
        cls, text: str, user_text: str = "", *, guard_echo: bool = True
    ) -> str:
        """去掉系统事件残留和 AI 腔格式，让回复更像真人打字。"""
        cleaned = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
        cleaned = re.sub(
            r"<system_reminder>.*?</system_reminder>",
            "",
            cleaned,
            flags=re.S,
        )
        # 整行删除带事件元数据的原始转写，例如：
        # [2026-11-04 周三 18:52:24] AI(ID:...): [戳一戳事件]你戳了...
        cleaned = re.sub(
            r"^.*?(?:AI\(ID:\d+\)|\[戳一戳事件\]|\[At:\d+\]|\[引用消息\(|\[CQ:).*$",
            "",
            cleaned,
            flags=re.M,
        )
        cleaned = re.sub(
            r"\[?\d{4}-\d{2}-\d{2}(?:\s+[^\]\n]*?)?\]\s*", "", cleaned
        )
        cleaned = re.sub(r"AI\(ID:\d+\):\s*", "", cleaned)
        cleaned = re.sub(r"\[戳一戳事件\]", "", cleaned)
        cleaned = re.sub(r"\[At:\d+\]", "", cleaned)
        cleaned = re.sub(r"\[引用消息\([^\]\n]*\)\]", "", cleaned)
        cleaned = re.sub(r"\[CQ:[^\]\n]+\]", "", cleaned)
        cleaned = re.sub(r"你戳了[^\n，。！？!?；;]*?(?:\(ID:\d+\))?", "", cleaned)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"[ \t]+(?=[。！？!?，,；;：:])", "", cleaned)
        cleaned = re.sub(r"(?<=[。！？!?，,；;：:])[ \t]+", "", cleaned)
        cleaned = re.sub(r"\n{2,}", "\n", cleaned)
        cleaned = "\n".join(
            line.strip() for line in cleaned.splitlines() if line.strip()
        ).strip()
        if (
            guard_echo
            and user_text
            and cls._plain_for_compare(cleaned)
            == cls._plain_for_compare(user_text)
        ):
            return "嗯。"
        return cleaned if cleaned else "嗯？"

    @classmethod
    def _trim_chat_flow(cls, text: str, user_text: str = "") -> str:
        """Cap private-chat replies without cutting commitments or key facts."""
        cleaned = str(text or "").strip()
        if not cleaned:
            return cleaned
        parts = [
            part.strip()
            for part in re.split(r"(?<=[。！？!?])|\n+", cleaned)
            if part.strip()
        ]
        if not parts:
            return cleaned

        protected = re.compile(
            r"(明天|后天|今天|今晚|明早|下周|周[一二三四五六日天]|"
            r"穿|戴|搭配|配饰|裙|裤|开衫|外套|鞋|袜子|"
            r"耳坠|耳环|项链|发夹|发型|颜色|银色|金色|银|金|"
            r"日程|安排|地点|几点|时间|约会|见面|回家|出门|"
            r"吃药|医院|生病|身体|安全|钱|付款|买|"
            r"定了|定好|我会|答应|记得|提醒|取消|推迟|改到)"
        )
        nag = re.compile(
            r"^(你|先|别|记得|下次|赶紧|去|把|要不|不是|"
            r"还有|顺便|对了|另外)"
        )
        ack_words = {"行", "好", "嗯", "知道了", "行吧", "可以", "没事"}
        short_ack = re.sub(r"\s+", "", str(user_text or ""))
        if short_ack in ack_words:
            first = parts[0]
            match = re.match(
                r"^(行|好|嗯|知道了|可以|没事)[，,。！!\s]+(.+)$", first
            )
            if match:
                tail = match.group(2).strip()
                if tail and protected.search(tail):
                    return first
                if tail and re.search(
                    r"(把|别|先|去|你|再|记得|赶紧|顺便|还有)", tail
                ):
                    return match.group(1) + "。"
                if not tail:
                    return match.group(1) + "。"
            if len(first) <= 6:
                return first

        kept: list[str] = []
        for part in parts:
            if not kept:
                kept.append(part)
                continue
            is_protected = bool(protected.search(part))
            is_nag = bool(nag.match(part))
            if is_protected:
                if part not in kept:
                    kept.append(part)
                continue
            if len(kept) < 2 and not is_nag:
                kept.append(part)
        return "".join(kept[:5]).strip() or cleaned

    async def _inject_group_life_state(
        self, event: AstrMessageEvent, req: ProviderRequest
    ) -> None:
        self._sanitize_group_request(req, event=event)
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
        except Exception:
            return
        now = self._now()
        plan = self.storage.get_plan(now.date().isoformat(), persona.id)
        if plan is None or not plan.has_schedule:
            return
        self._sanitize_group_request(req, plan=plan, event=event)
        text = self._group_life_context(plan, now)
        if not text:
            return
        req.extra_user_content_parts.append(TextPart(text=text).mark_as_temp())
        logger.info(
            "[虚拟人生] 群聊仅注入生理心情 umo=%s", event.unified_msg_origin
        )

    async def _camera_awareness_context(self, event: AstrMessageEvent) -> str:
        """Tell the character about recent observer-window photos on the next turn."""
        try:
            message_text = str(event.get_message_str() or "").strip()
        except Exception:
            message_text = ""
        if not message_text or message_text.startswith(("/", "／")):
            return ""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            events = camera_events.take_pending(
                self.data_dir, persona.id, now=self._now(), limit=2
            )
        except Exception:
            return ""
        if not events:
            return ""
        lines = ["【刚刚拍照】主人刚刚用观察窗相机拍了照片，你是知情者："]
        for item in events:
            target = str(item.get("target") or "")
            caption = str(item.get("caption") or "").strip()
            if target == camera_photo.TARGET_CHARACTER:
                what = "拍的是你本人"
            elif target == camera_photo.TARGET_ITEM:
                name = str(item.get("item_name") or "家具")
                what = f"拍的是家里的「{name}」"
            else:
                what = "拍的是当前房间"
            lines.append(f"- {what}" + (f"：{caption}" if caption else "。"))
        lines.append(
            "你已经知道这些照片存在。主人提到照片、相机或刚才拍摄时，"
            "要能自然接上；不要说自己没看见、不知道被拍，也不要主动复述这段提示。"
        )
        logger.info(
            "[虚拟人生] 注入拍照感知 persona=%s 数量=%s",
            persona.id,
            len(events),
        )
        return "\n".join(lines)

    @filter.on_llm_request()
    async def inject_virtual_state(
        self, event: AstrMessageEvent, req: ProviderRequest
    ) -> None:
        prompt = getattr(req, "system_prompt", "") or ""
        if isinstance(prompt, str) and HUMAN_CHAT_RULE.strip() not in prompt:
            req.system_prompt = prompt + HUMAN_CHAT_RULE
        if isinstance(req.system_prompt, str):
            if IMAGE_FACT_RULE.strip() not in req.system_prompt:
                req.system_prompt = req.system_prompt + IMAGE_FACT_RULE
            if SELFIE_CHAT_RULE.strip() not in req.system_prompt:
                req.system_prompt = req.system_prompt + SELFIE_CHAT_RULE
        camera_context = await self._camera_awareness_context(event)
        if camera_context:
            req.extra_user_content_parts.append(
                TextPart(text=camera_context).mark_as_temp()
            )
        schedule_allowed = self._schedule_available_for_umo(
            event.unified_msg_origin
        )
        if schedule_allowed and isinstance(req.system_prompt, str):
            if CURRENT_STATE_RULE.strip() not in req.system_prompt:
                req.system_prompt = req.system_prompt + CURRENT_STATE_RULE
        if isinstance(req.system_prompt, str):
            if REMOTE_CHAT_RULE.strip() not in req.system_prompt:
                req.system_prompt = req.system_prompt + REMOTE_CHAT_RULE
            if DIALOGUE_FLOW_RULE.strip() not in req.system_prompt:
                req.system_prompt = req.system_prompt + DIALOGUE_FLOW_RULE
            if FUTURE_OUTFIT_RULE.strip() not in req.system_prompt:
                req.system_prompt = req.system_prompt + FUTURE_OUTFIT_RULE
        pending_hint = ""
        if schedule_allowed:
            try:
                pending_persona = await self.personas.resolve(
                    event.unified_msg_origin
                )
                pending_actions = view_state.load_pending_actions(
                    self.data_dir / "plans.json", pending_persona.id
                )
                if pending_actions:
                    labels = "、".join(
                        str(action.get("label") or "递东西")
                        for action in pending_actions[:2]
                    )
                    pending_hint = (
                        "【观察窗待处理】主人之前在对话里提到要给月月东西，"
                        f"观察窗里已经出现「{labels}」按钮。可以自然提醒主人"
                        "去观察窗点一下；不要说得像系统提示。"
                    )
            except Exception:
                pending_hint = ""
        if schedule_allowed:
            self._apply_reply_delay_batch(event, req)
            if self.reply_delay_policy.enabled and not event.get_extra(
                "virtual_life_reply_delay_excluded", False
            ):
                event.set_extra("virtual_life_ordinary_llm_request", True)
            if pending_hint:
                req.extra_user_content_parts.append(
                    TextPart(text=pending_hint).mark_as_temp()
                )
            try:
                wallet_persona = await self.personas.resolve(
                    event.unified_msg_origin
                )
                await self._process_deliveries(wallet_persona, self._now())
                await self._settle_work_income(
                    wallet_persona, self._now().date() - timedelta(days=1)
                )
                await self._settle_work_income(
                    wallet_persona, self._now().date(), before=self._now()
                )
                wallet_balance = money.balance(
                    self.data_dir, wallet_persona.id
                )
                wallet_currency = str(
                    self._money_settings().get("currency") or "元"
                )
                wallet_snapshot = money.snapshot(
                    self.data_dir, wallet_persona.id, limit=3
                )
                recent_money = "；".join(
                    f"{'+' if float(item.get('amount') or 0) >= 0 else ''}"
                    f"{money.format_money(float(item.get('amount') or 0))} "
                    f"{wallet_currency} {item.get('reason') or ''}"
                    for item in wallet_snapshot.get("transactions") or []
                )
                recent_money = (
                    f"最近收支：{recent_money}。" if recent_money else ""
                )
                if float(wallet_balance) < 0:
                    balance_text = (
                        "现在欠款 "
                        f"{money.format_money(abs(float(wallet_balance)))} "
                        f"{wallet_currency}"
                    )
                else:
                    balance_text = (
                        "现在有 "
                        f"{money.format_money(wallet_balance)} "
                        f"{wallet_currency}"
                    )
                goal = wallet_snapshot.get("goal")
                goal_text = ""
                if goal:
                    wish = str(goal.get("wish") or "").strip()
                    if goal.get("fulfilled"):
                        state_text = "已经实现过了"
                    elif goal.get("achieved"):
                        state_text = "已经攒够，可以在合适的时候向主人提这个愿望"
                    else:
                        state_text = (
                            "还差 "
                            f"{money.format_money(goal['remaining'])} "
                            f"{wallet_currency}"
                        )
                    goal_text = (
                        f"存款目标是「{goal['name']}」"
                        f"{money.format_money(goal['target'])} {wallet_currency}，"
                        f"当前进度 {money.format_money(goal['progress'])}，"
                        f"{state_text}。"
                        + (
                            f"攒够后想让主人实现的愿望：{wish}。"
                            if wish
                            else ""
                        )
                    )
                possessions_text = ""
                owned = wallet_snapshot.get("possessions") or []
                if owned:
                    names = "、".join(
                        str(item.get("name") or "")
                        for item in owned[-6:]
                    )
                    possessions_text = f"你已经拥有：{names}。"
                placed_by_room: dict[str, list[str]] = {}
                for item in owned:
                    room = str(item.get("room") or "").strip()
                    if not room:
                        continue
                    placed_by_room.setdefault(room, []).append(
                        str(item.get("name") or "物品")
                    )
                placed_text = ""
                if placed_by_room:
                    placed_text = "家里摆放：" + "；".join(
                        f"{room} {'、'.join(names)}"
                        for room, names in list(placed_by_room.items())[:4]
                    ) + "。"
                delivery_text = ""
                try:
                    pending_delivery = delivery.pending_summary(
                        self.data_dir, wallet_persona.id
                    )
                    if pending_delivery:
                        delivery_text = f"快递在路上：{pending_delivery}。"
                except Exception:
                    delivery_text = ""
                recent_delivery_text = ""
                try:
                    recent_orders = delivery.recent_delivered(
                        self.data_dir,
                        wallet_persona.id,
                        now=self._now(),
                        hours=6,
                    )
                    if recent_orders:
                        names = "、".join(
                            str((order.get("goods") or {}).get("name") or "商品")
                            for order in recent_orders[-4:]
                        )
                        recent_delivery_text = f"刚刚收到快递：{names}。"
                except Exception:
                    recent_delivery_text = ""
                world_event_text = ""
                try:
                    garage_text = garage.context(
                        self.data_dir,
                        wallet_persona.id,
                        now=self._now(),
                    )
                except Exception:
                    garage_text = ""
                try:
                    current_event = world_events.recent(
                        self.data_dir,
                        wallet_persona.id,
                        self._now().date().isoformat(),
                    )
                    if current_event:
                        world_event_text = (
                            "【今天的小世界】"
                            f"{current_event.get('summary')} "
                            f"（心情 {int(current_event.get('mood') or 0):+d}）"
                        )
                except Exception:
                    world_event_text = ""
                req.extra_user_content_parts.append(
                    TextPart(
                        text=(
                            f"【你的钱包】{balance_text}。"
                            f"{goal_text}{recent_money}{possessions_text}"
                            f"{placed_text}{delivery_text}{recent_delivery_text}"
                            f"{world_event_text}"
                            f"【车库】{garage_text}"
                            "你可以正常工作赚钱，也可以花自己的钱买想要的东西；"
                            "想买东西先用 browse_goods 看价格，再用 buy_goods；"
                            "想看书用 read_book 翻内容，想记感想用 add_reading_note。"
                            "想吃、喝或使用已有物品时用 use_item；"
                            "想把东西摆进房间时用 place_item；"
                            "想回忆过去几天时用 recall_life，"
                            "找某个主题时把 keyword 一起传进去；"
                            "想自己开车出门时用 drive_self；"
                            "买的商品会先送到家。"
                            "花钱要符合实际，"
                            "只有确实在消费时才调用，不要虚构消费。"
                            "需要向主人要钱时调用 request_money，"
                            "金额合理，不要频繁开口。"
                        )
                    ).mark_as_temp()
                )
                try:
                    diary_entries = diary.list_entries(
                        self.data_dir, wallet_persona.id, limit=40
                    )
                    if diary_entries:
                        recent_diary = diary_entries[-1]
                        req.extra_user_content_parts.append(
                            TextPart(
                                text=(
                                    "【最近的日记】"
                                    f"{recent_diary.get('date')}："
                                    f"{recent_diary.get('summary')}"
                                )
                            ).mark_as_temp()
                        )
                        long_entries = [
                            entry
                            for entry in diary_entries
                            if str(entry.get("source") or "")
                            in ("weekly", "monthly", "yearly")
                        ][-3:]
                        if long_entries:
                            memory_text = "【长期记忆】"
                            for entry in long_entries:
                                memory_text += (
                                    f"\n{entry.get('date')} "
                                    f"{entry.get('title')}："
                                    f"{str(entry.get('summary') or '')[:220]}"
                                )
                            req.extra_user_content_parts.append(
                                TextPart(text=memory_text).mark_as_temp()
                            )
                        daily_entries = [
                            entry
                            for entry in diary_entries
                            if str(entry.get("source") or "")
                            in ("auto", "ai", "anniversary")
                        ][-3:]
                        if daily_entries:
                            daily_text = "【最近几天】"
                            for entry in daily_entries:
                                daily_text += (
                                    f"\n{entry.get('date')} "
                                    f"{entry.get('title')}："
                                    f"{str(entry.get('summary') or '')[:160]}"
                                )
                            req.extra_user_content_parts.append(
                                TextPart(text=daily_text).mark_as_temp()
                            )
                except Exception:
                    pass
                try:
                    relation = affection.snapshot(
                        self.data_dir,
                        wallet_persona.id,
                        now=self._now(),
                    )
                    score = int(relation.get("score") or 0)
                    if score < 100:
                        relation_hint = (
                            "你们还比较生疏，不要过度亲密，也别急着要钱要礼物。"
                        )
                    elif score < 450:
                        relation_hint = (
                            "你们已经熟悉，可以自然开玩笑、聊日常。"
                        )
                    else:
                        relation_hint = (
                            "你们关系亲近，可以更放松地撒娇、关心或开口要东西。"
                        )
                    milestones = relation.get("milestones") or []
                    milestone_text = (
                        f"最近一次关系变化：进入「{milestones[-1].get('level')}」。"
                        if milestones
                        else ""
                    )
                    anniversary_text = (
                        f"今天是你们认识第 {relation.get('days_known')} 天纪念日，"
                        "可以自然提一句。"
                        if relation.get("is_anniversary")
                        else ""
                    )
                    req.extra_user_content_parts.append(
                        TextPart(
                            text=(
                                "【你们的关系】好感度 "
                                f"{score} / 1000，"
                                f"当前阶段：{relation.get('level')}，"
                                f"认识第 {relation.get('days_known')} 天。"
                                f"你称呼主人为「{relation.get('nickname') or '主人'}」，不要叫错。"
                                f"{milestone_text}{anniversary_text}{relation_hint}"
                                "不要直接报好感度数字。"
                            )
                        ).mark_as_temp()
                    )
                except Exception:
                    pass
            except Exception:
                pass
        await self._inject_recent_chat(event, req)
        if not schedule_allowed:
            await self._inject_group_life_state(event, req)
            return
        await self._inject_user_state(event, req)
        if not self.smart_context_injector.enabled:
            return
        try:
            persona, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        except RuntimeError:
            return
        if plan.status != "ok":
            return
        now = self._now()
        current_item = next(
            (
                item
                for item in plan.timeline
                if (
                    item.start <= now.strftime("%H:%M") < item.end
                    or item.end == "24:00"
                )
                and item.participant_ids
            ),
            None,
        )
        participant_context = ""
        if current_item and current_item.participant_ids:
            participant_context = await self._personal_network_participants_context(
                persona.id, current_item.participant_ids
            )
        if current_item and any(
            word in current_item.activity for word in ("看书", "读书", "阅读", "翻书")
        ):
            try:
                wallet = money.snapshot(
                    self.data_dir, persona.id, limit=1
                )
                reading = books.reading_context(
                    current_item.activity,
                    wallet.get("possessions") or [],
                    data_dir=self.data_dir,
                    persona=persona.id,
                )
                if reading:
                    req.extra_user_content_parts.append(
                        TextPart(text=reading).mark_as_temp()
                    )
            except Exception:
                pass
        reading_item = next(
            (
                item
                for item in plan.timeline
                if (
                    item.start <= now.strftime("%H:%M") < item.end
                    or item.end == "24:00"
                )
                and any(
                    word in item.activity
                    for word in ("看书", "读书", "阅读", "翻书")
                )
            ),
            None,
        )
        if reading_item is not None and reading_item is not current_item:
            try:
                wallet = money.snapshot(
                    self.data_dir, persona.id, limit=1
                )
                reading = books.reading_context(
                    reading_item.activity,
                    wallet.get("possessions") or [],
                    data_dir=self.data_dir,
                    persona=persona.id,
                )
                if reading:
                    req.extra_user_content_parts.append(
                        TextPart(text=reading).mark_as_temp()
                    )
            except Exception:
                pass
        furniture_states, furniture_context = self._furniture_activity_context(now)
        health_summary = str(self._life_needs(plan, now).get("summary") or "")
        injection, modules, limit = self.smart_context_injector.build_details(
            plan,
            now,
            self.long_term,
            event.get_message_str(),
            participant_context=participant_context,
            furniture_context=furniture_context,
            furniture_states=furniture_states,
            history_plans=self._life_history_plans(plan),
            health_summary=health_summary,
        )
        if injection:
            req.extra_user_content_parts.append(TextPart(text=injection).mark_as_temp())
            logger.info(
                "[虚拟人生] 智能状态注入 persona=%s modules=%s chars=%s limit=%s\n%s",
                plan.persona_id,
                ",".join(modules),
                len(injection),
                limit,
                injection,
            )

    # ------------------------------------------------------------ 对话回顾

    def _furniture_activity_context(self, now) -> tuple[dict, str]:
        """Read live furniture state for normal chat and proactive context."""
        try:
            plans_path = self.data_dir / "plans.json"
            states = furniture_state.live_states(plans_path, now=now)
            context = furniture_state.furniture_context(plans_path, "", now=now)
        except (OSError, ValueError, TypeError):
            return {}, ""
        return states, context

    def _life_needs(self, plan, now, *, update_journal: bool = True) -> dict:
        """Current physiological snapshot including recent furniture effects."""
        furniture_states, _context = self._furniture_activity_context(now)
        try:
            journal_state = health_journal.persona_state(
                self.data_dir,
                str(getattr(plan, "persona_id", "") or "角色"),
                today=now.date(),
            )
            needs = life_state.compute(
                plan,
                now,
                furniture_states=furniture_states,
                history_plans=self._life_history_plans(plan),
                weak_constitution=bool(journal_state.get("weak_constitution")),
                recent_illness_days=int(
                    journal_state.get("recent_illness_days") or 0
                ),
            )
            if not update_journal:
                status = str(journal_state.get("status") or "healthy")
                needs["health_status"] = status
                needs["sick"] = status == "sick" or bool(needs.get("sick"))
                needs["recovering"] = status == "recovering" or bool(
                    needs.get("recovering")
                )
                if status == "sick":
                    needs["illness_label"] = "正在生病"
                elif status == "recovering":
                    needs["illness_label"] = "病后恢复中"
                return needs
            needs = health_journal.update(
                self.data_dir,
                str(getattr(plan, "persona_id", "") or "角色"),
                needs,
                now,
            )
            adjusted = item_effects.apply(
                self.data_dir,
                str(getattr(plan, "persona_id", "") or "角色"),
                needs,
                now,
            )
            try:
                mood_history.record(
                    self.data_dir,
                    str(getattr(plan, "persona_id", "") or "角色"),
                    adjusted,
                    now=now,
                )
            except Exception:
                pass
            return adjusted
        except (OSError, TypeError, ValueError):
            return {}

    def _life_history_plans(self, plan) -> list:
        """Recent plans used for sleep-debt continuity."""
        try:
            return sorted(
                (
                    value
                    for value in self.storage.plans.values()
                    if getattr(value, "persona_id", "") == getattr(plan, "persona_id", "")
                    and getattr(value, "date", "") < getattr(plan, "date", "")
                ),
                key=lambda value: value.date,
            )[-3:]
        except (AttributeError, TypeError, ValueError):
            return []

    def _chat_recall_settings(self) -> dict:
        return self.config.get("chat_recall_settings", {}) or {}

    async def _inject_recent_chat(
        self, event: AstrMessageEvent, req: ProviderRequest
    ) -> None:
        """普通聊天回复前，把最近一段时间的对话塞回上下文。

        AstrBot 自己会带历史，但长对话里早期消息会被截断；这里补一段
        时间窗内的短回顾，避免「聊到一半像失忆」。
        """
        if session_kind(event.unified_msg_origin) == "group":
            return
        settings = self._chat_recall_settings()
        if not bool(settings.get("enable", True)):
            return
        try:
            minutes = int(settings.get("minutes", 60))
            messages = int(settings.get("messages", 6))
            chars = int(settings.get("chars", 400))
        except (TypeError, ValueError):
            return
        if minutes <= 0 or messages <= 0:
            return
        recap = await self._recent_chat_lines(
            event.unified_msg_origin, minutes, messages, chars
        )
        interaction_recap = self._recent_interaction_lines(3)
        if session_kind(event.unified_msg_origin) == "group":
            recap = self._filter_group_recap(recap)
        if not recap and not interaction_recap:
            return
        hint = "接着上面的话题说，不要重复已经说过的话，也不要主动提更早的事；"
        if interaction_recap:
            hint += (
                "刚才互动里说过的菜、动作和事都还是同一段对话；"
                "主人现在说“给你加个菜/给你煮了吃的”，指的就是刚才那道菜，"
                "先认出并回应那道菜，不要当成新话题或装作没发生；"
            )
        if "主动发起" in recap:
            hint += (
                "标着「你（主动发起）」的是你自己主动找对方说的话，"
                "对方现在多半就是在接那条：先接住它的内容（认下、反驳、追问都行），"
                "别当没说过，也别重新介绍一遍自己的处境；"
            )
        hint += (
            "如果上面已经说过自己在做什么，就别再复述同一个动作或细节，"
            "换个角度说或者聊对方的事。"
        )
        text = f"【你们最近聊的（大约 {minutes} 分钟内）】\n{recap}\n{hint}"
        if interaction_recap:
            text += f"\n\n【刚才的互动】\n{interaction_recap}"
        req.extra_user_content_parts.append(TextPart(text=text).mark_as_temp())
        logger.info(
            "[虚拟人生] 对话回顾注入 umo=%s 行数=%s 字数=%s 互动=%s",
            event.unified_msg_origin,
            recap.count("\n") + 1,
            len(text),
            bool(interaction_recap),
        )

    def _recent_interaction_lines(self, limit: int = 3) -> str:
        """把最近几次观察窗互动带给普通聊天，接住刚才的菜/动作。"""
        try:
            items = self.interactions.recent(limit)
            now = self._now()
        except Exception:
            return ""
        cutoff = now - timedelta(minutes=45)
        lines = []
        for item in items:
            if not isinstance(item, dict):
                continue
            speech = str(item.get("speech") or "").strip()
            if not speech:
                continue
            at = str(item.get("at") or "").strip()
            try:
                at_time = datetime.fromisoformat(at)
            except (TypeError, ValueError):
                at_time = None
            if at_time is not None:
                if at_time.tzinfo is None and now.tzinfo is not None:
                    at_time = at_time.replace(tzinfo=now.tzinfo)
                if at_time < cutoff:
                    continue
            clock = at[11:16] if len(at) >= 16 else at
            item_name = str(item.get("item_name") or "").strip()
            action = str(item.get("action") or "").strip()
            where = "·".join(part for part in (item_name, action) if part)
            prefix = f"{clock} " if clock else ""
            lines.append(
                f"{prefix}{where + '，' if where else ''}你回：{speech}"
            )
        return "\n".join(lines)

    async def _recent_chat_lines(
        self, umo: str, minutes: int, messages: int, chars: int
    ) -> str:
        if not umo:
            return ""
        try:
            manager = self.context.conversation_manager
            conversation_id = await manager.get_curr_conversation_id(umo)
            if not conversation_id:
                return ""
            conversation = await manager.get_conversation(umo, conversation_id)
            raw = getattr(conversation, "history", "[]")
            history = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(history, list):
                return ""
            return self.interactions.format_history(
                history,
                now=self._now(),
                settings={
                    "history_minutes": minutes,
                    "history_messages": messages,
                    "history_chars": chars,
                },
            )
        except Exception as exc:
            logger.debug("[虚拟人生] 读取对话回顾失败 umo=%s: %s", umo, exc)
            return ""

    @filter.on_decorating_result(priority=90000)
    async def humanize_outgoing(self, event: AstrMessageEvent) -> None:
        result = event.get_result()
        chain = getattr(result, "chain", None) if result is not None else None
        if not chain:
            return
        user_text = ""
        getter = getattr(event, "get_message_str", None)
        if callable(getter):
            user_text = str(getter() or "")
        else:
            user_text = str(getattr(event, "message_str", "") or "")
        changed = False
        new_chain = []
        for component in chain:
            if isinstance(component, Plain):
                text = str(component.text or "")
                cleaned = self._humanize_reply(
                    text, user_text, guard_echo=False
                )
                if cleaned != text:
                    component.text = cleaned
                    changed = True
                if not component.text:
                    continue
            new_chain.append(component)
        if changed:
            try:
                result.chain = new_chain
            except Exception:
                pass

    @filter.on_llm_response()
    async def track_delayed_llm_response(
        self,
        event: AstrMessageEvent,
        response: LLMResponse | None,
    ) -> None:
        reply_text = ""
        if response is not None:
            reply_text = str(response.completion_text or "").strip()
            if reply_text:
                if session_kind(event.unified_msg_origin) == "group":
                    filtered = self._filter_group_reply(
                        reply_text,
                        extra_terms=event.get_extra(
                            "virtual_life_group_terms", ()
                        ),
                    )
                    if filtered != reply_text:
                        try:
                            response.completion_text = filtered
                        except Exception:
                            pass
                        reply_text = filtered
                user_text = ""
                getter = getattr(event, "get_message_str", None)
                if callable(getter):
                    user_text = str(getter() or "")
                else:
                    user_text = str(getattr(event, "message_str", "") or "")
                humanized = self._humanize_reply(reply_text, user_text)
                if session_kind(event.unified_msg_origin) != "group":
                    humanized = self._trim_chat_flow(humanized, user_text)
                if humanized != reply_text:
                    try:
                        response.completion_text = humanized
                    except Exception:
                        pass
                    reply_text = humanized
                event.set_extra("virtual_life_chat_reply_text", reply_text)
        if not event.get_extra("virtual_life_ordinary_llm_request", False):
            return
        if reply_text:
            event.set_extra("virtual_life_ordinary_llm_succeeded", True)

    @filter.after_message_sent()
    async def maybe_schedule_chat_activity(self, event: AstrMessageEvent) -> None:
        """消息发出后，异步判断要不要把聊天里的确定活动/菜谱补进日程。"""
        try:
            settings = self._chat_schedule_settings()
        except Exception:
            return
        if not bool(settings.get("enable", True)):
            return
        if event.get_extra("virtual_life_chat_activity_scheduled", False):
            return
        event.set_extra("virtual_life_chat_activity_scheduled", True)
        if not self._is_conversation_event(event):
            return
        umo = event.unified_msg_origin
        if not umo:
            return
        if not self._schedule_available_for_umo(umo):
            return
        if bool(settings.get("private_only", True)) and session_kind(umo) != "friend":
            return
        user_text = str(event.get_message_str() or "").strip()
        reply_text = str(
            event.get_extra("virtual_life_chat_reply_text") or ""
        ).strip()
        if not user_text or not reply_text:
            return
        if not chat_schedule_events.looks_relevant(
            user_text + "\n" + reply_text, settings
        ):
            return
        task = asyncio.create_task(
            self._detect_chat_activity(umo, user_text, reply_text)
        )
        self._chat_schedule_tasks.add(task)
        task.add_done_callback(self._chat_schedule_tasks.discard)

    @filter.after_message_sent()
    async def mark_active_conversation(self, event: AstrMessageEvent) -> None:
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return
        if not event.get_extra("virtual_life_ordinary_llm_succeeded", False):
            return
        self.reply_delay_coordinator.mark_replied(
            event.unified_msg_origin,
            self._now(),
            self.reply_delay_policy.active_conversation_seconds,
        )

    # ------------------------------------------------ 聊天日程自动补写（内部）
    def _chat_schedule_settings(self) -> dict[str, Any]:
        return chat_schedule_events.settings(
            self.config.get("chat_schedule_settings", {}) or {}
        )

    async def _detect_chat_activity(
        self, umo: str, user_text: str, reply_text: str
    ) -> None:
        if not self._schedule_available_for_umo(umo):
            return
        settings = self._chat_schedule_settings()
        if not bool(settings.get("enable", True)):
            return
        async with self._chat_schedule_lock:
            try:
                await self._run_chat_activity_detection(
                    umo, user_text, reply_text, settings
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(
                    "[虚拟人生] 聊天日程判定失败 umo=%s: %s", umo, exc
                )

    async def _run_chat_activity_detection(
        self,
        umo: str,
        user_text: str,
        reply_text: str,
        settings: dict[str, Any],
    ) -> None:
        now = self._now()
        date_str = now.date().isoformat()
        persona = await self.personas.resolve(umo)
        plan = self.storage.get_plan(date_str, persona.id)
        if plan is None or not plan.has_schedule:
            return
        current = timeline_item_at(plan, now)
        if (
            bool(settings.get("skip_when_sleeping", True))
            and current is not None
            and current.state == "sleep"
        ):
            return
        state = self.chat_schedule_state.load()
        if not chat_schedule_events.allow_check(state, umo, now, settings):
            return
        chat_schedule_events.mark_checked(state, umo, now)
        food = self.plan_generator.food
        menu = food.latest_menu(now.date(), persona.id)
        history_text = await self._recent_chat_lines(
            umo,
            int(settings.get("history_minutes") or 0),
            int(settings.get("history_messages") or 0),
            900,
        )
        system, prompt = chat_schedule_events.build_detection_prompt(
            persona_prompt=persona.prompt,
            now=now,
            current_activity=str(getattr(current, "activity", "") or ""),
            current_location=str(getattr(current, "location", "") or ""),
            schedule_text=chat_schedule_events.format_schedule_text(plan, now),
            menu_text=chat_schedule_events.format_menu_text(menu),
            history_text=history_text,
            user_text=user_text,
            reply_text=reply_text,
        )
        raw = await self.plan_generator.complete(
            prompt,
            system,
            f"chat_schedule_{self._umo_hash(umo)}_{int(now.timestamp())}",
        )
        decision = chat_schedule_events.parse_detection(
            raw,
            default_minutes=int(settings.get("default_minutes") or 30),
            max_minutes=int(settings.get("max_minutes") or 120),
        )
        schedule_decision = decision.get("schedule") or {}
        food_decision = decision.get("food") or {}
        plan_changed = False
        food_applied = False
        old_dish = ""
        new_dish = str(food_decision.get("dish") or "").strip()
        if (
            bool(food_decision.get("update"))
            and bool(settings.get("update_menu", True))
            and menu
            and new_dish
        ):
            food_state = food.load_state()
            old_dish, menu_changed = chat_schedule_events.update_menu_state(
                food_state,
                menu_key=f"{date_str}::{persona.id}",
                date_str=date_str,
                persona_id=persona.id,
                meal=str(food_decision.get("meal") or ""),
                dish=new_dish,
                ingredients=list(food_decision.get("ingredients") or []),
                method=str(food_decision.get("method") or ""),
                now=now,
            )
            if menu_changed:
                food.save_state(food_state)
                food_applied = True
                if (
                    bool(settings.get("update_plan_text", True))
                    and old_dish
                    and new_dish
                ):
                    plan, replaced = chat_schedule_events.replace_dish_in_timeline(
                        plan, old_dish, new_dish
                    )
                    plan_changed = plan_changed or replaced
        schedule_inserted = False
        if bool(schedule_decision.get("insert")) and bool(
            settings.get("insert_activity", True)
        ):
            activity = str(schedule_decision.get("activity") or "").strip()
            minutes = int(
                schedule_decision.get("minutes")
                or settings.get("default_minutes")
                or 30
            )
            location = str(schedule_decision.get("location") or "").strip()
            max_inserts = int(settings.get("max_inserts_per_day") or 0)
            if activity and max_inserts > 0 and (
                chat_schedule_events.count_schedule_inserts_today(state, date_str)
                >= max_inserts
            ):
                logger.info(
                    "[虚拟人生] 聊天日程：今日插入已达上限 %s，跳过 activity=%s",
                    max_inserts,
                    activity,
                )
            elif activity and chat_schedule_events.recently_inserted(
                state, umo, activity, now
            ):
                logger.info(
                    "[虚拟人生] 聊天日程：近期已插入过相近活动，跳过 activity=%s",
                    activity,
                )
            elif activity:
                moment = chat_schedule_events.resolve_start(
                    now, schedule_decision.get("start")
                )
                if chat_schedule_events.schedule_has_similar(
                    plan, activity, moment, minutes
                ):
                    logger.info(
                        "[虚拟人生] 聊天日程：当前日程已有相近活动，跳过 activity=%s",
                        activity,
                    )
                else:
                    try:
                        plan = insert_activity(
                            plan,
                            moment,
                            minutes,
                            activity,
                            location
                            or str(getattr(current, "location", "") or ""),
                        )
                    except Exception as exc:
                        logger.warning(
                            "[虚拟人生] 聊天日程写入失败 activity=%s: %s",
                            activity,
                            exc,
                        )
                    else:
                        plan_changed = True
                        schedule_inserted = True
                        chat_schedule_events.record_insert(
                            state,
                            umo=umo,
                            activity=activity,
                            kind="schedule",
                            now=now,
                        )
        if plan_changed:
            self.storage.plans[self.storage.plan_key(date_str, persona.id)] = plan
            await self.storage.save_plans()
        self.chat_schedule_state.save(state)
        logger.info(
            "[虚拟人生] 聊天日程判定 umo=%s insert=%s food=%s activity=%s "
            "start=%s meal=%s dish=%s reason=%s",
            umo,
            schedule_inserted,
            food_applied,
            str(schedule_decision.get("activity") or "")[:40],
            str(schedule_decision.get("start") or ""),
            str(food_decision.get("meal") or ""),
            new_dish,
            str(
                schedule_decision.get("reason")
                or food_decision.get("reason")
                or ""
            )[:60],
        )

    @filter.llm_tool(name="get_virtual_daily_schedule")
    async def get_virtual_daily_schedule(self, event: AstrMessageEvent) -> str:
        """查询机器人当前人格的完整虚拟日程、穿搭与当前活动。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "虚拟日程系统仅在私聊生效，群聊中不提供日程查询。"
        _, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if plan.status != "ok":
            return "今日没有日程和穿搭。"
        return format_plan(plan, self._now())

    @filter.llm_tool(name="set_future_outfit")
    async def set_future_outfit(
        self,
        event: AstrMessageEvent,
        when: str,
        outfit: str,
        accessories: str = "",
    ) -> str:
        """当主人指定未来某天的穿搭、衣服或配饰时调用。

        Args:
            when (str): 日期，支持今天/明天/后天或 YYYY-MM-DD。
            outfit (str): 明确的衣服、裙裤、鞋子等穿搭要求。
            accessories (str): 耳饰、项链、发饰等配饰要求，可留空。
        """
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不记录未来穿搭，私聊再说。"
        today = self._now().date()
        when_text = str(when or "").strip()
        aliases = {
            "今天": 0,
            "今日": 0,
            "明天": 1,
            "明日": 1,
            "后天": 2,
            "后日": 2,
        }
        try:
            if when_text in aliases:
                start = end = today + timedelta(days=aliases[when_text])
            else:
                start, end = parse_schedule_date_range(when_text, today)
        except ValueError as exc:
            return f"日期无法识别：{exc}。"
        outfit_text = str(outfit or "").strip()
        accessories_text = str(accessories or "").strip()
        if not outfit_text and not accessories_text:
            return "穿搭要求不能为空。"
        if end < today:
            return "只能记录今天或之后的穿搭。"
        if len(outfit_text) + len(accessories_text) > 500:
            return "穿搭要求太长了，精简到 500 字以内。"
        persona = await self.personas.resolve(event.unified_msg_origin)
        requirement_text = (
            f"【仅限穿搭，不要改动日程】{start.isoformat()} 至 {end.isoformat()}："
            f"{outfit_text or '保持日常穿搭'}"
            + (f"；配饰：{accessories_text}" if accessories_text else "")
            + "。耳鳍、尾巴等身体特征保持不变。"
        )
        for offset in range((end - start).days + 1):
            target = start + timedelta(days=offset)
            existing = self.storage.get_plan(target.isoformat(), persona.id)
            if existing and existing.has_schedule:
                active = self.storage.active_schedule_requirements(
                    persona.id, target
                )
                if len(active) >= 10:
                    return f"{target.isoformat()} 已有太多日程要求，无法再记录。"
        item = ScheduleRequirement(
            id=uuid.uuid4().hex[:12],
            persona_id=persona.id,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            requirement=requirement_text,
            created_at=self._now().isoformat(),
        )
        self.storage.schedule_requirements[item.id] = item
        try:
            await self.storage.save_plans()
        except Exception as exc:
            self.storage.schedule_requirements.pop(item.id, None)
            logger.warning(
                "[虚拟人生] 未来穿搭要求保存失败 persona=%s: %s",
                persona.id,
                exc,
            )
            return "穿搭要求保存失败，请检查日志后重试。"
        return (
            f"已记住 {start.isoformat()}"
            + (f" 至 {end.isoformat()}" if end != start else "")
            + " 的穿搭要求。"
        )

    @filter.llm_tool(name="take_selfie")
    async def take_selfie(
        self, event: AstrMessageEvent, action: str = ""
    ) -> str:
        """想给主人看现在的自己时调用；action 可写表情、姿势或想展示的东西。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            now = self._now()
            state = view_state.build_state(
                self.data_dir / "plans.json", persona.id, now=now
            )
            if not isinstance(state, dict) or state.get("ok") is False:
                return "现在没有可拍到的状态。"
            persona_visual = ""
            try:
                persona_visual = camera_photo.persona_visual_from_prompt(
                    str(getattr(persona, "prompt", "") or "")
                )
            except Exception:
                persona_visual = ""
            result = await camera_photo.generate(
                self,
                state,
                target=camera_photo.TARGET_CHARACTER,
                persona_visual=persona_visual,
                extra_prompt=str(action or "").strip()[:300],
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 自拍生成失败: %s", exc)
            return "这次没拍成，等会儿再试。"
        if not isinstance(result, dict) or not result.get("ok"):
            return str(
                (result or {}).get("error") if isinstance(result, dict) else ""
            ) or "这次没拍成，等会儿再试。"
        image_data = str(result.get("image") or "")
        try:
            if image_data.startswith("data:image") and "," in image_data:
                component = Image.fromBase64(image_data.split(",", 1)[1])
            elif image_data.startswith(("http://", "https://")):
                component = Image.fromURL(image_data)
            else:
                component = Image.fromFileSystem(image_data)
            sent = await self.context.send_message(
                event.unified_msg_origin,
                MessageChain(chain=[component]),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 自拍发送失败: %s", exc)
            return "照片生成了，但发送失败。"
        if not sent:
            return "照片生成了，但当前平台发送失败。"
        return "已经把照片发到聊天里了。你可以自然补一句，也可以不说。"

    @filter.llm_tool(name="request_money")
    async def request_money(
        self, event: AstrMessageEvent, amount: float, reason: str = ""
    ) -> str:
        """当你想向主人要点钱时调用；金额单位为元，最多 1000。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不能向主人要钱，私聊再说。"
        try:
            value = round(float(amount), 2)
        except (TypeError, ValueError):
            return "金额必须是数字。"
        if value <= 0:
            return "要钱的金额必须大于 0。"
        value = min(value, 1000.0)
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            pending = view_state.load_pending_actions(
                self.data_dir / "plans.json", persona.id
            )
            if any(
                str(action.get("kind") or "") == "money"
                for action in pending
            ):
                return "你已经有一个要钱按钮在观察窗里了，等主人处理完再开口。"
            label = "给月月一点钱"
            action = view_state.queue_pending_action(
                self.data_dir / "plans.json",
                persona=persona.id,
                label=label,
                source=(
                    f"月月想跟你要点钱（她想要约 "
                    f"{money.format_money(value)} 元）："
                    f"{str(reason or '').strip() or '没有说明'}"
                ),
                kind="money",
                amount=value,
                reason=str(reason or "").strip(),
                now=self._now(),
            )
            balance = money.balance(self.data_dir, persona.id)
        except Exception as exc:
            logger.warning("[虚拟人生] 发起要钱请求失败: %s", exc)
            return "要钱请求暂时发不出去，等会儿再试。"
        return (
            f"已向主人发起要钱请求：{action.get('label')}。"
            "主人可以在观察窗里自己填写金额给你。"
            f"你当前钱包余额是 {money.format_money(balance)} 元。"
        )

    @filter.llm_tool(name="spend_money")
    async def spend_money(
        self, event: AstrMessageEvent, amount: float, reason: str = ""
    ) -> str:
        """花自己钱包里的钱买东西或支付开销；金额单位为元，单次最多 500。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不能花钱，私聊再说。"
        settings = self._money_settings()
        if not bool(settings.get("enable_spending", True)):
            return "现在不能花钱。"
        try:
            value = round(float(amount), 2)
        except (TypeError, ValueError):
            return "金额必须是数字。"
        if value <= 0:
            return "花钱的金额必须大于 0。"
        value = min(value, 500.0)
        reason_text = str(reason or "").strip()[:120]
        if not reason_text:
            return "要说明这笔钱花在什么地方。"
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            now = self._now()
            daily_limit = float(settings.get("daily_spend_limit", 200) or 0)
            if daily_limit > 0:
                spent_today = money.spent_on(
                    self.data_dir, persona.id, now.date().isoformat()
                )
                if spent_today + value > daily_limit:
                    return (
                        f"今天已经花了 {money.format_money(spent_today)} 元，"
                        f"每日最多 {money.format_money(daily_limit)} 元；"
                        "这笔先别花了。"
                    )
            await self._settle_work_income(
                persona, now.date(), before=now
            )
            result = await asyncio.to_thread(
                money.spend,
                self.data_dir,
                persona.id,
                value,
                reason_text,
                kind="spend",
                at=now,
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 花钱失败: %s", exc)
            return "这笔钱暂时花不出去，等会儿再试。"
        if not result.get("ok"):
            return (
                f"{result.get('error') or '余额不足'}，"
                f"你现在只有 {money.format_money(result.get('balance') or 0)} 元。"
            )
        return (
            f"已花 {money.format_money(result['amount'])} 元：{reason_text}。"
            f"钱包余额 {money.format_money(result['balance'])} 元。"
        )

    @filter.llm_tool(name="browse_goods")
    async def browse_goods(
        self, event: AstrMessageEvent, category: str = ""
    ) -> str:
        """浏览可购买的商品，可按分类筛选，例如饮品、书籍、数码、穿搭。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不能逛商店，私聊再说。"
        items = goods.list_goods(category, limit=80)
        if not items:
            return "这个分类下暂时没有商品。"
        return "商店里有：\n" + goods.format_goods(items)

    @filter.llm_tool(name="buy_goods")
    async def buy_goods(
        self,
        event: AstrMessageEvent,
        goods_id: str,
        quantity: int = 1,
    ) -> str:
        """购买商品时调用；goods_id 可用 browse_goods 获得，quantity 默认 1。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不能买东西，私聊再说。"
        settings = self._money_settings()
        if not bool(settings.get("enable_spending", True)):
            return "现在不能花钱。"
        item = goods.find_goods(goods_id)
        if item is None:
            return "没有这件商品，先用 browse_goods 看看。"
        try:
            count = max(1, min(int(quantity or 1), 5))
        except (TypeError, ValueError):
            count = 1
        amount = round(float(item.get("price") or 0.0) * count, 2)
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            now = self._now()
            daily_limit = float(settings.get("daily_spend_limit", 200) or 0)
            if daily_limit > 0:
                spent_today = money.spent_on(
                    self.data_dir, persona.id, now.date().isoformat()
                )
                if spent_today + amount > daily_limit:
                    return (
                        f"今天已经花了 {money.format_money(spent_today)} 元，"
                        f"每日最多 {money.format_money(daily_limit)} 元；"
                        "这件先别买了。"
                    )
            await self._settle_work_income(
                persona, now.date(), before=now
            )
            result = await asyncio.to_thread(
                goods.purchase,
                self.data_dir,
                persona.id,
                str(item.get("id") or goods_id),
                count,
                at=now,
                delivery_minutes=int(
                    settings.get("delivery_minutes", 3) or 0
                ),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 购买商品失败: %s", exc)
            return "这笔钱暂时花不出去，等会儿再试。"
        if not result.get("ok"):
            return (
                f"{result.get('error') or '买不了'}，"
                f"你现在只有 {money.format_money(result.get('balance') or 0)} 元。"
            )
        if result.get("delivery"):
            order = result.get("order") or {}
            delivery_at = str(order.get("deliver_at") or "")[11:16]
            return (
                f"下单了 {result['goods'].get('name')} ×{result['quantity']}，"
                f"花了 {money.format_money(result['amount'])} 元。"
                f"预计 {delivery_at} 送到家，到时候会自动放进物品里。"
                f"钱包余额 {money.format_money(result['balance'])} 元。"
            )
        return (
            f"买了 {result['goods'].get('name')} ×{result['quantity']}，"
            f"花了 {money.format_money(result['amount'])} 元。"
            f"钱包余额 {money.format_money(result['balance'])} 元。"
        )

    @filter.llm_tool(name="use_item")
    async def use_item(
        self, event: AstrMessageEvent, item: str
    ) -> str:
        """使用自己的物品，例如喝奶茶、吃拉面、穿新衣服、摆弄相机。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不能用物品，私聊再说。"
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            result = await asyncio.to_thread(
                goods.use_item,
                self.data_dir,
                persona.id,
                item,
                at=self._now(),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 使用物品失败: %s", exc)
            return "这件东西暂时用不了，等会儿再试。"
        if not result.get("ok"):
            return result.get("error") or "没有这件东西。"
        used = result.get("item") or {}
        effects = result.get("effects") or {}
        effect_text = "、".join(
            f"{key} {value:+g}" for key, value in effects.items()
        )
        if result.get("consumed"):
            return (
                f"用掉了{used.get('name') or '物品'}。"
                + (f"身体反馈：{effect_text}。" if effect_text else "")
            )
        return (
            f"用了一下{used.get('name') or '物品'}。"
            + (f"现在的感受：{effect_text}。" if effect_text else "")
        )

    @filter.llm_tool(name="place_item")
    async def place_item(
        self, event: AstrMessageEvent, item: str, room: str
    ) -> str:
        """把物品摆到家里的房间，例如相机摆在书房。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不能摆东西，私聊再说。"
        allowed = {"卧室", "浴室", "书房", "客厅", "厨房", "阳台"}
        room_name = str(room or "").strip()
        if room_name not in allowed:
            return "房间只能是：卧室、浴室、书房、客厅、厨房、阳台。"
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            result = await asyncio.to_thread(
                money.place_possession,
                self.data_dir,
                persona.id,
                item,
                room_name,
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 摆放物品失败: %s", exc)
            return "这件东西暂时摆不出去。"
        if not result.get("ok"):
            return result.get("error") or "没有这件东西。"
        return (
            f"把{result['item'].get('name') or '物品'}摆到了{room_name}。"
        )

    @filter.llm_tool(name="recall_life")
    async def recall_life(
        self,
        event: AstrMessageEvent,
        days: int = 7,
        keyword: str = "",
    ) -> str:
        """回忆过去几天的日记和生活统计，可按关键词筛选，days 可选 1-60。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不回忆私人生活，私聊再说。"
        try:
            span = max(1, min(int(days or 7), 60))
        except (TypeError, ValueError):
            span = 7
        keyword = str(keyword or "").strip()[:30]
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            now = self._now()
            entries = [
                entry
                for entry in diary.list_entries(
                    self.data_dir, persona.id, limit=80
                )
                if str(entry.get("date") or "")
                >= (now.date() - timedelta(days=span - 1)).isoformat()
            ]
            if keyword:
                entries = [
                    entry
                    for entry in entries
                    if keyword
                    in (
                        str(entry.get("title") or "")
                        + str(entry.get("summary") or "")
                    )
                ]
            report = weekly.build(
                self.data_dir,
                persona.id,
                now=now,
                days=min(span, 30),
            )
            if keyword:
                report["entries"] = [
                    entry
                    for entry in report.get("entries") or []
                    if keyword
                    in (
                        str(entry.get("title") or "")
                        + str(entry.get("summary") or "")
                    )
                ]
        except Exception as exc:
            logger.warning("[虚拟人生] 回忆生活失败: %s", exc)
            return "这段时间的记忆暂时翻不出来。"
        if keyword:
            lines = [f"关于「{keyword}」最近 {span} 天的记录："]
        else:
            lines = [f"最近 {span} 天："]
        lines.append(weekly.format_report(report))
        if entries:
            lines.append("日记：")
            for entry in entries[-6:]:
                lines.append(
                    f"· {entry.get('date')} {entry.get('title')}："
                    f"{str(entry.get('summary') or '')[:160]}"
                )
        else:
            lines.append(
                "没有找到相关日记。"
                if keyword
                else "这几天没有写日记。"
            )
        return "\n".join(lines)

    @filter.llm_tool(name="drive_self")
    async def drive_self(
        self, event: AstrMessageEvent, destination: str = "兜风"
    ) -> str:
        """月月想自己开车出门时调用，destination 是目的地。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不能自己开车出门，私聊再说。"
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            now = self._now()
            result = garage.start(
                self.data_dir,
                persona.id,
                str(destination or "兜风"),
                "self",
                now=now,
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 自己开车失败: %s", exc)
            return "车暂时开不出去。"
        if not result.get("ok"):
            return str(result.get("error") or "车暂时开不出去。")
        trip = result.get("trip") or {}
        try:
            plan = self.storage.get_plan(now.date().isoformat(), persona.id)
            if plan is not None:
                updated = insert_garage_trip(plan, trip, now)
                self.storage.plans[
                    self.storage.plan_key(now.date().isoformat(), persona.id)
                ] = updated
                await self.storage.save_plans()
        except Exception as exc:
            logger.warning("[虚拟人生] 自己开车写入日程失败: %s", exc)
        eta = str(trip.get("eta") or "")
        eta_text = eta[11:16] if len(eta) >= 16 else eta
        return (
            f"你开车出门去{trip.get('destination') or destination}了，"
            f"预计 {eta_text} 回来。路上注意安全，回来再和主人说。"
        )

    @filter.llm_tool(name="write_diary")
    async def write_diary(
        self, event: AstrMessageEvent, text: str
    ) -> str:
        """把今天的一件事或心情写进日记。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不写日记，私聊再说。"
        content = str(text or "").strip()[:800]
        if not content:
            return "日记不能是空的。"
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            now = self._now()
            diary.add_entry(
                self.data_dir,
                persona.id,
                now.date().isoformat(),
                "今天",
                content,
                source="ai",
                now=now,
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 写日记失败: %s", exc)
            return "日记暂时写不进去，等会儿再试。"
        return "已经把这件事写进今天的日记了。"

    @filter.llm_tool(name="read_book")
    async def read_book(
        self, event: AstrMessageEvent, book: str, chapter: int = 0
    ) -> str:
        """翻看一本书的内容；book 可以是书名或 id，chapter 为 0 时接着上次读。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不看书，私聊再说。"
        item = books.find_book(book)
        if item is None:
            suggestions = "、".join(
                str(entry.get("title") or "")
                for entry in books.list_books()[:6]
            )
            return f"没找到这本书。书架上现有：{suggestions}。"
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
        except Exception:
            return "现在找不到这本书的主人。"
        chapters = item.get("chapters") or []
        total = max(1, len(chapters))
        progress = books.get_progress(
            self.data_dir, persona.id, str(item.get("id") or "")
        )
        if chapter <= 0:
            target = (
                total
                if progress.get("finished")
                else min(int(progress.get("chapter") or 0) + 1, total)
            )
        else:
            target = max(1, min(int(chapter), total))
        text = books.render_book(item, target)
        result = books.record_reading(
            self.data_dir,
            persona.id,
            str(item.get("id") or ""),
            target,
            total,
        )
        suffix = (
            "（这本已经读完了。）"
            if result.get("finished")
            else f"（读到第 {result.get('chapter')} / {total} 章。）"
        )
        return f"{text}\n\n{suffix}"

    @filter.llm_tool(name="add_reading_note")
    async def add_reading_note(
        self,
        event: AstrMessageEvent,
        book: str,
        note: str,
    ) -> str:
        """给正在读的书留一句笔记或感想。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不写读书笔记，私聊再说。"
        item = books.find_book(book)
        if item is None:
            return "没找到这本书。"
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
        except Exception:
            return "现在找不到这本书的主人。"
        result = books.add_note(
            self.data_dir,
            persona.id,
            str(item.get("id") or ""),
            note,
        )
        if not result.get("ok"):
            return result.get("error") or "笔记没写下来。"
        return f"已经把这条笔记写进《{item.get('title')}》的读书笔记里。"

    @filter.llm_tool(name="set_savings_goal")
    async def set_savings_goal_tool(
        self,
        event: AstrMessageEvent,
        name: str,
        target: float,
        wish: str = "",
    ) -> str:
        """给自己设置一个存钱目标，例如相机 500；wish 是攒够后想让主人实现的事。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不能设置存款目标，私聊再说。"
        goal_name = str(name or "").strip()[:40]
        try:
            target_value = round(float(target), 2)
        except (TypeError, ValueError):
            return "目标金额必须是数字。"
        if not goal_name:
            return "要说明存款目标是什么。"
        if target_value <= 0 or target_value > 100000:
            return "目标金额需要在 0 到 100000 元之间。"
        wish_text = str(wish or "").strip()[:120]
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            result = await asyncio.to_thread(
                money.set_goal,
                self.data_dir,
                persona.id,
                goal_name,
                target_value,
                wish=wish_text,
                at=self._now(),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 设置存款目标失败: %s", exc)
            return "存款目标暂时设不了，等会儿再试。"
        if not result.get("ok"):
            return result.get("error") or "设置失败。"
        return (
            f"已把「{goal_name}」设为存款目标，"
            f"目标 {money.format_money(target_value)} 元。"
            + (
                f"攒够后想让主人实现：{wish_text}。"
                if wish_text
                else "攒够后可以来向主人提愿望。"
            )
            + "之后可以慢慢攒钱，别乱花。"
        )

    @filter.llm_tool(name="request_goal_reward")
    async def request_goal_reward(self, event: AstrMessageEvent) -> str:
        """存款目标达成后，向主人提出实现愿望的请求。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "群聊里不能提愿望，私聊再说。"
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            snapshot = money.snapshot(
                self.data_dir, persona.id, limit=1
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 提愿望失败: %s", exc)
            return "愿望暂时提不出去，等会儿再试。"
        goal = snapshot.get("goal")
        if not goal:
            return "你还没有存款目标。"
        if goal.get("fulfilled"):
            return "这个愿望已经实现过了。"
        if not goal.get("achieved"):
            return (
                f"还没攒够，当前 {money.format_money(goal.get('progress') or 0)}，"
                f"还差 {money.format_money(goal.get('remaining') or 0)} 元。"
            )
        pending = view_state.load_pending_actions(
            self.data_dir / "plans.json", persona.id
        )
        if any(
            str(action.get("kind") or "") == "wish"
            for action in pending
        ):
            return "愿望按钮已经在观察窗里了，等主人处理。"
        wish = str(goal.get("wish") or "").strip()
        reason = wish or f"攒钱买{goal.get('name')}"
        try:
            view_state.queue_pending_action(
                self.data_dir / "plans.json",
                persona=persona.id,
                label=f"实现月月的愿望：{goal.get('name')}",
                source=(
                    f"月月攒够了 {money.format_money(goal.get('target') or 0)} 元，"
                    f"想让你实现：{reason}"
                ),
                kind="wish",
                amount=float(goal.get("target") or 0),
                reason=reason,
                now=self._now(),
            )
            money.mark_goal_requested(
                self.data_dir, persona.id, at=self._now()
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 生成愿望按钮失败: %s", exc)
            return "愿望按钮暂时生成不了，等会儿再试。"
        return (
            f"已向主人提出愿望：{reason}。"
            "观察窗里会出现按钮，主人点一下就能实现。"
        )

    @filter.llm_tool(name="get_long_term_timeline")
    async def get_long_term_timeline(self, event: AstrMessageEvent) -> str:
        """查询机器人当前人格全部已批准的大时间表阶段。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "虚拟日程系统仅在私聊生效，群聊中不提供大时间表查询。"
        persona = await self.personas.resolve(event.unified_msg_origin)
        stages = self.long_term.list_for_persona(persona.id)
        if not stages:
            return "当前人格没有已批准的大时间表。"
        enriched = [self.long_term.with_holidays(stage) for stage in stages]
        return json.dumps(
            {"persona_id": persona.id, "stages": enriched}, ensure_ascii=False, indent=2
        )

    async def get_virtual_life_snapshot(self, umo: str) -> dict[str, Any]:
        """供其他插件读取当前虚拟生活状态（只读，不触发日程生成）。

        This is a stable, read-only interface for other plugins (for example the
        image plugin that renders chat selfies). It only reads the in-memory
        plan cache: it never calls ``_ensure_plan_for_umo`` and therefore never
        triggers an LLM schedule generation or a plan file write.

        Args:
            umo: Unified message origin of the conversation to inspect.

        Returns:
            A JSON-serializable snapshot. ``ok`` is False with a ``reason`` when
            the persona cannot be resolved or today's plan is missing/failed.
        """
        now = self._now()
        time_text = now.strftime("%Y-%m-%d %H:%M")
        date_text = now.date().isoformat()
        try:
            persona = await self.personas.resolve(umo)
        except Exception as exc:
            logger.warning("[虚拟人生] 状态快照人格解析失败 umo=%s: %s", umo, exc)
            return {
                "ok": False,
                "reason": "persona_unavailable",
                "persona_id": "",
                "persona_name": "",
                "date": date_text,
                "time": time_text,
            }
        persona_name = str(getattr(persona, "name", "") or persona.id)
        plan = self.storage.get_plan(date_text, persona.id)
        if plan is None or plan.status != "ok":
            return {
                "ok": False,
                "reason": "no_plan",
                "persona_id": persona.id,
                "persona_name": persona_name,
                "date": date_text,
                "time": time_text,
                "timeline_count": len(plan.timeline) if plan is not None else 0,
            }
        snapshot = build_state_snapshot(plan, now)
        try:
            pose_hint = camera_photo.pose_hint_for_snapshot(snapshot)
            if pose_hint:
                snapshot["pose_hint"] = pose_hint
        except Exception:
            pass
        snapshot.update(
            {
                "ok": True,
                "persona_id": persona.id,
                "persona_name": persona_name,
                "time": time_text,
            }
        )
        return snapshot

    @filter.llm_tool(name="add_schedule_requirement")
    async def add_schedule_requirement_tool(
        self,
        event: AstrMessageEvent,
        start_date: str,
        end_date: str,
        requirement: str,
    ) -> str:
        """仅当当前管理员明确要求时，为当前人格未来日期的首次日程生成添加要求。

        Args:
            start_date(string): 开始日期，支持 YYYY-MM-DD、MM-DD 或 DD。
            end_date(string): 结束日期，支持 YYYY-MM-DD、MM-DD 或 DD；省略部分相对开始日期向后推导。
            requirement(string): 要应用于区间内每个日期首次日程生成的要求，最多 500 字。
        """
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            return "虚拟日程系统仅在私聊生效，群聊中不能修改日程要求。"
        return await self._add_schedule_requirement(
            event,
            f"{str(start_date).strip()}..{str(end_date).strip()}",
            requirement,
        )

    @filter.command_group("虚拟人生")
    def virtual_life_group(self):
        """虚拟人生命令组；不提供子命令时由 AstrBot 输出帮助。"""
        pass

    @virtual_life_group.command("订阅会话")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def subscribe_session(self, event: AstrMessageEvent):
        """订阅当前会话的主动消息。"""
        umo = event.unified_msg_origin
        added = self.policy.subscribe(umo)
        self.config.save_config()
        kind = "群聊" if session_kind(umo) == "group" else "私聊"
        action = "已订阅" if added else "已刷新订阅"
        logger.info("[虚拟人生] %s主动消息会话 umo=%s", action, umo)
        try:
            persona, plan = await self._ensure_plan_for_umo(umo)
            await self._schedule_session(umo, persona, plan)
            await self.storage.save_sessions()
        except Exception as exc:
            logger.warning("[虚拟人生] 订阅后即时调度失败 umo=%s: %s", umo, exc)
            yield event.plain_result(
                f"{action}当前{kind}会话，但今日日程调度失败，请检查日志或稍后重试。"
            )
            return
        yield event.plain_result(
            f"{action}当前{kind}会话，主动消息将在符合日程与发送规则时触发。"
        )

    @virtual_life_group.command("递东西")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def accept_pending_gift(self, event: AstrMessageEvent):
        """点击按钮失效时，用命令接受最近的递东西动作。"""
        umo = event.unified_msg_origin
        try:
            persona = await self.personas.resolve(umo)
            pending = view_state.load_pending_actions(
                self.data_dir / "plans.json", persona.id
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 读取待处理递东西失败: %s", exc)
            yield event.plain_result("读取待处理动作失败，请稍后重试。")
            return
        if not pending:
            yield event.plain_result("现在没有待处理的递东西动作。")
            return
        if not (self._interaction_settings().get("enable", True)):
            yield event.plain_result("即时互动已关闭，无法递东西。")
            return
        action = pending[0]
        label = str(action.get("label") or "把东西递给月月").strip()
        try:
            now = self._now()
            interaction = view_state.build_interaction_request(
                self.data_dir / "plans.json",
                {
                    "kind": "chat",
                    "text": f"（{label}）喏，给你。",
                    "persona": persona.id,
                },
                now=now,
            )
            view_state.write_interaction_request(
                self.data_dir / "plans.json", interaction
            )
            view_state.pop_pending_action(
                self.data_dir / "plans.json", str(action.get("id") or "")
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 命令递东西失败: %s", exc)
            yield event.plain_result("递东西失败，请稍后重试。")
            return
        logger.info(
            "[虚拟人生] 通过命令接受递东西 umo=%s action=%s",
            umo,
            label,
        )
        yield event.plain_result(
            f"已{label}，月月正在回应；观察窗里也能看到互动结果。"
        )

    @virtual_life_group.command("清空待处理")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def clear_pending_gift(self, event: AstrMessageEvent):
        """清空当前人格的待处理递东西动作。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            count = view_state.clear_pending_actions(
                self.data_dir / "plans.json", persona.id
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 清空待处理动作失败: %s", exc)
            yield event.plain_result("清空待处理动作失败，请稍后重试。")
            return
        yield event.plain_result(
            f"已清空 {count} 个待处理动作。" if count else "当前没有待处理动作。"
        )

    async def _record_garage_returns(self, persona, now) -> None:
        """Auto-returned trips become a diary entry and a little affection."""
        try:
            trips = garage.recent_returns(
                self.data_dir, persona.id, now=now, hours=36
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 检查回车记录失败: %s", exc)
            return
        for trip in trips:
            try:
                returned_at = str(trip.get("returned_at") or "")[:10]
                driver = (
                    "主人开车"
                    if trip.get("driver") == "master"
                    else "她自己开车"
                )
                day = returned_at or now.date().isoformat()
                if not diary.has_entry(self.data_dir, persona.id, day, "outing"):
                    diary.add_entry(
                        self.data_dir,
                        persona.id,
                        day,
                        "兜风回来",
                        f"{driver}带她去了{trip.get('destination') or '兜风'}，"
                        "回来的时候心情很好。",
                        source="outing",
                        now=now,
                    )
                    affection.add(
                        self.data_dir,
                        persona.id,
                        1,
                        "兜风回来",
                        now=now,
                    )
                garage.mark_noted(
                    self.data_dir, persona.id, str(trip.get("id") or "")
                )
            except Exception as exc:
                logger.warning("[虚拟人生] 记录回车失败: %s", exc)

    async def _ensure_world_event(self, persona, day) -> dict | None:
        try:
            event = world_events.get_or_create(
                self.data_dir, persona.id, day.isoformat()
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 生成今日小事失败: %s", exc)
            return None
        if event.get("created") and int(event.get("mood") or 0) != 0:
            try:
                item_effects.add(
                    self.data_dir,
                    persona.id,
                    {"mood": int(event.get("mood") or 0)},
                    label=f"今天的小事：{event.get('title')}",
                    now=self._now(),
                    ttl_minutes=12 * 60,
                )
            except Exception:
                pass
            logger.info(
                "[虚拟人生] 今日小事 persona=%s title=%s mood=%s",
                persona.id,
                event.get("title"),
                event.get("mood"),
            )
        return event

    async def _process_deliveries(self, persona, now=None) -> list[dict]:
        try:
            delivered = await asyncio.to_thread(
                delivery.deliver_due,
                self.data_dir,
                persona.id,
                now or self._now(),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 处理送货失败: %s", exc)
            return []
        if delivered:
            names = "、".join(
                str((order.get("goods") or {}).get("name") or "商品")
                for order in delivered
            )
            logger.info(
                "[虚拟人生] 送货到达 persona=%s items=%s",
                persona.id,
                names,
            )
        return delivered

    def _money_settings(self) -> dict:
        return self.config.get("money_settings", {}) or {}

    def _living_settings(self) -> dict:
        return self.config.get("living_cost_settings", {}) or {}

    async def _settle_work_income(self, persona, day, *, before=None) -> None:
        settings = self._money_settings()
        if not bool(settings.get("enable", True)):
            return
        try:
            plan = self.storage.get_plan(day.isoformat(), persona.id)
            if plan is None or not plan.has_schedule:
                return
            result = await asyncio.to_thread(
                money.settle_work_segments,
                self.data_dir,
                persona.id,
                day.isoformat(),
                plan,
                before=before,
                hourly_rate=float(settings.get("hourly_rate", 20)),
                at=self._now(),
            )
            if float(result.get("amount") or 0) > 0:
                logger.info(
                    "[虚拟人生] 工作收入结算 persona=%s date=%s minutes=%s amount=%s",
                    persona.id,
                    day.isoformat(),
                    result.get("minutes"),
                    result.get("amount"),
                )
            await self._settle_living_costs(
                persona, day, plan=plan, before=before
            )
            await self._maybe_queue_goal_wish(persona)
        except Exception as exc:
            logger.warning("[虚拟人生] 工作收入结算失败 persona=%s: %s", persona.id, exc)

    async def _settle_living_costs(
        self, persona, day, *, plan=None, before=None
    ) -> None:
        settings = self._living_settings()
        if not bool(settings.get("enable", True)):
            return
        try:
            if plan is None:
                plan = self.storage.get_plan(day.isoformat(), persona.id)
            if plan is None or not plan.has_schedule:
                return
            result = await asyncio.to_thread(
                money.settle_expense_segments,
                self.data_dir,
                persona.id,
                day.isoformat(),
                plan,
                before=before,
                breakfast=float(settings.get("breakfast", 8)),
                lunch=float(settings.get("lunch", 18)),
                dinner=float(settings.get("dinner", 22)),
                transport=float(settings.get("transport", 4)),
                at=self._now(),
            )
            if float(result.get("amount") or 0) > 0:
                logger.info(
                    "[虚拟人生] 生活开销结算 persona=%s date=%s amount=%s balance=%s",
                    persona.id,
                    day.isoformat(),
                    result.get("amount"),
                    result.get("balance"),
                )
        except Exception as exc:
            logger.warning("[虚拟人生] 生活开销结算失败 persona=%s: %s", persona.id, exc)

    async def _write_yearly_diary(self, persona, now) -> None:
        if now.month != 1 or now.day != 1:
            return
        try:
            end_day = now.date() - timedelta(days=1)
            if diary.has_entry(
                self.data_dir,
                persona.id,
                end_day.isoformat(),
                "yearly",
            ):
                return
            report = weekly.build(
                self.data_dir,
                persona.id,
                now=now - timedelta(days=1),
                days=365,
            )
            diary.add_entry(
                self.data_dir,
                persona.id,
                end_day.isoformat(),
                "这一年",
                weekly.format_report(report)[:1200],
                source="yearly",
                now=now,
            )
            logger.info(
                "[虚拟人生] 已生成年记 persona=%s end=%s",
                persona.id,
                end_day.isoformat(),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 生成年记失败: %s", exc)

    async def _write_monthly_diary(self, persona, now) -> None:
        if now.day != 1:
            return
        try:
            end_day = now.date() - timedelta(days=1)
            if diary.has_entry(
                self.data_dir,
                persona.id,
                end_day.isoformat(),
                "monthly",
            ):
                return
            report = weekly.build(
                self.data_dir,
                persona.id,
                now=now - timedelta(days=1),
                days=30,
            )
            diary.add_entry(
                self.data_dir,
                persona.id,
                end_day.isoformat(),
                "这个月",
                weekly.format_report(report)[:1200],
                source="monthly",
                now=now,
            )
            logger.info(
                "[虚拟人生] 已生成月记 persona=%s end=%s",
                persona.id,
                end_day.isoformat(),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 生成月记失败: %s", exc)

    async def _write_weekly_diary(self, persona, now) -> None:
        if now.weekday() != 0:
            return
        try:
            end_day = now.date() - timedelta(days=1)
            if diary.has_entry(
                self.data_dir,
                persona.id,
                end_day.isoformat(),
                "weekly",
            ):
                return
            report = weekly.build(
                self.data_dir,
                persona.id,
                now=now - timedelta(days=1),
                days=7,
            )
            summary = weekly.format_report(report)
            diary.add_entry(
                self.data_dir,
                persona.id,
                end_day.isoformat(),
                "这一周",
                summary[:1200],
                source="weekly",
                now=now,
            )
            logger.info(
                "[虚拟人生] 已生成周记 persona=%s end=%s",
                persona.id,
                end_day.isoformat(),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 生成周记失败: %s", exc)

    async def _record_anniversary(self, persona, now) -> None:
        try:
            info = affection.snapshot(
                self.data_dir, persona.id, now=now
            )
            if not info.get("is_anniversary"):
                return
            day_text = now.date().isoformat()
            if diary.has_entry(
                self.data_dir, persona.id, day_text, "anniversary"
            ):
                return
            days = int(info.get("days_known") or 1)
            diary.add_entry(
                self.data_dir,
                persona.id,
                day_text,
                f"认识第 {days} 天",
                (
                    f"今天是我们认识第 {days} 天。"
                    f"当前关系：{info.get('level')}，"
                    f"好感 {info.get('score')} / 1000。"
                ),
                source="anniversary",
                now=now,
            )
            logger.info(
                "[虚拟人生] 关系纪念日 persona=%s days=%s",
                persona.id,
                days,
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 记录关系纪念日失败: %s", exc)

    @staticmethod
    def _diary_weather_text(plan) -> str:
        """Render plan.weather as readable text instead of a dataclass repr."""
        weather = getattr(plan, "weather", None)
        if weather is None:
            return "未知"
        if isinstance(weather, dict):
            condition = str(weather.get("condition") or "").strip()
            description = str(weather.get("description") or "").strip()
            try:
                low = int(weather.get("temperature_low"))
                high = int(weather.get("temperature_high"))
                label = f"{condition} {low}~{high}°C".strip()
            except (TypeError, ValueError):
                label = condition
            if description:
                return (label + "，" + description).strip("，")
            return label or "未知"
        label = str(getattr(weather, "label", "") or "").strip()
        description = str(getattr(weather, "description", "") or "").strip()
        if label:
            return (label + "，" + description).strip("，") if description else label
        if description:
            return description
        return str(weather)

    async def _write_daily_diary(self, persona, day) -> None:
        """Create a small factual diary entry for a finished day."""
        try:
            if diary.has_entry(self.data_dir, persona.id, day.isoformat(), "auto"):
                return
            plan = self.storage.get_plan(day.isoformat(), persona.id)
            if plan is None or not plan.has_schedule:
                return
            snapshot = money.snapshot(self.data_dir, persona.id, limit=60)
            day_text = day.isoformat()
            day_transactions = [
                item
                for item in snapshot.get("transactions") or []
                if str(item.get("at") or "")[:10] == day_text
            ]
            income = sum(
                float(item.get("amount") or 0)
                for item in day_transactions
                if float(item.get("amount") or 0) > 0
            )
            expense = sum(
                -float(item.get("amount") or 0)
                for item in day_transactions
                if float(item.get("amount") or 0) < 0
            )
            work_minutes = money.work_minutes(plan)
            books_read = []
            purchases = []
            for item in snapshot.get("possessions") or []:
                book = books.find_book(
                    str(item.get("book_id") or item.get("name") or "")
                )
                if book is not None:
                    progress = books.get_progress(
                        self.data_dir,
                        persona.id,
                        str(book.get("id") or ""),
                    )
                    state_text = (
                        "读完"
                        if progress.get("finished")
                        else f"第 {progress.get('chapter')} 章"
                    )
                    books_read.append(f"《{book.get('title')}》{state_text}")
                if str(item.get("at") or "")[:10] == day_text:
                    purchases.append(str(item.get("name") or ""))
            lines = [
                f"主题：{getattr(plan, 'theme', '日常')}，"
                f"天气：{self._diary_weather_text(plan)}。",
            ]
            world_event = world_events.recent(
                self.data_dir, persona.id, day_text
            )
            if world_event:
                lines.append(
                    f"今天的小事：{world_event.get('summary')}"
                )
            if work_minutes:
                lines.append(f"工作 {work_minutes} 分钟。")
            if income or expense:
                lines.append(
                    f"收支：收入 {money.format_money(income)} 元，"
                    f"支出 {money.format_money(expense)} 元，"
                    f"余额 {money.format_money(snapshot.get('balance') or 0)} 元。"
                )
            if books_read:
                lines.append("书：" + "、".join(books_read[:4]) + "。")
            if purchases:
                lines.append("新东西：" + "、".join(purchases[:5]) + "。")
            goal = snapshot.get("goal")
            if goal:
                lines.append(
                    f"存款目标：{goal.get('name')} "
                    f"{money.format_money(goal.get('progress') or 0)}/"
                    f"{money.format_money(goal.get('target') or 0)} 元。"
                )
            diary.add_entry(
                self.data_dir,
                persona.id,
                day_text,
                f"{day.month} 月 {day.day} 日",
                "\n".join(lines),
                source="auto",
                now=self._now(),
            )
            logger.info(
                "[虚拟人生] 已生成日记 persona=%s date=%s",
                persona.id,
                day_text,
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 生成日记失败 persona=%s: %s", persona.id, exc)

    async def _maybe_queue_goal_wish(self, persona) -> None:
        """When a savings goal is reached, queue a wish request for the master."""
        try:
            snapshot = money.snapshot(
                self.data_dir, persona.id, limit=1
            )
        except Exception:
            return
        goal = snapshot.get("goal")
        if not goal or goal.get("fulfilled") or not goal.get("achieved"):
            return
        requested_at = str(goal.get("requested_at") or "")
        if requested_at:
            try:
                requested = datetime.fromisoformat(requested_at)
                if self._now() - requested < timedelta(hours=12):
                    return
            except ValueError:
                pass
        try:
            pending = view_state.load_pending_actions(
                self.data_dir / "plans.json", persona.id
            )
        except Exception:
            pending = []
        if any(
            str(action.get("kind") or "") == "wish"
            for action in pending
        ):
            return
        wish = str(goal.get("wish") or "").strip()
        reason = wish or f"攒钱买{goal.get('name')}"
        try:
            view_state.queue_pending_action(
                self.data_dir / "plans.json",
                persona=persona.id,
                label=f"实现月月的愿望：{goal.get('name')}",
                source=(
                    f"月月攒够了 {money.format_money(goal.get('target') or 0)} 元，"
                    f"想让你实现：{reason}"
                ),
                kind="wish",
                amount=float(goal.get("target") or 0),
                reason=reason,
                now=self._now(),
            )
            money.mark_goal_requested(
                self.data_dir, persona.id, at=self._now()
            )
            logger.info(
                "[虚拟人生] 已生成愿望请求 persona=%s goal=%s",
                persona.id,
                goal.get("name"),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 生成愿望请求失败: %s", exc)

    def _wallet_text(self, persona_id: str, limit: int = 3) -> str:
        settings = self._money_settings()
        currency = str(settings.get("currency") or "元")
        snapshot = money.snapshot(self.data_dir, persona_id, limit=limit)
        balance_value = float(snapshot["balance"])
        if balance_value < 0:
            lines = [
                f"钱包余额：欠款 {money.format_money(abs(balance_value))} {currency}"
            ]
        else:
            lines = [
                f"钱包余额：{money.format_money(balance_value)} {currency}"
            ]
        goal = snapshot.get("goal")
        if goal:
            state_text = (
                "，已实现。"
                if goal.get("fulfilled")
                else (
                    "，已达成，可以向主人提愿望。"
                    if goal.get("achieved")
                    else f"，还差 {money.format_money(goal['remaining'])} {currency}。"
                )
            )
            wish = str(goal.get("wish") or "").strip()
            lines.append(
                f"存款目标：{goal['name']} "
                f"{money.format_money(goal['progress'])}/"
                f"{money.format_money(goal['target'])} {currency}"
                + state_text
                + (f" 愿望：{wish}" if wish else "")
            )
        possessions = snapshot.get("possessions") or []
        if possessions:
            lines.append(
                "已有物品："
                + "、".join(
                    str(item.get("name") or "")
                    for item in possessions[-8:]
                )
            )
        transactions = snapshot.get("transactions") or []
        for item in transactions:
            amount = float(item.get("amount") or 0)
            sign = "+" if amount >= 0 else ""
            lines.append(
                f"{sign}{money.format_money(amount)} {currency} · "
                f"{item.get('reason') or ''}"
            )
        if not transactions:
            lines.append("还没有收支记录。")
        return "\n".join(lines)

    @virtual_life_group.command("钱包")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_wallet(self, event: AstrMessageEvent):
        """查看当前人格的钱包余额和最近收支。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            await self._process_deliveries(persona, self._now())
            await self._settle_work_income(
                persona, self._now().date() - timedelta(days=1)
            )
            await self._settle_work_income(
                persona, self._now().date(), before=self._now()
            )
            text = self._wallet_text(persona.id)
        except Exception as exc:
            logger.warning("[虚拟人生] 钱包查询失败: %s", exc)
            yield event.plain_result("钱包暂时无法读取，请稍后重试。")
            return
        yield event.plain_result(text)

    @virtual_life_group.command("快递")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_deliveries(self, event: AstrMessageEvent):
        """查看正在配送的订单。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            await self._process_deliveries(persona, self._now())
            orders = delivery.list_orders(self.data_dir, persona.id)
        except Exception as exc:
            logger.warning("[虚拟人生] 快递查询失败: %s", exc)
            yield event.plain_result("快递信息暂时无法读取。")
            return
        if not orders:
            yield event.plain_result("现在没有在路上的快递。")
            return
        lines = ["正在配送："]
        for order in orders:
            goods = order.get("goods") or {}
            lines.append(
                f"{goods.get('name') or '商品'} ×{order.get('quantity') or 1} · "
                f"预计 {str(order.get('deliver_at') or '')[11:16]} 送到"
            )
        yield event.plain_result("\n".join(lines))

    @virtual_life_group.command("流水")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_money_ledger(self, event: AstrMessageEvent):
        """查看最近 10 条收支记录。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            now = self._now()
            await self._settle_work_income(
                persona, now.date() - timedelta(days=1)
            )
            await self._settle_work_income(
                persona, now.date(), before=now
            )
            snapshot = money.snapshot(
                self.data_dir, persona.id, limit=10
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 流水查询失败: %s", exc)
            yield event.plain_result("流水暂时无法读取，请稍后重试。")
            return
        currency = str(self._money_settings().get("currency") or "元")
        lines = [
            f"钱包余额：{money.format_money(snapshot['balance'])} {currency}",
            "最近流水：",
        ]
        transactions = snapshot.get("transactions") or []
        if not transactions:
            lines.append("还没有收支记录。")
        for item in transactions:
            amount = float(item.get("amount") or 0)
            sign = "+" if amount >= 0 else ""
            lines.append(
                f"{str(item.get('at') or '')[5:16]}  "
                f"{sign}{money.format_money(amount)} {currency}  "
                f"{item.get('reason') or ''}"
            )
        yield event.plain_result("\n".join(lines))

    @virtual_life_group.command("存款目标")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def set_savings_goal_command(self, event: AstrMessageEvent):
        """设置存款目标：/虚拟人生 存款目标 相机 500"""
        raw = str(event.get_message_str() or "")
        match = re.search(
            r"存款目标\s*(\S+)\s*([0-9]+(?:\.[0-9]+)?)\s*(.*)", raw
        )
        if not match:
            yield event.plain_result(
                "用法：/虚拟人生 存款目标 相机 500 想拍照"
            )
            return
        goal_name = match.group(1)
        target = float(match.group(2))
        wish = match.group(3).strip()
        if target <= 0 or target > 100000:
            yield event.plain_result("目标金额需要在 0 到 100000 元之间。")
            return
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            result = await asyncio.to_thread(
                money.set_goal,
                self.data_dir,
                persona.id,
                goal_name,
                target,
                wish=wish,
                at=self._now(),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 设置存款目标失败: %s", exc)
            yield event.plain_result("存款目标设置失败，请稍后重试。")
            return
        if not result.get("ok"):
            yield event.plain_result(result.get("error") or "设置失败。")
            return
        goal = result.get("goal") or {}
        currency = str(self._money_settings().get("currency") or "元")
        detail = (
            f"攒够后想让你实现：{wish}。"
            if wish
            else "攒够后她会来向你提愿望。"
        )
        yield event.plain_result(
            f"已设置存款目标：{goal.get('name')} "
            f"{money.format_money(goal.get('target') or 0)} {currency}。"
            + detail
        )

    @virtual_life_group.command("存款")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_savings_goal(self, event: AstrMessageEvent):
        """查看当前存款目标进度。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            snapshot = money.snapshot(
                self.data_dir, persona.id, limit=1
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 存款目标查询失败: %s", exc)
            yield event.plain_result("存款目标暂时无法读取。")
            return
        goal = snapshot.get("goal")
        if not goal:
            yield event.plain_result(
                "还没有存款目标。可以发送：/虚拟人生 存款目标 相机 500"
            )
            return
        currency = str(self._money_settings().get("currency") or "元")
        wish = str(goal.get("wish") or "").strip()
        wish_line = f"\n愿望：{wish}" if wish else ""
        if goal.get("fulfilled"):
            yield event.plain_result(
                f"存款目标「{goal['name']}」已经实现过了。"
                f"当前余额 {money.format_money(goal['progress'])} {currency}。"
                + wish_line
            )
            return
        if goal.get("achieved"):
            yield event.plain_result(
                f"存款目标「{goal['name']}」已经达成！"
                f"当前 {money.format_money(goal['progress'])} {currency}。"
                + wish_line
                + "\n观察窗里应该已经有愿望按钮，点一下就能实现。"
            )
            return
        yield event.plain_result(
            f"存款目标：{goal['name']} "
            f"{money.format_money(goal['target'])} {currency}\n"
            f"当前进度：{money.format_money(goal['progress'])} {currency}，"
            f"还差 {money.format_money(goal['remaining'])} {currency}。"
            + wish_line
        )

    @virtual_life_group.command("商品")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_goods(self, event: AstrMessageEvent):
        """查看商店商品：/虚拟人生 商品 书籍"""
        raw = str(event.get_message_str() or "")
        category = re.sub(r"^.*?商品\s*", "", raw, count=1).strip()
        items = goods.list_goods(category, limit=80)
        if not items:
            yield event.plain_result("这个分类下暂时没有商品。")
            return
        lines = ["商店商品："]
        for item in items:
            lines.append(
                f"{item.get('icon') or '·'} {item.get('name')} "
                f"{item.get('price')} 元 · {item.get('category')}"
            )
        yield event.plain_result("\n".join(lines))

    @virtual_life_group.command("物品")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_possessions(self, event: AstrMessageEvent):
        """查看月月已经拥有的东西。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            snapshot = money.snapshot(
                self.data_dir, persona.id, limit=1
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 物品查询失败: %s", exc)
            yield event.plain_result("物品暂时无法读取。")
            return
        items = snapshot.get("possessions") or []
        if not items:
            yield event.plain_result("她还没有买过或实现过什么东西。")
            return
        currency = str(self._money_settings().get("currency") or "元")
        lines = ["已经拥有："]
        for item in items[-10:]:
            price = float(item.get("price") or 0)
            lines.append(
                f"{item.get('name')} · {price:g} {currency} · "
                f"{item.get('source') or ''}"
            )
        yield event.plain_result("\n".join(lines))

    @virtual_life_group.command("使用")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def use_item_command(self, event: AstrMessageEvent):
        """使用物品：/虚拟人生 使用 奶茶"""
        raw = str(event.get_message_str() or "")
        query = re.sub(r"^.*?使用\s*", "", raw, count=1).strip()
        if not query:
            yield event.plain_result("用法：/虚拟人生 使用 奶茶")
            return
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            result = await asyncio.to_thread(
                goods.use_item,
                self.data_dir,
                persona.id,
                query,
                at=self._now(),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 使用物品失败: %s", exc)
            yield event.plain_result("这件东西暂时用不了。")
            return
        if not result.get("ok"):
            yield event.plain_result(result.get("error") or "没有这件东西。")
            return
        item = result.get("item") or {}
        effects = result.get("effects") or {}
        effect_text = "、".join(
            f"{key} {value:+g}" for key, value in effects.items()
        )
        yield event.plain_result(
            f"月月用了{item.get('name') or '物品'}。"
            + (f"效果：{effect_text}。" if effect_text else "")
        )

    @virtual_life_group.command("摆放")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def place_item_command(self, event: AstrMessageEvent):
        """摆放物品：/虚拟人生 摆放 相机 书房"""
        raw = str(event.get_message_str() or "")
        match = re.search(r"摆放\s*(\S+)\s+(\S+)", raw)
        if not match:
            yield event.plain_result("用法：/虚拟人生 摆放 相机 书房")
            return
        item_name, room_name = match.group(1), match.group(2)
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            result = await asyncio.to_thread(
                money.place_possession,
                self.data_dir,
                persona.id,
                item_name,
                room_name,
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 摆放物品失败: %s", exc)
            yield event.plain_result("这件东西暂时摆不出去。")
            return
        if not result.get("ok"):
            yield event.plain_result(result.get("error") or "没有这件东西。")
            return
        yield event.plain_result(
            f"把{result['item'].get('name') or '物品'}摆到了{room_name}。"
        )

    @virtual_life_group.command("好感")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_affection(self, event: AstrMessageEvent):
        """查看当前人格与主人的好感度。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            text = affection.format_status(self.data_dir, persona.id)
        except Exception as exc:
            logger.warning("[虚拟人生] 好感查询失败: %s", exc)
            yield event.plain_result("好感度暂时无法读取。")
            return
        yield event.plain_result(text)

    @virtual_life_group.command("称呼")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def set_nickname(self, event: AstrMessageEvent):
        """设置月月对主人的称呼：/虚拟人生 称呼 老板"""
        raw = str(event.get_message_str() or "")
        nickname = re.sub(r"^.*?称呼\s*", "", raw, count=1).strip()
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
        except Exception as exc:
            logger.warning("[虚拟人生] 称呼解析失败: %s", exc)
            yield event.plain_result("称呼暂时无法设置。")
            return
        if not nickname:
            info = affection.snapshot(
                self.data_dir, persona.id, now=self._now()
            )
            yield event.plain_result(
                f"月月现在称呼你为：{info.get('nickname') or '主人'}。"
                "修改用法：/虚拟人生 称呼 老板"
            )
            return
        result = affection.set_nickname(
            self.data_dir,
            persona.id,
            nickname,
            now=self._now(),
        )
        if not result.get("ok"):
            yield event.plain_result(result.get("error") or "称呼设置失败。")
            return
        yield event.plain_result(
            f"月月现在会称呼你为「{result.get('nickname')}」。"
        )

    @virtual_life_group.command("周报")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_weekly_report(self, event: AstrMessageEvent):
        """查看最近 7 天的生活周报。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            report = weekly.build(
                self.data_dir, persona.id, now=self._now()
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 周报生成失败: %s", exc)
            yield event.plain_result("周报暂时无法生成。")
            return
        yield event.plain_result(weekly.format_report(report))

    @virtual_life_group.command("年总结")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_yearly_report(self, event: AstrMessageEvent):
        """查看最近一年的生活总结。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            report = weekly.build(
                self.data_dir, persona.id, now=self._now(), days=365
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 年度总结生成失败: %s", exc)
            yield event.plain_result("年度总结暂时无法生成。")
            return
        yield event.plain_result(weekly.format_report(report))

    @virtual_life_group.command("月报")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_monthly_report(self, event: AstrMessageEvent):
        """查看最近 30 天的生活月报。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            report = weekly.build(
                self.data_dir, persona.id, now=self._now(), days=30
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 月报生成失败: %s", exc)
            yield event.plain_result("月报暂时无法生成。")
            return
        yield event.plain_result(weekly.format_report(report))

    @virtual_life_group.command("日记")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_diary(self, event: AstrMessageEvent):
        """查看最近的日记。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            entries = diary.list_entries(self.data_dir, persona.id, limit=6)
        except Exception as exc:
            logger.warning("[虚拟人生] 日记查询失败: %s", exc)
            yield event.plain_result("日记暂时无法读取。")
            return
        yield event.plain_result(diary.format_entries(entries))

    @virtual_life_group.command("读书")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def read_book_command(self, event: AstrMessageEvent):
        """读书：/虚拟人生 读书 云层以下"""
        raw = str(event.get_message_str() or "")
        query = re.sub(r"^.*?读书\s*", "", raw, count=1).strip()
        if not query:
            titles = "、".join(
                str(book.get("title") or "")
                for book in books.list_books()
            )
            yield event.plain_result(f"想读哪本？书架上有：{titles}")
            return
        book = books.find_book(query)
        if book is None:
            yield event.plain_result("没找到这本书。")
            return
        yield event.plain_result(books.render_book(book, 1))

    @virtual_life_group.command("书架")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_bookshelf(self, event: AstrMessageEvent):
        """查看月月拥有的书和阅读进度。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            snapshot = money.snapshot(
                self.data_dir, persona.id, limit=1
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 书架查询失败: %s", exc)
            yield event.plain_result("书架暂时无法读取。")
            return
        lines = ["书架："]
        owned_books = []
        for item in snapshot.get("possessions") or []:
            book_id = str(item.get("book_id") or "").strip()
            book = books.find_book(book_id or str(item.get("name") or ""))
            if book is None:
                continue
            owned_books.append(book)
            total = len(book.get("chapters") or [])
            progress = books.get_progress(
                self.data_dir, persona.id, str(book.get("id") or "")
            )
            state_text = (
                "已读完"
                if progress.get("finished")
                else f"读到第 {progress.get('chapter')} / {total} 章"
            )
            notes = progress.get("notes") or []
            lines.append(
                f"《{book.get('title')}》{state_text}"
                + (f" · {len(notes)} 条笔记" if notes else "")
            )
        if not owned_books:
            yield event.plain_result("她还没有买书。")
            return
        yield event.plain_result("\n".join(lines))

    @virtual_life_group.command("笔记")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def show_reading_notes(self, event: AstrMessageEvent):
        """查看读书笔记。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            snapshot = money.snapshot(
                self.data_dir, persona.id, limit=1
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 读书笔记查询失败: %s", exc)
            yield event.plain_result("读书笔记暂时无法读取。")
            return
        lines = ["读书笔记："]
        for item in snapshot.get("possessions") or []:
            book_id = str(item.get("book_id") or "").strip()
            book = books.find_book(book_id or str(item.get("name") or ""))
            if book is None:
                continue
            progress = books.get_progress(
                self.data_dir, persona.id, str(book.get("id") or "")
            )
            for note in progress.get("notes") or []:
                lines.append(
                    f"《{book.get('title')}》：{note.get('text')}"
                )
        if len(lines) == 1:
            yield event.plain_result("她还没有写读书笔记。")
            return
        yield event.plain_result("\n".join(lines[-12:]))

    @virtual_life_group.command("给钱")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def give_money(self, event: AstrMessageEvent):
        """主人给当前人格一笔钱：/虚拟人生 给钱 100"""
        raw = str(event.get_message_str() or "")
        match = re.search(r"(?:给钱|转账)\s*([0-9]+(?:\.[0-9]+)?)", raw)
        amount = float(match.group(1)) if match else 0.0
        if amount <= 0:
            yield event.plain_result("用法：/虚拟人生 给钱 100")
            return
        if amount > 100000:
            yield event.plain_result("一次最多给 100000 元。")
            return
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            result = await asyncio.to_thread(
                money.add,
                self.data_dir,
                persona.id,
                amount,
                "主人给的钱",
                kind="master",
                at=self._now(),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 给钱失败: %s", exc)
            yield event.plain_result("转账失败，请稍后重试。")
            return
        await self._maybe_queue_goal_wish(persona)
        currency = str(self._money_settings().get("currency") or "元")
        yield event.plain_result(
            f"已给月月 {money.format_money(amount)} {currency}，"
            f"当前余额 {money.format_money(result['balance'])} {currency}。"
        )

    @virtual_life_group.command("测试按钮")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def create_test_pending_gift(self, event: AstrMessageEvent):
        """创建一个测试用待处理按钮，方便验证观察窗前端。"""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            action = view_state.queue_pending_action(
                self.data_dir / "plans.json",
                persona=persona.id,
                label="把东西递给月月",
                source="[测试按钮] 管理员创建",
                now=self._now(),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 创建测试按钮失败: %s", exc)
            yield event.plain_result("创建测试按钮失败，请稍后重试。")
            return
        yield event.plain_result(
            f"已创建测试按钮：{action.get('label')}。"
            "请完全关闭观察窗再打开并 Ctrl+Shift+R；"
            "如果仍然看不到，发送 /虚拟人生 递东西 即可。"
        )

    @virtual_life_group.command("自检")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def self_check(self, event: AstrMessageEvent):
        """查看当前会话的虚拟人生隐私与主动消息配置。"""
        umo = event.unified_msg_origin
        kind = session_kind(umo)
        kind_text = "群聊" if kind == "group" else "私聊"
        schedule_allowed = self._schedule_available_for_umo(umo)
        settings_key = "group_settings" if kind == "group" else "friend_settings"
        settings = self.config.get(settings_key, {}) or {}
        sessions = [str(item) for item in (settings.get("session_list") or [])]
        lines = [
            f"插件版本：{_plugin_version()}",
            f"预期前端版本：{_frontend_ui_version()}",
            f"Personal Network：{self._personal_network_status()}",
            f"当前会话：{kind_text}",
            f"日程数据：{'允许使用' if schedule_allowed else '仅私聊，本会话不注入日程'}",
            f"日程私聊限制：{'开启' if self._schedule_private_only() else '关闭'}",
            f"{kind_text}主动开关：{'开启' if settings.get('enable') else '关闭'}",
            f"本会话已订阅：{'是' if umo in sessions else '否'}",
        ]
        if kind == "group":
            lines.extend(
                [
                    f"群聊每日预算：{settings.get('daily_budget_min', 0)}–{settings.get('daily_budget_max', 0)}",
                    f"群聊硬上限：{settings.get('daily_hard_max', 0)}",
                    "群聊隔离：已开启（日程工具移除、旧日程历史清洗、回复过滤）",
                    "群聊窗口消息：不占自主预算、不受普通主动冷却限制",
                ]
            )
        try:
            persona = await self.personas.resolve(umo)
            currency = str(self._money_settings().get("currency") or "元")
            try:
                now = self._now()
                await self._settle_work_income(
                    persona, now.date() - timedelta(days=1)
                )
                await self._settle_work_income(
                    persona, now.date(), before=now
                )
                data_dir = getattr(self, "data_dir", None)
                wallet_balance = (
                    money.balance(data_dir, persona.id)
                    if data_dir is not None
                    else 0.0
                )
            except Exception:
                wallet_balance = 0.0
            lines.append(
                f"钱包余额：{money.format_money(wallet_balance)} {currency}"
            )
            plan = self.storage.get_plan(self._now().date().isoformat(), persona.id)
            if plan is None:
                lines.append("今日计划：未生成")
            else:
                needs = self._life_needs(plan, self._now(), update_journal=False)
                labels = needs.get("labels") or {}
                label_text = "；".join(
                    f"{title} {labels[key]}"
                    for key, title in (
                        ("energy", "精力"),
                        ("mood", "心情"),
                        ("health", "健康"),
                    )
                    if labels.get(key)
                )
                if label_text:
                    lines.append(f"当前生理：{label_text}")
                states = []
                if needs.get("morning_grogginess") and not needs.get(
                    "morning_grogginess_relief"
                ):
                    states.append("早上没睡醒")
                if needs.get("afternoon_dip") and not needs.get(
                    "afternoon_dip_relief"
                ):
                    states.append("午后犯困")
                if needs.get("evening_sleepiness"):
                    states.append("晚上困了")
                if needs.get("sick"):
                    states.append("生病中")
                elif needs.get("recovering"):
                    states.append("病后恢复中")
                if states:
                    lines.append("当前状态：" + "、".join(states))
            try:
                pending = view_state.load_pending_actions(
                    self.data_dir / "plans.json", persona.id
                )
                if pending:
                    labels = "、".join(
                        str(action.get("label") or "递东西")
                        for action in pending[:3]
                    )
                    lines.append(f"待处理动作：{len(pending)} 个（{labels}）")
                    lines.append("可发送 /虚拟人生 递东西 直接接受，或 /虚拟人生 清空待处理 取消")
            except Exception:
                pass
        except Exception as exc:
            logger.warning("[虚拟人生] 自检读取当前状态失败 umo=%s: %s", umo, exc)
        try:
            state = self.storage.sessions.get(umo)
            if state and str(getattr(state, "date", "")) == self._now().date().isoformat():
                lines.append(
                    f"今日主动：{getattr(state, 'sent_count', 0)}/{getattr(state, 'daily_budget', 0)}"
                )
                lines.append(
                    f"连续未回复：{getattr(state, 'unanswered_count', 0)}"
                )
        except Exception as exc:
            logger.warning("[虚拟人生] 自检读取主动状态失败 umo=%s: %s", umo, exc)
        yield event.plain_result("\n".join(lines))

    @filter.command("回复延迟")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def reply_delay_command(self, event: AstrMessageEvent, action: str):
        action = str(action).strip()
        if action == "结算":
            batch = await self.reply_delay_coordinator.settle_now(
                event.unified_msg_origin
            )
            if batch is None:
                yield event.plain_result("当前会话没有等待结算的回复批次。")
                return
            logger.info(
                "[虚拟人生] 管理员立即结算回复延迟批次 会话=%s 消息数=%s",
                event.unified_msg_origin,
                len(batch.messages),
            )
            yield event.plain_result(
                f"已立即结算当前会话的回复批次，共 {len(batch.messages)} 条消息。"
            )
            return
        if action not in {"开启", "关闭"}:
            yield event.plain_result("用法：/回复延迟 开启|关闭|结算")
            return

        enabled = action == "开启"
        settings = self.config.get("reply_delay_settings", {}) or {}
        changed = bool(settings.get("enable")) != enabled
        settings["enable"] = enabled
        self.config["reply_delay_settings"] = settings
        self.reply_delay_policy.settings = settings
        if changed:
            self.config.save_config()

        settled_count = 0
        if not enabled:
            batches = await self.reply_delay_coordinator.settle_all_now()
            settled_count = len(batches)
        logger.info(
            "[虚拟人生] 管理员%s回复延迟 配置变更=%s 结算批次=%s",
            action,
            changed,
            settled_count,
        )
        state = "已开启" if enabled else "已关闭"
        suffix = f"，并立即结算 {settled_count} 个等待批次" if settled_count else ""
        yield event.plain_result(f"回复延迟{state}{suffix}。")

    @filter.command_group("虚拟日程")
    def virtual_daily_group(self):
        """虚拟日程命令组；不提供子命令时由 AstrBot 输出帮助。"""
        pass

    @virtual_daily_group.command("要求")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def add_schedule_requirement_command(
        self,
        event: AstrMessageEvent,
        date_range: str,
        requirement=GreedyStr,
    ):
        """为当前人格未来日期的首次日程生成添加要求。"""
        yield event.plain_result(
            await self._add_schedule_requirement(event, date_range, requirement)
        )

    @virtual_daily_group.command("查看")
    async def show_schedule(self, event: AstrMessageEvent):
        """查看今日虚拟日程时间轴图片。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            yield event.plain_result("虚拟日程系统仅在私聊生效，群聊中不提供日程查看。")
            return
        persona, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if not plan.has_schedule:
            yield event.plain_result("今日没有日程。")
            return
        now = self._now()
        target = date.fromisoformat(plan.date)
        long_term_day = self.long_term.expand_day(persona.id, target) or {
            "stage": None,
            "active_periods": [],
            "holidays": self.long_term.holidays.on(target),
        }
        fallback = format_timeline(plan, now, long_term_day)
        results = await self._image_view_results(
            event,
            f"{persona.id} · {plan.date} 虚拟日程",
            fallback,
            [lambda: self.image_renderer.render_timeline(plan, now, long_term_day)],
        )
        for result in results:
            yield result

    @virtual_daily_group.command("穿搭")
    async def show_outfit(self, event: AstrMessageEvent):
        """查看今日穿搭图片。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            yield event.plain_result("虚拟日程系统仅在私聊生效，群聊中不提供穿搭查看。")
            return
        persona, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if not plan.has_outfit:
            yield event.plain_result("今日没有穿搭。")
            return
        now = self._now()
        results = await self._image_view_results(
            event,
            f"{persona.id} · {plan.date} 今日穿搭",
            format_outfit(plan),
            [lambda: self.image_renderer.render_outfit(plan, now)],
        )
        for result in results:
            yield result

    @virtual_daily_group.command("菜单")
    async def show_food_menu(self, event: AstrMessageEvent):
        """查看今天的菜品、在家做饭/外食安排和采购清单。"""
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            yield event.plain_result("虚拟日程系统仅在私聊生效，群聊中不提供菜单查看。")
            return
        settings = self.config.get("food_settings", {}) or {}
        if not bool(settings.get("enable", True)):
            yield event.plain_result("饮食细节已关闭。")
            return
        persona, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        menu = self.plan_generator.food.latest_menu(
            date.fromisoformat(plan.date), persona.id
        )
        if not menu:
            yield event.plain_result("今天还没有排出菜单；日程生成后会自动安排。")
            return
        yield event.plain_result(self.plan_generator.food.format_menu_text(menu))

    @virtual_daily_group.command("旅行")
    async def travel_command(
        self, event: AstrMessageEvent, action: str = "", target=GreedyStr
    ):
        """查看当前旅行；管理员可用「旅行 规划 <目的地> [日期] [天数]」或「旅行 取消」。

        不带参数时显示正在进行的旅行或下一趟行程；「目的地」列出可选城市。
        """
        if not self._schedule_available_for_umo(event.unified_msg_origin):
            yield event.plain_result("虚拟日程系统仅在私聊生效，群聊中不提供旅行日程。")
            return
        yield event.plain_result(
            await self._handle_travel_command(event, action, str(target or ""))
        )

    @virtual_daily_group.command("重写")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def rewrite_schedule(self, event: AstrMessageEvent, extra: str | None = None):
        """重新生成今日完整虚拟日程。"""
        include_schedule, include_outfit = self._daily_generation_flags()
        if not include_schedule and not include_outfit:
            yield event.plain_result("日程生成和穿搭生成均已关闭。")
            return
        persona, plan = await self._ensure_plan_for_umo(
            event.unified_msg_origin,
            force=True,
            extra=extra or "",
            preserve_disabled=True,
        )
        await self._reschedule_plan_sessions(persona, plan)
        yield event.plain_result(
            "重写失败，请检查 LLM 输出。"
            if plan.status != "ok"
            else format_plan(plan, self._now())
        )

    @virtual_daily_group.command("重写日程")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def rewrite_daily_timeline(
        self, event: AstrMessageEvent, extra: str | None = None
    ):
        """保留主题、心情与穿搭，只重写今日时间日程。"""
        include_schedule, _ = self._daily_generation_flags()
        if not include_schedule:
            yield event.plain_result("日程生成功能已关闭。")
            return
        persona, current = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if current.status != "ok":
            yield event.plain_result(
                "今日没有可局部重写的有效日程，请先使用“虚拟日程 重写”。"
            )
            return
        long_term_context = ""
        long_term_settings = self.config.get("long_term_settings", {}) or {}
        if long_term_settings.get("enable", True):
            long_term_context = self.long_term.format_day_context(
                persona.id,
                date.fromisoformat(current.date),
                fallback_to_latest=True,
            )
        try:
            relationship_context = await self._personal_network_context(persona.id)
            plan = await self.plan_generator.rewrite_schedule(
                current,
                persona,
                extra=extra or "",
                long_term_context=long_term_context,
                relationship_context=relationship_context,
            )
        except Exception as exc:
            logger.warning(
                "[Virtual Life] Schedule rewrite failed persona=%s: %s", persona.id, exc
            )
            yield event.plain_result(
                "日程重写失败，已保留原日程，请检查 LLM 输出或日志。"
            )
            return
        try:
            self.storage.plans[self.storage.plan_key(plan.date, persona.id)] = plan
            await self.storage.save_plans()
            await self._reschedule_plan_sessions(persona, plan)
        except Exception as exc:
            logger.warning(
                "[Virtual Life] Schedule rewrite persistence failed persona=%s: %s",
                persona.id,
                exc,
            )
            yield event.plain_result("日程已生成，但保存或调度失败，请检查日志。")
            return
        yield event.plain_result(format_plan(plan, self._now()))

    @virtual_daily_group.command("重写穿搭")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def rewrite_daily_outfit(
        self, event: AstrMessageEvent, extra: str | None = None
    ):
        """保留主题、心情与时间日程，只重写今日穿搭。"""
        _, include_outfit = self._daily_generation_flags()
        if not include_outfit:
            yield event.plain_result("穿搭生成功能已关闭。")
            return
        persona, current = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if current.status != "ok":
            yield event.plain_result(
                "今日没有可局部重写的有效穿搭，请先使用“虚拟日程 重写”。"
            )
            return
        try:
            plan = await self.plan_generator.rewrite_outfit(
                current, persona, extra=extra or ""
            )
        except Exception as exc:
            logger.warning(
                "[Virtual Life] Outfit rewrite failed persona=%s: %s", persona.id, exc
            )
            yield event.plain_result(
                "穿搭重写失败，已保留原穿搭，请检查 LLM 输出或日志。"
            )
            return
        try:
            self.storage.plans[self.storage.plan_key(plan.date, persona.id)] = plan
            await self.storage.save_plans()
            await self._reschedule_plan_sessions(persona, plan)
        except Exception as exc:
            logger.warning(
                "[Virtual Life] Outfit rewrite persistence failed persona=%s: %s",
                persona.id,
                exc,
            )
            yield event.plain_result("穿搭已生成，但保存或调度失败，请检查日志。")
            return
        yield event.plain_result(format_outfit(plan))

    @filter.command_group("大时间表")
    def long_term_group(self):
        """大时间表命令组；不提供子命令时由 AstrBot 输出帮助。"""
        pass

    @long_term_group.command("生成")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_generate(
        self, event: AstrMessageEvent, requirements: str | None = None
    ):
        """根据自然语言要求生成追加草稿。"""
        persona = await self.personas.resolve(event.unified_msg_origin)
        latest = self.long_term.latest_stage(persona.id)
        start = (
            date.fromisoformat(latest["end_date"]) + timedelta(days=1)
            if latest
            else self._now().date()
        )
        try:
            await self._create_long_term_draft(
                persona=persona,
                admin_umo=event.unified_msg_origin,
                requirements=requirements or "",
                start_date=start,
                previous_stage=latest,
                source="natural",
                mode="append",
            )
        except Exception as exc:
            yield event.plain_result(f"生成草稿失败：{exc}")
            return
        yield event.plain_result(
            "已生成大时间表草稿，使用 /大时间表 草稿 查看，确认后执行 /大时间表 批准。"
        )

    @long_term_group.command("导入")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_import(self, event: AstrMessageEvent, content: str):
        """导入结构化 JSON 为替换全部阶段的草稿。"""
        persona = await self.personas.resolve(event.unified_msg_origin)
        try:
            stages = self._parse_long_term_json(content, persona.id)
            await self.long_term.set_draft(
                persona.id,
                stages,
                source="json",
                admin_umo=event.unified_msg_origin,
                created_at=self._now().isoformat(),
                requirements="结构化数据导入",
                mode="replace_all",
            )
            self.image_renderer.invalidate_persona(persona.id)
        except Exception as exc:
            yield event.plain_result(f"导入草稿失败：{exc}")
            return
        yield event.plain_result("结构化数据已保存为草稿，确认后执行 /大时间表 批准。")

    @long_term_group.command("草稿")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_draft(self, event: AstrMessageEvent):
        """查看当前人格待批准草稿。"""
        persona = await self.personas.resolve(event.unified_msg_origin)
        draft = self.long_term.get_draft(persona.id)
        if not draft:
            yield event.plain_result("当前人格没有待批准草稿。")
            return
        stages = [self.long_term.with_holidays(stage) for stage in draft["stages"]]
        fallback = json.dumps({**draft, "stages": stages}, ensure_ascii=False, indent=2)
        jobs = [
            lambda stage=stage: self.image_renderer.render_stage(
                stage,
                persona.id,
                status="draft",
                draft_metadata=draft,
            )
            for stage in stages
        ]
        results = await self._image_view_results(
            event,
            f"{persona.id} · 大时间表草稿 · 待批准 · 共 {len(jobs)} 个阶段",
            fallback,
            jobs,
        )
        for result in results:
            yield result

    @long_term_group.command("批准")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_approve(self, event: AstrMessageEvent):
        """批准草稿并重新生成今日日程。"""
        persona = await self.personas.resolve(event.unified_msg_origin)
        try:
            approved = await self.long_term.approve_draft(
                persona.id, event.unified_msg_origin
            )
            self.image_renderer.invalidate_persona(persona.id)
            plan = await self._refresh_persona_daily_plan(persona)
        except Exception as exc:
            yield event.plain_result(f"批准失败：{exc}")
            return
        components = []
        if plan.has_schedule:
            components.append("日程")
        if plan.has_outfit:
            components.append("穿搭")
        generation_result = (
            "，已按开关重生成今日" + "和".join(components)
            if components
            else "；日程和穿搭生成均已关闭，未生成今日内容"
        )
        yield event.plain_result(
            "大时间表已生效"
            + generation_result
            + "："
            + "、".join(stage["name"] for stage in approved)
        )

    @long_term_group.command("拒绝")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_reject(
        self, event: AstrMessageEvent, feedback: str | None = None
    ):
        """拒绝草稿；提供修改意见时重新生成。"""
        persona = await self.personas.resolve(event.unified_msg_origin)
        draft = self.long_term.get_draft(persona.id)
        if not draft:
            yield event.plain_result("当前人格没有待拒绝草稿。")
            return
        await self.long_term.reject_draft(persona.id)
        self.image_renderer.invalidate_persona(persona.id)
        if not feedback:
            yield event.plain_result("草稿已拒绝并删除。")
            return
        start = date.fromisoformat(draft["stages"][0]["start_date"])
        previous = (
            self.long_term.latest_stage(persona.id)
            if draft.get("mode") == "append"
            else None
        )
        requirements = "；".join(
            part
            for part in (draft.get("requirements", ""), f"修改意见：{feedback}")
            if part
        )
        try:
            await self._create_long_term_draft(
                persona=persona,
                admin_umo=event.unified_msg_origin,
                requirements=requirements,
                start_date=start,
                previous_stage=previous,
                source="revision",
                mode=str(draft.get("mode", "append")),
            )
        except Exception as exc:
            yield event.plain_result(f"草稿已拒绝，但重新生成失败：{exc}")
            return
        yield event.plain_result("已按修改意见重新生成草稿，使用 /大时间表 草稿 查看。")

    @long_term_group.command("列表")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_list(self, event: AstrMessageEvent):
        """查看当前人格全部已批准阶段。"""
        persona = await self.personas.resolve(event.unified_msg_origin)
        stages = self.long_term.list_for_persona(persona.id)
        if not stages:
            yield event.plain_result("当前人格没有已批准的大时间表。")
            return
        fallback = "\n".join(
            f"{stage['id']} | {stage['name']} | {stage['kind']} | {stage['start_date']} 至 {stage['end_date']} | 优先级 {stage['priority']}"
            for stage in stages
        )
        results = await self._image_view_results(
            event,
            f"{persona.id} · 已批准阶段，共 {len(stages)} 个",
            fallback,
            [lambda: self.image_renderer.render_stage_list(stages, persona.id)],
        )
        for result in results:
            yield result

    @long_term_group.command("查看")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_view(
        self, event: AstrMessageEvent, stage_id: str | None = None
    ):
        """查看阶段；可省略参数或输入阶段 ID、名称及唯一片段。"""
        persona = await self.personas.resolve(event.unified_msg_origin)
        stage, candidates = self.long_term.resolve_stage(
            persona.id, self._now().date(), stage_id or ""
        )
        if not stage:
            if candidates:
                lines = ["找到多个匹配阶段，请使用完整 ID 或名称："]
                lines.extend(
                    f"- {item['id']} | {item['name']} | {item['start_date']} 至 {item['end_date']}"
                    for item in candidates
                )
                yield event.plain_result("\n".join(lines))
            elif stage_id:
                yield event.plain_result(
                    "未找到匹配阶段，请先使用 /大时间表 列表 查看可用 ID。"
                )
            else:
                yield event.plain_result("当前人格没有已批准的大时间表。")
            return
        stage = self.long_term.with_holidays(stage)
        fallback = json.dumps(stage, ensure_ascii=False, indent=2)
        results = await self._image_view_results(
            event,
            f"{persona.id} · {stage['name']}",
            fallback,
            [lambda: self.image_renderer.render_stage(stage, persona.id)],
        )
        for result in results:
            yield result

    @long_term_group.command("重生成")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_regenerate(
        self, event: AstrMessageEvent, requirements: str | None = None
    ):
        """重新生成替换全部阶段的草稿。"""
        persona = await self.personas.resolve(event.unified_msg_origin)
        previous = self.long_term.latest_stage(persona.id)
        try:
            await self._create_long_term_draft(
                persona=persona,
                admin_umo=event.unified_msg_origin,
                requirements=requirements or "重新规划完整大时间表",
                start_date=self._now().date(),
                previous_stage=previous,
                source="regenerate",
                mode="replace_all",
            )
        except Exception as exc:
            yield event.plain_result(f"重生成草稿失败：{exc}")
            return
        yield event.plain_result(
            "已生成替换全部阶段的草稿，使用 /大时间表 草稿 查看，批准后才会生效。"
        )

    @filter.command_group("主动消息")
    def proactive_group(self):
        """主动消息命令组；不提供子命令时由 AstrBot 输出帮助。"""
        pass

    @proactive_group.command("状态")
    async def proactive_status(self, event: AstrMessageEvent):
        persona, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if not plan.has_schedule:
            yield event.plain_result("今日没有日程，主动消息未安排。")
            return
        state = self.policy.ensure_state(
            event.unified_msg_origin, persona.id, plan, self._now()
        )
        yield event.plain_result(
            f"人格：{persona.id}\n今日预算：{state.sent_count}/{state.daily_budget}\n"
            f"连续未回复：{state.unanswered_count}"
        )

    @proactive_group.command("立即")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def trigger_now(self, event: AstrMessageEvent):
        persona, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        if not plan.has_schedule:
            yield event.plain_result("今日没有日程，无法发送测试主动消息。")
            return
        sent = await self._deliver(
            event.unified_msg_origin,
            persona,
            plan,
            "管理员要求立即测试主动消息",
            0,
            self._conversation_generation(event.unified_msg_origin),
        )
        yield event.plain_result(
            "测试主动消息已发送。" if sent else "会话状态已变化，测试主动消息未发送。"
        )

    @proactive_group.command("执行时间")
    async def proactive_execution_times(self, event: AstrMessageEvent):
        _, plan = await self._ensure_plan_for_umo(event.unified_msg_origin)
        entries = self._scheduled_proactive_entries(event.unified_msg_origin, plan)
        if not entries:
            yield event.plain_result("当前会话没有已安排的主动消息。")
            return
        lines = ["主动消息具体执行时间："]
        lines.extend(
            f"- {run_at.astimezone(self.timezone).strftime('%Y-%m-%d %H:%M:%S %z')}｜{label}"
            for run_at, label in entries
        )
        yield event.plain_result("\n".join(lines))
