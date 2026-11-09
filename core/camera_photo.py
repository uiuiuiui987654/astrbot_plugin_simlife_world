"""观察窗相机：根据用户拍到的目标 + 当前虚拟人生状态生成照片。"""

from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path
from typing import Any

import aiohttp

OMNIDRAW_PLUGIN_ID = "astrbot_plugin_omnidraw"
COMFY_PROXY_URL = "http://127.0.0.1:8189/v1/images/generations"

DEFAULT_STYLE_PROMPT = (
    "masterpiece, best quality, anime illustration, clean linework, "
    "soft colors, detailed background, no text, no watermark"
)
DEFAULT_CHARACTER = "yueyue"
DEFAULT_CHARACTER_PROMPT = (
    "1girl, solo, long silver-white hair, lavender gradient hair, purple eyes, "
    "whale-fin ear ornaments, whale tail, pale skin, detailed hair"
)

ANIME_STYLE = (
    "masterpiece, best quality, anime illustration, 1girl, solo, yueyue, "
    "long silver-white hair, lavender gradient hair, purple eyes, "
    "whale-fin ear ornaments, whale tail, pale skin, detailed hair, "
    "clean linework, soft colors, detailed background, "
    "no text, no watermark"
)

DEFAULT_NEGATIVE_PROMPT = (
    "lowres, {bad}, error, fewer, extra, missing, worst quality, "
    "jpeg artifacts, bad quality, watermark, unfinished, displeasing, "
    "chromatic aberration, signature, extra digits, artistic error, "
    "username, scan, [abstract]"
)


def camera_settings(config: Any) -> dict[str, Any]:
    if not isinstance(config, dict):
        return {}
    section = config.get("camera_settings")
    return section if isinstance(section, dict) else {}


def compose_style_prompt(settings: dict[str, Any]) -> str:
    """Build the drawing-model prompt from the three user-facing pieces."""
    style = str(settings.get("style_prompt") or DEFAULT_STYLE_PROMPT).strip()
    character = str(settings.get("character") or DEFAULT_CHARACTER).strip()
    character_prompt = str(
        settings.get("character_prompt") or DEFAULT_CHARACTER_PROMPT
    ).strip()
    return ", ".join(
        part for part in (style, character, character_prompt) if part
    )

ROOM_EN = {
    "卧室": "bedroom",
    "主卧": "bedroom",
    "次卧": "bedroom",
    "厨房": "kitchen",
    "客厅": "living room",
    "书房": "study",
    "餐厅": "dining room",
    "浴室": "bathroom",
    "卫生间": "bathroom",
    "露台": "terrace",
    "阳台": "balcony",
    "健身房": "home gym",
    "健身室": "home gym",
    "画室": "art studio",
    "衣帽间": "walk-in closet",
    "影音室": "home theater",
    "楼梯厅": "stair hall",
    "玄关": "entryway",
    "洗衣房": "laundry room",
    "走廊": "hallway",
}

ROOM_ENV_EN = {
    "bedroom": "bed with a rumpled duvet, wooden nightstand, warm bedside lamp, bookshelf",
    "kitchen": "kitchen table, wooden cabinets, warm ceiling lamp",
    "living room": "sofa, coffee table, warm floor lamp",
    "study": "desk, bookshelf, warm desk lamp",
    "dining room": "dining table, wooden chairs, warm pendant lamp",
    "bathroom": "clean bathroom, soft warm light",
    "terrace": "metal railing, potted plants, open sky",
    "balcony": "metal railing, potted plants, open sky",
    "home gym": "yoga mat, fitness mirror, dumbbells, treadmill, gym equipment",
    "art studio": "easel, paint cart, canvases, wooden floor",
    "walk-in closet": "wardrobe rail, shelves, full-length mirror",
    "home theater": "screen, sofa, popcorn machine",
    "stair hall": "staircase, handrail, entry shelf",
    "entryway": "shoe cabinet, key tray, front door",
}

OUTDOOR_SCENES = {
    "cafe": ("cozy cafe", "wooden tables, coffee cups, warm pendant lights, window seats"),
    "park": ("green park", "trees, walking path, benches, sunlight through leaves"),
    "bookstore": ("bookstore", "tall bookshelves, warm reading lamps, quiet aisles"),
    "museum": ("art museum", "white gallery walls, framed paintings, polished floor"),
    "cinema": ("cinema", "movie posters, marquee lights, popcorn stand"),
    "beach": ("seaside beach", "sand, ocean waves, blue sky, distant horizon"),
    "mall": ("shopping mall", "glass storefronts, escalators, bright atrium"),
    "office": ("modern office", "desks, monitors, glass windows, city view"),
    "street": ("old street", "stone pavement, shop signs, potted plants"),
    "food": ("canteen", "serving counter, tables, trays of food"),
    "supermarket": ("supermarket", "product aisles, shopping cart, bright ceiling lights"),
    "grocery": ("small grocery store", "shelves of snacks and drinks, wooden counter"),
    "market": ("bustling food market", "market stalls, produce baskets, warm daylight"),
    "nightmarket": ("night market", "glowing lanterns, food stalls, crowded street"),
    "station": ("train station", "platform, railway tracks, departure board"),
    "airport": ("airport terminal", "check-in counters, large windows, departure boards"),
    "hotel": ("hotel lobby", "reception desk, lounge sofas, warm lamps"),
    "travel": ("unfamiliar city", "foreign street, signs, distant buildings"),
    "temple": ("shrine", "torii gate, stone steps, lanterns, old trees"),
    "onsen": ("hot spring ryokan", "steaming bath, wooden deck, mountains"),
    "harbor": ("harbor", "boats, sea wind, railings, distant water"),
    "mountain": ("mountain trail", "trees, rocky path, misty peaks"),
    "izakaya": ("izakaya", "counter seats, warm lanterns, bottles on shelves"),
    "transit": ("on the way", "moving train or bus interior, window view of the city"),
    "botanical": ("botanical garden", "greenhouse, tropical plants, glass roof"),
    "riverside": ("riverside walkway", "river, railing, trees, footpath"),
    "lakeside": ("lakeside", "calm lake, distant mountains, wooden pier"),
    "campsite": ("campsite", "tent, campfire, pine trees, open sky"),
    "amusement": ("amusement park", "ferris wheel, colorful rides, park path"),
    "flower_shop": ("flower shop", "bouquets, buckets of flowers, wooden shelves"),
    "bakery": ("bakery", "bread shelves, warm oven light, pastry counter"),
    "library": ("library", "tall bookshelves, reading tables, green desk lamps"),
    "generic": ("city street", "shops, street lamps, trees, passing people"),
}

ACTIVITY_EN = (
    ("泡澡", "soaking in a warm bath"),
    ("泡浴", "soaking in a warm bath"),
    ("淋浴", "taking a shower"),
    ("洗澡", "taking a shower"),
    ("沐浴", "taking a bath"),
    ("教程", "sitting at the desk studying a tutorial and organizing notes"),
    ("笔记", "sitting at the desk studying a tutorial and organizing notes"),
    ("复习", "reviewing notes at the desk"),
    ("学习", "studying at the desk"),
    ("平板支撑", "doing a plank"),
    ("瑜伽", "doing yoga"),
    ("拉伸", "stretching"),
    ("看书", "reading a book"),
    ("阅读", "reading a book"),
    ("读书", "reading a book"),
    ("摘抄", "writing notes in a notebook"),
    ("写字", "writing"),
    ("做饭", "cooking"),
    ("吃饭", "eating a meal"),
    ("喝咖啡", "drinking coffee"),
    ("喝茶", "drinking tea"),
    ("午睡", "taking a nap"),
    ("小睡", "taking a nap"),
    ("打盹", "dozing off"),
    ("睡觉", "sleeping"),
    ("休息", "resting"),
    ("听音乐", "listening to music"),
    ("刷手机", "using a smartphone"),
    ("玩手机", "using a smartphone"),
    ("护肤", "doing skincare"),
    ("梳头", "brushing her hair"),
    ("换衣服", "changing clothes"),
    ("发呆", "spacing out"),
    ("撑伞", "walking home in the rain, holding an umbrella"),
    ("步行", "walking along the street"),
    ("走回家", "walking home along the street"),
    ("路上", "walking along the street"),
    ("散步", "taking a walk"),
)

OUTFIT_EN = (
    ("睡衣", "white and lavender whale-print pajama set with collared top and long pants, whale-shaped slippers"),
    ("睡裙", "white and lavender sleep dress, barefoot"),
    ("女仆", "white and lavender frilly maid dress"),
    ("卫衣", "oversized hoodie and casual pants"),
    ("毛衣", "cozy knit sweater and skirt"),
    ("校服", "school uniform"),
    ("和服", "kimono"),
    ("汉服", "hanfu"),
    ("旗袍", "qipao"),
    ("风衣", "light grey thin trench coat"),
    ("薄外套", "lightweight cropped color-block jacket"),
    ("外套", "light outerwear jacket"),
    ("直筒休闲裤", "straight-leg long casual pants"),
    ("休闲裤", "long casual pants"),
    ("直筒裤", "straight-leg trousers"),
    ("长裤", "long pants"),
    ("牛仔裤", "jeans"),
    ("短裤", "casual shorts"),
    ("针织", "cozy knit top"),
    ("短袖", "short-sleeve top"),
    ("拼色", "color-block"),
    ("百褶", "pleated skirt"),
    ("半身裙", "pleated midi skirt"),
    ("短袜", "white ankle socks"),
    ("袜", "white ankle socks"),
    ("单鞋", "pale purple low-heel shoes"),
    ("运动鞋", "white sneakers"),
    ("鞋", "pale purple low-heel shoes"),
    ("项链", "thin silver necklace"),
    ("发夹", "lavender hair clip"),
    ("斜挎包", "small crossbody bag"),
    ("包", "small white handbag"),
    ("裙", "casual dress"),
    ("衬衫", "casual shirt"),
    ("运动服", "sportswear"),
)


def _english_activity(activity: str) -> str:
    text = str(activity or "")
    for key, value in ACTIVITY_EN:
        if key in text:
            return value
    return "relaxing at home"


def _is_workout(state: dict[str, Any]) -> bool:
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    activity = str(now.get("activity") or "")
    return any(
        word in activity
        for word in ("拉伸", "伸展", "拉筋", "健身", "运动", "瑜伽", "跑步", "锻炼")
    )


def _is_bathing(state: dict[str, Any]) -> bool:
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    raw = " ".join(
        [
            str(now.get("activity") or ""),
            str(now.get("state") or ""),
        ]
    )
    return any(
        word in raw
        for word in ("泡澡", "泡浴", "洗澡", "淋浴", "沐浴", "浴缸", "浴盐")
    )


def _english_outfit(
    state: dict[str, Any], *, for_sleep: bool = False, at_home: bool = False
) -> str:
    appearance = state.get("appearance")
    if isinstance(appearance, dict):
        text = str(
            appearance.get("description") or appearance.get("name") or ""
        )
        structured = state.get("outfit")
        if isinstance(structured, dict):
            parts = []
            for item in structured.get("items") or []:
                if not isinstance(item, dict):
                    continue
                parts.append(
                    " ".join(
                        str(item.get(key) or "")
                        for key in ("name", "details")
                    ).strip()
                )
            text = (text + " " + " ".join(parts)).strip()
        if for_sleep:
            for key, value in OUTFIT_EN:
                if key in ("睡衣", "睡裙") and key in text:
                    return value
            return (
                "soft white and lavender pajama set, barefoot, no shoes, "
                "cozy sleepwear"
            )
        if appearance.get("is_sleepwear"):
            return OUTFIT_EN[0][1]
        if _is_bathing(state):
            now = state.get("now") if isinstance(state.get("now"), dict) else {}
            activity = str(now.get("activity") or "")
            if any(word in activity for word in ("淋浴", "洗澡", "冲")):
                return (
                    "a soft white bath towel wrapped around her, wet hair, "
                    "barefoot, no outdoor clothes or shoes"
                )
            return (
                "a soft white towel wrapped around her hair, bare shoulders above "
                "the bath water, barefoot, no outdoor clothes or shoes"
            )
        if _is_workout(state):
            return (
                "fitted white and lavender athletic top, dark grey leggings, "
                "barefoot or clean indoor training shoes, hair tied back, "
                "light workout outfit"
            )
        matches: list[str] = []
        for key, value in OUTFIT_EN:
            if key not in text or value in matches:
                continue
            if at_home and key in ("鞋", "单鞋", "运动鞋"):
                continue
            if key == "外套" and "薄外套" in text:
                continue
            if key in ("休闲裤", "直筒裤", "长裤") and "直筒休闲裤" in text:
                continue
            if key == "袜" and "短袜" in text:
                continue
            if key == "鞋" and "运动鞋" in text:
                continue
            if key == "包" and "斜挎包" in text:
                continue
            if key == "半身裙" and "百褶" in text:
                continue
            if key == "裙" and any(
                word in text for word in ("女仆", "百褶", "半身裙")
            ):
                continue
            matches.append(value)
        if matches:
            if "针织" in text and "短袖" in text:
                matches = [
                    item
                    for item in matches
                    if item not in ("cozy knit top", "short-sleeve top")
                ]
                matches.insert(
                    0,
                    "white short-sleeve knit top"
                    if "白色" in text
                    else "short-sleeve knit top",
                )
            if "浅紫" in text:
                matches = [
                    item.replace(
                        "straight-leg long casual pants",
                        "light purple straight-leg long casual pants",
                    )
                    for item in matches
                ]
            outfit = ", ".join(matches)
            if at_home:
                outfit += (
                    ", barefoot or wearing soft indoor slippers, no outdoor shoes"
                )
            if any(word in outfit for word in ("pants", "trousers")):
                outfit += ", no skirt, no dress, no waist belt"
            return outfit
    return "casual home outfit"


def _at_home(state: dict[str, Any]) -> bool:
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    if str(now.get("kind") or "").strip() == "home":
        return True
    return bool(str(now.get("room") or "").strip())


def _is_napping(state: dict[str, Any]) -> bool:
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    activity = str(now.get("activity") or "")
    return any(word in activity for word in ("午睡", "午休", "小睡", "小憩", "打盹"))


def _is_sleeping(state: dict[str, Any]) -> bool:
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    raw = " ".join(
        [
            str(now.get("activity") or ""),
            str(now.get("state") or ""),
        ]
    )
    return (
        "sleep" in raw.lower()
        or "睡觉" in raw
        or "睡眠" in raw
        or "入睡" in raw
        or "午睡" in raw
        or "小睡" in raw
        or "打盹" in raw
        or "赖床" in raw
    )


def _english_room(state: dict[str, Any]) -> str:
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    for text in (now.get("room"), now.get("location")):
        cleaned = _clean(text, 30)
        for key, value in ROOM_EN.items():
            if key in cleaned:
                return value
    return "home room"


def _outdoor_context(state: dict[str, Any]) -> tuple[str, str]:
    """Return an English subject and environment for the current outside scene."""
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    scene = str(now.get("scene") or "").strip()
    activity = str(now.get("activity") or "")
    location = str(now.get("location") or "")
    raw = f"{activity} {location}"
    walking = any(
        word in raw for word in ("步行", "走路", "散步", "撑伞", "走回家", "回家路上", "路上")
    )
    if walking:
        rainy = any(
            word in raw for word in ("雨", "撑伞", "打伞", "伞")
        ) or "雨" in str(
            (state.get("weather") or {}).get("description")
            if isinstance(state.get("weather"), dict)
            else ""
        )
        if rainy:
            return (
                "rainy city street",
                "wet pavement reflecting street lamps, light rain, raindrops, "
                "trees along the sidewalk, a light purple folding umbrella, "
                "outdoors on the street",
            )
        if scene == "transit" or "路上" in location:
            return (
                "city street",
                "sidewalk, street lamps, trees, shops, outdoors on the street",
            )
    if scene == "transit":
        return (
            "on the way",
            "moving train or bus interior, window view of the city",
        )
    return OUTDOOR_SCENES.get(
        scene,
        ("city street", "shops, street lamps, trees, passing people"),
    )


def _english_time_light(state: dict[str, Any]) -> str:
    now_time = _clean(state.get("now_time"), 10)
    hour = 20
    if ":" in now_time:
        try:
            hour = int(now_time.split(":", 1)[0])
        except ValueError:
            hour = 20
    if 5 <= hour < 8:
        return "early morning, soft morning light"
    if 8 <= hour < 12:
        return "morning, natural daylight"
    if 12 <= hour < 17:
        return "afternoon, natural daylight"
    if 17 <= hour < 19:
        return "evening, warm golden light"
    return "night, warm indoor lighting, window with night sky"


def _time_negative_prompt(
    state: dict[str, Any], base: str = DEFAULT_NEGATIVE_PROMPT
) -> str:
    """Keep a daytime scene from drifting into a night scene."""
    base = str(base or DEFAULT_NEGATIVE_PROMPT).strip()
    now_time = str(state.get("now_time") or "")
    hour = 20
    if ":" in now_time:
        try:
            hour = int(now_time.split(":", 1)[0])
        except ValueError:
            hour = 20
    if 6 <= hour < 18:
        return (
            base
            + ", night, night sky, city night lights, dark room, "
            "indoor nighttime lighting, moon"
        )
    if hour > 5 and hour < 6:
        return base + ", bright noon sunlight, harsh midday sun"
    return base


def _english_weather(state: dict[str, Any]) -> str:
    weather = state.get("weather") if isinstance(state.get("weather"), dict) else {}
    text = str(weather.get("description") or weather.get("condition") or "")
    now_time = _clean(state.get("now_time"), 10)
    hour = 20
    if ":" in now_time:
        try:
            hour = int(now_time.split(":", 1)[0])
        except ValueError:
            hour = 20
    if "微风" in text:
        return "gentle breeze"
    if "晴朗" in text or "晴" in text:
        return "clear night sky" if hour >= 19 or hour < 5 else "clear sky"
    if "多云" in text:
        return "partly cloudy"
    if "阴" in text:
        return "overcast"
    if "雨" in text:
        return "light rain"
    return "calm weather"


def _english_pose(state: dict[str, Any], activity_en: str, room: str) -> str:
    """让构图服从当前活动，避免睡觉时还坐着。"""
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    raw = " ".join(
        [
            str(now.get("activity") or ""),
            str(now.get("state") or ""),
            str(activity_en or ""),
        ]
    )
    # A desk/table nap is a leaning pose, not a full nap on the sofa.
    if any(
        word in raw
        for word in ("趴在", "趴桌", "趴着", "趴在桌上", "趴在书桌", "打盹")
    ) and ("桌" in raw or room in ("study", "art studio", "dining room")):
        if room in ("study", "art studio") or any(
            word in raw for word in ("书桌", "桌面", "桌子")
        ):
            return (
                "leaning forward with her head resting on her folded arms on the desk, "
                "eyes half closed, relaxed sleepy posture"
            )
        return (
            "leaning forward with her head resting on her folded arms on the table, "
            "eyes half closed, relaxed sleepy posture"
        )
    if _is_sleeping(state):
        if room == "bedroom":
            return (
                "lying in bed on her side, curled up, a thick duvet pulled up to her chin "
                "completely covering her body, only her head on the pillow and one hand visible, "
                "body and legs hidden under the blanket, eyes peacefully closed, asleep, "
                "no shoes or slippers on the bed"
            )
        return (
            "lying on the sofa on her side, head resting on a cushion, curled up, "
            "eyes peacefully closed, asleep, a soft blanket over her body, "
            "relaxed napping pose"
        )
    if _is_bathing(state):
        if any(word in raw for word in ("淋浴", "洗澡", "冲")):
            return (
                "standing under a warm shower, water streaming over her shoulders, "
                "wet hair, relaxed posture, steam around her"
            )
        return (
            "soaking in a bathtub filled with warm water, shoulders above the water, "
            "head tilted back against the tub, eyes half closed, relaxed posture, "
            "steam and a few bubbles around her"
        )
    if not _at_home(state):
        scene = str(now.get("scene") or "").strip()
        if any(word in raw for word in ("散步", "走", "逛", "步行", "walk")):
            if any(word in raw for word in ("撑伞", "打伞", "雨伞")) or "雨" in raw:
                return (
                    "walking on a rainy street while holding a light purple "
                    "folding umbrella, relaxed stride, raindrops around her, "
                    "outdoors, no vehicle interior"
                )
            if any(word in raw for word in ("逛店", "逛商场", "购物", "逛街")):
                return (
                    "walking while carrying a small shopping bag, relaxed stride, "
                    "looking around the shops"
                )
            return "walking naturally along the path, relaxed stride"
        if any(word in raw for word in ("跑", "晨跑", "慢跑", "run", "jog")):
            return "jogging along the path, natural running posture"
        if any(word in raw for word in ("骑", "单车", "自行车", "cycle")):
            return "riding a bicycle along the path, relaxed posture"
        if any(word in raw for word in ("游泳", "泳池", "海里", "swim")):
            return "swimming in the water, shoulders above the surface, natural motion"
        if any(word in raw for word in ("野餐", "草地", "picnic")):
            return "sitting on a picnic blanket, relaxed posture, one hand resting on the blanket"
        if any(word in raw for word in ("钓鱼", "垂钓", "fishing")):
            return "sitting by the water fishing, relaxed posture, holding a fishing rod"
        if any(word in raw for word in ("看书", "阅读", "读书", "reading")):
            if scene in ("cafe", "bookstore", "library"):
                return "sitting at a table reading a book, relaxed posture"
            return "sitting on a bench reading a book, relaxed posture"
        if any(word in raw for word in ("吃饭", "用餐", "吃", "eating")):
            return "sitting at a table eating, casual posture"
        if any(word in raw for word in ("喝", "咖啡", "茶", "drink")):
            if scene in ("cafe", "bakery", "restaurant"):
                return "sitting at a cafe table with a warm drink, relaxed posture"
            return "holding a warm drink, relaxed posture"
        if any(word in raw for word in ("拍照", "相机", "photo", "camera")):
            return "holding a camera, looking through the viewfinder"
        if any(word in raw for word in ("购物", "买东西", "逛街", "购物袋", "shopping")):
            if scene in ("supermarket", "grocery", "market", "nightmarket", "mall"):
                return (
                    "walking through the shop with a shopping basket, relaxed posture, "
                    "looking at the shelves"
                )
            return "walking with a small shopping bag, relaxed posture"
        if any(word in raw for word in ("坐着", "坐下", "休息", "发呆", "晒太阳", "sit")):
            if scene in ("beach", "harbor", "lakeside"):
                return "sitting by the water, relaxed posture, looking at the view"
            return "sitting on a bench, relaxed posture"
        if any(word in raw for word in ("看电影", "演出", "剧场", "cinema")):
            return "sitting in a theater seat, relaxed posture"
        if any(word in raw for word in ("温泉", "泡汤", "onsen")):
            return "soaking in a warm outdoor hot spring, shoulders above the water, relaxed posture"
        if any(word in raw for word in ("坐车", "地铁", "公交", "火车", "高铁", "transit")):
            return "sitting by the window, relaxed posture, looking out at the view"
        if any(word in raw for word in ("聊天", "约会", "聊天", "chat")):
            return "sitting together and chatting, relaxed posture"
        if any(word in raw for word in ("等", "排队", "wait")):
            return "standing and waiting patiently, hands in pockets"
        if any(word in raw for word in ("看展", "博物馆", "美术馆", "museum")):
            return "standing in front of an exhibit, looking at the artwork, relaxed posture"
        if any(word in raw for word in ("逛花店", "花店", "花", "flower")):
            return "standing at a flower shop, looking at the bouquets, relaxed posture"
        # Scene-aware fallback: never default every outdoor photo to standing.
        if scene in ("cafe", "bakery", "food", "izakaya"):
            return "sitting at a table, relaxed posture"
        if scene in ("bookstore", "library"):
            return "sitting at a reading table with a book, relaxed posture"
        if scene in ("park", "botanical", "riverside", "lakeside"):
            return "sitting on a bench, relaxed posture, enjoying the view"
        if scene == "beach":
            return "walking barefoot along the beach, relaxed stride"
        if scene == "harbor":
            return "standing by the harbor railing, looking at the water, relaxed posture"
        if scene == "museum":
            return "walking slowly through the gallery, looking at the exhibits"
        if scene == "cinema":
            return "sitting in a theater seat, relaxed posture"
        if scene in ("mall", "supermarket", "grocery", "market", "nightmarket"):
            return "walking through the shops, relaxed posture"
        if scene in ("office",):
            return "sitting at a desk, relaxed posture"
        if scene in ("station", "airport", "transit"):
            return "sitting with luggage, relaxed posture"
        if scene == "temple":
            return "standing quietly at the shrine, relaxed posture"
        if scene == "onsen":
            return "soaking in a warm hot spring, shoulders above the water, relaxed posture"
        if scene == "campsite":
            return "sitting by the campfire, relaxed posture"
        if scene in ("amusement", "travel", "street", "generic"):
            return "walking along the street, relaxed posture"
        if scene == "flower_shop":
            return "standing at the flower shop, looking at the bouquets, relaxed posture"
        return "walking slowly and enjoying the view, relaxed posture"
    # At home, pick a posture from the current activity and the furniture close to her.
    if any(word in raw for word in ("摇椅", "摇摇椅", "秋千", "风铃", "毛毯", "晒太阳")):
        if room in ("balcony", "terrace"):
            return (
                "sitting in a rocking chair on the balcony, wrapped in a soft blanket, "
                "relaxed posture, soft daylight on her, a wind chime hanging nearby, "
                "open sky beyond the railing"
            )
        return (
            "sitting in a comfortable chair, wrapped in a soft blanket, relaxed posture, "
            "soft daylight on her, a wind chime nearby"
        )
    if any(word in raw for word in ("趴在", "趴着", "趴桌", "打盹", "眯一会儿")):
        if room in ("study", "art studio") or any(
            word in raw for word in ("书桌", "桌面", "桌子")
        ):
            return (
                "leaning forward with her head resting on her folded arms on the desk, "
                "eyes half closed, relaxed sleepy posture"
            )
        return (
            "leaning forward with her head resting on her folded arms on the table, "
            "eyes half closed, relaxed sleepy posture"
        )
    if any(word in raw for word in ("看书", "阅读", "读书", "摘抄", "翻书")):
        seat = {
            "bedroom": "on the edge of the bed",
            "study": "at the desk",
            "art studio": "at the drafting table",
            "living room": "on the sofa",
            "dining room": "at the dining table",
            "balcony": "on the balcony chair",
            "terrace": "on the terrace chair",
        }.get(room, "on the sofa")
        return f"sitting {seat} reading a book, relaxed posture"
    if any(word in raw for word in ("吃饭", "用餐", "吃", "喝", "茶", "咖啡", "早餐", "午餐", "晚餐")):
        if any(word in raw for word in ("做饭", "烹饪", "下厨", "烘焙")):
            return "standing in the kitchen cooking, relaxed posture"
        return "sitting at the table eating and drinking, casual posture"
    if any(word in raw for word in ("看电视", "电影", "看剧", "追剧", "综艺", "纪录片", "视频")):
        return "sitting on the sofa watching the screen, relaxed posture"
    if any(word in raw for word in ("游戏", "桌游", "拼图")):
        return "sitting at the table playing a game, leaning forward slightly"
    if any(word in raw for word in ("聊天", "说话", "聊天", "聊两句")):
        return "sitting comfortably while chatting, relaxed posture"
    if any(word in raw for word in ("护肤", "化妆", "面膜", "梳妆")):
        return "sitting in front of the vanity mirror, relaxed posture"
    if room == "bedroom" and any(
        word in raw for word in ("看书", "阅读", "读书", "摘抄", "翻书")
    ):
        return "sitting on the edge of the bed reading a book, relaxed posture"
    if room == "study" and any(
        word in raw for word in ("教程", "笔记", "学习", "复习")
    ):
        return (
            "sitting at the desk in front of the monitor, studying a tutorial "
            "and organizing notes, relaxed upright posture"
        )
    if any(word in raw for word in ("平板支撑", "plank")):
        return "holding a plank on a yoga mat"
    if any(word in raw for word in ("拉伸", "伸展", "拉筋", "stretching")):
        return (
            "stretching on a yoga mat beside the fitness mirror, one leg extended, "
            "relaxed workout posture, comfortable athletic outfit"
        )
    if any(word in raw for word in ("瑜伽", "yoga")):
        return "doing yoga on a yoga mat"
    if any(word in raw for word in ("做饭", "cooking")):
        return "standing in the kitchen cooking"
    if any(word in raw for word in ("吃饭", "用餐", "eating")):
        return "sitting at the dining table eating"
    if any(word in raw for word in ("工作", "办公", "写代码", "working")):
        return "sitting at the desk working"
    if any(word in raw for word in ("听音乐", "耳机", "music")):
        return "relaxing with headphones"
    if any(word in raw for word in ("刷手机", "玩手机", "手机")):
        if room == "bedroom":
            return "lying on the bed using a smartphone"
        if room == "study":
            return "sitting at the desk using a smartphone"
        return "sitting on the sofa using a smartphone"
    if any(word in raw for word in ("绘画", "画画", "画水彩", "画插画", "速写")):
        return "sitting at the drafting table drawing, leaning slightly forward"
    if any(word in raw for word in ("发呆", "休息", "放松", "放空")):
        if room == "bedroom":
            return "lying on the bed relaxing"
        if room == "study":
            return "leaning back in the desk chair, resting, relaxed posture"
        return "sitting on the sofa relaxing"
    if any(word in raw for word in ("躺", "蜷")):
        if room == "bedroom":
            return "lying on the bed, relaxed and awake, eyes open"
        return "lying on the sofa, relaxed and awake, eyes open"
    if room == "bedroom":
        return "sitting on the edge of the bed, relaxed posture"
    if room in ("study", "art studio"):
        return "sitting at the desk, relaxed posture"
    if room == "living room":
        return "sitting on the sofa, relaxed posture"
    if room == "dining room":
        return "sitting at the dining table, relaxed posture"
    if room == "kitchen":
        return "standing in the kitchen, relaxed posture"
    if room == "home gym":
        return "sitting on the yoga mat, relaxed posture"
    return "sitting at home, relaxed posture"


def _snapshot_is_home(location: str) -> bool:
    text = str(location or "")
    return any(
        word in text
        for word in (
            "卧室",
            "主卧",
            "次卧",
            "浴室",
            "卫生间",
            "厨房",
            "客厅",
            "书房",
            "餐厅",
            "健身室",
            "健身房",
            "阳台",
            "玄关",
            "衣帽间",
            "画室",
            "影音室",
            "露台",
            "楼梯厅",
        )
    )


def _scene_from_snapshot_location(location: str) -> str:
    text = str(location or "")
    groups = (
        ("cafe", ("咖啡馆", "咖啡店", "咖啡厅")),
        ("park", ("公园", "植物园")),
        ("library", ("图书馆",)),
        ("bookstore", ("书店",)),
        ("mall", ("商场", "购物中心")),
        ("supermarket", ("超市",)),
        ("market", ("市集", "夜市", "市场")),
        ("beach", ("海边", "沙滩", "海滩")),
        ("harbor", ("港口", "码头")),
        ("museum", ("博物馆", "美术馆")),
        ("cinema", ("电影院", "影院")),
        ("station", ("车站", "火车站", "地铁站", "机场")),
        ("office", ("公司", "办公室")),
        ("temple", ("神社", "寺庙")),
        ("onsen", ("温泉",)),
        ("campsite", ("营地", "露营地")),
        ("amusement", ("游乐园",)),
        ("riverside", ("河边", "河畔")),
        ("lakeside", ("湖边", "湖畔")),
        ("bakery", ("面包店", "烘焙")),
        ("flower_shop", ("花店",)),
        ("transit", ("地铁", "公交", "高铁", "列车")),
    )
    for scene, words in groups:
        if any(word in text for word in words):
            return scene
    return "generic"


def pose_hint_for_snapshot(snapshot: dict[str, Any]) -> str:
    """Return an English pose hint for a virtual-life snapshot.

    Used by the OmniDraw selfie tool so chat selfies follow the same
    sit/lie/lean rules as the in-app camera.
    """
    if not isinstance(snapshot, dict) or snapshot.get("ok") is not True:
        return ""
    current = snapshot.get("current")
    if not isinstance(current, dict):
        return ""
    activity = str(current.get("activity") or "").strip()
    location = str(current.get("location") or "").strip()
    state_name = str(current.get("state") or "").strip()
    if not activity and not location:
        return ""
    kind = "home" if _snapshot_is_home(location) else "outside"
    state = {
        "now": {
            "activity": activity,
            "state": state_name,
            "kind": kind,
            "room": "" if kind == "outside" else location,
            "location": location,
            "scene": "" if kind == "home" else _scene_from_snapshot_location(location),
        }
    }
    return _english_pose(
        state,
        _english_activity(activity),
        _english_room(state),
    )


def build_anime_prompt(
    state: dict[str, Any], *, style_prompt: str = "", extra_prompt: str = ""
) -> str:
    """为有月月的照片构造 Illustrious 能理解的英文二次元 prompt。"""
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    activity = _english_activity(now.get("activity"))
    at_home = _at_home(state)
    if at_home:
        place = _english_room(state)
        furniture = ROOM_ENV_EN.get(place, "cozy home interior")
        if _is_bathing(state):
            furniture = (
                "bathtub filled with warm water and bath salts, soft steam, "
                "folded towels, a waterproof speaker nearby"
            )
    else:
        place, furniture = _outdoor_context(state)
    sleeping = _is_sleeping(state)
    appearance = state.get("appearance")
    appearance = appearance if isinstance(appearance, dict) else {}
    for_sleep = bool(appearance.get("is_sleepwear")) or (
        sleeping and not _is_napping(state)
    )
    outfit = _english_outfit(
        state,
        for_sleep=for_sleep,
        at_home=at_home,
    )
    time_light = _english_time_light(state)
    weather = _english_weather(state)
    placement = _english_pose(state, activity, place)
    background_style = "detailed interior" if at_home else "detailed scenery"
    outfit_phrase = outfit if _is_bathing(state) else f"wearing {outfit}"
    style = style_prompt or ANIME_STYLE
    extra = str(extra_prompt or "").strip().strip(",")
    extra_phrase = f"{extra}, " if extra else ""
    return (
        f"{style}, {extra_phrase}{time_light}, ({placement}:1.2), {outfit_phrase}, {activity}, "
        f"{place}, {furniture}, {weather}, "
        f"lived-in and cozy, {background_style}, casual anime snapshot, "
        "correct anatomy, no extra limbs"
    )

TARGET_CHARACTER = "character"
TARGET_ITEM = "item"
TARGET_ROOM = "room"


def _clean(value: Any, limit: int = 200) -> str:
    return str(value or "").strip()[:limit]


def _appearance_text(state: dict[str, Any]) -> str:
    appearance = state.get("appearance")
    if not isinstance(appearance, dict):
        return ""
    return _clean(
        appearance.get("description") or appearance.get("day_outfit"),
        260,
    )


def persona_visual_from_prompt(prompt: str) -> str:
    """从人格系统提示里抽取“银白长发、紫色眼睛”这类可画出来的外貌关键词。"""
    text = str(prompt or "")
    match = re.search(r"固定立绘是[^：:\n]{0,20}[：:]([^。；\n]+)", text)
    if not match:
        return ""
    parts = [
        part.strip(" ，,。")
        for part in re.split(r"[、,，]", match.group(1))
        if part.strip()
    ]
    visual = [
        part
        for part in parts
        if any(word in part for word in ("发", "眼睛", "瞳"))
        and not any(word in part for word in ("耳鳍", "尾巴", "女仆装", "衣服"))
    ]
    return "、".join(visual[:2])


def _time_period(hour: int) -> str:
    if 5 <= hour < 8:
        return "清晨"
    if 8 <= hour < 11:
        return "上午"
    if 11 <= hour < 13:
        return "中午"
    if 13 <= hour < 17:
        return "下午"
    if 17 <= hour < 19:
        return "傍晚"
    if 19 <= hour < 23:
        return "夜晚"
    return "深夜"


OUTDOOR_MARKERS = (
    "露台",
    "阳台",
    "庭院",
    "院子",
    "花园",
    "屋顶",
    "天台",
    "户外",
    "街",
    "公园",
    "小区",
    "门口",
    "海边",
    "山",
)


def _is_outdoor(
    kind: str, location: str, room: str, floor: int | None = None
) -> bool:
    if kind and kind != "home":
        return True
    text = f"{location} {room}"
    return any(marker in text for marker in OUTDOOR_MARKERS)


def _furniture_environment(
    home_items: list[dict[str, Any]] | None,
    *,
    room: str = "",
    floor: int | None = None,
) -> str:
    items = [item for item in (home_items or []) if isinstance(item, dict)]
    room_text = str(room or "").strip()
    if room_text:
        selected = [
            item
            for item in items
            if str(item.get("room") or "").strip() == room_text
        ]
    elif floor is not None:
        selected = [
            item for item in items if int(item.get("floor") or 0) == floor
        ]
    else:
        selected = []
    if not selected:
        return ""
    names: list[str] = []
    for item in selected:
        name = _clean(item.get("name"), 20)
        if name and name not in names:
            names.append(name)
        if len(names) >= 8:
            break
    if not names:
        return ""
    detail = "、".join(names)
    descriptions = [
        _clean(item.get("description"), 40)
        for item in selected[:2]
        if _clean(item.get("description"), 40)
    ]
    if descriptions:
        detail += "（" + "；".join(descriptions) + "）"
    return "房间里能看到" + detail + "。"


def _item_description_for_weather(description: Any, weather_text: str) -> str:
    """物品描述里可能带着旧天气（如坐垫被雨淋湿），与当前天气冲突时弱化。"""
    text = _clean(description, 120)
    if not text:
        return ""
    rainy_now = any(
        marker in weather_text for marker in ("雨", "阵雨", "雷雨", "暴雨", "小雨")
    )
    wet_words = ("雨", "淋湿", "湿透", "水渍", "积水", "潮湿")
    if not rainy_now and any(word in text for word in wet_words):
        return "有日常使用的痕迹，当前天气不是雨天"
    return text


def build_environment(
    state: dict[str, Any],
    home_items: list[dict[str, Any]] | None = None,
    *,
    room: str = "",
    floor: int | None = None,
    anime: bool = False,
) -> str:
    """把当前地点、时间、天气和房间家具写成生图用的环境描写。"""
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    now_location = _clean(now.get("location"), 40)
    now_room = _clean(now.get("room"), 20)
    current_room = _clean(room or now_room, 20)
    floor_value = floor if floor is not None else now.get("floor")
    try:
        floor_number = int(floor_value) if floor_value is not None else None
    except (TypeError, ValueError):
        floor_number = None
    kind = _clean(now.get("kind"), 10) or "home"
    weather = state.get("weather") if isinstance(state.get("weather"), dict) else {}
    weather_text = _clean(
        weather.get("description") or weather.get("condition"), 60
    )
    now_time = _clean(state.get("now_time"), 10)
    hour = 20
    if ":" in now_time:
        try:
            hour = int(now_time.split(":", 1)[0])
        except ValueError:
            hour = 20
    period = _time_period(hour)

    if current_room and current_room != now_room and floor_number is not None:
        location = f"{floor_number}楼{current_room}"
    else:
        location = now_location or current_room or "家里"
    outdoor = _is_outdoor(kind, location, current_room, floor_number)

    header = (
        "【当前场景，画面须保持一致】"
        if anime
        else "【当前真实环境，必须保留，不要改成白天或其他天气】"
    )
    parts = [
        header
        + f"现在是{period}（{now_time or '当前时间'}），"
        f"天气：{weather_text or '未知'}，地点是{location}"
    ]
    if floor_number is not None and current_room:
        parts.append(f"（{floor_number}楼{current_room}）")
    parts.append("。")
    furniture = _furniture_environment(
        home_items, room=current_room, floor=floor_number
    )
    if furniture:
        parts.append(
            ("露台/室外空间里能看到" if outdoor else "房间里能看到")
            + furniture.replace("房间里能看到", "", 1)
        )
    if 19 <= hour or hour < 6:
        if outdoor:
            parts.append(
                "现在是有风/微风的夜晚，露台灯光与室内透出的光线照亮局部，天空是夜色；"
                "不要改成白天、阴天日光或晴天，也不要下雨。"
            )
        else:
            parts.append(
                "室内亮着暖色灯光，窗外是夜色，光线柔和但有生活阴影；"
                "不要改成白天或室外日光，也不要下雨。"
            )
    elif outdoor:
        parts.append("室外有自然天光，空气通透，保留真实天气和光线。")
    elif anime:
        parts.append("室内有自然光，日常生活的使用痕迹。")
    else:
        parts.append("自然光从窗户照进来，室内有日常生活的使用痕迹。")
    parts.append("不是样板间，不要摆拍式的完美整洁。")
    text = "".join(parts)
    if anime:
        # 让 node_auto 稳定选择 Illustrious 二次元引擎，避免触发风景/ZImage 关键词。
        text = (
            text.replace("城市", "街区")
            .replace("夜景", "夜晚")
            .replace("真实环境", "当前场景")
            .replace("真实", "")
            .replace("摄影", "")
            .replace("照片", "")
        )
    return text


ITEM_EN = {
    "餐桌": "dining table",
    "摇椅": "rocking chair",
    "沙发": "sofa",
    "床": "bed",
    "书桌": "desk",
    "书柜": "bookshelf",
    "书架": "bookshelf",
    "衣柜": "wardrobe",
    "冰箱": "refrigerator",
    "床头灯": "bedside lamp",
    "茶几": "coffee table",
    "洗衣机": "washing machine",
    "电视": "television",
    "地毯": "rug",
    "椅子": "chair",
    "灯": "lamp",
    "花盆": "potted plant",
    "植物": "potted plant",
    "烧烤架": "barbecue grill",
    "跑步机": "treadmill",
    "瑜伽垫": "yoga mat",
    "镜子": "mirror",
    "梳妆台": "vanity table",
    "置物架": "shelf",
    "鞋柜": "shoe cabinet",
}


def _english_room_name(value: Any) -> str:
    text = _clean(value, 30)
    for key, room in ROOM_EN.items():
        if key in text:
            return room
    return "home room"


def _english_item_name(value: Any) -> str:
    text = _clean(value, 30)
    for key, name in ITEM_EN.items():
        if key in text:
            return name
    return "furniture"


def build_anime_scene_prompt(
    state: dict[str, Any],
    *,
    item: dict[str, Any] | None = None,
    style_prompt: str = "",
) -> str:
    """没有人物时，用 MOSS 的二次元背景/家具 prompt。"""
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    if isinstance(item, dict):
        room = _english_room_name(item.get("room"))
        item_name = _english_item_name(item.get("name"))
        subject = f"focus on a {item_name}"
        furniture = ROOM_ENV_EN.get(room, "cozy home interior")
        setting = f"{room} at {_english_time_light(state)}"
    elif not _at_home(state):
        place, furniture = _outdoor_context(state)
        subject = f"{place} background"
        setting = f"{place} at {_english_time_light(state)}"
    else:
        room = _english_room(state)
        subject = f"interior background of the {room}"
        furniture = ROOM_ENV_EN.get(room, "cozy home interior")
        setting = f"{room} at {_english_time_light(state)}"
    weather = _english_weather(state)
    style = style_prompt or (
        "2D anime background, flat cel shading, colorful anime illustration"
    )
    return (
        f"{style}, "
        "no humans, no people, no characters, "
        f"{subject}, {setting}, {furniture}, {weather}, "
        "detailed background, cozy lived-in atmosphere, "
        "no photorealistic, no 3D render, no text, no watermark"
    )


def build_prompt(
    state: dict[str, Any],
    *,
    target: str,
    item: dict[str, Any] | None = None,
    home_items: list[dict[str, Any]] | None = None,
    persona_visual: str = "",
    style_prompt: str = "",
    extra_prompt: str = "",
) -> tuple[str, str, str]:
    """返回 (prompt, mode, caption)。

    mode 为 selfie 时使用万象画卷的人设参考图；空字符串走普通文生图。
    """
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    persona = _clean(state.get("persona"), 20) or "角色"
    activity = _clean(now.get("activity"), 80) or "在家里待着"
    location = _clean(now.get("location"), 40) or _clean(now.get("room"), 20) or "家里"
    appearance = _appearance_text(state)
    caption = ""
    if target == TARGET_CHARACTER:
        return (
            build_anime_prompt(
            state, style_prompt=style_prompt, extra_prompt=extra_prompt
        ),
            "",
            f"拍下了{activity}",
        )

    if target == TARGET_ITEM and isinstance(item, dict):
        item_name = _clean(item.get("name"), 30) or "家具"
        return (
            build_anime_scene_prompt(
                state, item=item, style_prompt=style_prompt
            ),
            "",
            f"拍下了{item_name}",
        )

    return (
        build_anime_scene_prompt(state, style_prompt=style_prompt),
        "",
        f"拍下了{location}",
    )


def extract_image(result: dict[str, Any]) -> str:
    """从万象画卷返回的图片数据里提取可在页面展示的地址。"""
    images = result.get("images")
    if not isinstance(images, list) or not images:
        return ""
    image = images[0]
    if not isinstance(image, dict):
        return ""
    for key in ("url", "image_url", "data_url"):
        value = str(image.get(key) or "").strip()
        if value.startswith(("http://", "https://", "data:image")):
            return value
    file_path = str(image.get("file_path") or "").strip()
    if file_path:
        path = Path(file_path)
        try:
            data = path.read_bytes()
        except OSError:
            return ""
        mime = mimetypes.guess_type(str(path))[0] or "image/png"
        return "data:%s;base64,%s" % (
            mime,
            base64.b64encode(data).decode("ascii"),
        )
    return ""


async def _materialize_image(image: str) -> str:
    """把远程图片下载为内联 data URL，避免 WebUI 的跨域/CSP 导致裂图。"""
    if not image:
        return ""
    if image.startswith("data:image"):
        return image
    if image.startswith(("http://", "https://")):
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(image) as response:
                    if response.status != 200:
                        return image
                    data = await response.read()
                    if not data or len(data) > 16 * 1024 * 1024:
                        return image
                    content_type = str(
                        response.headers.get("Content-Type") or ""
                    ).strip()
                    if not content_type.startswith("image/"):
                        content_type = (
                            mimetypes.guess_type(image.split("?")[0])[0]
                            or "image/png"
                        )
                    return "data:%s;base64,%s" % (
                        content_type,
                        base64.b64encode(data).decode("ascii"),
                    )
        except Exception:
            # 下载失败时退回原地址，至少给页面一次机会直接加载。
            return image
    path = Path(image)
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if not data or len(data) > 16 * 1024 * 1024:
        return ""
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    return "data:%s;base64,%s" % (
        mime,
        base64.b64encode(data).decode("ascii"),
    )


async def _generate_via_proxy(
    prompt: str,
    *,
    models: tuple[str, ...] = ("moss",),
    size: str = "864x1152",
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    api_url: str = COMFY_PROXY_URL,
    api_key: str = "",
    timeout_seconds: int = 240,
) -> str:
    """调用本机 ComfyUI OpenAI 代理的二次元引擎。

    默认优先 MOSS-Image（细节和复杂构图更好），失败时退回 Illustrious。
    """
    timeout = aiohttp.ClientTimeout(total=max(30, int(timeout_seconds or 240)))
    headers = (
        {"Authorization": f"Bearer {api_key}"} if str(api_key or "").strip() else None
    )
    for model in models:
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    api_url or COMFY_PROXY_URL,
                    headers=headers,
                    json={
                        "model": model,
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "size": size,
                        "n": 1,
                    },
                ) as response:
                    if response.status != 200:
                        continue
                    payload = await response.json()
                    images = payload.get("data") or []
                    if not images:
                        continue
                    url = str(images[0].get("url") or "").strip()
                    if not url:
                        continue
                    image = await _materialize_image(url)
                    if image:
                        return image
        except Exception:
            continue
    return ""


async def generate(
    plugin: Any,
    state: dict[str, Any],
    *,
    target: str,
    item: dict[str, Any] | None = None,
    home_items: list[dict[str, Any]] | None = None,
    persona_visual: str = "",
    extra_prompt: str = "",
) -> dict[str, Any]:
    """Generate a photo through the plugin's configured drawing endpoint."""
    settings = camera_settings(getattr(plugin, "config", None))
    full_style = compose_style_prompt(settings)
    scene_style = str(
        settings.get("style_prompt") or DEFAULT_STYLE_PROMPT
    ).strip()
    prompt, mode, caption = build_prompt(
        state,
        target=target,
        item=item,
        home_items=home_items,
        persona_visual=persona_visual,
        style_prompt=full_style if target == TARGET_CHARACTER else scene_style,
        extra_prompt=extra_prompt,
    )
    api_url = str(settings.get("api_url") or COMFY_PROXY_URL).strip()
    api_key = str(settings.get("api_key") or "").strip()
    model_text = str(settings.get("model") or "moss").strip()
    models = tuple(
        part.strip() for part in model_text.split(",") if part.strip()
    ) or ("moss",)
    character_size = str(settings.get("size_character") or "864x1152").strip()
    scene_size = str(settings.get("size_scene") or "1152x864").strip()
    try:
        timeout_seconds = int(settings.get("timeout_seconds") or 240)
    except (TypeError, ValueError):
        timeout_seconds = 240
    base_negative = str(
        settings.get("negative_prompt") or DEFAULT_NEGATIVE_PROMPT
    ).strip()
    now = state.get("now") if isinstance(state.get("now"), dict) else {}
    raw_now = f"{now.get('activity') or ''} {now.get('location') or ''}"
    walking_transit = any(
        word in raw_now for word in ("步行", "走路", "散步", "撑伞", "走回家", "路上")
    ) and (
        str(now.get("scene") or "") == "transit"
        or "路上" in str(now.get("location") or "")
    )
    if walking_transit:
        base_negative += (
            ", train interior, bus interior, car interior, vehicle cabin, "
            "row of seats, inside a vehicle"
        )
    negative = _time_negative_prompt(state, base_negative)
    if target == TARGET_CHARACTER:
        anime_image = await _generate_via_proxy(
            prompt,
            models=models,
            size=character_size,
            negative_prompt=negative,
            api_url=api_url,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
        if anime_image:
            return {
                "ok": True,
                "image": anime_image,
                "caption": caption,
                "prompt": prompt,
                "target": target,
                "mode": "moss-anime",
            }
    if target in (TARGET_ITEM, TARGET_ROOM):
        scene_image = await _generate_via_proxy(
            prompt,
            models=models,
            size=scene_size,
            negative_prompt=negative,
            api_url=api_url,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
        if scene_image:
            return {
                "ok": True,
                "image": scene_image,
                "caption": caption,
                "prompt": prompt,
                "target": target,
                "mode": "moss-scene",
            }
    if bool(settings.get("fallback_to_omnidraw", False)):
        try:
            meta = plugin.context.get_registered_star(OMNIDRAW_PLUGIN_ID)
        except Exception:
            meta = None
        star = getattr(meta, "star_cls", None) if meta is not None else None
        generator = getattr(star, "generate_images_for_plugin", None)
        if callable(generator):
            try:
                result = await generator(
                    prompt=prompt,
                    count=1,
                    aspect_ratio="3:4" if target == TARGET_CHARACTER else "4:3",
                    mode=mode,
                    event=None,
                )
            except Exception as exc:
                return {
                    "ok": False,
                    "error": f"显影失败：{type(exc).__name__}",
                }
            if isinstance(result, dict) and result.get("success"):
                image = extract_image(result)
                display_image = await _materialize_image(image)
                if display_image:
                    return {
                        "ok": True,
                        "image": display_image,
                        "caption": caption,
                        "prompt": prompt,
                        "target": target,
                        "mode": result.get("mode") or mode or "text2img",
                    }
    return {
        "ok": False,
        "error": "相机显影失败，请检查插件相机设置里的绘图接口、模型和提示词",
    }
