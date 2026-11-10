"""Money, deliveries, diaries, anniversaries and garage returns.

Mixin for ProactiveVirtualDailyPlugin; split out of main.py without behaviour changes.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from astrbot.api import logger

from .. import (
    affection,
    books,
    delivery,
    diary,
    garage,
    item_effects,
    money,
    view_state,
    weekly,
    world_events,
)


class LifeEventsMixin:
    async def _record_garage_returns(self, persona, now) -> None:
        """Auto-returned trips become a diary entry and a little affection."""
        try:
            trips = garage.recent_returns(self.data_dir, persona.id, now=now, hours=36)
        except Exception as exc:
            logger.warning("[模拟人生] 检查回车记录失败: %s", exc)
            return
        for trip in trips:
            try:
                returned_at = str(trip.get("returned_at") or "")[:10]
                driver = "主人开车" if trip.get("driver") == "master" else "她自己开车"
                day = returned_at or now.date().isoformat()
                if not diary.has_entry(self.data_dir, persona.id, day, "outing"):
                    diary.add_entry(
                        self.data_dir,
                        persona.id,
                        day,
                        "兜风回来",
                        f"{driver}带她去了{trip.get('destination') or '兜风'}，"
                        "回来的时候心情很好。",
                        source="outing",
                        now=now,
                    )
                    affection.add(
                        self.data_dir,
                        persona.id,
                        1,
                        "兜风回来",
                        now=now,
                    )
                garage.mark_noted(self.data_dir, persona.id, str(trip.get("id") or ""))
            except Exception as exc:
                logger.warning("[模拟人生] 记录回车失败: %s", exc)

    async def _ensure_world_event(self, persona, day) -> dict | None:
        try:
            event = world_events.get_or_create(
                self.data_dir, persona.id, day.isoformat()
            )
        except Exception as exc:
            logger.warning("[模拟人生] 生成今日小事失败: %s", exc)
            return None
        if event.get("created") and int(event.get("mood") or 0) != 0:
            try:
                item_effects.add(
                    self.data_dir,
                    persona.id,
                    {"mood": int(event.get("mood") or 0)},
                    label=f"今天的小事：{event.get('title')}",
                    now=self._now(),
                    ttl_minutes=12 * 60,
                )
            except Exception:
                logger.debug("[模拟人生] _ensure_world_event 出错，已忽略", exc_info=True)
            logger.info(
                "[模拟人生] 今日小事 persona=%s title=%s mood=%s",
                persona.id,
                event.get("title"),
                event.get("mood"),
            )
        return event

    async def _process_deliveries(self, persona, now=None) -> list[dict]:
        try:
            delivered = await asyncio.to_thread(
                delivery.deliver_due,
                self.data_dir,
                persona.id,
                now or self._now(),
            )
        except Exception as exc:
            logger.warning("[模拟人生] 处理送货失败: %s", exc)
            return []
        if delivered:
            names = "、".join(
                str((order.get("goods") or {}).get("name") or "商品")
                for order in delivered
            )
            logger.info(
                "[模拟人生] 送货到达 persona=%s items=%s",
                persona.id,
                names,
            )
        return delivered

    def _money_settings(self) -> dict:
        return self.config.get("money_settings", {}) or {}

    def _living_settings(self) -> dict:
        return self.config.get("living_cost_settings", {}) or {}

    async def _settle_work_income(self, persona, day, *, before=None) -> None:
        settings = self._money_settings()
        if not bool(settings.get("enable", True)):
            return
        try:
            plan = self.storage.get_plan(day.isoformat(), persona.id)
            if plan is None or not plan.has_schedule:
                return
            result = await asyncio.to_thread(
                money.settle_work_segments,
                self.data_dir,
                persona.id,
                day.isoformat(),
                plan,
                before=before,
                hourly_rate=float(settings.get("hourly_rate", 20)),
                at=self._now(),
            )
            if float(result.get("amount") or 0) > 0:
                logger.info(
                    "[模拟人生] 工作收入结算 persona=%s date=%s minutes=%s amount=%s",
                    persona.id,
                    day.isoformat(),
                    result.get("minutes"),
                    result.get("amount"),
                )
            await self._settle_living_costs(persona, day, plan=plan, before=before)
            await self._maybe_queue_goal_wish(persona)
        except Exception as exc:
            logger.warning(
                "[模拟人生] 工作收入结算失败 persona=%s: %s", persona.id, exc
            )

    async def _settle_living_costs(
        self, persona, day, *, plan=None, before=None
    ) -> None:
        settings = self._living_settings()
        if not bool(settings.get("enable", True)):
            return
        try:
            if plan is None:
                plan = self.storage.get_plan(day.isoformat(), persona.id)
            if plan is None or not plan.has_schedule:
                return
            result = await asyncio.to_thread(
                money.settle_expense_segments,
                self.data_dir,
                persona.id,
                day.isoformat(),
                plan,
                before=before,
                breakfast=float(settings.get("breakfast", 8)),
                lunch=float(settings.get("lunch", 18)),
                dinner=float(settings.get("dinner", 22)),
                transport=float(settings.get("transport", 4)),
                at=self._now(),
            )
            if float(result.get("amount") or 0) > 0:
                logger.info(
                    "[模拟人生] 生活开销结算 persona=%s date=%s amount=%s balance=%s",
                    persona.id,
                    day.isoformat(),
                    result.get("amount"),
                    result.get("balance"),
                )
        except Exception as exc:
            logger.warning(
                "[模拟人生] 生活开销结算失败 persona=%s: %s", persona.id, exc
            )

    async def _write_yearly_diary(self, persona, now) -> None:
        if now.month != 1 or now.day != 1:
            return
        try:
            end_day = now.date() - timedelta(days=1)
            if diary.has_entry(
                self.data_dir,
                persona.id,
                end_day.isoformat(),
                "yearly",
            ):
                return
            report = weekly.build(
                self.data_dir,
                persona.id,
                now=now - timedelta(days=1),
                days=365,
            )
            diary.add_entry(
                self.data_dir,
                persona.id,
                end_day.isoformat(),
                "这一年",
                weekly.format_report(report)[:1200],
                source="yearly",
                now=now,
            )
            logger.info(
                "[模拟人生] 已生成年记 persona=%s end=%s",
                persona.id,
                end_day.isoformat(),
            )
        except Exception as exc:
            logger.warning("[模拟人生] 生成年记失败: %s", exc)

    async def _write_monthly_diary(self, persona, now) -> None:
        if now.day != 1:
            return
        try:
            end_day = now.date() - timedelta(days=1)
            if diary.has_entry(
                self.data_dir,
                persona.id,
                end_day.isoformat(),
                "monthly",
            ):
                return
            report = weekly.build(
                self.data_dir,
                persona.id,
                now=now - timedelta(days=1),
                days=30,
            )
            diary.add_entry(
                self.data_dir,
                persona.id,
                end_day.isoformat(),
                "这个月",
                weekly.format_report(report)[:1200],
                source="monthly",
                now=now,
            )
            logger.info(
                "[模拟人生] 已生成月记 persona=%s end=%s",
                persona.id,
                end_day.isoformat(),
            )
        except Exception as exc:
            logger.warning("[模拟人生] 生成月记失败: %s", exc)

    async def _write_weekly_diary(self, persona, now) -> None:
        if now.weekday() != 0:
            return
        try:
            end_day = now.date() - timedelta(days=1)
            if diary.has_entry(
                self.data_dir,
                persona.id,
                end_day.isoformat(),
                "weekly",
            ):
                return
            report = weekly.build(
                self.data_dir,
                persona.id,
                now=now - timedelta(days=1),
                days=7,
            )
            summary = weekly.format_report(report)
            diary.add_entry(
                self.data_dir,
                persona.id,
                end_day.isoformat(),
                "这一周",
                summary[:1200],
                source="weekly",
                now=now,
            )
            logger.info(
                "[模拟人生] 已生成周记 persona=%s end=%s",
                persona.id,
                end_day.isoformat(),
            )
        except Exception as exc:
            logger.warning("[模拟人生] 生成周记失败: %s", exc)

    async def _record_anniversary(self, persona, now) -> None:
        try:
            info = affection.snapshot(self.data_dir, persona.id, now=now)
            if not info.get("is_anniversary"):
                return
            day_text = now.date().isoformat()
            if diary.has_entry(self.data_dir, persona.id, day_text, "anniversary"):
                return
            days = int(info.get("days_known") or 1)
            diary.add_entry(
                self.data_dir,
                persona.id,
                day_text,
                f"认识第 {days} 天",
                (
                    f"今天是我们认识第 {days} 天。"
                    f"当前关系：{info.get('level')}，"
                    f"好感 {info.get('score')} / 1000。"
                ),
                source="anniversary",
                now=now,
            )
            logger.info(
                "[模拟人生] 关系纪念日 persona=%s days=%s",
                persona.id,
                days,
            )
        except Exception as exc:
            logger.warning("[模拟人生] 记录关系纪念日失败: %s", exc)

    @staticmethod
    def _diary_weather_text(plan) -> str:
        """Render plan.weather as readable text instead of a dataclass repr."""
        weather = getattr(plan, "weather", None)
        if weather is None:
            return "未知"
        if isinstance(weather, dict):
            condition = str(weather.get("condition") or "").strip()
            description = str(weather.get("description") or "").strip()
            try:
                low = int(weather.get("temperature_low"))
                high = int(weather.get("temperature_high"))
                label = f"{condition} {low}~{high}°C".strip()
            except (TypeError, ValueError):
                label = condition
            if description:
                return (label + "，" + description).strip("，")
            return label or "未知"
        label = str(getattr(weather, "label", "") or "").strip()
        description = str(getattr(weather, "description", "") or "").strip()
        if label:
            return (label + "，" + description).strip("，") if description else label
        if description:
            return description
        return str(weather)

    async def _write_daily_diary(self, persona, day) -> None:
        """Create a small factual diary entry for a finished day."""
        try:
            if diary.has_entry(self.data_dir, persona.id, day.isoformat(), "auto"):
                return
            plan = self.storage.get_plan(day.isoformat(), persona.id)
            if plan is None or not plan.has_schedule:
                return
            snapshot = money.snapshot(self.data_dir, persona.id, limit=60)
            day_text = day.isoformat()
            day_transactions = [
                item
                for item in snapshot.get("transactions") or []
                if str(item.get("at") or "")[:10] == day_text
            ]
            income = sum(
                float(item.get("amount") or 0)
                for item in day_transactions
                if float(item.get("amount") or 0) > 0
            )
            expense = sum(
                -float(item.get("amount") or 0)
                for item in day_transactions
                if float(item.get("amount") or 0) < 0
            )
            work_minutes = money.work_minutes(plan)
            books_read = []
            purchases = []
            for item in snapshot.get("possessions") or []:
                book = books.find_book(
                    str(item.get("book_id") or item.get("name") or "")
                )
                if book is not None:
                    progress = books.get_progress(
                        self.data_dir,
                        persona.id,
                        str(book.get("id") or ""),
                    )
                    state_text = (
                        "读完"
                        if progress.get("finished")
                        else f"第 {progress.get('chapter')} 章"
                    )
                    books_read.append(f"《{book.get('title')}》{state_text}")
                if str(item.get("at") or "")[:10] == day_text:
                    purchases.append(str(item.get("name") or ""))
            lines = [
                f"主题：{getattr(plan, 'theme', '日常')}，"
                f"天气：{self._diary_weather_text(plan)}。",
            ]
            world_event = world_events.recent(self.data_dir, persona.id, day_text)
            if world_event:
                lines.append(f"今天的小事：{world_event.get('summary')}")
            if work_minutes:
                lines.append(f"工作 {work_minutes} 分钟。")
            if income or expense:
                lines.append(
                    f"收支：收入 {money.format_money(income)} 元，"
                    f"支出 {money.format_money(expense)} 元，"
                    f"余额 {money.format_money(snapshot.get('balance') or 0)} 元。"
                )
            if books_read:
                lines.append("书：" + "、".join(books_read[:4]) + "。")
            if purchases:
                lines.append("新东西：" + "、".join(purchases[:5]) + "。")
            goal = snapshot.get("goal")
            if goal:
                lines.append(
                    f"存款目标：{goal.get('name')} "
                    f"{money.format_money(goal.get('progress') or 0)}/"
                    f"{money.format_money(goal.get('target') or 0)} 元。"
                )
            diary.add_entry(
                self.data_dir,
                persona.id,
                day_text,
                f"{day.month} 月 {day.day} 日",
                "\n".join(lines),
                source="auto",
                now=self._now(),
            )
            logger.info(
                "[模拟人生] 已生成日记 persona=%s date=%s",
                persona.id,
                day_text,
            )
        except Exception as exc:
            logger.warning("[模拟人生] 生成日记失败 persona=%s: %s", persona.id, exc)

    async def _maybe_queue_goal_wish(self, persona) -> None:
        """When a savings goal is reached, queue a wish request for the master."""
        try:
            snapshot = money.snapshot(self.data_dir, persona.id, limit=1)
        except Exception:
            logger.debug("[模拟人生] _maybe_queue_goal_wish 出错，已忽略", exc_info=True)
            return
        goal = snapshot.get("goal")
        if not goal or goal.get("fulfilled") or not goal.get("achieved"):
            return
        requested_at = str(goal.get("requested_at") or "")
        if requested_at:
            try:
                requested = datetime.fromisoformat(requested_at)
                if self._now() - requested < timedelta(hours=12):
                    return
            except ValueError:
                pass
        try:
            pending = view_state.load_pending_actions(
                self.data_dir / "plans.json", persona.id
            )
        except Exception:
            logger.debug("[模拟人生] _maybe_queue_goal_wish 出错，已忽略", exc_info=True)
            pending = []
        if any(str(action.get("kind") or "") == "wish" for action in pending):
            return
        wish = str(goal.get("wish") or "").strip()
        reason = wish or f"攒钱买{goal.get('name')}"
        try:
            view_state.queue_pending_action(
                self.data_dir / "plans.json",
                persona=persona.id,
                label=f"实现月月的愿望：{goal.get('name')}",
                source=(
                    f"月月攒够了 {money.format_money(goal.get('target') or 0)} 元，"
                    f"想让你实现：{reason}"
                ),
                kind="wish",
                amount=float(goal.get("target") or 0),
                reason=reason,
                now=self._now(),
            )
            money.mark_goal_requested(self.data_dir, persona.id, at=self._now())
            logger.info(
                "[模拟人生] 已生成愿望请求 persona=%s goal=%s",
                persona.id,
                goal.get("name"),
            )
        except Exception as exc:
            logger.warning("[模拟人生] 生成愿望请求失败: %s", exc)

    def _wallet_text(self, persona_id: str, limit: int = 3) -> str:
        settings = self._money_settings()
        currency = str(settings.get("currency") or "元")
        snapshot = money.snapshot(self.data_dir, persona_id, limit=limit)
        balance_value = float(snapshot["balance"])
        if balance_value < 0:
            lines = [
                f"钱包余额：欠款 {money.format_money(abs(balance_value))} {currency}"
            ]
        else:
            lines = [f"钱包余额：{money.format_money(balance_value)} {currency}"]
        goal = snapshot.get("goal")
        if goal:
            state_text = (
                "，已实现。"
                if goal.get("fulfilled")
                else (
                    "，已达成，可以向主人提愿望。"
                    if goal.get("achieved")
                    else f"，还差 {money.format_money(goal['remaining'])} {currency}。"
                )
            )
            wish = str(goal.get("wish") or "").strip()
            lines.append(
                f"存款目标：{goal['name']} "
                f"{money.format_money(goal['progress'])}/"
                f"{money.format_money(goal['target'])} {currency}"
                + state_text
                + (f" 愿望：{wish}" if wish else "")
            )
        possessions = snapshot.get("possessions") or []
        if possessions:
            lines.append(
                "已有物品："
                + "、".join(str(item.get("name") or "") for item in possessions[-8:])
            )
        transactions = snapshot.get("transactions") or []
        for item in transactions:
            amount = float(item.get("amount") or 0)
            sign = "+" if amount >= 0 else ""
            lines.append(
                f"{sign}{money.format_money(amount)} {currency} · "
                f"{item.get('reason') or ''}"
            )
        if not transactions:
            lines.append("还没有收支记录。")
        return "\n".join(lines)
