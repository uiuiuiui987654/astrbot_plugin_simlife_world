"""Long-term timeline renewals and drafts.

Mixin for ProactiveVirtualDailyPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain

from ..long_term import validate_stage_bundle
from ..models import (
    DailyPlan,
)
from ..persona import PersonaContext


class LongTermMixin:
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
