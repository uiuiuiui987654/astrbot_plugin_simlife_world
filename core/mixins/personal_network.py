"""Optional link to the personal-network plugin: who she knows, who was there, what happened.

Everything here degrades to "no context" when the plugin is missing or fails.
"""

from __future__ import annotations

import random
from datetime import datetime

from astrbot.api import logger

from ..persona import PersonaContext

NETWORK_PLUGIN = "astrbot_plugin_personal_network"
SOURCE = "astrbot_plugin_simlife_world"
NETWORK_API = ("get_context_for_plugin", "record_life_event_from_plugin")
NEW_CHARACTER_REF = "new_char"


class PersonalNetworkMixin:
    def _network_settings(self) -> dict:
        return self.config.get("personal_network_integration", {}) or {}

    def _personal_network_plugin(self):
        """The network plugin instance when enabled, loaded and new enough; warns once otherwise."""
        if not self._network_settings().get("enable", False):
            return None
        lookup = getattr(self.context, "get_registered_star", None)
        meta = lookup(NETWORK_PLUGIN) if callable(lookup) else None
        plugin = meta.star_cls if meta and meta.activated and meta.star_cls else None
        if plugin is None or not all(hasattr(plugin, name) for name in NETWORK_API):
            if not self._personal_network_unavailable_logged:
                logger.warning(
                    "[模拟人生] 已启用人际关系联动，但没有找到可用的 personal_network 插件"
                )
                self._personal_network_unavailable_logged = True
            return None
        self._personal_network_unavailable_logged = False
        return plugin

    def _personal_network_status(self) -> str:
        if not self._network_settings().get("enable", False):
            return "未启用"
        try:
            connected = bool(self._personal_network_plugin())
        except Exception:
            logger.debug("[模拟人生] 查询人际关系插件状态失败", exc_info=True)
            connected = False
        return "已连接" if connected else "已启用但插件不可用"

    async def _generate_new_character(self, persona: PersonaContext) -> str:
        """Sometimes invent a new acquaintance, store it in the network and return a schedule hint ("" otherwise)."""
        try:
            chance = max(
                0.0,
                min(
                    1.0,
                    float(
                        self._network_settings().get("new_character_probability", 0.0)
                    ),
                ),
            )
        except (TypeError, ValueError):
            chance = 0.0
        if chance <= 0.0 or random.random() >= chance:
            return ""
        plugin = self._personal_network_plugin()
        if plugin is None or not hasattr(plugin, "upsert_batch_for_plugin"):
            return ""
        try:
            person = await self.plan_generator.generate_new_character(persona)
        except Exception:
            logger.exception("[模拟人生] 新人物生成失败 persona=%s", persona.id)
            return ""
        try:
            result = await plugin.upsert_batch_for_plugin(
                persona.id,
                characters=[
                    {
                        "ref": NEW_CHARACTER_REF,
                        **{
                            key: person[key]
                            for key in (
                                "name",
                                "bio",
                                "personality",
                                "preferences",
                                "facts",
                            )
                        },
                    }
                ],
                relationships=[
                    {
                        "source": "persona",
                        "target": NEW_CHARACTER_REF,
                        "type": person["relationship_type"],
                        "strength": 30,
                        "status": "active",
                        "description": person["relationship_description"],
                    }
                ],
                source=SOURCE,
            )
            if not result.get("updated"):
                logger.warning(
                    "[模拟人生] 人际关系插件拒绝写入新人物 persona=%s: %s",
                    persona.id,
                    result.get("reason", "unknown"),
                )
                return ""
            logger.info(
                "[模拟人生] 新人物已写入人际关系 persona=%s name=%s uuid=%s",
                persona.id,
                person["name"],
                result.get("refs", {}).get(NEW_CHARACTER_REF, ""),
            )
        except Exception:
            logger.exception("[模拟人生] 新人物写入人际关系失败 persona=%s", persona.id)
            return ""
        return (
            f"今天她会碰到 {person['name']}（{person['relationship_type']}，{person['relationship_description']}）。"
            f"这个人：{person['bio']}。"
            "在时间线里自然地安排一次见面，并把这个人在关系数据里的 id 填进那一项的 participant_ids。"
        )

    async def _personal_network_participants_context(
        self, persona_id: str, participant_ids: tuple[str, ...]
    ) -> str:
        """ "Who is with her right now" lines for the chat prompt."""
        if not participant_ids or not self._network_settings().get(
            "inject_current_participants", True
        ):
            return ""
        plugin = self._personal_network_plugin()
        if plugin is None or not hasattr(plugin, "get_network_for_plugin"):
            return ""
        try:
            network = await plugin.get_network_for_plugin(persona_id)
        except Exception:
            logger.exception("[模拟人生] 读取当前参与人物失败 persona=%s", persona_id)
            return ""
        wanted = set(participant_ids)
        present = [
            person
            for person in network.get("characters") or []
            if person.get("id") in wanted
        ]
        if not present:
            return ""

        def describe(person: dict) -> str:
            bio, personality = person.get("bio", ""), person.get("personality", "")
            extra = [bio, f"性格：{personality}" if personality else ""]
            return "- " + "；".join(
                [person.get("name", "（未知）"), *(part for part in extra if part)]
            )

        return "\n".join(["此刻和她在一起的人：", *map(describe, present)])

    async def _personal_network_context(self, persona_id: str) -> str:
        plugin = self._personal_network_plugin()
        if plugin is None:
            return ""
        try:
            limit = max(
                500,
                min(
                    12000, int(self._network_settings().get("max_context_chars", 4000))
                ),
            )
        except (TypeError, ValueError):
            limit = 4000
        try:
            return await plugin.get_context_for_plugin(persona_id, max_chars=limit)
        except Exception:
            logger.exception("[模拟人生] 读取人际关系上下文失败 persona=%s", persona_id)
            return ""

    async def _record_completed_personal_network_events(
        self, persona_id: str, now: datetime
    ) -> None:
        """Log finished timeline items that had participants as shared life events (idempotent per item)."""
        if not self._network_settings().get("record_completed_events", True):
            return
        plugin = self._personal_network_plugin()
        if plugin is None:
            return
        for plan in self.storage.plans.values():
            if plan.persona_id != persona_id or plan.status != "ok":
                continue
            for item in plan.timeline:
                if not item.participant_ids:
                    continue
                ended_at = self._end_time(plan.date, item.end)
                if ended_at > now:
                    continue
                try:
                    await plugin.record_life_event_from_plugin(
                        persona_id,
                        participant_ids=list(item.participant_ids),
                        event_type="virtual_schedule",
                        summary=item.activity
                        + (f"（地点：{item.location}）" if item.location else ""),
                        occurred_at=ended_at.isoformat(),
                        importance=50,
                        emotional_tone=plan.mood,
                        source=SOURCE,
                        source_key=f"{plan.date}:{item.id}",
                    )
                except ValueError as exc:
                    logger.warning(
                        "[模拟人生] 跳过人际关系事件 persona=%s item=%s: %s",
                        persona_id,
                        item.id,
                        exc,
                    )
                except Exception:
                    logger.exception(
                        "[模拟人生] 记录人际关系事件失败 persona=%s item=%s",
                        persona_id,
                        item.id,
                    )
