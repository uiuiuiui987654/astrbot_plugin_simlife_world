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
