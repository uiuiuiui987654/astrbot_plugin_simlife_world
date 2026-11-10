"""Wallet, savings goal, shop and garage."""

from __future__ import annotations


from astrbot.api import logger

from .. import (
    affection,
    diary,
    garage,
    goods,
    money,
)

from .context import RouteContext


class MoneyRoutes:
    """Mixin for VirtualLifeViewAPI; expects ``self.plugin`` and ``self.plans_path``."""

    def _get_wallet(self, ctx: RouteContext) -> dict:
        """GET wallet"""
        params = ctx.params
        target_persona = str(params.get("persona") or "").strip()
        if not target_persona:
            return {"ok": False, "error": "缺少人格"}
        return {
            "ok": True,
            "wallet": money.snapshot(
                self.plans_path.parent, target_persona, limit=30
            ),
        }

    def _get_garage(self, ctx: RouteContext) -> dict:
        """GET garage"""
        params = ctx.params
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

    def _get_shop(self, ctx: RouteContext) -> dict:
        """GET shop"""
        params = ctx.params
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

    def _post_wallet_goal_clear(self, ctx: RouteContext) -> dict:
        """POST wallet/goal/clear"""
        params = ctx.params
        payload = ctx.payload
        target_persona = str(
            payload.get("persona") or params.get("persona") or ""
        ).strip()
        if not target_persona:
            return {"ok": False, "error": "缺少人格"}
        return money.clear_goal(self.plans_path.parent, target_persona)

    def _post_garage_drive(self, ctx: RouteContext) -> dict:
        """POST garage/drive"""
        params = ctx.params
        payload = ctx.payload
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

    def _post_garage_return(self, ctx: RouteContext) -> dict:
        """POST garage/return"""
        params = ctx.params
        payload = ctx.payload
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

    def _post_garage_refuel(self, ctx: RouteContext) -> dict:
        """POST garage/refuel"""
        params = ctx.params
        payload = ctx.payload
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

    def _post_wallet_give(self, ctx: RouteContext) -> dict:
        """POST wallet/give"""
        params = ctx.params
        payload = ctx.payload
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
            logger.warning("[模拟人生] dispatch 失败: %s", exc, exc_info=True)
            return {"ok": False, "error": f"给钱失败：{exc}"}
        return {
            "ok": True,
            "amount": result.get("amount", amount),
            "balance": result.get("balance"),
            "wallet": money.snapshot(
                self.plans_path.parent, target_persona, limit=30
            ),
        }

    def _post_wallet_goal(self, ctx: RouteContext) -> dict:
        """POST wallet/goal"""
        actual = ctx.actual
        now = ctx.now
        payload = ctx.payload
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

    def _post_shop_buy(self, ctx: RouteContext) -> dict:
        """POST shop/buy"""
        actual = ctx.actual
        item = ctx.item
        item_id = ctx.item_id
        now = ctx.now
        payload = ctx.payload
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
