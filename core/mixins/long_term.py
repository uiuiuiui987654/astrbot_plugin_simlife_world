"""Long-term timeline upkeep: automatic renewal, drafts, admin notices, job overview."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain

from ..long_term import validate_stage_bundle
from ..models import DailyPlan
from ..persona import PersonaContext

RENEWAL_REQUIREMENT = (
    "接着上一个阶段往下排：经历要连得上，可以进入新的学期、假期、项目或生活阶段。"
)
JOB_LABELS = (("window-retry:", "延迟窗口"), ("window:", "日程窗口"))


def _stage_span(stage: dict) -> str:
    return f"{stage['name']}（{stage['start_date']} 至 {stage['end_date']}）"


class LongTermMixin:
    def _long_term_settings(self) -> dict:
        return self.config.get("long_term_settings", {}) or {}

    async def _check_long_term_renewals(self, target: date) -> None:
        """Renew every persona whose last approved stage has run out."""
        if not self._long_term_settings().get("enable", True):
            return
        for persona_id in {
            str(stage.get("persona_id", ""))
            for stage in self.long_term.stages
            if stage.get("persona_id")
        }:
            latest = self.long_term.latest_stage(persona_id)
            if not latest:
                continue
            ends = date.fromisoformat(latest["end_date"])
            if target >= ends and not self.long_term.has_stage_starting_after(
                persona_id, ends
            ):
                await self._run_long_term_renewal(persona_id)

    async def _run_long_term_renewal(self, persona_id: str) -> None:
        """Generate the next stages; on failure tell the admin and retry later (bounded)."""
        latest = self.long_term.latest_stage(persona_id)
        admin = self.long_term.notification_target(persona_id)
        if not latest or not admin:
            return
        attempt = self.renewal_attempts[persona_id] = (
            self.renewal_attempts.get(persona_id, 0) + 1
        )
        settings = self._long_term_settings()
        try:
            persona = await self.personas.resolve_id(persona_id, admin)
            stages = await self.plan_generator.generate_long_term_timeline(
                persona,
                start_date=date.fromisoformat(latest["end_date"]) + timedelta(days=1),
                previous_stage=latest,
                requirements=RENEWAL_REQUIREMENT,
            )
            await self.long_term.add_auto_renewal(persona_id, stages)
            self.image_renderer.invalidate_persona(persona_id)
            self.renewal_attempts.pop(persona_id, None)
            await self._notify_admin(
                admin,
                f"{persona_id} 的长期安排已自动续上："
                + "、".join(map(_stage_span, stages)),
            )
        except Exception as exc:
            logger.warning(
                "[虚拟人生] 大时间表自动续期失败 persona=%s: %s",
                persona_id,
                exc,
                exc_info=True,
            )
            await self._notify_admin(
                admin,
                f"{persona_id} 的长期安排到期了，自动续写第 {attempt} 次没成功：{exc}",
            )
            if attempt >= max(1, int(settings.get("renewal_max_attempts", 6))):
                return
            wait = max(1, int(settings.get("renewal_retry_minutes", 60)))
            self.runtime.add_date_job(
                f"pvd:long-term-renewal:{hashlib.sha1(persona_id.encode()).hexdigest()[:12]}",
                self._now() + timedelta(minutes=wait),
                self._run_long_term_renewal,
                persona_id,
            )

    async def _notify_admin(self, umo: str, text: str) -> None:
        try:
            await self.context.send_message(umo, MessageChain().message(text))
        except Exception as exc:
            logger.error("[虚拟人生] 没能通知管理员 %s: %s", umo, exc)

    def _scheduled_proactive_entries(
        self, umo: str, plan: DailyPlan
    ) -> list[tuple[datetime, str]]:
        """``(time, label)`` of this session's pending proactive jobs, soonest first."""
        jobs = dict(self.runtime.scheduled_jobs())
        prefix = f"pvd:{self._umo_hash(umo)}:"
        intents = {window.id: window.intent for window in plan.proactive_windows}
        entries = (
            [(jobs[prefix + "idle"], "沉默主动")] if jobs.get(prefix + "idle") else []
        )
        for job_id, run_at in jobs.items():
            if not job_id.startswith(prefix + "plan:"):
                continue
            name = job_id[len(prefix + "plan:") :]
            if name == "sleep":
                entries.append((run_at, "睡眠异常主动"))
                continue
            for marker, label in JOB_LABELS:
                if name.startswith(marker):
                    window_id = name[len(marker) :]
                    intent = intents.get(window_id)
                    entries.append(
                        (
                            run_at,
                            f"{label} [{window_id}]"
                            + (f" · {intent}" if intent is not None else ""),
                        )
                    )
                    break
        return sorted(entries)

    async def _refresh_persona_daily_plan(self, persona: PersonaContext) -> DailyPlan:
        plan = await self._ensure_plan(
            persona, self._now().date(), force=True, preserve_disabled=True
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
        """Render cards when images are on; fall back to text if rendering fails."""
        if not self.image_renderer.enabled:
            return [event.plain_result(fallback)]
        try:
            paths = [await job() for job in jobs]
        except Exception:
            logger.exception("[虚拟人生] 卡片没画出来，改发文字")
            return [event.plain_result("卡片没画出来，先看文字版：\n" + fallback)]
        return [event.plain_result(title), *map(event.image_result, paths)]

    @staticmethod
    def _parse_long_term_json(content: str, persona_id: str) -> list[dict]:
        """Admin-supplied JSON: a ``{"stages": [...]}`` bundle or one bare stage."""
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON 格式有误：{exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("最外层要是一个 JSON 对象")
        return validate_stage_bundle(
            payload if "stages" in payload else {"stages": [payload]}, persona_id
        )
