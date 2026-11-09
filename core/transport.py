"""Daily travel-mode options and costs.

The schedule generator is asked to put a concrete mode in every ``transit``
activity (for example ``地铁通勤`` or ``骑单车去咖啡店``).  The money layer uses
the same keywords to deduct a mode-appropriate fare.
"""

from __future__ import annotations

MODES = (
    ("步行", 0.0, "1 公里内、天气好、不赶时间"),
    ("单车", 1.5, "2-4 公里、天气好、想活动一下"),
    ("电摩", 3.0, "3-8 公里、赶时间、天气一般"),
    ("公交", 2.0, "3-8 公里、不赶时间、下雨也可以"),
    ("地铁", 4.0, "5 公里以上、赶时间、天气差时优先"),
    ("出租车", 18.0, "赶时间、天气很差、太累或带东西"),
    ("开车", 12.0, "远距离、下雨、买了很多东西"),
)

MODE_COST_KEYWORDS = (
    ("步行", 0.0),
    ("走路", 0.0),
    ("单车", 1.5),
    ("骑车", 1.5),
    ("自行车", 1.5),
    ("电摩", 3.0),
    ("电动车", 3.0),
    ("摩托", 3.0),
    ("公交", 2.0),
    ("巴士", 2.0),
    ("地铁", 4.0),
    ("出租", 18.0),
    ("打车", 18.0),
    ("网约车", 18.0),
    ("开车", 12.0),
    ("自驾", 12.0),
)


def transport_prompt() -> str:
    lines = [
        "【出行方式】",
        "每一段 transit 都要写清具体出行方式，例如「地铁通勤」「骑单车去咖啡店」"
        "「打车回家」「开车去超市」，不要只写「通勤」「路上」「出门」。",
        "可选的日常出行方式：",
    ]
    for name, cost, note in MODES:
        price = "免费" if cost <= 0 else f"约 {cost:g} 元"
        lines.append(f"- {name}：{price}，适合{note}")
    lines.append(
        "选择规则：\n"
        "- 1 公里内优先步行或单车；2-4 公里可单车、公交或电摩；"
        "5 公里以上优先地铁；赶时间或天气很差可出租车。\n"
        "- 下雨、大风、寒冷或很累时少骑单车，优先地铁、公交、开车或出租车；"
        "天气好且距离短可以骑车。\n"
        "- 开车需要目的地好停车、人也方便；不要每段都打车，按距离和预算自然选择。\n"
        "- 交通费会按方式从钱包扣除；穷的时候可以多走路、坐公交或地铁。\n"
        "- 同一天尽量别所有 transit 都用同一种方式；但天气或距离限制时可以重复。"
    )
    return "\n".join(lines)


def cost_for(activity: str, default: float = 4.0) -> float:
    text = str(activity or "")
    for keyword, cost in MODE_COST_KEYWORDS:
        if keyword in text:
            return float(cost)
    return float(default)
