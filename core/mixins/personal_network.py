"""Bridge to the personal-network plugin (new characters, shared events).

Mixin for ProactiveVirtualDailyPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from astrbot.api import logger

from ..persona import PersonaContext


class PersonalNetworkMixin:
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
            logger.debug("[虚拟人生] _personal_network_status 出错，已忽略", exc_info=True)
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
