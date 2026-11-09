"""Authenticated APIs used by the embedded AstrBot plugin view."""

from __future__ import annotations

import asyncio
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from astrbot.api import logger
from astrbot.api.web import request

from . import (
    affection,
    books,
    camera_events,
    camera_photo,
    cooking,
    delivery,
    diagnostics,
    diary,
    food,
    furniture_slots,
    furniture_state,
    garage,
    goods,
    health_journal,
    holiday_calendar,
    home_decor,
    integrations,
    money,
    schedule_edit,
    travel,
    view_state,
    weekly,
    world_events,
)


class VirtualLifeViewAPI:
    """Connect the view to this plugin instance's state and interaction queue."""

    def __init__(self, plugin):
        self.plugin = plugin
        self.plans_path = plugin.data_dir / "plans.json"
        self.lock = asyncio.Lock()

    def register(self) -> None:
        """Register instance-bound routes behind AstrBot dashboard authentication.

        Returns:
            None.
        """
        self.plugin.context.register_web_api(
            "/astrbot_plugin_simlife_world/view/<path:endpoint>",
            self.handle,
            ["GET", "POST"],
            "Virtual life scene, furniture, wardrobe and interaction view",
        )

    async def handle(self, endpoint: str):
        """Serve a validated scene read or explicit user interaction.

        Args:
            endpoint: View operation within the fixed route namespace.

        Returns:
            JSON data consumed by the dashboard bridge, without local paths.
        """
        endpoint = endpoint.strip("/")
        params = dict(request.query.items())
        payload = {}
        if request.method == "POST":
            try:
                raw = await request.body()
                limit = 8_000_000 if endpoint.strip("/") == "backup/restore" else 65536
                if len(raw) > limit:
                    return {"ok": False, "error": "请求过大"}
                payload = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeError):
                return {"ok": False, "error": "请求内容必须是 JSON"}
            if not isinstance(payload, dict):
                return {"ok": False, "error": "请求内容必须是对象"}
        try:
            if endpoint == "camera/photo":
                return await self._camera_photo(payload)
            async with self.lock:
                result = await asyncio.to_thread(
                    self.dispatch, endpoint, request.method, params, payload
                )
                if (
                    endpoint in {"garage/drive", "garage/return"}
                    and isinstance(result, dict)
                    and result.get("ok")
                ):
                    await self._apply_garage_schedule(endpoint, payload, result)
                return result
        except (OSError, ValueError, TypeError):
            return {"ok": False, "error": "操作暂不可用，请稍后重试"}

    async def _camera_photo(self, payload: dict) -> dict:
        """观察窗相机：把用户拍到的目标交给万象画卷生成照片。"""
        now = datetime.now(self.plugin.timezone)
        persona = str(payload.get("persona") or "").strip() or None
        state = view_state.build_state(self.plans_path, persona, now=now)
        if not isinstance(state, dict) or state.get("ok") is False:
            return {"ok": False, "error": "现在没有可拍到的状态"}
        target = str(payload.get("target") or "room").strip()
        valid_targets = {
            camera_photo.TARGET_CHARACTER,
            camera_photo.TARGET_ITEM,
            camera_photo.TARGET_ROOM,
        }
        if target not in valid_targets:
            return {"ok": False, "error": "无效的拍照目标"}
        item = None
        items, _ = view_state.load_home_items(self.plans_path)
        items = items + view_state.load_placed_items(self.plans_path, persona)
        if target == camera_photo.TARGET_ITEM:
            item_id = str(payload.get("item_id") or "").strip()
            if not item_id:
                return {"ok": False, "error": "没有选中家具"}
            item = next(
                (
                    entry
                    for entry in items
                    if str(entry.get("id") or "") == item_id
                ),
                None,
            )
            if item is None:
                return {"ok": False, "error": "没有找到这件家具"}
        persona_visual = ""
        try:
            resolved = await self.plugin.personas.resolve(None)
            persona_visual = camera_photo.persona_visual_from_prompt(
                str(getattr(resolved, "prompt", "") or "")
            )
        except Exception:
            persona_visual = ""
        result = await camera_photo.generate(
            self.plugin,
            state,
            target=target,
            item=item,
            home_items=items,
            persona_visual=persona_visual,
        )
        if isinstance(result, dict) and result.get("ok"):
            resolved_persona = str(
                persona or state.get("persona") or ""
            ).strip()
            if not resolved_persona:
                try:
                    resolved_persona = (await self.plugin.personas.resolve(None)).id
                except Exception:
                    resolved_persona = ""
            if resolved_persona:
                event = None
                try:
                    event = camera_events.record(
                        self.plans_path.parent,
                        resolved_persona,
                        target,
                        str(result.get("caption") or ""),
                        item_name=str((item or {}).get("name") or ""),
                        now=now,
                    )
                except Exception:
                    event = None
                if event:
                    handler = getattr(self.plugin, "react_to_camera", None)
                    if callable(handler):
                        try:
                            asyncio.create_task(
                                handler(resolved_persona, event)
                            )
                        except Exception:
                            pass
        return result

    async def _apply_garage_schedule(
        self, endpoint: str, payload: dict, result: dict
    ) -> None:
        """把车库出发/回家写进当天时间线，避免车库与日程各说各的。"""
        try:
            persona = str(
                payload.get("persona")
                or (result.get("garage") or {}).get("persona")
                or ""
            ).strip()
            if not persona:
                return
            now = self.plugin._now()
            date_str = now.date().isoformat()
            plan = self.plugin.storage.get_plan(date_str, persona)
            if plan is None:
                logger.info(
                    "[虚拟人生] 车库行程未写入日程：%s 当天没有日程", persona
                )
                return
            if endpoint == "garage/drive":
                trip = (result.get("garage") or {}).get("trip") or {}
                destination = str(trip.get("destination") or "").strip()
                if not destination:
                    return
                driver = str(trip.get("driver") or "self")
                activity = (
                    f"主人开车载她去{destination}"
                    if driver == "master"
                    else f"载他去{destination}"
                )
                updated = schedule_edit.insert_garage_trip(
                    plan, trip, now, activity=activity
                )
            else:
                trip = result.get("trip") or {}
                updated = schedule_edit.insert_garage_return(
                    plan, trip, now
                )
            key = self.plugin.storage.plan_key(date_str, persona)
            self.plugin.storage.plans[key] = updated
            await self.plugin.storage.save_plans()
        except (OSError, ValueError, TypeError) as exc:
            logger.warning("[虚拟人生] 车库行程写入日程失败: %s", exc)
        except Exception as exc:
            logger.warning("[虚拟人生] 车库行程写入日程异常: %s", exc)

    def dispatch(self, endpoint: str, method: str, params: dict, payload: dict) -> dict:
        """Read only this instance and enqueue explicitly requested interactions.

        Args:
            endpoint: Validated operation name.
            method: Request method.
            params: Query string values.
            payload: JSON object for a user initiated operation.

        Returns:
            A view response without configuration secrets or filesystem paths.
        """
        now = datetime.now(self.plugin.timezone)
        persona = (
            str(params.get("persona") or payload.get("persona") or "").strip() or None
        )
        if method == "GET":
            if endpoint == "integrations":
                return integrations.collect_integrations(self.plugin)
            if endpoint == "trips":
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
            if endpoint == "backup":
                files = {}
                for path in sorted(self.plans_path.parent.glob("*.json")):
                    try:
                        files[path.name] = json.loads(
                            path.read_text(encoding="utf-8")
                        )
                    except (OSError, ValueError, TypeError):
                        continue
                return {
                    "ok": True,
                    "exported_at": now.isoformat(timespec="seconds"),
                    "files": files,
                }
            if endpoint == "state":
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
            if endpoint == "cooking/history":
                path = self.plans_path.parent / "cooking_history.json"
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError, TypeError):
                    payload = []
                items = payload if isinstance(payload, list) else []
                return {"ok": True, "items": items[-10:]}
            if endpoint == "recent_activity":
                target_persona = str(params.get("persona") or "").strip()
                if not target_persona:
                    return {"ok": False, "error": "缺少人格"}
                events = []
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
                        ) + " · " + str(item.get("status") or ""),
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
                return {"ok": True, "events": events[:30]}
            if endpoint == "home_items":
                items, _ = view_state.load_home_items(self.plans_path, persona)
                states = furniture_state.live_states(self.plans_path, now=now)
                decorated = furniture_state.decorate_items(items, states, now=now)
                decorated += view_state.load_placed_items(self.plans_path, persona)
                return {"ok": True, "items": decorated}
            if endpoint == "decor/items":
                target_persona = str(persona or "").strip() or (
                    view_state.active_persona(self.plans_path) or ""
                )
                base, _ = view_state.load_home_items(
                    self.plans_path, apply_overrides=False
                )
                return {
                    "ok": True,
                    "items": home_decor.describe(
                        base, self.plans_path.parent, target_persona
                    ),
                }
            if endpoint == "fridge":
                fridge = view_state.load_fridge(self.plans_path)
                food_system = food.FoodSystem(
                    self.plans_path.parent,
                    Path(__file__).with_name("food_catalog.json"),
                )
                food_state = food_system.load_state()
                target_persona = persona or str(fridge.get("persona") or "")
                shopping = [
                    item
                    for item in (food_state.get("shopping") or [])
                    if isinstance(item, dict)
                    and (
                        not target_persona
                        or str(item.get("persona_id") or "") == target_persona
                    )
                ]
                return {
                    "ok": True,
                    "ingredients": fridge["ingredients"],
                    "updated_at": fridge["updated_at"],
                    "menu": view_state.current_menu(
                        self.plans_path, persona=persona, today=now.date()
                    ),
                    "shopping": shopping[-8:],
                }
            if endpoint == "fridge/recipe":
                recipe = view_state.pick_recipe(self.plans_path)
                if recipe:
                    recipe.pop("source", None)
                return {"ok": recipe is not None, "recipe": recipe or {}}
            if endpoint == "cooking/dishes":
                dishes = cooking.makeable_dishes(self.plugin.plan_generator.food)
                return {"ok": True, "dishes": dishes, "count": len(dishes)}
            if endpoint == "item_wishes":
                wishes = view_state.load_wishes(self.plans_path)
                wishes = [
                    w for w in wishes if not w.get("persona") or w["persona"] == persona
                ]
                return {"ok": True, "wishes": wishes}
            if endpoint == "interact":
                request_id = str(params.get("id") or "")
                if not re.fullmatch(r"it-[A-Za-z0-9-]{6,80}", request_id):
                    return {"ok": False, "error": "无效的互动标识"}
                response = view_state.load_interaction_response(
                    self.plans_path, request_id
                )
                if response:
                    response = {
                        key: response[key]
                        for key in (
                            "id",
                            "ok",
                            "status",
                            "speech",
                            "reply",
                            "text",
                            "dish",
                            "error",
                            "created_at",
                            "handled_at",
                            "finished_at",
                        )
                        if key in response
                    }
                return {"ok": True, "pending": response is None, "response": response}
            if endpoint == "wallet":
                target_persona = str(params.get("persona") or "").strip()
                if not target_persona:
                    return {"ok": False, "error": "缺少人格"}
                return {
                    "ok": True,
                    "wallet": money.snapshot(
                        self.plans_path.parent, target_persona, limit=30
                    ),
                }
            if endpoint == "garage":
                target_persona = str(params.get("persona") or "").strip()
                if not target_persona:
                    return {"ok": False, "error": "缺少人格"}
                return {
                    "ok": True,
                    "garage": garage.snapshot(
                        self.plans_path.parent,
                        target_persona,
                        now=self.plugin._now(),
                    ),
                }
            if endpoint == "memory":
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
            if endpoint == "diagnostics":
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
            if endpoint == "shop":
                category = str(params.get("category") or "").strip()
                items = goods.list_goods(category, limit=300)
                categories = sorted(
                    {
                        str(item.get("category") or "")
                        for item in goods.load_goods()
                        if str(item.get("category") or "")
                    }
                )
                return {
                    "ok": True,
                    "items": items,
                    "categories": categories,
                }
            if endpoint == "furniture_slots":
                target_persona = str(params.get("persona") or "").strip() or (
                    view_state.active_persona(self.plans_path) or ""
                )
                item_query = str(params.get("item") or "").strip()
                catalog_item = goods.find_goods(item_query) if item_query else None
                slots = furniture_slots.describe_slots(
                    self.plans_path.parent,
                    target_persona,
                    goods=catalog_item,
                    room=str(params.get("room") or "").strip(),
                )
                return {
                    "ok": True,
                    "slots": slots,
                    "installable": bool(catalog_item and catalog_item.get("installable")),
                }
            if endpoint == "weekly":
                target_persona = str(params.get("persona") or "").strip()
                if not target_persona:
                    return {"ok": False, "error": "缺少人格"}
                try:
                    days = int(params.get("days") or 7)
                except (TypeError, ValueError):
                    days = 7
                days = 365 if days >= 300 else 30 if days >= 28 else 7
                return {
                    "ok": True,
                    "report": weekly.build(
                        self.plans_path.parent,
                        target_persona,
                        now=now,
                        days=days,
                    ),
                    "previous": weekly.build(
                        self.plans_path.parent,
                        target_persona,
                        now=now - timedelta(days=days),
                        days=days,
                    ),
                }
            if endpoint == "diary":
                target_persona = str(params.get("persona") or "").strip()
                if not target_persona:
                    return {"ok": False, "error": "缺少人格"}
                return {
                    "ok": True,
                    "persona": target_persona,
                    "entries": diary.list_entries(
                        self.plans_path.parent, target_persona, limit=20
                    ),
                }
            if endpoint == "book":
                item = books.find_book(
                    str(params.get("id") or params.get("name") or "")
                )
                if item is None:
                    return {"ok": False, "error": "没有这本书"}
                raw_chapter = params.get("chapter")
                try:
                    requested_chapter = int(raw_chapter or 0)
                except (TypeError, ValueError):
                    requested_chapter = 0
                target_persona = str(
                    params.get("persona") or payload.get("persona") or ""
                ).strip()
                progress = (
                    books.get_progress(
                        self.plans_path.parent,
                        target_persona,
                        str(item.get("id") or ""),
                    )
                    if target_persona
                    else {}
                )
                total_chapters = max(1, len(item.get("chapters") or []))
                if requested_chapter > 0:
                    chapter = min(requested_chapter, total_chapters)
                else:
                    chapter = min(
                        int(progress.get("chapter") or 1) or 1,
                        total_chapters,
                    )
                all_notes = list(progress.get("notes") or [])
                return {
                    "ok": True,
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "author": item.get("author"),
                    "genre": item.get("genre"),
                    "chapter": chapter,
                    "chapters": total_chapters,
                    "chapter_titles": [
                        str(chapter_item.get("title") or "")
                        for chapter_item in (item.get("chapters") or [])
                    ],
                    "notes": len(all_notes),
                    "note_items": [
                        {**note, "index": index}
                        for index, note in enumerate(all_notes)
                    ],
                    "content": books.render_book(item, chapter),
                }
            if endpoint == "ping":
                return {"ok": True}
        elif method == "POST":
            if endpoint == "backup/restore":
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
                        temporary = target.with_name(target.name + ".restore_tmp")
                        temporary.write_text(
                            json.dumps(content, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                        temporary.replace(target)
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
            if endpoint == "wallet/goal/clear":
                target_persona = str(
                    payload.get("persona") or params.get("persona") or ""
                ).strip()
                if not target_persona:
                    return {"ok": False, "error": "缺少人格"}
                return money.clear_goal(self.plans_path.parent, target_persona)
            if params.get("time") or payload.get("preview"):
                return {"ok": False, "error": "时间预览只供查看，请回到当前时间再互动"}
            if endpoint == "garage/drive":
                target_persona = str(
                    payload.get("persona") or params.get("persona") or ""
                ).strip()
                if not target_persona:
                    return {"ok": False, "error": "缺少人格"}
                result = garage.start(
                    self.plans_path.parent,
                    target_persona,
                    str(payload.get("destination") or ""),
                    str(payload.get("driver") or "self"),
                    now=self.plugin._now(),
                    vehicle_id=str(payload.get("vehicle_id") or ""),
                )
                if not result.get("ok"):
                    return result
                return {
                    "ok": True,
                    "garage": garage.snapshot(
                        self.plans_path.parent,
                        target_persona,
                        now=self.plugin._now(),
                    ),
                }
            if endpoint == "garage/return":
                target_persona = str(
                    payload.get("persona") or params.get("persona") or ""
                ).strip()
                if not target_persona:
                    return {"ok": False, "error": "缺少人格"}
                result = garage.return_home(
                    self.plans_path.parent,
                    target_persona,
                    now=self.plugin._now(),
                    vehicle_id=str(payload.get("vehicle_id") or ""),
                )
                if not result.get("ok"):
                    return result
                trip = result.get("trip") or {}
                if trip:
                    driver = (
                        "主人开车"
                        if trip.get("driver") == "master"
                        else "她自己开车"
                    )
                    diary.add_entry(
                        self.plans_path.parent,
                        target_persona,
                        self.plugin._now().date().isoformat(),
                        "兜风",
                        f"{driver}带她去了{trip.get('destination')}，"
                        "回来的时候心情很好。",
                        source="outing",
                        now=self.plugin._now(),
                    )
                    affection.add(
                        self.plans_path.parent,
                        target_persona,
                        2,
                        "一起出门兜风",
                        now=self.plugin._now(),
                    )
                    garage.mark_noted(
                        self.plans_path.parent,
                        target_persona,
                        str(trip.get("id") or ""),
                    )
                return {
                    "ok": True,
                    "trip": trip,
                    "garage": garage.snapshot(
                        self.plans_path.parent,
                        target_persona,
                        now=self.plugin._now(),
                    ),
                }
            if endpoint == "garage/refuel":
                target_persona = str(
                    payload.get("persona") or params.get("persona") or ""
                ).strip()
                if not target_persona:
                    return {"ok": False, "error": "缺少人格"}
                settings = self.plugin.config.get("money_settings", {}) or {}
                if not bool(settings.get("enable_spending", True)):
                    return {"ok": False, "error": "现在不能花钱"}
                balance = money.balance(self.plans_path.parent, target_persona)
                if balance < garage.REFUEL_COST:
                    return {
                        "ok": False,
                        "error": f"余额不够，加油需要 {garage.REFUEL_COST:g} 元",
                    }
                result = garage.refuel(
                    self.plans_path.parent,
                    target_persona,
                    now=self.plugin._now(),
                    vehicle_id=str(payload.get("vehicle_id") or ""),
                )
                if not result.get("ok"):
                    return result
                money.add(
                    self.plans_path.parent,
                    target_persona,
                    -garage.REFUEL_COST,
                    "给车加油",
                    kind="car",
                    at=self.plugin._now(),
                )
                return {
                    "ok": True,
                    "garage": garage.snapshot(
                        self.plans_path.parent,
                        target_persona,
                        now=self.plugin._now(),
                    ),
                    "cost": garage.REFUEL_COST,
                }
            if endpoint == "wallet/give":
                target_persona = str(
                    payload.get("persona") or params.get("persona") or ""
                ).strip()
                if not target_persona:
                    return {"ok": False, "error": "缺少人格"}
                try:
                    amount = round(float(payload.get("amount") or 0), 2)
                except (TypeError, ValueError):
                    amount = 0.0
                if amount <= 0:
                    return {"ok": False, "error": "请填写要给月月的金额"}
                if amount > 100000:
                    return {"ok": False, "error": "一次最多给 100000 元"}
                try:
                    result = money.add(
                        self.plans_path.parent,
                        target_persona,
                        amount,
                        "主人在观察窗给的钱",
                        kind="master",
                        at=self.plugin._now(),
                    )
                    affection.add(
                        self.plans_path.parent,
                        target_persona,
                        2,
                        "主人给钱",
                        now=self.plugin._now(),
                    )
                except Exception as exc:
                    return {"ok": False, "error": f"给钱失败：{exc}"}
                return {
                    "ok": True,
                    "amount": result.get("amount", amount),
                    "balance": result.get("balance"),
                    "wallet": money.snapshot(
                        self.plans_path.parent, target_persona, limit=30
                    ),
                }
            if endpoint in {"decor/place", "decor/store", "decor/reset"}:
                target_persona = str(persona or "").strip() or (
                    view_state.active_persona(self.plans_path) or ""
                )
                if not target_persona:
                    return {"ok": False, "error": "缺少人格"}
                item_id = str(
                    payload.get("item_id") or payload.get("id") or ""
                ).strip()
                if endpoint == "decor/reset":
                    return home_decor.reset(
                        self.plans_path.parent, target_persona, item_id
                    )
                base, _ = view_state.load_home_items(
                    self.plans_path, apply_overrides=False
                )
                valid_ids = {str(item.get("id") or "") for item in base}
                if not item_id or item_id not in valid_ids:
                    return {"ok": False, "error": "没有这件家具"}
                if endpoint == "decor/store":
                    return home_decor.store(
                        self.plans_path.parent, target_persona, item_id
                    )
                return home_decor.place(
                    self.plans_path.parent,
                    target_persona,
                    item_id,
                    str(payload.get("room") or ""),
                    payload.get("x"),
                    payload.get("y"),
                    facing=str(payload.get("facing") or "S"),
                )
            if endpoint == "book/progress":
                target_persona = str(
                    persona or payload.get("persona") or ""
                ).strip() or (view_state.active_persona(self.plans_path) or "")
                if not target_persona:
                    return {"ok": False, "error": "缺少人格"}
                item = books.find_book(
                    str(payload.get("id") or payload.get("book_id") or "")
                )
                if item is None:
                    return {"ok": False, "error": "没有这本书"}
                try:
                    read_chapter = int(payload.get("chapter") or 0)
                except (TypeError, ValueError):
                    read_chapter = 0
                total = max(1, len(item.get("chapters") or []))
                result = books.record_reading(
                    self.plans_path.parent,
                    target_persona,
                    str(item.get("id") or ""),
                    read_chapter,
                    total,
                )
                return {"ok": True, **result}
            actual = view_state.build_state(self.plans_path, persona, now=now)
            if not actual.get("ok") or not actual.get("is_today"):
                return {"ok": False, "error": "请先生成所选人格今天的虚拟日程"}
            if endpoint == "wallet/goal":
                try:
                    target = float(payload.get("target") or 0)
                except (TypeError, ValueError):
                    target = 0
                return money.set_goal(
                    self.plans_path.parent,
                    actual["persona"],
                    str(payload.get("name") or ""),
                    target,
                    wish=str(payload.get("wish") or ""),
                    at=now,
                )
            if endpoint == "affection/nickname":
                return affection.set_nickname(
                    self.plans_path.parent,
                    actual["persona"],
                    str(payload.get("nickname") or ""),
                    now=now,
                )
            current = actual.get("now") or {}
            items, _ = view_state.load_home_items(self.plans_path)
            states = furniture_state.live_states(self.plans_path, now=now)
            items = furniture_state.decorate_items(items, states, now=now)
            items += view_state.load_placed_items(
                self.plans_path, actual.get("persona")
            )
            item_id = str(payload.get("item_id") or "").strip()
            item = next((i for i in items if str(i.get("id")) == item_id), None)
            if item_id and not item:
                return {"ok": False, "error": "未知家具"}
            action = str(payload.get("action") or "").strip()
            if item and action and action not in item.get("actions", []):
                return {"ok": False, "error": "未知家具动作"}
            if item and current.get("kind") != "home":
                return {"ok": False, "error": "角色正在外面，回家后才能使用家具"}
            if endpoint == "interact":
                if not (self.plugin.config.get("interaction_settings", {}) or {}).get(
                    "enable", True
                ):
                    return {"ok": False, "error": "即时互动已关闭，请在插件设置中开启"}
                safe_payload = dict(payload, persona=actual["persona"])
                interaction = view_state.build_interaction_request(
                    self.plans_path, safe_payload, now=now
                )
                view_state.write_interaction_request(self.plans_path, interaction)
                return {"ok": True, "id": interaction["id"]}
            if endpoint == "shop/buy":
                settings = self.plugin.config.get("money_settings", {}) or {}
                if not bool(settings.get("enable_spending", True)):
                    return {"ok": False, "error": "现在不能花钱"}
                item_id = str(payload.get("id") or "").strip()
                try:
                    quantity = max(1, min(int(payload.get("quantity") or 1), 5))
                except (TypeError, ValueError):
                    quantity = 1
                item = goods.find_goods(item_id)
                if item is None:
                    return {"ok": False, "error": "没有这件商品"}
                amount = round(
                    float(item.get("price") or 0.0) * quantity, 2
                )
                daily_limit = float(
                    settings.get("daily_spend_limit", 200) or 0
                )
                if daily_limit > 0:
                    spent = money.spent_on(
                        self.plans_path.parent,
                        actual["persona"],
                        now.date().isoformat(),
                    )
                    if spent + amount > daily_limit:
                        return {"ok": False, "error": "今日消费已超过上限"}
                result = goods.purchase(
                    self.plans_path.parent,
                    actual["persona"],
                    item_id,
                    quantity,
                    at=now,
                    delivery_minutes=int(
                        settings.get("delivery_minutes", 3) or 0
                    ),
                )
                return result
            if endpoint == "use_item":
                result = goods.use_item(
                    self.plans_path.parent,
                    actual["persona"],
                    str(payload.get("item") or payload.get("id") or ""),
                    at=now,
                )
                return result
            if endpoint == "book/note":
                try:
                    note_chapter = int(payload.get("chapter") or 0)
                except (TypeError, ValueError):
                    note_chapter = 0
                return books.add_note(
                    self.plans_path.parent,
                    actual["persona"],
                    str(payload.get("id") or payload.get("book_id") or ""),
                    str(payload.get("text") or ""),
                    chapter=note_chapter,
                )
            if endpoint == "book/note/delete":
                try:
                    note_index = int(payload.get("index") or 0)
                except (TypeError, ValueError):
                    note_index = -1
                return books.delete_note(
                    self.plans_path.parent,
                    actual["persona"],
                    str(payload.get("id") or payload.get("book_id") or ""),
                    note_index,
                )
            if endpoint == "place_item":
                result = money.place_possession(
                    self.plans_path.parent,
                    actual["persona"],
                    str(payload.get("item") or payload.get("id") or ""),
                    str(payload.get("room") or ""),
                    x=payload.get("x"),
                    y=payload.get("y"),
                    slot_id=str(payload.get("slot_id") or ""),
                    auto_slot=bool(payload.get("auto_slot")),
                    z_cm=payload.get("z_cm"),
                    surface_id=str(payload.get("surface_id") or ""),
                )
                return result
            if endpoint == "item_wish":
                if not item:
                    return {"ok": False, "error": "请选择家具"}
                wish_date = str(payload.get("date") or now.date().isoformat())
                if date.fromisoformat(wish_date) < now.date():
                    return {"ok": False, "error": "不能修改过去的安排"}
                wish_action = action or next(iter(item.get("actions", [])), "")
                updated_item = furniture_state.record_action(
                    self.plans_path,
                    item,
                    wish_action,
                    actual["persona"],
                    now=now,
                )
                wish = {
                    "date": wish_date,
                    "id": item_id,
                    "persona": actual["persona"],
                    "room": item.get("room", ""),
                    "name": item.get("name", item_id),
                    "action": wish_action,
                    "created_at": now.isoformat(timespec="seconds"),
                }
                wishes = [
                    w
                    for w in view_state.load_wishes(self.plans_path)
                    if not (
                        w.get("date") == wish_date
                        and w.get("id") == item_id
                        and w.get("action") == wish["action"]
                        and w.get("persona") == actual["persona"]
                    )
                ]
                wishes.append(wish)
                view_state.save_wishes(self.plans_path, wishes)
                return {
                    "ok": True,
                    "wish": wish,
                    "item": updated_item,
                    "message": furniture_state.action_message(
                        item, wish_action, now=now
                    ),
                    "wishes": [
                        w for w in wishes if w.get("persona") == actual["persona"]
                    ],
                }
            if endpoint == "cooking/cook":
                dish_name = str(payload.get("dish") or "").strip()
                if not dish_name:
                    return {"ok": False, "error": "请选择一道菜"}
                dishes = cooking.makeable_dishes(
                    self.plugin.plan_generator.food
                )
                dish = next(
                    (
                        entry
                        for entry in dishes
                        if str(entry.get("name") or "") == dish_name
                    ),
                    None,
                )
                if dish is None:
                    return {
                        "ok": False,
                        "error": "这道菜现在做不了：冰箱里的食材不齐全",
                    }
                taste = cooking.rate_taste(
                    payload.get("score"), len(dish.get("ingredients") or [])
                )
                usage = cooking.consume_ingredients(self.plugin, dish)
                cooking.record_cook(
                    self.plugin, dish, taste, usage, now=now
                )
                return {
                    "ok": True,
                    "dish": dish,
                    "taste": taste,
                    "consumed": usage.get("used") or [],
                    "missing": usage.get("missing") or [],
                }
            if endpoint == "gift/dismiss":
                action_id = str(payload.get("id") or "").strip()
                if not re.fullmatch(r"pa-[A-Za-z0-9_.-]{6,80}", action_id):
                    return {"ok": False, "error": "无效的待处理标识"}
                visible = view_state.load_pending_actions(
                    self.plans_path, str(actual.get("persona") or "")
                )
                if not any(
                    str(action.get("id") or "") == action_id
                    for action in visible
                ):
                    return {"ok": False, "error": "这个待处理入口已经失效了"}
                action = view_state.pop_pending_action(
                    self.plans_path, action_id
                )
                if not action:
                    return {"ok": False, "error": "这个待处理入口已经失效了"}
                return {"ok": True, "id": action_id}
            if endpoint == "gift/accept":
                if not (
                    self.plugin.config.get("interaction_settings", {}) or {}
                ).get("enable", True):
                    return {"ok": False, "error": "即时互动已关闭，无法递东西"}
                action_id = str(payload.get("id") or "").strip()
                if not re.fullmatch(r"pa-[A-Za-z0-9_.-]{6,80}", action_id):
                    return {"ok": False, "error": "无效的递东西标识"}
                actual_persona = str(actual.get("persona") or "").strip()
                visible = view_state.load_pending_actions(
                    self.plans_path, actual_persona
                )
                if not any(
                    str(action.get("id") or "") == action_id
                    for action in visible
                ):
                    return {"ok": False, "error": "这个入口已经失效了"}
                visible_action = next(
                    (
                        action
                        for action in visible
                        if str(action.get("id") or "") == action_id
                    ),
                    None,
                )
                if (
                    visible_action is not None
                    and str(visible_action.get("kind") or "gift") == "wish"
                ):
                    action = view_state.pop_pending_action(
                        self.plans_path, action_id
                    )
                    if not action:
                        return {"ok": False, "error": "这个愿望入口已经失效了"}
                    action_persona = str(action.get("persona") or "").strip()
                    if (
                        action_persona
                        and actual_persona
                        and action_persona != actual_persona
                    ):
                        return {
                            "ok": False,
                            "error": "这个愿望入口不属于当前人格",
                        }
                    result = money.fulfill_goal(
                        self.plans_path.parent,
                        action_persona or actual_persona,
                        at=now,
                    )
                    if not result.get("ok"):
                        return result
                    affection.add(
                        self.plans_path.parent,
                        action_persona or actual_persona,
                        6,
                        "实现愿望",
                        now=now,
                    )
                    return {
                        "ok": True,
                        "kind": "wish",
                        "amount": result["amount"],
                        "balance": result["balance"],
                        "label": str(action.get("label") or ""),
                        "goal": result.get("goal"),
                    }
                if (
                    visible_action is not None
                    and str(visible_action.get("kind") or "gift") == "money"
                ):
                    action = view_state.pop_pending_action(
                        self.plans_path, action_id
                    )
                    if not action:
                        return {"ok": False, "error": "这个要钱入口已经失效了"}
                    action_persona = str(action.get("persona") or "").strip()
                    if (
                        action_persona
                        and actual_persona
                        and action_persona != actual_persona
                    ):
                        return {
                            "ok": False,
                            "error": "这个要钱入口不属于当前人格",
                        }
                    try:
                        amount = round(
                            float(
                                payload.get("amount")
                                or action.get("amount")
                                or 0.0
                            ),
                            2,
                        )
                    except (TypeError, ValueError):
                        amount = 0.0
                    if amount <= 0:
                        return {"ok": False, "error": "请填写要给月月的金额"}
                    if amount > 100000:
                        return {"ok": False, "error": "一次最多给 100000 元"}
                    result = money.add(
                        self.plans_path.parent,
                        action_persona or actual_persona,
                        amount,
                        "月月向主人要钱："
                        + str(action.get("reason") or "没有说明理由"),
                        kind="ask",
                        at=now,
                    )
                    affection.add(
                        self.plans_path.parent,
                        action_persona or actual_persona,
                        2,
                        "主人给了钱",
                        now=now,
                    )
                    return {
                        "ok": True,
                        "kind": "money",
                        "amount": result["amount"],
                        "balance": result["balance"],
                        "label": str(action.get("label") or ""),
                    }
                current = actual.get("now") or {}
                if current and str(current.get("kind") or "home") != "home":
                    where = str(current.get("location") or "外面").strip()
                    return {
                        "ok": False,
                        "error": f"月月现在在{where}，不在家；等她回来再递吧",
                    }
                current_state = str((current or {}).get("state") or "").strip()
                current_activity = str((current or {}).get("activity") or "").strip()
                if current_state == "sleep" or "睡" in current_activity:
                    return {
                        "ok": False,
                        "error": "月月已经睡了，等她醒来再递吧",
                    }
                action = view_state.pop_pending_action(
                    self.plans_path, action_id
                )
                if not action:
                    return {"ok": False, "error": "这个递东西入口已经失效了"}
                action_persona = str(action.get("persona") or "").strip()
                if action_persona and actual_persona and action_persona != actual_persona:
                    return {"ok": False, "error": "这个递东西入口不属于当前人格"}
                label = str(action.get("label") or "把东西递给月月").strip()
                gift_item = ""
                if label.startswith("把") and label.endswith("递给月月"):
                    gift_item = label[1 : -len("递给月月")].strip()
                interaction = view_state.build_interaction_request(
                    self.plans_path,
                    {
                        "kind": "chat",
                        "text": f"（{label}）喏，给你。",
                        "persona": actual["persona"],
                        "action": "give",
                        "item_name": gift_item,
                        "gift_source": str(action.get("source") or ""),
                    },
                    now=now,
                )
                view_state.write_interaction_request(
                    self.plans_path, interaction
                )
                affection.add(
                    self.plans_path.parent,
                    actual_persona,
                    4,
                    "主人递了东西",
                    now=now,
                )
                return {
                    "ok": True,
                    "id": interaction["id"],
                    "text": interaction.get("text"),
                    "label": label,
                }
            if endpoint == "cooking/serve":
                dish_name = str(payload.get("dish") or "").strip()
                if not dish_name:
                    return {"ok": False, "error": "请选择做好的菜"}
                if not (
                    self.plugin.config.get("interaction_settings", {}) or {}
                ).get("enable", True):
                    return {
                        "ok": False,
                        "error": "即时互动已关闭，无法呼叫角色来吃饭",
                    }
                taste = (
                    payload.get("taste")
                    if isinstance(payload.get("taste"), dict)
                    else {}
                )
                label = str(
                    taste.get("label")
                    or payload.get("taste_label")
                    or "还行"
                ).strip()
                interaction_payload = cooking.serve_interaction_payload(
                    dish_name, label, persona=str(actual.get("persona") or "")
                )
                interaction = view_state.build_interaction_request(
                    self.plans_path, interaction_payload, now=now
                )
                view_state.write_interaction_request(
                    self.plans_path, interaction
                )
                cooking.mark_served(self.plugin, dish_name, now=now)
                return {
                    "ok": True,
                    "id": interaction["id"],
                    "text": interaction.get("text"),
                    "dish": dish_name,
                }
        return {"ok": False, "error": "未知视图操作"}
