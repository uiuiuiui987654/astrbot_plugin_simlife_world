def outfit_payload(summary: str = "清爽的日常造型", style: str = "日常休闲风") -> dict:
    return {
        "style": style,
        "summary": summary,
        "items": [
            {"category": "hairstyle", "name": "自然披肩发", "details": "梳理整齐"},
            {"category": "underwear", "name": "浅色无痕内衣", "details": "轻薄舒适"},
            {"category": "underpants", "name": "浅色无痕内裤", "details": "棉质中腰"},
            {"category": "top", "name": "白色短袖衬衫", "details": "透气棉质"},
            {"category": "bottom", "name": "深蓝百褶裙", "details": "长度及膝"},
            {"category": "shoes", "name": "黑色乐福鞋", "details": "低跟软底"},
        ],
    }


def life_timeline(
    item_id: str = "all",
    activity: str = "正常生活",
    location: str = "家",
    state: str = "available",
    availability: str = "normal",
) -> list[dict]:
    """A full day that passes the plugin's realism checks (sleep, two meals,
    an afternoon rest). The block under test keeps ``item_id``/``activity``."""

    def block(block_id, start, end, act, loc="家", st="available", av="normal"):
        return {
            "id": block_id,
            "start": start,
            "end": end,
            "activity": act,
            "location": loc,
            "state": st,
            "availability": av,
        }

    return [
        block(item_id + "-night", "00:00", "07:00", "睡觉", "卧室", "sleep", "blocked"),
        block(item_id + "-breakfast", "07:00", "07:30", "吃早饭", "厨房"),
        block(item_id, "07:30", "12:00", activity, location, state, availability),
        block(item_id + "-lunch", "12:00", "12:45", "吃午饭", "餐厅"),
        block(item_id + "-rest", "12:45", "13:30", "午睡休息", "卧室", "available", "low"),
        block(item_id + "-afternoon", "13:30", "18:00", activity, location, state, availability),
        block(item_id + "-dinner", "18:00", "19:00", "吃晚饭", "餐厅"),
        block(item_id + "-evening", "19:00", "23:00", "看书放松", "客厅"),
        block(item_id + "-sleep", "23:00", "24:00", "睡觉", "卧室", "sleep", "blocked"),
    ]


def simple_day(**overrides) -> dict:
    """Small but valid plan payload: sleep / one long day block / sleep, one window at noon."""

    def slot(slot_id, start, end, activity, state="available", availability="normal"):
        return {"id": slot_id, "start": start, "end": end, "activity": activity, "state": state, "availability": availability}

    payload = {
        "date": "2026-07-14",
        "persona_id": "alice",
        "theme": "探索日",
        "mood": "轻快",
        "outfit": outfit_payload("清爽的夏日学院风"),
        "timeline": [
            slot("sleep", "00:00", "07:00", "睡觉", "sleep", "blocked"),
            slot("day", "07:00", "23:00", "生活与工作"),
            slot("night", "23:00", "24:00", "睡觉", "sleep", "blocked"),
        ],
        "proactive_windows": [{"id": "hello", "at": "12:00", "intent": "分享午饭", "audience": "both", "source_item_id": "day"}],
        "budget_bonus": {"private": 2, "group": 1},
    }
    payload.update(overrides)
    return payload


def nap_day():
    """Morning / blocked noon nap / afternoon, with one window in the morning (as a DailyPlan)."""
    from astrbot_plugin_simlife_world.core.models import DailyPlan

    return DailyPlan.from_dict(
        {
            "date": "2026-07-14",
            "persona_id": "alice",
            "theme": "日常",
            "mood": "平静",
            "outfit": outfit_payload(),
            "timeline": [
                {"id": "morning", "start": "00:00", "end": "12:00", "activity": "上午日程"},
                {"id": "rest", "start": "12:00", "end": "14:00", "activity": "午休", "state": "sleep", "availability": "blocked"},
                {"id": "afternoon", "start": "14:00", "end": "24:00", "activity": "下午日程", "availability": "high"},
            ],
            "proactive_windows": [{"id": "w1", "at": "10:00", "intent": "上午打个招呼", "audience": "both", "source_item_id": "morning"}],
            "budget_bonus": {"private": 1, "group": 0},
        }
    )
