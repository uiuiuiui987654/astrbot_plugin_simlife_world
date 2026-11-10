"""Human-like reply delays.

A per-availability formula (``random(30, 90) + message_length``…) decides how
long she takes to answer; messages arriving meanwhile are collected into one
batch and answered together.
"""

from __future__ import annotations

import ast
import asyncio
import math
import operator
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .models import TimelineItem, minute_of_day

# ---------------------------------------------------------------------------- formulas


class FormulaError(ValueError):
    pass


MAX_FORMULA_LENGTH = 500
MAX_FORMULA_NODES = 100
BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class SafeFormulaEvaluator:
    """Arithmetic over named variables plus a few helper functions; nothing else parses."""

    def __init__(self, random_fn: Callable[[float, float], float] | None = None) -> None:
        self.random_fn = random_fn or random.uniform

    def evaluate(self, expression: str, variables: dict[str, float]) -> float:
        if not isinstance(expression, str) or not expression.strip():
            raise FormulaError("the formula is empty")
        if len(expression) > MAX_FORMULA_LENGTH:
            raise FormulaError("the formula is longer than allowed")
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise FormulaError(f"the formula does not parse: {exc.msg}") from exc
        if sum(1 for _ in ast.walk(tree)) > MAX_FORMULA_NODES:
            raise FormulaError("the formula has too many parts")
        try:
            result = float(self._eval(tree.body, variables))
        except FormulaError:
            raise
        except (ArithmeticError, TypeError, ValueError) as exc:
            raise FormulaError(f"could not compute the formula: {exc}") from exc
        if not math.isfinite(result):
            raise FormulaError("the formula did not give a finite number")
        return result

    def _eval(self, node: ast.AST, variables: dict[str, float]) -> float:
        match node:
            case ast.Constant(value=value):
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise FormulaError("constants must be numbers")
                return float(value)
            case ast.Name(id=name):
                if name not in variables:
                    raise FormulaError(f"no variable called {name}")
                return float(variables[name])
            case ast.BinOp(left=left, op=op, right=right):
                apply = BINARY.get(type(op))
                if apply is None:
                    raise FormulaError("only + - * / are allowed between values")
                return float(apply(self._eval(left, variables), self._eval(right, variables)))
            case ast.UnaryOp(op=op, operand=operand):
                apply = UNARY.get(type(op))
                if apply is None:
                    raise FormulaError("only + and - are allowed in front of a value")
                return float(apply(self._eval(operand, variables)))
            case ast.Call():
                return self._call(node, variables)
        raise FormulaError(f"{type(node).__name__} is not allowed in a formula")

    def _call(self, node: ast.Call, variables: dict[str, float]) -> float:
        if not isinstance(node.func, ast.Name) or node.keywords:
            raise FormulaError("call functions by name with plain arguments")
        name = node.func.id
        args = [self._eval(arg, variables) for arg in node.args]

        def arity(*allowed: int, message: str) -> None:
            if len(args) not in allowed:
                raise FormulaError(message)

        if name == "random":
            arity(2, message="random() takes two numbers")
            low, high = args
            if high < low:
                raise FormulaError("random(low, high) needs high >= low")
            return float(self.random_fn(low, high))
        if name == "probability":
            arity(2, 3, message="probability() takes two or three values")
            chance, hit = args[:2]
            miss = args[2] if len(args) == 3 else 0.0
            if not 0 <= chance <= 1:
                raise FormulaError("probability p has to be within 0..1")
            if chance in (0, 1):
                return float(hit if chance else miss)
            return float(hit if self.random_fn(0.0, 1.0) < chance else miss)
        if name in ("min", "max"):
            if not args:
                raise FormulaError(f"{name}() needs at least one value")
            return float((min if name == "min" else max)(args))
        if name == "round":
            arity(1, 2, message="round() takes one or two values")
            return float(round(args[0], int(args[1]) if len(args) == 2 else 0))
        if name in ("ceil", "floor"):
            arity(1, message=f"{name}() takes one value")
            return float((math.ceil if name == "ceil" else math.floor)(args[0]))
        raise FormulaError(f"there is no function called {name}")


# ---------------------------------------------------------------------------- body state → extra seconds


def _extra_from_bars(needs: dict) -> int:
    """Seconds added for low energy / satiety / hygiene / mood / willingness / health."""

    def bar(key: str) -> float | None:
        try:
            return max(0.0, min(100.0, float(needs.get(key))))
        except (TypeError, ValueError):
            return None

    rules = (  # (bar, below, seconds) — energy checks the stricter threshold first
        ("energy", 20, 60),
        ("energy", 35, 30),
        ("satiety", 25, 20),
        ("hygiene", 30, 10),
        ("mood", 35, 30),
        ("willingness", 30, 20),
        ("health", 50, 30),
    )
    extra, counted = 0, set()
    for key, below, seconds in rules:
        level = bar(key)
        if key not in counted and level is not None and level < below:
            extra += seconds
            counted.add(key)
    return extra


def _count(needs: dict, key: str, default: int = 0) -> int:
    return int(needs.get(key) or default)


def _flag(key: str) -> Callable[[dict], bool]:
    return lambda needs: bool(needs.get(key))


def _unrelieved(key: str) -> Callable[[dict], bool]:
    return lambda needs: bool(needs.get(key)) and not needs.get(f"{key}_relief")


def _at_least(key: str, threshold: int) -> Callable[[dict], bool]:
    return lambda needs: _count(needs, key) >= threshold


# Applied in order; a negative step never takes the running total below zero.
NEED_STEPS: tuple[tuple[Callable[[dict], bool], Callable[[dict], int]], ...] = (
    (_flag("weak_constitution"), lambda n: 20),
    (_at_least("rainy_streak", 2), lambda n: 10),
    (_at_least("sleep_regularity_minutes", 120), lambda n: 15),
    (_at_least("social_jetlag_minutes", 90), lambda n: 10),
    (_at_least("late_night_streak", 3), lambda n: 10),
    (_at_least("sunny_streak", 3), lambda n: -10),
    (lambda n: _count(n, "hydration", 100) < 30, lambda n: 10),
    (_flag("hangover"), lambda n: 30 if str(n.get("hangover_severity") or "") == "severe" else 20),
    (_flag("alcohol_today"), lambda n: 10),
    (_flag("tipsy"), lambda n: -10),
    (_flag("frequent_drinking"), lambda n: 10),
    (_flag("drinking_recovery"), lambda n: -5),
    (_at_least("work_stress", 4), lambda n: 10),
    (_flag("overwork"), lambda n: 10),
    (_flag("caffeine_crash"), lambda n: 10),
    (_flag("fever_recovery"), lambda n: 10),
    (_flag("eye_strain"), lambda n: 5),
    (_flag("muscle_soreness"), lambda n: 5),
    (_flag("frequent_heavy_food"), lambda n: 5),
    (lambda n: True, lambda n: min(20, _count(n, "discomfort_count") * 3)),
    (_flag("energetic_music_sleep"), lambda n: -5),
    (_flag("audio_sleep_relief"), lambda n: 5),
    (_flag("body_odor"), lambda n: 8),
    (_flag("monday_blues"), lambda n: 5),
    (_flag("socially_satisfied"), lambda n: -5),
    (_flag("need_solitude"), lambda n: 8),
    (_flag("social_hangover_yesterday"), lambda n: 5),
    (_unrelieved("afternoon_dip"), lambda n: 3),
    (_unrelieved("morning_grogginess"), lambda n: 3),
    (_flag("evening_sleepiness"), lambda n: 2),
    (
        _flag("sick"),
        lambda n: 60 + (30 if str(n.get("illness_severity") or "") == "severe" else 0) + (30 if n.get("fever") else 0),
    ),
)
MAX_NEED_DELAY = 180


def need_delay_seconds(needs: dict | None) -> int:
    """Tired / hungry / unwell characters take a little longer to reply (capped at 3 minutes)."""
    if not isinstance(needs, dict):
        return 0
    extra = _extra_from_bars(needs)
    for applies, seconds in NEED_STEPS:
        if applies(needs):
            step = seconds(needs)
            extra = extra + step if step >= 0 else max(0, extra + step)
    return min(extra, MAX_NEED_DELAY)


# ---------------------------------------------------------------------------- policy


@dataclass(slots=True, frozen=True)
class DelayDecision:
    delay_seconds: int
    remaining_seconds: int
    availability: str
    formula: str
    public_reason: str
    formula_error: str = ""
    active_conversation: bool = False


def _seconds_until_end(item: TimelineItem, now: datetime) -> int:
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    ends_at = midnight + timedelta(minutes=minute_of_day(item.end))
    return max(0, math.floor((ends_at - now).total_seconds()))


class ReplyDelayPolicy:
    def __init__(self, settings: dict[str, Any] | None = None, *, evaluator: SafeFormulaEvaluator | None = None) -> None:
        self.settings = settings or {}
        self.evaluator = evaluator or SafeFormulaEvaluator()

    def _seconds(self, key: str) -> int:
        try:
            return max(0, int(self.settings.get(key)))
        except (TypeError, ValueError):
            return 0

    def _per_availability(self, key: str, availability: str) -> str:
        table = self.settings.get(key, {}) or {}
        value = table.get(availability) if isinstance(table, dict) else None
        return "" if value is None else str(value).strip()

    enabled = property(lambda self: bool(self.settings.get("enable")))
    notify_user = property(lambda self: bool(self.settings.get("notify_user")))
    active_conversation_seconds = property(lambda self: self._seconds("active_conversation_seconds"))
    max_delay_seconds = property(lambda self: self._seconds("max_delay_seconds"))
    merge_window_seconds = property(
        lambda self: self._seconds("merge_window_seconds"),
        doc="Wait this long even mid-conversation, so a burst of messages gets one reply.",
    )
    merge_extend = property(
        lambda self: bool(self.settings.get("merge_extend", True)),
        doc="Whether a message arriving inside the merge window pushes the deadline back.",
    )
    max_merge_seconds = property(
        lambda self: self._seconds("max_merge_seconds"),
        doc="Upper bound for one batch, so a chatty user still gets an answer.",
    )

    def decide(
        self,
        item: TimelineItem,
        now: datetime,
        message_length: int,
        *,
        active_conversation: bool = False,
        needs: dict | None = None,
    ) -> DelayDecision:
        remaining = _seconds_until_end(item, now)
        decision = dict(
            remaining_seconds=remaining,
            availability=item.availability,
            formula=self._per_availability("delay_formulas", item.availability),
            public_reason=self._per_availability("public_reasons", item.availability),
        )
        if active_conversation:
            merge = self.merge_window_seconds
            if self.max_delay_seconds:
                merge = min(merge, self.max_delay_seconds)
            return DelayDecision(delay_seconds=min(merge, remaining), active_conversation=True, **decision)

        error = ""
        try:
            computed = self.evaluator.evaluate(
                decision["formula"], {"remaining": float(remaining), "message_length": float(max(0, message_length))}
            )
        except FormulaError as exc:
            error, computed = str(exc), 0.0
        delay = math.ceil(max(0.0, computed)) or self.merge_window_seconds
        delay += need_delay_seconds(needs)
        return DelayDecision(
            delay_seconds=min(delay, remaining, self.max_delay_seconds), formula_error=error, **decision
        )

    _need_delay_seconds = staticmethod(need_delay_seconds)
    _remaining_seconds = staticmethod(_seconds_until_end)

    def _formula(self, availability: str) -> str:
        return self._per_availability("delay_formulas", availability)

    def _public_reason(self, availability: str) -> str:
        return self._per_availability("public_reasons", availability)

    def _nonnegative_int(self, key: str) -> int:
        return self._seconds(key)

    def notification(self, decision: DelayDecision) -> str:
        template = str(self.settings.get("notification_template") or "").strip()
        if not template:
            return ""
        try:
            return template.format_map(
                {
                    "delay_seconds": decision.delay_seconds,
                    "public_reason": decision.public_reason,
                    "availability": decision.availability,
                }
            ).strip()
        except (KeyError, ValueError):
            return ""


# ---------------------------------------------------------------------------- batching


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
    """One open batch per conversation; messages that arrive before its deadline join it."""

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
        """``(batch, is_new)``; ``(None, True)`` means answer right away."""
        async with self._lock:
            open_batch = self._batches.get(umo)
            if open_batch is not None and message.received_at < open_batch.deadline:
                open_batch.messages.append(message)
                if extend_seconds > 0:
                    pushed = message.received_at + timedelta(seconds=extend_seconds)
                    if max_total_seconds > 0:
                        pushed = min(pushed, open_batch.created_at + timedelta(seconds=max_total_seconds))
                    open_batch.deadline = max(open_batch.deadline, pushed)
                return open_batch, False
            self._batches.pop(umo, None)
            if decision.delay_seconds <= 0:
                return None, True
            batch = DelayBatch(
                umo=umo,
                created_at=message.received_at,
                deadline=message.received_at + timedelta(seconds=decision.delay_seconds),
                decision=decision,
                arrival_item=arrival_item,
                messages=[message],
            )
            self._batches[umo] = batch
            return batch, True

    async def settle(self, batch: DelayBatch, now: datetime) -> tuple[QueuedMessage, ...]:
        """Wait until the deadline (or an early settle) and close the batch."""
        wait = max(0.0, (batch.deadline - now).total_seconds())
        if wait:
            try:
                await asyncio.wait_for(batch.settle_event.wait(), timeout=wait)
            except TimeoutError:
                pass
        async with self._lock:
            if self._batches.get(batch.umo) is batch:
                del self._batches[batch.umo]
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
        until = self._active_until.get(umo)
        if until is not None and now >= until:
            del self._active_until[umo]
            return False
        return until is not None

    def mark_replied(self, umo: str, now: datetime, active_seconds: int) -> None:
        if active_seconds > 0:
            self._active_until[umo] = now + timedelta(seconds=active_seconds)
        else:
            self._active_until.pop(umo, None)

    def clear(self) -> None:
        for batch in self._batches.values():
            batch.settle_event.set()
        self._batches.clear()
        self._active_until.clear()


# ---------------------------------------------------------------------------- prompt text


def _sender_label(message: QueuedMessage, group: bool) -> str:
    if not group:
        return "用户"
    label = message.sender_name or message.sender_id or "群成员"
    if message.sender_id and message.sender_id not in label:
        label += f" ({message.sender_id})"
    return label


def _message_body(message: QueuedMessage) -> str:
    text = message.prompt.strip()
    attachments = [
        f"{len(urls)} {unit}" for urls, unit in ((message.image_urls, "张图片"), (message.audio_urls, "条音频")) if urls
    ]
    if attachments:
        text = (text + " " if text else "") + "[附件：" + "、".join(attachments) + "]"
    return text or "[无文本]"


def format_queued_messages(messages: tuple[QueuedMessage, ...], *, group: bool) -> str:
    if len(messages) <= 1:
        return messages[0].prompt if messages else ""
    lines = [
        f"[{message.received_at.strftime('%H:%M:%S')}] {_sender_label(message, group)}：{_message_body(message)}"
        for message in messages
    ]
    return "\n".join(["<delayed_user_messages>", "这些消息是你忙的时候陆续收到的（按时间先后）：", *lines, "</delayed_user_messages>"])


def _item_lines(prefix: str, item: TimelineItem, *, with_slot: bool) -> list[str]:
    lines = [
        f"{prefix}活动：{item.activity}",
        f"{prefix}地点：{item.location or '未说明'}",
        f"{prefix}状态：{item.state}",
        f"{prefix}可打扰度：{item.availability}",
    ]
    return lines + [f"{prefix}段：{item.start}-{item.end}"] if with_slot else lines


def format_delay_context(batch: DelayBatch, settled_at: datetime, current_item: TimelineItem | None) -> str:
    waited = max(0, math.ceil((settled_at - batch.created_at).total_seconds()))
    lines = [
        "<reply_delay_context>",
        f"第一条消息收到于：{batch.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"计划回复延迟：{batch.decision.delay_seconds} 秒",
        f"实际等待时间：{waited} 秒",
        f"消息批次数量：{len(batch.messages)}",
    ]
    if batch.decision.active_conversation:
        lines.append("延迟判定：处于连续对话窗口，只等待合并窗口后再回应。")
    if len(batch.messages) > 1:
        lines.append("本批次包含连续发来的多条消息：请合并理解后一次性回复，不要逐条分别回答。")
    if batch.arrival_item is not None:
        lines += _item_lines("消息到达时", batch.arrival_item, with_slot=True)
    if current_item is not None:
        lines += _item_lines("结算时", current_item, with_slot=False)
    lines += [
        "回复方式：按上面的真实状态自然地回，保持人设；具体在做什么、在哪里，按你们的关系决定说多少；等了多久、为什么等，这些规则都别跟对方讲。",
        "</reply_delay_context>",
    ]
    return "\n".join(lines)
