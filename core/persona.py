"""Find the AstrBot persona (id + system prompt) a chat is using."""

from __future__ import annotations

from dataclasses import dataclass

from astrbot.api import logger

FALLBACK_PROMPT = "你是一个温和、乐于帮忙的伙伴。"
NO_PERSONA = "[%None]"  # AstrBot's marker for "persona explicitly disabled"


@dataclass(slots=True, frozen=True)
class PersonaContext:
    id: str
    prompt: str


class PersonaResolver:
    def __init__(self, context):
        self.context = context

    async def _conversation_persona_id(self, umo: str) -> str | None:
        manager = self.context.conversation_manager
        try:
            conversation_id = await manager.get_curr_conversation_id(umo)
            if not conversation_id:
                return None
            conversation = await manager.get_conversation(umo, conversation_id)
        except Exception as exc:
            logger.warning("[模拟人生] 读不到这个会话的人格 %s: %s", umo, exc)
            return None
        return getattr(conversation, "persona_id", None)

    async def _prompt_of(self, persona_id: str) -> str:
        """System prompt of a stored persona, or ``""`` when it has none / cannot be read."""
        try:
            persona = await self.context.persona_manager.get_persona(persona_id)
        except Exception:
            logger.debug("[模拟人生] 读取人格 %s 失败", persona_id, exc_info=True)
            return ""
        return str(getattr(persona, "system_prompt", "") or "").strip()

    async def resolve(self, umo: str | None) -> PersonaContext:
        """The chat's own persona if it has one, otherwise AstrBot's default persona."""
        chosen = await self._conversation_persona_id(umo) if umo else None
        if chosen and chosen != NO_PERSONA:
            prompt = await self._prompt_of(chosen)
            if prompt:
                return PersonaContext(str(chosen), prompt)
        try:
            default = await self.context.persona_manager.get_default_persona_v3(umo=umo)
        except Exception as exc:
            logger.warning("[模拟人生] 改用默认人格：%s", exc)
            return PersonaContext("default", FALLBACK_PROMPT)
        return PersonaContext(str(default.get("name", "default")), str(default.get("prompt", "") or FALLBACK_PROMPT))

    async def resolve_id(self, persona_id: str, fallback_umo: str | None = None) -> PersonaContext:
        """Load a specific persona; raise if it no longer exists and the fallback differs."""
        prompt = await self._prompt_of(persona_id)
        if prompt:
            return PersonaContext(persona_id, prompt)
        try:
            legacy = self.context.persona_manager.get_persona_v3_by_id(persona_id)
        except Exception:
            logger.debug("[模拟人生] 读取人格 %s 失败", persona_id, exc_info=True)
            legacy = None
        if legacy:
            return PersonaContext(persona_id, str(legacy.get("prompt", "") or ""))
        resolved = await self.resolve(fallback_umo)
        if resolved.id != persona_id:
            raise RuntimeError(f"找不到人格 {persona_id}")
        return resolved
