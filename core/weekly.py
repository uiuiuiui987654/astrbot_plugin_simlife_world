from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from . import affection, diary, money, mood_history


def _day(value: Any) -> str:
    return str(value or "")[:10]


def build(
    data_dir: Path,
    persona: str,
    *,
    now: datetime | None = None,
    days: int = 7,
) -> dict[str, Any]:
    moment = now or datetime.now()
    span = max(1, int(days or 7))
    start_date = moment.date() - timedelta(days=span - 1)
    start = start_date.isoformat()
    end = moment.date().isoformat()
    entries = [
        entry
        for entry in diary.list_entries(data_dir, persona, limit=80)
        if start <= str(entry.get("date") or "") <= end
    ]
    snapshot = money.snapshot(data_dir, persona, limit=60)
    transactions = [
        item
        for item in snapshot.get("transactions") or []
        if start <= _day(item.get("at")) <= end
    ]
    income = round(
        sum(
            float(item.get("amount") or 0)
            for item in transactions
            if float(item.get("amount") or 0) > 0
        ),
        2,
    )
    expense = round(
        sum(
            -float(item.get("amount") or 0)
            for item in transactions
            if float(item.get("amount") or 0) < 0
        ),
        2,
    )
    work_minutes = 0
    for entry in entries:
        summary = str(entry.get("summary") or "")
        for value in re.findall(r"工作\s*(\d+)\s*分钟", summary):
            work_minutes += int(value)
    # snapshot() 只带最近 10 件物品；月报 / 年报要看完整列表
    purchases = [
        item
        for item in money.possessions(data_dir, persona)
        if start <= _day(item.get("at")) <= end
    ]
    category_labels = {
        "work": "工作",
        "master": "主人给钱",
        "ask": "要钱",
        "purchase": "购物",
        "living": "生活开销",
        "wish": "愿望",
        "spend": "消费",
    }
    income_categories: dict[str, float] = {}
    expense_categories: dict[str, float] = {}
    for item in transactions:
        kind = str(item.get("kind") or "other")
        label = category_labels.get(kind, "其他")
        amount = float(item.get("amount") or 0)
        if amount >= 0:
            income_categories[label] = round(
                income_categories.get(label, 0.0) + amount, 2
            )
        else:
            expense_categories[label] = round(
                expense_categories.get(label, 0.0) - amount, 2
            )
    relation = affection.snapshot(data_dir, persona, now=moment)
    affection_events = [
        event
        for event in relation.get("events") or []
        if start <= _day(event.get("at")) <= end
    ]
    gained = sum(int(event.get("points") or 0) for event in affection_events)
    moods = mood_history.between(data_dir, persona, start, end)

    def average(key: str) -> float:
        if not moods:
            return 0.0
        values = [
            float(item.get(key) or 0)
            for item in moods
            if isinstance(item.get(key), (int, float))
        ]
        return round(sum(values) / len(values), 1) if values else 0.0

    mood_average = average("mood")
    energy_average = average("energy")
    satiety_average = average("satiety")
    top_goods: dict[str, dict[str, Any]] = {}
    for item in purchases:
        name = str(item.get("name") or "物品")
        entry = top_goods.setdefault(
            name, {"name": name, "count": 0, "amount": 0.0}
        )
        entry["count"] += 1
        entry["amount"] = round(
            entry["amount"] + float(item.get("price") or 0), 2
        )
    top_goods_list = sorted(
        top_goods.values(), key=lambda item: (-item["count"], -item["amount"])
    )[:6]
    return {
        "persona": str(persona),
        "start": start,
        "end": end,
        "days": span,
        "balance": float(snapshot.get("balance") or 0),
        "income": income,
        "expense": expense,
        "net": round(income - expense, 2),
        "average_expense": round(expense / max(1, span), 2),
        "work_minutes": work_minutes,
        "diary_count": len(entries),
        "entries": entries[-7:],
        "purchases": purchases[-12:],
        "affection_score": int(relation.get("score") or 0),
        "affection_level": str(relation.get("level") or "陌生"),
        "affection_gained": gained,
        "moods": moods,
        "mood_average": mood_average,
        "energy_average": energy_average,
        "satiety_average": satiety_average,
        "top_goods": top_goods_list,
        "income_categories": [
            {"label": label, "amount": amount}
            for label, amount in sorted(
                income_categories.items(), key=lambda item: -item[1]
            )
        ],
        "expense_categories": [
            {"label": label, "amount": amount}
            for label, amount in sorted(
                expense_categories.items(), key=lambda item: -item[1]
            )
        ],
    }


def format_report(report: dict[str, Any]) -> str:
    def money_text(value: Any) -> str:
        return money.format_money(float(value or 0))

    days = int(report.get("days") or 7)
    title = (
        "年度总结"
        if days >= 300
        else "生活月报"
        if days >= 28
        else "生活周报"
    )
    lines = [
        f"{title} · {report.get('start')} 至 {report.get('end')}",
        (
            f"收支：收入 {money_text(report.get('income'))} 元，"
            f"支出 {money_text(report.get('expense'))} 元，"
            f"余额 {money_text(report.get('balance'))} 元。"
        ),
    ]
    income_categories = report.get("income_categories") or []
    if income_categories:
        lines.append(
            "收入分类："
            + "、".join(
                f"{item.get('label')} {money_text(item.get('amount'))}"
                for item in income_categories[:5]
            )
            + " 元。"
        )
    expense_categories = report.get("expense_categories") or []
    if expense_categories:
        lines.append(
            "支出分类："
            + "、".join(
                f"{item.get('label')} {money_text(item.get('amount'))}"
                for item in expense_categories[:5]
            )
            + " 元。"
        )
    if report.get("work_minutes"):
        lines.append(f"工作：{report.get('work_minutes')} 分钟。")
    if report.get("moods"):
        lines.append(
            f"心情：平均 {money_text(report.get('mood_average'))} / 100，"
            f"精力 {money_text(report.get('energy_average'))}，"
            f"饱腹 {money_text(report.get('satiety_average'))}，"
            f"记录 {len(report.get('moods') or [])} 天。"
        )
    lines.append(
        f"关系：{report.get('affection_level')} "
        f"{report.get('affection_score')} / 1000，"
        f"本期 +{report.get('affection_gained')}。"
    )
    purchases = report.get("purchases") or []
    if purchases:
        names = "、".join(str(item.get("name") or "") for item in purchases[:6])
        lines.append(f"新物品：{names}。")
    lines.append(f"日记：{report.get('diary_count')} 篇。")
    entries = report.get("entries") or []
    for entry in entries[-3:]:
        lines.append(f"· {entry.get('date')} {entry.get('title')}")
    return "\n".join(lines)
