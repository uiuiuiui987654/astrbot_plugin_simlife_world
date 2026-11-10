"""Authenticated APIs used by the embedded AstrBot plugin view."""

from __future__ import annotations

from dataclasses import replace

import asyncio
import json
from datetime import datetime

from astrbot.api import logger
from astrbot.api.web import request

from . import (
    camera_events,
    camera_photo,
    furniture_state,
    schedule_edit,
    view_state,
)
from .view_routes.context import RouteContext
from .view_routes.home import HomeRoutes
from .view_routes.journal import JournalRoutes
from .view_routes.money import MoneyRoutes
from .view_routes.system import SystemRoutes


class VirtualLifeViewAPI(SystemRoutes, HomeRoutes, MoneyRoutes, JournalRoutes):
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
            logger.debug("[模拟人生] _camera_photo 出错，已忽略", exc_info=True)
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
                    logger.debug("[模拟人生] _camera_photo 出错，已忽略", exc_info=True)
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
                    logger.debug("[模拟人生] _camera_photo 出错，已忽略", exc_info=True)
                    event = None
                if event:
                    handler = getattr(self.plugin, "react_to_camera", None)
                    if callable(handler):
                        try:
                            asyncio.create_task(
                                handler(resolved_persona, event)
                            )
                        except Exception:
                            logger.debug("[模拟人生] _camera_photo 出错，已忽略", exc_info=True)
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
                    "[模拟人生] 车库行程未写入日程：%s 当天没有日程", persona
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
            logger.warning("[模拟人生] 车库行程写入日程失败: %s", exc)
        except Exception as exc:
            logger.warning("[模拟人生] 车库行程写入日程异常: %s", exc)

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
        ctx = RouteContext(
            endpoint=endpoint, method=method, now=now, persona=persona, params=params, payload=payload
        )
        if method == "GET":
            if endpoint == "integrations":
                return self._get_integrations(ctx)
            if endpoint == "trips":
                return self._get_trips(ctx)
            if endpoint == "backup":
                return self._get_backup(ctx)
            if endpoint == "state":
                return self._get_state(ctx)
            if endpoint == "cooking/history":
                return self._get_cooking_history(ctx)
            if endpoint == "recent_activity":
                return self._get_recent_activity(ctx)
            if endpoint == "home_items":
                return self._get_home_items(ctx)
            if endpoint == "decor/items":
                return self._get_decor_items(ctx)
            if endpoint == "fridge":
                return self._get_fridge(ctx)
            if endpoint == "fridge/recipe":
                return self._get_fridge_recipe(ctx)
            if endpoint == "cooking/dishes":
                return self._get_cooking_dishes(ctx)
            if endpoint == "item_wishes":
                return self._get_item_wishes(ctx)
            if endpoint == "interact":
                return self._get_interact(ctx)
            if endpoint == "wallet":
                return self._get_wallet(ctx)
            if endpoint == "garage":
                return self._get_garage(ctx)
            if endpoint == "memory":
                return self._get_memory(ctx)
            if endpoint == "diagnostics":
                return self._get_diagnostics(ctx)
            if endpoint == "shop":
                return self._get_shop(ctx)
            if endpoint == "furniture_slots":
                return self._get_furniture_slots(ctx)
            if endpoint == "weekly":
                return self._get_weekly(ctx)
            if endpoint == "diary":
                return self._get_diary(ctx)
            if endpoint == "book":
                return self._get_book(ctx)
            if endpoint == "ping":
                return self._get_ping(ctx)
        elif method == "POST":
            if endpoint == "backup/restore":
                return self._post_backup_restore(ctx)
            if endpoint == "wallet/goal/clear":
                return self._post_wallet_goal_clear(ctx)
            if params.get("time") or payload.get("preview"):
                return {"ok": False, "error": "时间预览只供查看，请回到当前时间再互动"}
            if endpoint == "garage/drive":
                return self._post_garage_drive(ctx)
            if endpoint == "garage/return":
                return self._post_garage_return(ctx)
            if endpoint == "garage/refuel":
                return self._post_garage_refuel(ctx)
            if endpoint == "wallet/give":
                return self._post_wallet_give(ctx)
            if endpoint in {"decor/place", "decor/store", "decor/reset"}:
                return self._post_decor(ctx)
            if endpoint == "book/progress":
                return self._post_book_progress(ctx)
            actual = view_state.build_state(self.plans_path, persona, now=now)
            if not actual.get("ok") or not actual.get("is_today"):
                return {"ok": False, "error": "请先生成所选人格今天的虚拟日程"}
            if endpoint == "wallet/goal":
                return self._post_wallet_goal(replace(ctx, actual=actual))
            if endpoint == "affection/nickname":
                return self._post_affection_nickname(replace(ctx, actual=actual))
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
                return self._post_interact(replace(ctx, actual=actual))
            if endpoint == "shop/buy":
                return self._post_shop_buy(replace(ctx, actual=actual, item=item, item_id=item_id))
            if endpoint == "use_item":
                return self._post_use_item(replace(ctx, actual=actual))
            if endpoint == "book/note":
                return self._post_book_note(replace(ctx, actual=actual))
            if endpoint == "book/note/delete":
                return self._post_book_note_delete(replace(ctx, actual=actual))
            if endpoint == "place_item":
                return self._post_place_item(replace(ctx, actual=actual))
            if endpoint == "item_wish":
                return self._post_item_wish(replace(ctx, action=action, actual=actual, item=item, item_id=item_id))
            if endpoint == "cooking/cook":
                return self._post_cooking_cook(ctx)
            if endpoint == "gift/dismiss":
                return self._post_gift_dismiss(replace(ctx, action=action, actual=actual))
            if endpoint == "gift/accept":
                return self._post_gift_accept(replace(ctx, action=action, actual=actual, current=current))
            if endpoint == "cooking/serve":
                return self._post_cooking_serve(replace(ctx, actual=actual))
        return {"ok": False, "error": "未知视图操作"}
