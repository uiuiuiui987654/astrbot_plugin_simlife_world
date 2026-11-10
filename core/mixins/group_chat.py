"""Group-chat privacy filtering and reply humanizing.

Mixin for SimLifeWorldPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

import re
from datetime import datetime

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.agent.message import TextPart
from astrbot.core.provider.entities import ProviderRequest

from .. import (
    camera_events,
    camera_photo,
)
from ..models import (
    DailyPlan,
)
from .common import (
    GROUP_OUTPUT_TERMS,
    GROUP_PRIVACY_RULE,
    GROUP_PRIVACY_TERMS,
    _group_message_text,
    _group_plan_terms,
)


class GroupChatMixin:
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
            text + "\n（这是群聊：不要主动提自己的日程、地点、穿搭或家具，"
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
                event.set_extra("simlife_group_terms", terms)
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
                        logger.debug("[模拟人生] _sanitize_group_request 出错，已忽略", exc_info=True)
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
            logger.debug("[模拟人生] 群聊请求隔离失败: %s", exc)

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
        cleaned = re.sub(r"\[?\d{4}-\d{2}-\d{2}(?:\s+[^\]\n]*?)?\]\s*", "", cleaned)
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
            and cls._plain_for_compare(cleaned) == cls._plain_for_compare(user_text)
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
            match = re.match(r"^(行|好|嗯|知道了|可以|没事)[，,。！!\s]+(.+)$", first)
            if match:
                tail = match.group(2).strip()
                if tail and protected.search(tail):
                    return first
                if tail and re.search(r"(把|别|先|去|你|再|记得|赶紧|顺便|还有)", tail):
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
            logger.debug("[模拟人生] _inject_group_life_state 出错，已忽略", exc_info=True)
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
        logger.info("[模拟人生] 群聊仅注入生理心情 umo=%s", event.unified_msg_origin)

    async def _camera_awareness_context(self, event: AstrMessageEvent) -> str:
        """Tell the character about recent observer-window photos on the next turn."""
        try:
            message_text = str(event.get_message_str() or "").strip()
        except Exception:
            logger.debug("[模拟人生] _camera_awareness_context 出错，已忽略", exc_info=True)
            message_text = ""
        if not message_text or message_text.startswith(("/", "／")):
            return ""
        try:
            persona = await self.personas.resolve(event.unified_msg_origin)
            events = camera_events.take_pending(
                self.data_dir, persona.id, now=self._now(), limit=2
            )
        except Exception:
            logger.debug("[模拟人生] _camera_awareness_context 出错，已忽略", exc_info=True)
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
            "[模拟人生] 注入拍照感知 persona=%s 数量=%s",
            persona.id,
            len(events),
        )
        return "\n".join(lines)
