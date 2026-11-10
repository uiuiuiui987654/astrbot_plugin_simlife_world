"""State snapshot, trips, backup / restore, diagnostics and activity history."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from astrbot.api import logger

from .. import (
    affection,
    diagnostics,
    diary,
    garage,
    health_journal,
    holiday_calendar,
    integrations,
    life_memory,
    money,
    privacy,
    travel,
    view_state,
    world_events,
)
from ..jsonio import atomic_write_json
from .context import RouteContext


class SystemRoutes:
    """Mixin for VirtualLifeViewAPI; expects ``self.plugin`` and ``self.plans_path``."""

    def _get_integrations(self, ctx: RouteContext) -> dict:
        """GET integrations"""
        return integrations.collect_integrations(self.plugin)

    def _get_trips(self, ctx: RouteContext) -> dict:
        """GET trips"""
        now = ctx.now
        params = ctx.params
        target_persona = str(params.get("persona") or "").strip()
        if not target_persona:
            return {"ok": False, "error": "缺少人格"}
        service = travel.TravelService(
            self.plans_path.parent,
            Path(__file__).with_name("travel_destinations.json"),
        )
        trips = []
        for trip in service.trips_for(target_persona):
            item = trip.to_dict()
            item["phase"] = service.phase(trip, now.date())
            item["length"] = trip.length
            trips.append(item)
        trips.sort(key=lambda item: (
            str(item.get("depart") or ""),
            str(item.get("id") or ""),
        ))
        return {
            "ok": True,
            "today": now.date().isoformat(),
            "trips": trips,
        }

    def _get_backup(self, ctx: RouteContext) -> dict:
        """GET backup"""
        now = ctx.now
        files = {}
        for path in sorted(self.plans_path.parent.glob("*.json")):
            try:
                files[path.name] = json.loads(
                    path.read_text(encoding="utf-8")
                )
            except (OSError, ValueError, TypeError):
                continue
        result = {
            "ok": True,
            "exported_at": now.isoformat(timespec="seconds"),
            "files": files,
        }
        if str(ctx.params.get("safe") or "") in {"1", "true", "yes"}:
            # 脱敏导出：隐藏会话标识、去掉只属于本机的文件，方便附在 issue 里
            result["files"], result["privacy"] = privacy.sanitize_backup(files)
        return result

    def _get_state(self, ctx: RouteContext) -> dict:
        """GET state"""
        now = ctx.now
        params = ctx.params
        persona = ctx.persona
        preview = view_state.parse_preview_time(params.get("time"))
        state = view_state.build_state(
            self.plans_path, persona, preview, now=now
        )
        state["user_state"] = self.plugin.user_states.snapshot(now)
        pending_persona = persona or str(state.get("persona") or "")
        state["pending_actions"] = view_state.load_pending_actions(
            self.plans_path, pending_persona or None
        )
        try:
            travel_service = travel.TravelService(
                self.plans_path.parent,
                Path(__file__).with_name("travel_destinations.json"),
            )
            upcoming = travel_service.upcoming(
                pending_persona or "",
                now.date(),
            )
            if upcoming is None:
                upcoming = travel_service.current(
                    pending_persona or "",
                    now.date(),
                )
            if upcoming is not None:
                state["travel"] = {
                    "city": upcoming.city,
                    "depart": upcoming.depart,
                    "back": upcoming.back,
                    "days": upcoming.length,
                    "transport": upcoming.transport,
                    "phase": travel_service.phase(
                        upcoming, now.date()
                    ),
                    "days_until": (
                        upcoming.depart_date - now.date()
                    ).days,
                }
        except (OSError, ValueError, TypeError):
            pass
        try:
            calendar = holiday_calendar.ChinaHolidayCalendar()
            state["holidays"] = {
                "today": calendar.on(now.date()),
                "upcoming": calendar.upcoming(now.date(), 14)[:6],
            }
        except (OSError, ValueError, TypeError, ImportError):
            pass
        try:
            wallet = money.snapshot(
                self.plans_path.parent,
                pending_persona or "",
                limit=80,
            )
            today_key = now.date().isoformat()
            today_income = 0.0
            today_expense = 0.0
            for tx in wallet.get("transactions") or []:
                if not str(tx.get("at") or "").startswith(today_key):
                    continue
                amount = float(tx.get("amount") or 0)
                if amount >= 0:
                    today_income += amount
                else:
                    today_expense -= amount
            state["wallet"] = {
                "balance": wallet.get("balance"),
                "goal": wallet.get("goal"),
                "today_income": round(today_income, 2),
                "today_expense": round(today_expense, 2),
            }
        except (OSError, ValueError, TypeError):
            pass
        try:
            state["health"] = health_journal.persona_state(
                self.plans_path.parent,
                pending_persona or "",
                today=now.date(),
            )
        except (OSError, ValueError, TypeError):
            pass
        return state

    def _get_recent_activity(self, ctx: RouteContext) -> dict:
        """GET recent_activity"""
        now = ctx.now
        params = ctx.params
        target_persona = str(params.get("persona") or "").strip()
        if not target_persona:
            return {"ok": False, "error": "缺少人格"}
        events = []
        # 生活记忆：吃了什么、路上见闻、和主人的互动……按天同步后并入动态
        memory_kinds = {
            "meal": "meal",
            "encounter": "way",
            "outing": "way",
            "interaction": "together",
            "photo": "together",
            "milestone": "together",
            "delivery": "life",
            "shopping": "life",
        }
        for offset in range(6, -1, -1):
            day = now.date() - timedelta(days=offset)
            storage = getattr(self.plugin, "storage", None)
            plan = storage.get_plan(day.isoformat(), target_persona) if storage else None
            try:
                items = life_memory.sync_day(
                    self.plans_path.parent,
                    target_persona,
                    day,
                    plan,
                    now=now if offset == 0 else None,
                )
            except Exception:
                logger.debug("[模拟人生] 动态读取生活记忆失败", exc_info=True)
                items = []
            for item in items:
                kind = memory_kinds.get(str(item.get("kind") or ""))
                if not kind:
                    continue
                time_text = str(item.get("time") or "") or "23:59"
                events.append({
                    "at": f"{day.isoformat()}T{time_text}:00",
                    "kind": kind,
                    "icon": str(item.get("icon") or "·"),
                    "title": str(item.get("text") or ""),
                    "detail": "",
                })
        for entry in diary.list_entries(
            self.plans_path.parent, target_persona, limit=20
        ):
            events.append({
                "at": str(
                    entry.get("created_at")
                    or entry.get("at")
                    or entry.get("date")
                    or ""
                ),
                "kind": "diary",
                "icon": "📔",
                "title": str(entry.get("title") or "写了一篇日记"),
                "detail": str(
                    entry.get("summary")
                    or entry.get("text")
                    or ""
                )[:160],
            })
        for event in world_events.list_recent(
            self.plans_path.parent, target_persona, limit=12
        ):
            events.append({
                "at": str(event.get("date") or ""),
                "kind": "world",
                "icon": "🌤️",
                "title": str(event.get("title") or "小世界"),
                "detail": str(event.get("summary") or "")[:160],
            })
        try:
            history = json.loads(
                (self.plans_path.parent / "cooking_history.json")
                .read_text(encoding="utf-8")
            )
        except (OSError, ValueError, TypeError):
            history = []
        for item in (history if isinstance(history, list) else [])[-10:]:
            if not isinstance(item, dict):
                continue
            events.append({
                "at": str(item.get("at") or ""),
                "kind": "cooking",
                "icon": "🍳",
                "title": "做了" + str(item.get("dish") or "一道菜"),
                "detail": str(item.get("score") or 0) + " 分 · " +
                str(item.get("grade") or "") + " · " +
                str(item.get("label") or ""),
            })
        wallet = money.snapshot(
            self.plans_path.parent, target_persona, limit=30
        )
        for tx in wallet.get("transactions") or []:
            amount = float(tx.get("amount") or 0)
            events.append({
                "at": str(tx.get("at") or ""),
                "kind": "money",
                "icon": "💰",
                "title": str(tx.get("reason") or "一笔流水"),
                "detail": ("+" if amount >= 0 else "") +
                f"{amount:g} 元",
            })
        garage_state = garage.snapshot(
            self.plans_path.parent, target_persona, now=now
        )
        for item in garage_state.get("history") or []:
            events.append({
                "at": str(item.get("started_at") or ""),
                "kind": "garage",
                "icon": "🚗",
                "title": "去了" + str(item.get("destination") or "兜风"),
                "detail": (
                    "主人带" if item.get("driver") == "master"
                    else "自己开"
                ) + " · " + {"returned": "已回来", "out": "还在外面"}.get(
                    str(item.get("status") or ""), str(item.get("status") or "")
                ),
            })
        health = health_journal.persona_state(
            self.plans_path.parent, target_persona, today=now.date()
        )
        for episode in health.get("episodes") or []:
            if not isinstance(episode, dict):
                continue
            events.append({
                "at": str(episode.get("onset") or ""),
                "kind": "health",
                "icon": "❤️",
                "title": "生了一场病",
                "detail": str(episode.get("days") or 0) + " 天 · " +
                ("已恢复" if episode.get("recovered") else "恢复中"),
            })
        for recovery in health.get("recovery_log") or []:
            if not isinstance(recovery, dict):
                continue
            actions = [
                str(item)
                for item in (recovery.get("actions") or [])
                if str(item).strip()
            ]
            harmful = [
                str(item)
                for item in (recovery.get("harmful") or [])
                if str(item).strip()
            ]
            if not actions and not harmful:
                continue
            detail_parts = []
            if actions:
                detail_parts.append("恢复：" + "、".join(actions))
            if harmful:
                detail_parts.append("不利：" + "、".join(harmful))
            events.append({
                "at": str(recovery.get("date") or ""),
                "kind": "health",
                "icon": "🩹",
                "title": "今天的恢复",
                "detail": "；".join(detail_parts)[:160],
            })
        events.sort(
            key=lambda item: str(item.get("at") or ""),
            reverse=True,
        )
        return {"ok": True, "events": events[:80]}

    def _get_memory(self, ctx: RouteContext) -> dict:
        """GET memory"""
        params = ctx.params
        target_persona = str(params.get("persona") or "").strip()
        if not target_persona:
            return {"ok": False, "error": "缺少人格"}
        entries = diary.list_entries(
            self.plans_path.parent, target_persona, limit=40
        )
        relation = affection.snapshot(
            self.plans_path.parent,
            target_persona,
            now=self.plugin._now(),
        )
        current_event = None
        try:
            current_event = world_events.recent(
                self.plans_path.parent,
                target_persona,
                self.plugin._now().date().isoformat(),
            )
        except Exception:
            logger.debug("[模拟人生] dispatch 出错，已忽略", exc_info=True)
            current_event = None
        long_term = [
            entry
            for entry in entries
            if str(entry.get("source") or "")
            in ("weekly", "monthly", "yearly")
        ][-4:]
        recent = [
            entry
            for entry in entries
            if str(entry.get("source") or "")
            not in ("weekly", "monthly", "yearly")
        ][-12:]
        return {
            "ok": True,
            "memory": {
                "entries": entries[-40:],
                "long_term": long_term,
                "recent": recent,
                "milestones": list(relation.get("milestones") or [])[-8:],
                "world_event": current_event,
                "world_history": world_events.list_recent(
                    self.plans_path.parent,
                    target_persona,
                    limit=8,
                ),
                "relationship": {
                    "score": relation.get("score"),
                    "level": relation.get("level"),
                    "days_known": relation.get("days_known"),
                    "nickname": relation.get("nickname"),
                    "next_anniversary": relation.get("next_anniversary"),
                },
            },
        }

    def _get_diagnostics(self, ctx: RouteContext) -> dict:
        """GET diagnostics"""
        params = ctx.params
        target_persona = str(params.get("persona") or "").strip()
        if not target_persona:
            return {"ok": False, "error": "缺少人格"}
        return {
            "ok": True,
            "diagnostics": diagnostics.build(
                self.plans_path.parent,
                self.plans_path,
                target_persona,
                now=self.plugin._now(),
            ),
        }

    def _get_ping(self, ctx: RouteContext) -> dict:
        """GET ping"""
        return {"ok": True}

    def _post_backup_restore(self, ctx: RouteContext) -> dict:
        """POST backup/restore"""
        payload = ctx.payload
        raw_files = payload.get("files")
        if not isinstance(raw_files, dict) or not raw_files:
            return {"ok": False, "error": "备份内容为空"}
        data_dir = self.plans_path.parent
        restored = []
        skipped = []
        for name, content in raw_files.items():
            clean = str(name or "").strip()
            if (
                not clean.endswith(".json")
                or "/" in clean
                or "\\" in clean
                or ".." in clean
                or clean.startswith(".")
            ):
                skipped.append(clean)
                continue
            if not isinstance(content, (dict, list)):
                skipped.append(clean)
                continue
            target = data_dir / clean
            try:
                if target.exists():
                    target.with_name(
                        target.name + ".before_restore"
                    ).write_bytes(target.read_bytes())
                atomic_write_json(target, content)
            except OSError:
                skipped.append(clean)
                continue
            restored.append(clean)
        return {
            "ok": True,
            "restored": len(restored),
            "files": restored,
            "skipped": skipped,
        }
