"""Small things that happen on the way: 路上见闻.

Every finished transit / outdoor segment of the day may produce one small,
ordinary encounter (a cat on the wall, a busker, rain on the bus window…). The
pick is deterministic per persona, day and segment, so the same day always
"remembers" the same thing, and it depends on the transport, the weather and
the time of day.
"""

from __future__ import annotations

import random

# (tags, text). A line is eligible when every tag is satisfied by the context.
# Tags: transport (subway/bus/walk/bike/car/taxi), weather (rain/snow/hot/cold/sunny),
# time (morning/noon/evening/night).
ENCOUNTERS: tuple[tuple[frozenset[str], str], ...] = tuple(
    (frozenset(tags), text)
    for tags, text in (
        # subway
        (("subway",), "地铁里有人抱着一大束向日葵，整节车厢都被照亮了一点"),
        (("subway",), "地铁到站时广播报错了站名，全车厢的人一起愣了一下"),
        (("subway",), "地铁上坐对面的小孩一路都在用手指在玻璃上画画"),
        (("subway", "morning"), "早高峰地铁挤得只能看见别人的后脑勺，下车时差点被带过站"),
        (("subway", "evening"), "晚上的地铁很空，对面车窗映出自己有点累的样子"),
        (("subway",), "换乘通道里有人在弹吉他，弹的是一首小时候听过的歌"),
        # bus
        (("bus",), "公交车司机等了一位小跑过来的老奶奶，车上没人催"),
        (("bus",), "公交车经过的路口新开了一家面包店，香味飘进车里"),
        (("bus", "rain"), "雨天坐公交，车窗上的水痕把路灯拉成一条条光"),
        (("bus", "morning"), "早上的公交上，前排两个学生在小声背英语单词"),
        (("bus",), "公交上有人的手机外放了猫叫声，好几个人偷偷笑了"),
        # walk
        (("walk",), "路过小区围墙时，那只常见的橘猫正趴在墙头晒太阳"),
        (("walk",), "街角的花店把一桶打折的满天星摆在了门口"),
        (("walk",), "走路时踩到一片特别脆的落叶，咔嚓一声很解压"),
        (("walk", "morning"), "早上路过早餐摊，蒸笼一掀开全是白气"),
        (("walk", "evening"), "傍晚走回来时，天边的云被染成了粉紫色"),
        (("walk", "night"), "夜里路过便利店，店员在门口给流浪猫放了一小碟猫粮"),
        (("walk",), "有只小狗挣脱了绳子跑过来闻了闻她的鞋，又被主人追回去了"),
        (("walk", "sunny"), "阳光把树影投在人行道上，她故意踩着光斑走了一段"),
        (("walk",), "路边有人在给共享单车排队，一辆一辆摆得整整齐齐"),
        # bike
        (("bike",), "骑车下坡的时候风特别舒服，差点哼出歌来"),
        (("bike",), "骑车经过河边，看到有人在钓鱼，桶里一条都没有"),
        (("bike", "morning"), "早上骑车，路边的洒水车慢悠悠地经过，赶紧绕开了"),
        (("bike",), "红灯时旁边骑车的大叔车筐里装着一只很淡定的柯基"),
        # car / taxi
        (("car",), "开车路过的那条街正在换新的路灯，一排灯杆还包着塑料膜"),
        (("car",), "等红灯时收音机里放了一首很久没听的老歌"),
        (("car", "evening"), "傍晚开车回来，车窗外整条街的灯一下子都亮了"),
        (("taxi",), "出租车司机一路在讲他家女儿考上大学的事，讲得特别骄傲"),
        (("taxi",), "打车的司机车里挂着一串小风铃，转弯时叮叮响"),
        # weather
        (("rain",), "出门时雨下得正大，在屋檐下等了几分钟才敢冲出去"),
        (("rain",), "路上有个小学生穿着黄色雨衣专门踩水坑，溅了自己一身"),
        (("rain",), "雨后的路面映着天空，像多了一层镜子"),
        (("snow",), "路边不知道谁堆了个歪歪扭扭的小雪人，还插了两根树枝当手"),
        (("snow",), "雪落在围巾上半天没化，拍下来像撒了一层糖"),
        (("hot",), "天太热，路边冰粉摊前排了好长的队"),
        (("hot",), "路过商场门口被冷气吹了一下，舒服得不想走"),
        (("cold",), "冷得手都缩进袖子里了，路过烤红薯摊没忍住多看了两眼"),
        (("cold",), "呼出的气变成白雾，路边的人都缩着脖子走得很快"),
        (("sunny",), "天特别蓝，几架飞机拉出的白线在头顶交叉成一个叉"),
        # time of day
        (("morning",), "路过学校门口，值日的学生在门口喊老师好"),
        (("noon",), "中午路过写字楼楼下，外卖小哥们在树荫下排成一排等单"),
        (("evening",), "路边的烧烤摊刚支起来，炭火的味道一下子飘了过来"),
        (("night",), "夜里路过的公园还有人在跳广场舞，音乐声很远都能听到"),
        # anywhere
        ((), "路上看到一个小朋友把冰淇淋掉在地上，愣了三秒才哭出来"),
        ((), "有人在路边问路，她顺手指了方向，对方连说了好几声谢谢"),
        ((), "路过的小店在放歌，正好是最近单曲循环的那首"),
        ((), "路上捡到一张不知道谁掉的公交卡，交给了旁边的保安"),
        ((), "看到两个老人手牵手慢慢过马路，红灯了也不着急"),
        ((), "一阵风把谁的帽子吹到了她脚边，帮忙捡起来递了回去"),
    )
)

TRANSPORT_WORDS = (
    ("subway", ("地铁", "轻轨")),
    ("bus", ("公交", "巴士")),
    ("bike", ("单车", "骑车", "自行车", "电摩", "电动车")),
    ("taxi", ("打车", "出租", "网约车")),
    ("car", ("开车", "自驾", "车载", "载他", "载她")),
    ("walk", ("步行", "走路", "散步", "走回", "走去", "逛")),
)
WEATHER_WORDS = (
    ("rain", ("雨",)),
    ("snow", ("雪",)),
    ("hot", ("高温", "炎热", "闷热", "酷暑")),
    ("cold", ("寒", "冷", "冰冻")),
    ("sunny", ("晴",)),
)
MOVING_WORDS = ("通勤", "路上", "赶路", "地铁", "公交", "巴士", "打车", "出租", "开车", "自驾", "骑车", "单车", "步行", "走路", "散步", "载他", "载她")
INDOOR_ROOMS = ("卧室", "客厅", "书房", "厨房", "浴室", "餐厅", "健身室", "影音室", "画室", "衣帽间")
CHANCE = 0.6


def context_tags(activity: str, location: str, weather: str, hour: int, temperature: float | None = None) -> set[str]:
    text = f"{activity} {location}"
    tags: set[str] = set()
    for tag, words in TRANSPORT_WORDS:
        if any(word in text for word in words):
            tags.add(tag)
            break
    else:
        tags.add("walk")
    for tag, words in WEATHER_WORDS:
        if any(word in str(weather or "") for word in words):
            tags.add(tag)
    if temperature is not None:
        if temperature >= 32:
            tags.add("hot")
        elif temperature <= 5:
            tags.add("cold")
    if 5 <= hour < 10:
        tags.add("morning")
    elif 11 <= hour < 14:
        tags.add("noon")
    elif 17 <= hour < 20:
        tags.add("evening")
    elif hour >= 21 or hour < 5:
        tags.add("night")
    return tags


def is_on_the_way(activity: str, location: str, state: str = "") -> bool:
    """Whether a timeline segment is spent moving around outside."""
    if str(state or "") == "transit":
        return True
    if any(room in str(location or "") for room in INDOOR_ROOMS):
        return False
    text = f"{activity} {location}"
    return any(word in text for word in MOVING_WORDS)


def pick(seed: str, tags: set[str], *, chance: float | None = None, exclude: set[str] | None = None) -> str:
    """Deterministically choose an encounter for ``seed`` (or nothing)."""
    chance = CHANCE if chance is None else chance
    rng = random.Random(seed)
    if rng.random() >= chance:
        return ""
    blocked = exclude or set()
    eligible = [text for need, text in ENCOUNTERS if need <= tags and text not in blocked]
    specific = [text for need, text in ENCOUNTERS if need and need <= tags and text not in blocked]
    pool = specific if specific and rng.random() < 0.75 else eligible
    return rng.choice(pool) if pool else ""
