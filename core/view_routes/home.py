"""Furniture, decor, fridge, cooking, wishes, gifts and furniture interactions."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path


from .. import (
    affection,
    cooking,
    food,
    furniture_slots,
    furniture_state,
    goods,
    home_decor,
    money,
    view_state,
)

from .context import RouteContext


class HomeRoutes:
    """Mixin for VirtualLifeViewAPI; expects ``self.plugin`` and ``self.plans_path``."""

    def _get_cooking_history(self, ctx: RouteContext) -> dict:
        """GET cooking/history"""
        payload = ctx.payload
        path = self.plans_path.parent / "cooking_history.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            payload = []
        items = payload if isinstance(payload, list) else []
        return {"ok": True, "items": items[-10:]}

    def _get_home_items(self, ctx: RouteContext) -> dict:
        """GET home_items"""
        now = ctx.now
        persona = ctx.persona
        items, _ = view_state.load_home_items(self.plans_path, persona)
        states = furniture_state.live_states(self.plans_path, now=now)
        decorated = furniture_state.decorate_items(items, states, now=now)
        decorated += view_state.load_placed_items(self.plans_path, persona)
        return {"ok": True, "items": decorated}

    def _get_decor_items(self, ctx: RouteContext) -> dict:
        """GET decor/items"""
        persona = ctx.persona
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

    def _get_fridge(self, ctx: RouteContext) -> dict:
        """GET fridge"""
        now = ctx.now
        persona = ctx.persona
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

    def _get_fridge_recipe(self, ctx: RouteContext) -> dict:
        """GET fridge/recipe"""
        recipe = view_state.pick_recipe(self.plans_path)
        if recipe:
            recipe.pop("source", None)
        return {"ok": recipe is not None, "recipe": recipe or {}}

    def _get_cooking_dishes(self, ctx: RouteContext) -> dict:
        """GET cooking/dishes"""
        dishes = cooking.makeable_dishes(self.plugin.plan_generator.food)
        return {"ok": True, "dishes": dishes, "count": len(dishes)}

    def _get_item_wishes(self, ctx: RouteContext) -> dict:
        """GET item_wishes"""
        persona = ctx.persona
        wishes = view_state.load_wishes(self.plans_path)
        wishes = [
            w for w in wishes if not w.get("persona") or w["persona"] == persona
        ]
        return {"ok": True, "wishes": wishes}

    def _get_interact(self, ctx: RouteContext) -> dict:
        """GET interact"""
        params = ctx.params
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

    def _get_furniture_slots(self, ctx: RouteContext) -> dict:
        """GET furniture_slots"""
        params = ctx.params
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

    def _post_decor(self, ctx: RouteContext) -> dict:
        """POST decor/place/decor/store/decor/reset"""
        endpoint = ctx.endpoint
        payload = ctx.payload
        persona = ctx.persona
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

    def _post_interact(self, ctx: RouteContext) -> dict:
        """POST interact"""
        actual = ctx.actual
        now = ctx.now
        payload = ctx.payload
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

    def _post_use_item(self, ctx: RouteContext) -> dict:
        """POST use_item"""
        actual = ctx.actual
        now = ctx.now
        payload = ctx.payload
        result = goods.use_item(
            self.plans_path.parent,
            actual["persona"],
            str(payload.get("item") or payload.get("id") or ""),
            at=now,
        )
        return result

    def _post_place_item(self, ctx: RouteContext) -> dict:
        """POST place_item"""
        actual = ctx.actual
        payload = ctx.payload
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

    def _post_item_wish(self, ctx: RouteContext) -> dict:
        """POST item_wish"""
        action = ctx.action
        actual = ctx.actual
        item = ctx.item
        item_id = ctx.item_id
        now = ctx.now
        payload = ctx.payload
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

    def _post_cooking_cook(self, ctx: RouteContext) -> dict:
        """POST cooking/cook"""
        now = ctx.now
        payload = ctx.payload
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

    def _post_gift_dismiss(self, ctx: RouteContext) -> dict:
        """POST gift/dismiss"""
        action = ctx.action
        actual = ctx.actual
        payload = ctx.payload
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

    def _post_gift_accept(self, ctx: RouteContext) -> dict:
        """POST gift/accept"""
        action = ctx.action
        actual = ctx.actual
        current = ctx.current
        now = ctx.now
        payload = ctx.payload
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

    def _post_cooking_serve(self, ctx: RouteContext) -> dict:
        """POST cooking/serve"""
        actual = ctx.actual
        now = ctx.now
        payload = ctx.payload
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
