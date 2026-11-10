from __future__ import annotations

import asyncio
import base64
import json
import re
import sys
from pathlib import Path
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.message_components import Image, Plain
from astrbot.api.star import Context, Star, StarTools
from astrbot.core.agent.message import TextPart
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.provider.entities import LLMResponse, ProviderRequest
from astrbot.core.star.filter.command import GreedyStr

from .core.context_injection import SmartContextInjector
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
from .core import migrations
from .core import platforms
from .core import privacy
from .core import character_assets
from .core import wardrobe
from .core import (
    affection,
    books,
    camera_photo,
    delivery,
    diary,
    garage,
    goods,
    money,
    view_state,
    weekly,
    world_events,
)
from .core.generator import DailyPlanGenerator
from .core.image_renderer import ScheduleImageRenderer
from .core.interaction import InteractionService
from .core.long_term import LongTermTimelineStore
from .core.message_generator import ProactiveMessageGenerator
from .core.message_segmenter import ProactiveMessageSegmenter
from .core.models import (
    ScheduleRequirement,
)
from .core.persona import PersonaResolver
from .core.proactive import ProactivePolicy, session_kind
from .core.reply_delay import (
    ReplyDelayCoordinator,
    ReplyDelayPolicy,
)
from .core.runtime import SchedulerRuntime
from .core.schedule_edit import insert_garage_trip
from .core.storage import PluginStorage
from .core.user_state import UserStateStore
from .core.utils import (
    format_plan,
    parse_schedule_date_range,
)
from .core.view_api import VirtualLifeViewAPI
from .core.mixins.common import (
    _plugin_version,
    _migrate_legacy_data,
    _frontend_ui_version,
)
from .core.mixins.runtime_state import RuntimeStateMixin
from .core.mixins.personal_network import PersonalNetworkMixin
from .core.mixins.planning import PlanningMixin
from .core.mixins.scheduling import SchedulingMixin
from .core.mixins.proactive import ProactiveMixin
from .core.mixins.interactions import InteractionsMixin
from .core.mixins.long_term import LongTermMixin
from .core.mixins.reply_delay import ReplyDelayMixin
from .core.mixins.incoming import IncomingMixin
from .core.mixins.group_chat import GroupChatMixin
from .core.mixins.life_context import LifeContextMixin
from .core.mixins.chat_activity import ChatActivityMixin
from .core.mixins.life_events import LifeEventsMixin
from .core.mixins.admin_commands import AdminCommandsMixin


class ProactiveVirtualDailyPlugin(
    RuntimeStateMixin,
    PersonalNetworkMixin,
    PlanningMixin,
    SchedulingMixin,
    ProactiveMixin,
    InteractionsMixin,
    LongTermMixin,
    ReplyDelayMixin,
    IncomingMixin,
    GroupChatMixin,
    LifeContextMixin,
    ChatActivityMixin,
    LifeEventsMixin,
    AdminCommandsMixin,
    Star,
):
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
            logger.debug("[虚拟人生] _resolve_timezone 出错，已忽略", exc_info=True)
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
        try:
            # 升级旧格式的数据文件（先备份），必须在任何模块读文件之前
            await asyncio.to_thread(
                migrations.migrate_all,
                self.data_dir,
                plugin_version=_plugin_version(),
            )
        except Exception as exc:
            logger.warning("[虚拟人生] 数据版本检查失败，继续使用原数据：%s", exc)
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

    # ------------------------------------------------------- 发言机会（自主决定）

    # ------------------------------------------------------------- interactions

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE, priority=999)
    async def on_friend_message(self, event: AstrMessageEvent) -> None:
        await self._handle_incoming(event)

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE, priority=998)
    async def on_group_message(self, event: AstrMessageEvent) -> None:
        await self._handle_incoming(event)

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
                logger.debug("[虚拟人生] inject_virtual_state 出错，已忽略", exc_info=True)
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
                    logger.debug("[虚拟人生] inject_virtual_state 出错，已忽略", exc_info=True)
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
                    logger.debug("[虚拟人生] inject_virtual_state 出错，已忽略", exc_info=True)
                    recent_delivery_text = ""
                world_event_text = ""
                try:
                    garage_text = garage.context(
                        self.data_dir,
                        wallet_persona.id,
                        now=self._now(),
                    )
                except Exception:
                    logger.debug("[虚拟人生] inject_virtual_state 出错，已忽略", exc_info=True)
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
                    logger.debug("[虚拟人生] inject_virtual_state 出错，已忽略", exc_info=True)
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
                    logger.debug("[虚拟人生] inject_virtual_state 出错，已忽略", exc_info=True)
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
                    logger.debug("[虚拟人生] inject_virtual_state 出错，已忽略", exc_info=True)
            except Exception:
                logger.debug("[虚拟人生] inject_virtual_state 出错，已忽略", exc_info=True)
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
                logger.debug("[虚拟人生] inject_virtual_state 出错，已忽略", exc_info=True)
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
                logger.debug("[虚拟人生] inject_virtual_state 出错，已忽略", exc_info=True)
        try:
            memory = self._life_memory_context(
                persona.id, now, event.get_message_str()
            )
            if memory:
                req.extra_user_content_parts.append(
                    TextPart(text=memory).mark_as_temp()
                )
        except Exception:
            logger.debug("[虚拟人生] inject_virtual_state 出错，已忽略", exc_info=True)
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
                logger.debug("[虚拟人生] humanize_outgoing 出错，已忽略", exc_info=True)

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
                            logger.debug("[虚拟人生] track_delayed_llm_response 出错，已忽略", exc_info=True)
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
                        logger.debug("[虚拟人生] track_delayed_llm_response 出错，已忽略", exc_info=True)
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
            logger.debug("[虚拟人生] maybe_schedule_chat_activity 出错，已忽略", exc_info=True)
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
                logger.debug("[虚拟人生] take_selfie 出错，已忽略", exc_info=True)
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

        async def deliver(component) -> bool:
            return bool(
                await self.context.send_message(
                    event.unified_msg_origin, MessageChain(chain=[component])
                )
            )

        # 不同平台接受的图片来源不同：base64 发不出去时改用本地文件再试
        sent, method = await platforms.send_image(
            deliver, Image, image_data, data_dir=self.data_dir
        )
        if not sent:
            logger.warning("[虚拟人生] 自拍发送失败: %s", method)
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
            logger.debug("[虚拟人生] read_book 出错，已忽略", exc_info=True)
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
            logger.debug("[虚拟人生] add_reading_note 出错，已忽略", exc_info=True)
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

    @virtual_life_group.command("平台测试")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def platform_test(self, event: AstrMessageEvent):
        """在当前聊天测试文字和图片的几种发送方式，结果记入 /虚拟人生 自检。"""
        umo = event.unified_msg_origin
        try:
            platform = str(event.get_platform_name() or "")
        except Exception:
            logger.debug("[虚拟人生] platform_test 出错，已忽略", exc_info=True)
            platform = ""
        platform = platform or umo.split(":", 1)[0] or "unknown"
        results: dict[str, str] = {}

        async def attempt(key: str, chain: MessageChain) -> None:
            try:
                sent = await self.context.send_message(umo, chain)
                results[key] = "ok" if sent else "fail: 平台返回发送失败"
            except Exception as exc:
                logger.warning("[虚拟人生] 平台测试 %s 失败: %s", key, exc)
                results[key] = f"fail: {type(exc).__name__}"

        png = platforms.tiny_png()
        path = platforms.spool_image(self.data_dir, png)
        await attempt("text", MessageChain().message("【平台测试 1/4】主动发文字"))
        await attempt("image_file", MessageChain(chain=[Image.fromFileSystem(str(path))]))
        await attempt(
            "image_base64",
            MessageChain(chain=[Image.fromBase64(base64.b64encode(png).decode("ascii"))]),
        )
        results["reply_image"] = "sent"
        platforms.record_check(self.data_dir, platform, results, now=self._now())
        labels = "\n".join(
            f"{label}：{results.get(key, '未测')}"
            for key, label in platforms.CHECK_LABELS.items()
        )
        yield event.plain_result(
            f"平台：{platforms.platform_label(platform)}\n{labels}\n"
            "第 2、3 张应是淡紫色小方块；下面再发一张作为指令回复（4/4）。"
            "没收到的那一项就是这个平台不支持的方式。"
        )
        yield event.image_result(str(path))

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
                logger.debug("[虚拟人生] self_check 出错，已忽略", exc_info=True)
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
                logger.debug("[虚拟人生] self_check 出错，已忽略", exc_info=True)
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
        lines.append(migrations.summary(migrations.load_manifest(self.data_dir)))
        camera_config = (self.config.get("camera_settings", {}) or {}) if hasattr(self.config, "get") else {}
        lines.append(
            "绘图密钥来源："
            + privacy.describe_secret_source(
                camera_config.get("api_key"), fallback_env="SIMLIFE_IMAGE_API_KEY"
            )
        )
        lines.append("平台测试：\n" + platforms.format_checks(platforms.load_checks(self.data_dir)))
        yield event.plain_result("\n".join(lines))

    @filter.command("回复延迟")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def reply_delay_command(self, event: AstrMessageEvent, action: str):
        yield event.plain_result(await self._cmd_reply_delay(event, action))

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
        for result in await self._cmd_show_schedule(event):
            yield result

    @virtual_daily_group.command("穿搭")
    async def show_outfit(self, event: AstrMessageEvent):
        """查看今日穿搭图片。"""
        for result in await self._cmd_show_outfit(event):
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
        yield event.plain_result(await self._cmd_rewrite_all(event, extra))

    @virtual_daily_group.command("重写日程")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def rewrite_daily_timeline(
        self, event: AstrMessageEvent, extra: str | None = None
    ):
        """保留主题、心情与穿搭，只重写今日时间日程。"""
        yield event.plain_result(await self._cmd_rewrite_part(event, extra, part="schedule"))

    @virtual_daily_group.command("重写穿搭")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def rewrite_daily_outfit(
        self, event: AstrMessageEvent, extra: str | None = None
    ):
        """保留主题、心情与时间日程，只重写今日穿搭。"""
        yield event.plain_result(await self._cmd_rewrite_part(event, extra, part="outfit"))

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
        yield event.plain_result(await self._cmd_long_term_generate(event, requirements))

    @long_term_group.command("导入")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_import(self, event: AstrMessageEvent, content: str):
        """导入结构化 JSON 为替换全部阶段的草稿。"""
        yield event.plain_result(await self._cmd_long_term_import(event, content))

    @long_term_group.command("草稿")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_draft(self, event: AstrMessageEvent):
        """查看当前人格待批准草稿。"""
        for result in await self._cmd_long_term_draft(event):
            yield result

    @long_term_group.command("批准")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_approve(self, event: AstrMessageEvent):
        """批准草稿并重新生成今日日程。"""
        yield event.plain_result(await self._cmd_long_term_approve(event))

    @long_term_group.command("拒绝")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_reject(
        self, event: AstrMessageEvent, feedback: str | None = None
    ):
        """拒绝草稿；提供修改意见时重新生成。"""
        yield event.plain_result(await self._cmd_long_term_reject(event, feedback))

    @long_term_group.command("列表")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_list(self, event: AstrMessageEvent):
        """查看当前人格全部已批准阶段。"""
        for result in await self._cmd_long_term_list(event):
            yield result

    @long_term_group.command("查看")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_view(
        self, event: AstrMessageEvent, stage_id: str | None = None
    ):
        """查看阶段；可省略参数或输入阶段 ID、名称及唯一片段。"""
        for result in await self._cmd_long_term_view(event, stage_id):
            yield result

    @long_term_group.command("重生成")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def long_term_regenerate(
        self, event: AstrMessageEvent, requirements: str | None = None
    ):
        """重新生成替换全部阶段的草稿。"""
        yield event.plain_result(await self._cmd_long_term_regenerate(event, requirements))

    @filter.command_group("主动消息")
    def proactive_group(self):
        """主动消息命令组；不提供子命令时由 AstrBot 输出帮助。"""
        pass

    @proactive_group.command("状态")
    async def proactive_status(self, event: AstrMessageEvent):
        yield event.plain_result(await self._cmd_proactive_status(event))

    @proactive_group.command("立即")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def trigger_now(self, event: AstrMessageEvent):
        yield event.plain_result(await self._cmd_proactive_now(event))

    @proactive_group.command("执行时间")
    async def proactive_execution_times(self, event: AstrMessageEvent):
        yield event.plain_result(await self._cmd_proactive_times(event))
