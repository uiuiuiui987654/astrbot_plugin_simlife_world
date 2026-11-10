"""Writes proactive messages: assembles the prompt, asks the LLM, records the result."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from astrbot.api import logger
from astrbot.core.agent.message import AssistantMessageSegment, TextPart, UserMessageSegment

from .human_style import CURRENT_STATE_RULE, HUMAN_PROACTIVE_RULE
from .persona import PersonaContext
from .state_hints import state_hints

PROACTIVE_MARK = "（你主动发起的消息）"
NO_HISTORY = "无"
RESPONSE_TEXT_FIELDS = ("completion_text", "completion", "text", "content")

FOLLOW_UP_RULE = (
    "\n\n【衔接要求】上面是你们最近的对话：如果最后几轮里对方说了具体的事"
    "（在忙什么、刚聊到的话题、提到的东西），优先接着那件事说；"
    "不要凭空开一个和上文无关的新话题，也不要重复你上一次主动说过的状态。"
)
FRESH_ANGLE_RULE = (
    "这次必须换一个真正的角度：不要复述同一件家务、同一个动作、同一个数字、同一种比喻；"
    "如果上面最近几条都属于同一个主题或同一个场景（例如都在说起床、早饭、换衣服、天气、出门），"
    "这次不要再用同类问候、同一种开场和收尾，必须换成一个完全不同的主题或由头；"
    "可以聊对方的事、刚发生的小变化、一件具体的见闻，或者一件新进展；"
    "如果实在没有新的东西可说，就保持沉默。"
)
DECIDE_RULE = (
    "\n\n【先决定要不要开口】这次不是必须说话。先掂量此刻开口是否自然："
    "对方刚说完话/正在聊天、你正忙或专注、刚主动说过、没什么具体由头时，"
    "就应该选择不说；只有真的想说（有具体的事、确实想他、有明确由头）才开口。"
    "不要为了刷存在感而说话。"
    '只输出 JSON：{"decision":"send" 或 "silent",'
    '"reason":"一句话理由","text":"要说的话，silent 时留空"}'
)
GROUP_DECIDE_RULE = (
    "\n\n【群聊补充】这是群聊，不是一对一私聊。群聊安静、没人接话时，"
    "可以更主动地打破冷场：有具体见闻、想分享的小事、或一句自然的吐槽，"
    "就优先选择 send；不要因为怕打扰而习惯性沉默，也不要为了活跃而硬开话题。"
)

SEND_WORDS = frozenset({"send", "yes"})
DECISION_WORDS = SEND_WORDS | {"silent", "skip", "no"}
HINT_LINE = re.compile(r"^\s*(\d+)\s*[:：]\s*(.+?)\s*$")


def _text_of(content: Any) -> Any:
    """Flatten a multi-part message into its text parts; other content passes through."""
    if not isinstance(content, list):
        return content
    return " ".join(
        str(part.get("text", "")) for part in content if isinstance(part, dict) and part.get("type") == "text"
    )


class ProactiveMessageGenerator:
    def __init__(self, context, config):
        self.context = context
        self.config = config

    def _delivery(self) -> dict:
        return self.config.get("delivery_settings", {}) or {}

    # ------------------------------------------------------------------ prompt

    async def generate(
        self,
        *,
        umo: str,
        persona: PersonaContext,
        current_time: datetime,
        current_state: str,
        intent: str,
        unanswered_count: int,
        relationship_context: str = "",
        timeline_context: str = "",
        recent_sent: list[str] | None = None,
        retry_note: str = "",
        decide: bool = False,
        include_history: bool = True,
        group_mode: bool = False,
    ) -> str:
        """The message to send; ``""`` when the model chose to stay silent (``decide=True``)."""
        settings = self._delivery()
        task = str(settings.get("proactive_prompt", "")).format(
            current_time=current_time.strftime("%Y-%m-%d %H:%M"),
            current_state=current_state,
            intent=intent,
            unanswered_count=unanswered_count,
            unanswered_hint=self._build_unanswered_hint(settings, unanswered_count),
        )
        history = (
            await self._recent_history(umo, int(settings.get("recent_chat_messages", 8))) if include_history else NO_HISTORY
        )
        parts = [
            f"<persona>\n{persona.prompt}\n</persona>\n\n<recent_conversation>\n{history}\n</recent_conversation>\n\n{task}",
            HUMAN_PROACTIVE_RULE,
        ]
        if history and history.strip() != NO_HISTORY:
            parts.append(FOLLOW_UP_RULE)
        if recent_sent:
            said = "\n".join(f"- {line}" for line in recent_sent[:8])
            parts.append(
                f"\n\n<recent_proactive>\n你最近已经主动说过的话（不要重复这些内容、场景和句式）：\n{said}\n</recent_proactive>\n"
                + FRESH_ANGLE_RULE
            )
        if retry_note:
            parts.append("\n\n【重写要求】" + retry_note)
        if decide:
            parts.append(DECIDE_RULE + (GROUP_DECIDE_RULE if group_mode else ""))
        if timeline_context:
            parts += ["\n\n" + block for block in (timeline_context, *state_hints(timeline_context))]
        if relationship_context:
            parts.append("\n\n" + relationship_context)
        if timeline_context:
            parts.append(CURRENT_STATE_RULE)

        raw = await self._ask(umo, "".join(parts))
        if not decide:
            return raw
        verdict = self.parse_decision(raw)
        if not verdict:
            return raw
        if verdict["decision"] != "send":
            logger.info("[虚拟人生] 这次决定不开口 umo=%s 理由=%s", umo, verdict["reason"] or "无")
            return ""
        return verdict["text"].strip()

    async def _ask(self, umo: str, prompt: str) -> str:
        provider_id = str((self.config.get("schedule_settings", {}) or {}).get("proactive_llm_provider") or "").strip()
        provider = (self.context.get_provider_by_id(provider_id) if provider_id else None) or self.context.get_using_provider()
        if not provider:
            raise RuntimeError("no LLM provider available")
        response = await provider.text_chat(prompt, session_id=f"proactive_message::{umo}")
        for name in RESPONSE_TEXT_FIELDS:
            value = getattr(response, name, None)
            if isinstance(value, str) and value.strip():
                return value.strip()
        raise RuntimeError("LLM returned empty proactive message")

    @staticmethod
    def parse_decision(raw: str) -> dict:
        """``{"decision": "send"|"silent", "reason", "text"}`` from the model's JSON, or ``{}``."""
        found = re.search(r"\{.*\}", str(raw or ""), re.S)
        if not found:
            return {}
        try:
            data = json.loads(found.group(0))
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        word = str(data.get("decision") or "").strip().lower()
        if word not in DECISION_WORDS:
            return {}
        return {
            "decision": "send" if word in SEND_WORDS else "silent",
            "reason": str(data.get("reason") or "").strip()[:120],
            "text": str(data.get("text") or "").strip(),
        }

    # ------------------------------------------------------------------ unanswered hint

    @staticmethod
    def _build_unanswered_hint(settings: dict, count: int) -> str:
        method = str(settings.get("unanswered_hint_method", "segmented") or "segmented").strip().lower()
        if method != "placeholder":
            return ProactiveMessageGenerator._parse_unanswered_hint(settings.get("unanswered_hint_template", ""), count)
        template = str(settings.get("unanswered_hint_placeholder_template", "") or "").strip()
        if not template:
            return ""
        try:
            return template.format(unanswered_count=max(0, int(count)))
        except (KeyError, IndexError, ValueError, TypeError):
            return ""

    @staticmethod
    def _parse_unanswered_hint(template: object, count: int) -> str:
        """Lines look like ``<n>: <text>``; the line with the highest ``n`` not above ``count`` wins."""
        try:
            count = max(0, int(count))
        except (TypeError, ValueError):
            count = 0
        candidates = []
        for order, line in enumerate(str(template).splitlines()):
            found = HINT_LINE.match(line)
            if found and found.group(2).strip() and int(found.group(1)) <= count:
                candidates.append((int(found.group(1)), order, found.group(2).strip()))
        return max(candidates)[2] if candidates else ""

    # ------------------------------------------------------------------ conversation history

    async def _load_history(self, umo: str) -> list | None:
        manager = self.context.conversation_manager
        conversation_id = await manager.get_curr_conversation_id(umo)
        if not conversation_id:
            return None
        conversation = await manager.get_conversation(umo, conversation_id)
        raw = getattr(conversation, "history", "[]")
        history = json.loads(raw) if isinstance(raw, str) else raw
        return history if isinstance(history, list) else None

    async def _recent_history(self, umo: str, count: int) -> str:
        if count <= 0:
            return NO_HISTORY
        try:
            history = await self._load_history(umo)
            if history is None:
                return NO_HISTORY
            lines = [
                f"{item.get('role', 'unknown')}: {_text_of(item.get('content', ''))}"
                for item in history[-count:]
                if isinstance(item, dict)
            ]
            return "\n".join(lines) or NO_HISTORY
        except Exception as exc:
            logger.debug("[虚拟人生] 读取历史失败 %s: %s", umo, exc)
            return NO_HISTORY

    async def recent_proactive_texts(self, umo: str, limit: int = 5) -> list[str]:
        """Her last few self-initiated messages, newest first."""
        if limit <= 0:
            return []
        try:
            history = await self._load_history(umo)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("[虚拟人生] 读取主动消息历史失败 %s: %s", umo, exc)
            return []
        texts: list[str] = []
        prompt_before = ""
        for item in history or []:
            if not isinstance(item, dict):
                continue
            role = item.get("role", "")
            text = str(_text_of(item.get("content", "")) or "").strip()
            if role == "user":
                prompt_before = text
            elif role == "assistant":
                if text and prompt_before.startswith(PROACTIVE_MARK):
                    texts.append(text)
                prompt_before = ""
        return texts[-limit:][::-1]

    def _history_note(self, intent: str) -> str:
        template = str(self._delivery().get("proactive_history_note_template", "")).strip()
        fallback = f"{PROACTIVE_MARK}\n背景：{intent}"
        if not template:
            return fallback
        try:
            return template.format(intent=intent)
        except (KeyError, IndexError, ValueError):
            return fallback

    async def record_conversation(self, *, umo: str, persona_id: str, intent: str, assistant_text: str) -> bool:
        """Store the proactive message in the chat history so later replies know she said it."""
        manager = self.context.conversation_manager
        try:
            conversation_id = await manager.get_curr_conversation_id(umo) or await manager.new_conversation(
                umo, persona_id=persona_id
            )
            if not conversation_id:
                logger.warning("[虚拟人生] 主动消息未写入上下文：无法创建对话 umo=%s", umo)
                return False
            await manager.add_message_pair(
                cid=conversation_id,
                user_message=UserMessageSegment(content=[TextPart(text=self._history_note(intent))]),
                assistant_message=AssistantMessageSegment(content=[TextPart(text=assistant_text)]),
            )
            logger.info("[虚拟人生] 主动消息已写入对话上下文 umo=%s conversation=%s", umo, conversation_id)
            return True
        except Exception as exc:
            logger.error("[虚拟人生] 主动消息写入对话上下文失败 umo=%s: %s", umo, exc)
            return False
