from __future__ import annotations

import ast
import asyncio
import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .models import TimelineItem, minute_of_day


class FormulaError(ValueError):
    pass


class SafeFormulaEvaluator:
    _binary_operators = {
        ast.Add: lambda left, right: left + right,
        ast.Sub: lambda left, right: left - right,
        ast.Mult: lambda left, right: left * right,
        ast.Div: lambda left, right: left / right,
    }
    _unary_operators = {
        ast.UAdd: lambda value: value,
        ast.USub: lambda value: -value,
    }

    def __init__(
        self, random_fn: Callable[[float, float], float] | None = None
    ) -> None:
        self.random_fn = random_fn or random.uniform

    def evaluate(self, expression: str, variables: dict[str, float]) -> float:
        if not isinstance(expression, str) or not expression.strip():
            raise FormulaError("formula must be a non-empty string")
        if len(expression) > 500:
            raise FormulaError("formula is too long")
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise FormulaError(f"invalid formula syntax: {exc.msg}") from exc
        if sum(1 for _ in ast.walk(tree)) > 100:
            raise FormulaError("formula is too complex")
        try:
            result = float(self._evaluate_node(tree.body, variables))
        except FormulaError:
            raise
        except (ArithmeticError, TypeError, ValueError) as exc:
            raise FormulaError(f"formula evaluation failed: {exc}") from exc
        if not math.isfinite(result):
            raise FormulaError("formula result must be finite")
        return result

    def _evaluate_node(self, node: ast.AST, variables: dict[str, float]) -> float:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise FormulaError("only numeric constants are allowed")
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise FormulaError(f"unknown variable: {node.id}")
            return float(variables[node.id])
        if isinstance(node, ast.BinOp):
            operation = self._binary_operators.get(type(node.op))
            if operation is None:
                raise FormulaError("unsupported binary operator")
            return float(
                operation(
                    self._evaluate_node(node.left, variables),
                    self._evaluate_node(node.right, variables),
                )
            )
        if isinstance(node, ast.UnaryOp):
            operation = self._unary_operators.get(type(node.op))
            if operation is None:
                raise FormulaError("unsupported unary operator")
            return float(operation(self._evaluate_node(node.operand, variables)))
        if isinstance(node, ast.Call):
            return self._evaluate_call(node, variables)
        raise FormulaError(f"unsupported formula element: {type(node).__name__}")

    def _evaluate_call(self, node: ast.Call, variables: dict[str, float]) -> float:
        if not isinstance(node.func, ast.Name) or node.keywords:
            raise FormulaError(
                "only direct function calls without keywords are allowed"
            )
        name = node.func.id
        arguments = [self._evaluate_node(item, variables) for item in node.args]
        if name == "random":
            if len(arguments) != 2:
                raise FormulaError("random requires exactly two arguments")
            low, high = arguments
            if high < low:
                raise FormulaError("random upper bound must not be below lower bound")
            return float(self.random_fn(low, high))
        if name == "probability":
            if len(arguments) not in {2, 3}:
                raise FormulaError("probability requires two or three arguments")
            chance, hit_value = arguments[:2]
            if not 0 <= chance <= 1:
                raise FormulaError("probability must be between 0 and 1")
            miss_value = arguments[2] if len(arguments) == 3 else 0.0
            if chance == 0:
                return float(miss_value)
            if chance == 1:
                return float(hit_value)
            return float(hit_value if self.random_fn(0.0, 1.0) < chance else miss_value)
        if name in {"min", "max"}:
            if not arguments:
                raise FormulaError(f"{name} requires at least one argument")
            return float(min(arguments) if name == "min" else max(arguments))
        if name == "round":
            if len(arguments) not in {1, 2}:
                raise FormulaError("round requires one or two arguments")
            digits = int(arguments[1]) if len(arguments) == 2 else 0
            return float(round(arguments[0], digits))
        if name in {"ceil", "floor"}:
            if len(arguments) != 1:
                raise FormulaError(f"{name} requires exactly one argument")
            return float(
                math.ceil(arguments[0]) if name == "ceil" else math.floor(arguments[0])
            )
        raise FormulaError(f"unsupported function: {name}")


@dataclass(slots=True, frozen=True)
class DelayDecision:
    delay_seconds: int
    remaining_seconds: int
    availability: str
    formula: str
    public_reason: str
    formula_error: str = ""
    active_conversation: bool = False


class ReplyDelayPolicy:
    def __init__(
        self,
        settings: dict[str, Any] | None = None,
        *,
        evaluator: SafeFormulaEvaluator | None = None,
    ) -> None:
        self.settings = settings or {}
        self.evaluator = evaluator or SafeFormulaEvaluator()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.get("enable"))

    @property
    def notify_user(self) -> bool:
        return bool(self.settings.get("notify_user"))

    @property
    def active_conversation_seconds(self) -> int:
        return self._nonnegative_int("active_conversation_seconds")

    @property
    def max_delay_seconds(self) -> int:
        return self._nonnegative_int("max_delay_seconds")

    @property
    def merge_window_seconds(self) -> int:
        """连续对话里也等待这么久，把连发的几条消息合并成一次回复。"""
        return self._nonnegative_int("merge_window_seconds")

    @property
    def merge_extend(self) -> bool:
        """新消息在合并窗口内到达时，是否顺延截止时间。"""
        return bool(self.settings.get("merge_extend", True))

    @property
    def max_merge_seconds(self) -> int:
        """单批次最多等多久，防止用户一直发消息时永远不回复。"""
        return self._nonnegative_int("max_merge_seconds")

    def decide(
        self,
        item: TimelineItem,
        now: datetime,
        message_length: int,
        *,
        active_conversation: bool = False,
        needs: dict | None = None,
    ) -> DelayDecision:
        remaining = self._remaining_seconds(item, now)
        formula = self._formula(item.availability)
        reason = self._public_reason(item.availability)
        if active_conversation:
            merge = self.merge_window_seconds
            if self.max_delay_seconds:
                merge = min(merge, self.max_delay_seconds)
            return DelayDecision(
                delay_seconds=min(merge, remaining),
                remaining_seconds=remaining,
                availability=item.availability,
                formula=formula,
                public_reason=reason,
                active_conversation=True,
            )

        variables = {
            "remaining": float(remaining),
            "message_length": float(max(0, message_length)),
        }
        formula_error = ""
        try:
            calculated = self.evaluator.evaluate(formula, variables)
        except FormulaError as exc:
            formula_error = str(exc)
            calculated = 0.0
        delay = math.ceil(max(0.0, calculated))
        if delay == 0 and self.merge_window_seconds:
            delay = self.merge_window_seconds
        delay += self._need_delay_seconds(needs)
        delay = min(delay, remaining, self.max_delay_seconds)
        return DelayDecision(
            delay_seconds=delay,
            remaining_seconds=remaining,
            availability=item.availability,
            formula=formula,
            public_reason=reason,
            formula_error=formula_error,
        )

    @staticmethod
    def _need_delay_seconds(needs: dict | None) -> int:
        """Tired / hungry / low-mood characters take a little longer to reply."""
        if not isinstance(needs, dict):
            return 0

        def value(key: str) -> float | None:
            try:
                return max(0.0, min(100.0, float(needs.get(key))))
            except (TypeError, ValueError):
                return None

        extra = 0
        energy = value("energy")
        satiety = value("satiety")
        hygiene = value("hygiene")
        mood = value("mood")
        willingness = value("willingness")
        health = value("health")
        if energy is not None:
            if energy < 20:
                extra += 60
            elif energy < 35:
                extra += 30
        if satiety is not None and satiety < 25:
            extra += 20
        if hygiene is not None and hygiene < 30:
            extra += 10
        if mood is not None and mood < 35:
            extra += 30
        if willingness is not None and willingness < 30:
            extra += 20
        if health is not None and health < 50:
            extra += 30
        if isinstance(needs, dict) and needs.get("weak_constitution"):
            extra += 20
        if isinstance(needs, dict) and int(needs.get("rainy_streak") or 0) >= 2:
            extra += 10
        if isinstance(needs, dict) and int(
            needs.get("sleep_regularity_minutes") or 0
        ) >= 120:
            extra += 15
        if isinstance(needs, dict) and int(
            needs.get("social_jetlag_minutes") or 0
        ) >= 90:
            extra += 10
        if isinstance(needs, dict) and int(needs.get("late_night_streak") or 0) >= 3:
            extra += 10
        if isinstance(needs, dict) and int(needs.get("sunny_streak") or 0) >= 3:
            extra = max(0, extra - 10)
        if isinstance(needs, dict) and int(needs.get("hydration") or 100) < 30:
            extra += 10
        if isinstance(needs, dict) and needs.get("hangover"):
            extra += 20
            if str(needs.get("hangover_severity") or "") == "severe":
                extra += 10
        if isinstance(needs, dict) and needs.get("alcohol_today"):
            extra += 10
        if isinstance(needs, dict) and needs.get("tipsy"):
            extra = max(0, extra - 10)
        if isinstance(needs, dict) and needs.get("frequent_drinking"):
            extra += 10
        if isinstance(needs, dict) and needs.get("drinking_recovery"):
            extra = max(0, extra - 5)
        if isinstance(needs, dict) and int(needs.get("work_stress") or 0) >= 4:
            extra += 10
        if isinstance(needs, dict) and needs.get("overwork"):
            extra += 10
        if isinstance(needs, dict) and needs.get("caffeine_crash"):
            extra += 10
        if isinstance(needs, dict) and needs.get("fever_recovery"):
            extra += 10
        if isinstance(needs, dict) and needs.get("eye_strain"):
            extra += 5
        if isinstance(needs, dict) and needs.get("muscle_soreness"):
            extra += 5
        if isinstance(needs, dict) and needs.get("frequent_heavy_food"):
            extra += 5
        if isinstance(needs, dict):
            extra += min(20, int(needs.get("discomfort_count") or 0) * 3)
        if isinstance(needs, dict) and needs.get("energetic_music_sleep"):
            extra = max(0, extra - 5)
        if isinstance(needs, dict) and needs.get("audio_sleep_relief"):
            extra += 5
        if isinstance(needs, dict) and needs.get("body_odor"):
            extra += 8
        if isinstance(needs, dict) and needs.get("monday_blues"):
            extra += 5
        if isinstance(needs, dict) and needs.get("socially_satisfied"):
            extra = max(0, extra - 5)
        if isinstance(needs, dict) and needs.get("need_solitude"):
            extra += 8
        if isinstance(needs, dict) and needs.get("social_hangover_yesterday"):
            extra += 5
        if isinstance(needs, dict) and needs.get("afternoon_dip") and not needs.get(
            "afternoon_dip_relief"
        ):
            extra += 3
        if isinstance(needs, dict) and needs.get("morning_grogginess") and not needs.get(
            "morning_grogginess_relief"
        ):
            extra += 3
        if isinstance(needs, dict) and needs.get("evening_sleepiness"):
            extra += 2
        if isinstance(needs, dict) and needs.get("sick"):
            extra += 60
            if str(needs.get("illness_severity") or "") == "severe":
                extra += 30
            if needs.get("fever"):
                extra += 30
        return min(extra, 180)

    def notification(self, decision: DelayDecision) -> str:
        template = str(self.settings.get("notification_template") or "").strip()
        if not template:
            return ""
        values = {
            "delay_seconds": decision.delay_seconds,
            "public_reason": decision.public_reason,
            "availability": decision.availability,
        }
        try:
            return template.format_map(values).strip()
        except (KeyError, ValueError):
            return ""

    def _formula(self, availability: str) -> str:
        configured = self.settings.get("delay_formulas", {}) or {}
        value = configured.get(availability) if isinstance(configured, dict) else None
        return str(value).strip() if value is not None else ""

    def _public_reason(self, availability: str) -> str:
        configured = self.settings.get("public_reasons", {}) or {}
        value = configured.get(availability) if isinstance(configured, dict) else None
        return str(value).strip() if value is not None else ""

    def _nonnegative_int(self, key: str) -> int:
        try:
            return max(0, int(self.settings.get(key)))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _remaining_seconds(item: TimelineItem, now: datetime) -> int:
        end_minute = minute_of_day(item.end)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_at = day_start + timedelta(minutes=end_minute)
        return max(0, math.floor((end_at - now).total_seconds()))


@dataclass(slots=True, frozen=True)
class QueuedMessage:
    received_at: datetime
    sender_id: str
    sender_name: str
    prompt: str
    image_urls: tuple[str, ...] = ()
    audio_urls: tuple[str, ...] = ()
    temporary_files: tuple[str, ...] = ()


@dataclass(slots=True)
class DelayBatch:
    umo: str
    created_at: datetime
    deadline: datetime
    decision: DelayDecision
    arrival_item: TimelineItem | None = None
    messages: list[QueuedMessage] = field(default_factory=list)
    settle_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)


class ReplyDelayCoordinator:
    def __init__(self) -> None:
        self._batches: dict[str, DelayBatch] = {}
        self._active_until: dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def enqueue(
        self,
        umo: str,
        message: QueuedMessage,
        decision: DelayDecision,
        arrival_item: TimelineItem | None = None,
        *,
        extend_seconds: int = 0,
        max_total_seconds: int = 0,
    ) -> tuple[DelayBatch | None, bool]:
        async with self._lock:
            current = self._batches.get(umo)
            if current is not None and message.received_at < current.deadline:
                current.messages.append(message)
                if extend_seconds > 0:
                    candidate = message.received_at + timedelta(
                        seconds=extend_seconds
                    )
                    if max_total_seconds > 0:
                        candidate = min(
                            candidate,
                            current.created_at
                            + timedelta(seconds=max_total_seconds),
                        )
                    if candidate > current.deadline:
                        current.deadline = candidate
                return current, False
            if current is not None:
                self._batches.pop(umo, None)
            if decision.delay_seconds <= 0:
                return None, True
            batch = DelayBatch(
                umo=umo,
                created_at=message.received_at,
                deadline=message.received_at
                + timedelta(seconds=decision.delay_seconds),
                decision=decision,
                arrival_item=arrival_item,
                messages=[message],
            )
            self._batches[umo] = batch
            return batch, True

    async def settle(
        self, batch: DelayBatch, now: datetime
    ) -> tuple[QueuedMessage, ...]:
        remaining = max(0.0, (batch.deadline - now).total_seconds())
        if remaining:
            try:
                await asyncio.wait_for(batch.settle_event.wait(), timeout=remaining)
            except TimeoutError:
                pass
        async with self._lock:
            if self._batches.get(batch.umo) is batch:
                self._batches.pop(batch.umo, None)
            return tuple(batch.messages)

    async def settle_now(self, umo: str) -> DelayBatch | None:
        async with self._lock:
            batch = self._batches.pop(umo, None)
            if batch is not None:
                batch.settle_event.set()
            return batch

    async def settle_all_now(self) -> tuple[DelayBatch, ...]:
        async with self._lock:
            batches = tuple(self._batches.values())
            self._batches.clear()
            for batch in batches:
                batch.settle_event.set()
            return batches

    def is_active(self, umo: str, now: datetime) -> bool:
        active_until = self._active_until.get(umo)
        if active_until is None:
            return False
        if now >= active_until:
            self._active_until.pop(umo, None)
            return False
        return True

    def mark_replied(self, umo: str, now: datetime, active_seconds: int) -> None:
        if active_seconds <= 0:
            self._active_until.pop(umo, None)
            return
        self._active_until[umo] = now + timedelta(seconds=active_seconds)

    def clear(self) -> None:
        for batch in self._batches.values():
            batch.settle_event.set()
        self._batches.clear()
        self._active_until.clear()


def format_queued_messages(messages: tuple[QueuedMessage, ...], *, group: bool) -> str:
    if not messages:
        return ""
    if len(messages) == 1:
        return messages[0].prompt
    lines = ["<delayed_user_messages>", "以下消息在同一等待批次中按时间顺序收到："]
    for message in messages:
        sender = "用户"
        if group:
            sender = message.sender_name or message.sender_id or "群成员"
            if message.sender_id and message.sender_id not in sender:
                sender += f" ({message.sender_id})"
        content = message.prompt.strip()
        media = []
        if message.image_urls:
            media.append(f"{len(message.image_urls)} 张图片")
        if message.audio_urls:
            media.append(f"{len(message.audio_urls)} 条音频")
        if media:
            content = (
                (content + " " if content else "") + "[附件：" + "、".join(media) + "]"
            )
        lines.append(
            f"[{message.received_at.strftime('%H:%M:%S')}] {sender}：{content or '[无文本]'}"
        )
    lines.append("</delayed_user_messages>")
    return "\n".join(lines)


def format_delay_context(
    batch: DelayBatch,
    settled_at: datetime,
    current_item: TimelineItem | None,
) -> str:
    arrival = batch.arrival_item
    actual_delay = max(0, math.ceil((settled_at - batch.created_at).total_seconds()))
    lines = [
        "<reply_delay_context>",
        f"首条消息到达时间：{batch.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"计划回复延迟：{batch.decision.delay_seconds} 秒",
        f"实际等待时间：{actual_delay} 秒",
        f"消息批次数量：{len(batch.messages)}",
    ]
    if batch.decision.active_conversation:
        lines.append("延迟判定：处于连续对话窗口，只等待合并窗口后再回应。")
    if len(batch.messages) > 1:
        lines.append(
            "本批次包含连续发来的多条消息：请合并理解后一次性回复，不要逐条分别回答。"
        )
    if arrival is not None:
        lines.extend(
            [
                f"消息到达时活动：{arrival.activity}",
                f"消息到达时地点：{arrival.location or '未说明'}",
                f"消息到达时状态：{arrival.state}",
                f"消息到达时可打扰度：{arrival.availability}",
                f"消息到达时段：{arrival.start}-{arrival.end}",
            ]
        )
    if current_item is not None:
        lines.extend(
            [
                f"结算时活动：{current_item.activity}",
                f"结算时地点：{current_item.location or '未说明'}",
                f"结算时状态：{current_item.state}",
                f"结算时可打扰度：{current_item.availability}",
            ]
        )
    lines.extend(
        [
            "角色行为要求：结合上述具体状态自然回复，保持角色一致；按照与用户的关系，选择性披露具体活动、地点；不要主动向用户披露内部延迟计算规则。",
            "</reply_delay_context>",
        ]
    )
    return "\n".join(lines)
