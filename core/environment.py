"""Shared building and destination knowledge for planning and live AI context.

Only existing state is described. Selecting a preview or clicking furniture does
not silently teleport the character or alter its schedule.
"""
from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

if __package__:
    from .wardrobe import appearance_context
else:
    # The interaction regression suite loads this module directly from a file.
    import importlib.util
    _wardrobe_spec = importlib.util.spec_from_file_location("simlife_wardrobe", Path(__file__).with_name("wardrobe.py"))
    _wardrobe = importlib.util.module_from_spec(_wardrobe_spec)
    _wardrobe_spec.loader.exec_module(_wardrobe)
    appearance_context = _wardrobe.appearance_context


@lru_cache(maxsize=1)
def world() -> dict:
    try:
        return json.loads(Path(__file__).with_name("world_layout.json").read_text("utf-8"))
    except (OSError, ValueError):
        return {"rooms": [], "scenes": [], "building": {}}


@lru_cache(maxsize=1)
def furniture() -> list[dict]:
    try:
        return json.loads(Path(__file__).with_name("home_items.json").read_text("utf-8")).get("items", [])
    except (OSError, ValueError):
        return []


def find_room(location: str) -> dict | None:
    location = str(location or "")
    # Destination-prefixed locations belong to a trip; floor prefixes do not.
    if "·" in location and location.split("·", 1)[0] not in {"一楼", "二楼", "1楼", "2楼", "1F", "2F", "家", "家里"}:
        return None
    return next((room for room in world().get("rooms", []) if room["name"] in location), None)


def building_prompt() -> str:
    lines = ["【真实住宅与空间规则】", "住宅为两层庭居，层高约3米；一楼玄关通过木楼梯连接二楼楼梯厅。"]
    for floor in (1, 2):
        rooms = [r for r in world().get("rooms", []) if r.get("floor") == floor]
        lines.append(f"{floor}楼：" + "；".join(r["name"] + "（" + r["description"] + "）" for r in rooms))
    lines.append("活动须使用真实房间与设施；换楼层需要上下楼，不能在同一时刻身处两处。阳台和露台外侧均为开放栏杆，没有封闭外墙，室内入口通过推拉门连接；阳台有遮檐，露台没有屋顶。开放露台在雨雪、大风或雷雨时减少停留，烧烤改期；有遮檐的阳台可以短暂停留。室内只从窗户感知雨雪，不要描写雨落到床或书桌上。")
    return "\n".join(lines)


def environment_context(location: str, now: datetime, weather=None, activity: str = "", state: str = "", *, timeline=None, outfit=None) -> str:
    """Describe the character's actual environment and visual clothing.

    Args:
        location: Scheduled room or destination.
        now: Current local moment.
        weather: Weather mapping or plugin weather object.
        activity: Activity used to prioritize nearby furniture.
        state: Current timeline state used for sleep clothing.
        timeline: Today's schedule used to follow dressing transitions.
        outfit: Today's planned outfit; the actual clothing follows it.

    Returns:
        Concise context for ordinary, proactive and observer conversations.
    """
    hour = now.hour + now.minute / 60
    band = "夜晚" if hour < 5 or hour >= 19 else "晨光" if hour < 8 else "白天" if hour < 16.5 else "黄昏"
    condition = weather.get("condition", "") if isinstance(weather, dict) else getattr(weather, "condition", "")
    condition = str(condition or "天气未记录")
    room = find_room(location)
    lines = [f"【此刻的环境】{band}；{condition}。", appearance_context(location, activity, state, now, timeline=timeline, outfit=outfit)]
    if room:
        name, floor = room["name"], room["floor"]
        nearby = [i for i in furniture() if i.get("room") == name]
        # Mention furniture involved in the current activity first.
        nearby.sort(key=lambda i: 0 if i.get("name", "") in activity or any(str(a) in activity for a in i.get("actions", [])) else 1)
        lines.append(f"你在自家{floor}楼·{name}，层高约3米。{room['description']}。")
        lines.append("身边设施：" + "、".join(i["name"] for i in nearby[:7]) + "。")
        lines.append("家具以暖木、奶油白与浅绿为主；木纹、布艺缝线、金属把手和玻璃反光清晰可见。")
        lines.append("去另一层需经过木楼梯；一楼是起居餐厨区，二楼是休息创作区。")
        if name == "露台":
            lines.append("这里外侧是通透栏杆，没有封闭外墙，也没有屋顶遮挡，能直接感到日照、风与雨雪。")
        elif name == "阳台":
            lines.append("这里外侧是通透栏杆，没有封闭外墙；有遮檐，可以看到外景并听见户外风雨，盆栽和风铃会受风影响，雨可能飘入外缘。推拉门一侧才是室内。")
        else:
            lines.append("你在室内，窗外天气影响采光和声音；雨雪不会落到室内家具上。")
        lines.append("夜里使用室内暖灯，白天参考窗光。" if band == "夜晚" else "窗光会随晨光、白天与黄昏改变。")
    else:
        candidates = world().get("scenes", [])
        scene = next((s for s in candidates if s.get("name") and s["name"] in str(location)), None)
        if scene:
            lines.append(f"你在{location}。{scene.get('description', '')}。")
            lines.append(scene.get("weather_notes", "结合时间和天气感知环境。"))
        else:
            lines.append(f"你当前在{location or '未说明的地点'}；结合当前活动感知周围环境，不要凭空假定自己在家。")
    lines.append("自然利用这些环境细节回应，不要复述清单；界面预览不代表你实际移动了位置。")
    return "\n".join(lines)
