from __future__ import annotations

import json
import random
from datetime import date, datetime
from pathlib import Path
from typing import Any
from .jsonio import STATE_LOCK, atomic_write_json

LOCK = STATE_LOCK  # shared re-entrant lock for all state files (see jsonio)

EVENTS = (
    (
        "面包店",
        "楼下新开了一家面包店，路过时闻到黄油味。",
        3,
    ),
    (
        "装修声",
        "隔壁在装修，电钻声断断续续响了一上午。",
        -4,
    ),
    (
        "晚点的公交",
        "公交晚点了十分钟，站台上有人分了你半把伞。",
        2,
    ),
    (
        "关东煮",
        "常去的便利店换了新的关东煮汤底。",
        1,
    ),
    (
        "路边的花",
        "路边有人卖花，收摊前还剩最后一束。",
        2,
    ),
    (
        "屏幕细纹",
        "手机屏幕不知道什么时候多了一道细纹。",
        -5,
    ),
    (
        "旧照片",
        "旧同学发来一张以前的照片，两个人都笑得很傻。",
        4,
    ),
    (
        "楼下的猫",
        "公司楼下的猫今天肯让人摸了。",
        3,
    ),
    (
        "新开的书店",
        "街角的小书店亮起了新招牌，橱窗里摆着旧杂志。",
        2,
    ),
    (
        "雨天",
        "下午忽然下了一阵雨，空气里有泥土味。",
        1,
    ),
    (
        "外卖迟了",
        "点的外卖迟了半小时，汤已经有点凉。",
        -3,
    ),
    (
        "邻居的琴声",
        "晚上隔壁传来断断续续的钢琴声，弹得不太熟。",
        2,
    ),
    (
        "新开的面馆",
        "巷口新开了一家面馆，汤头熬得很浓。",
        3,
    ),
    (
        "咖啡拉花",
        "常去的咖啡店今天拉花多画了一只小猫。",
        2,
    ),
    (
        "便利店新品",
        "便利店上了新的草莓布丁，冰柜前站了半天。",
        2,
    ),
    (
        "水果摊试吃",
        "水果摊老板切了块橙子递过来，很甜。",
        2,
    ),
    (
        "晚饭做咸了",
        "晚饭盐放多了，喝了两杯水。",
        -2,
    ),
    (
        "烤焦的吐司",
        "吐司烤焦了一片，厨房里全是焦味。",
        -1,
    ),
    (
        "风吹落衣架",
        "风把阳台上的衣架吹倒了，捡了半天。",
        -2,
    ),
    (
        "晒被子",
        "太阳很好，把被子抱到阳台晒了晒。",
        4,
    ),
    (
        "晚霞",
        "傍晚的云烧成橘红色，站在窗边看了很久。",
        4,
    ),
    (
        "忽然下雨",
        "出门没带伞，在便利店门口等雨停。",
        -1,
    ),
    (
        "降温",
        "气温突然降下来，翻出了厚一点的外套。",
        0,
    ),
    (
        "雾天",
        "早上起了雾，楼下的树只剩一个轮廓。",
        0,
    ),
    (
        "楼道灯坏了",
        "楼道灯坏了一盏，晚上上楼摸黑。",
        -1,
    ),
    (
        "电梯里的花",
        "电梯里有人抱着一大束花，香味留了一层。",
        2,
    ),
    (
        "路边橘猫",
        "路边一只橘猫蹲在车盖上，谁叫都不理。",
        3,
    ),
    (
        "跟着走的小狗",
        "一只小狗跟着走了半条街，最后被主人喊回去。",
        2,
    ),
    (
        "窗台的鸟",
        "有只鸟停在窗台，歪头看了半天。",
        2,
    ),
    (
        "楼下修路",
        "楼下开始修路，早上被冲击钻叫醒。",
        -3,
    ),
    (
        "快递提前到",
        "快递比预计早到一天，纸箱上还带着雨气。",
        2,
    ),
    (
        "快递放错柜",
        "快递被放进隔壁柜子，绕了一圈才拿到。",
        -1,
    ),
    (
        "旧书里的票根",
        "整理书时翻出一张旧电影票根。",
        3,
    ),
    (
        "失踪的耳机",
        "在沙发缝里找到了失踪半个月的耳机。",
        3,
    ),
    (
        "手机更新",
        "手机系统更新完，图标全换了个排列。",
        0,
    ),
    (
        "充电线坏了",
        "充电线又接触不良，充了一下午还是半格电。",
        -2,
    ),
    (
        "随机到好歌",
        "随机播放撞到一首很合心意的歌。",
        2,
    ),
    (
        "旧歌回忆",
        "听到一首很久以前的歌，突然想起某个夏天。",
        2,
    ),
    (
        "邻居搬家",
        "隔壁搬来新邻居，门口堆了一下午纸箱。",
        0,
    ),
    (
        "朋友的长语音",
        "朋友发来一段很长的语音，边说边笑。",
        3,
    ),
    (
        "群里冷场",
        "群里聊到一半突然没人接话。",
        -1,
    ),
    (
        "被夸衣服",
        "有人夸今天的衣服颜色好看。",
        3,
    ),
    (
        "被认错人",
        "路上被人认错，解释了两句才走开。",
        -1,
    ),
    (
        "地铁让座",
        "地铁上有人给老人让座，车厢里安静了一下。",
        1,
    ),
    (
        "公交坐过站",
        "公交坐过一站，只好多走一段路。",
        -2,
    ),
    (
        "好骑的单车",
        "扫到一辆很好骑的共享单车，链条不响。",
        2,
    ),
    (
        "街头艺人",
        "地下通道有人弹吉他，唱得不算准但很认真。",
        2,
    ),
    (
        "夜市的套圈摊",
        "夜市新摆了一个套圈摊，围观的人比玩的多。",
        2,
    ),
    (
        "旧杂志",
        "报刊亭收摊前买到最后一本旧杂志。",
        1,
    ),
    (
        "图书馆的窗边",
        "图书馆靠窗的位置空着，坐下就不想起来。",
        3,
    ),
    (
        "洗澡时的点子",
        "洗澡时突然想到一个不错的点子，赶紧记下来。",
        3,
    ),
    (
        "卡文",
        "写到一半卡住，盯着光标看了很久。",
        -1,
    ),
    (
        "会议取消",
        "临时通知会议取消，空出来一小时。",
        3,
    ),
    (
        "打印机卡纸",
        "打印机卡纸，修了半天手上全是墨。",
        -2,
    ),
    (
        "提前做完的活",
        "手里的活比预想早做完，关电脑时天还没黑。",
        3,
    ),
    (
        "计划被打乱",
        "原定的事临时变了，只能重新排一遍。",
        -2,
    ),
    (
        "突然大扫除",
        "突然想大扫除，清出一袋不用的东西。",
        2,
    ),
    (
        "口袋里的纸币",
        "洗衣服时发现口袋里有张忘了的纸币。",
        3,
    ),
    (
        "冰箱空了",
        "打开冰箱发现只剩半盒鸡蛋。",
        -1,
    ),
    (
        "灯泡坏了",
        "客厅灯泡闪了两下就灭了。",
        -2,
    ),
    (
        "水龙头滴水",
        "厨房水龙头一直滴水，垫了块毛巾。",
        -2,
    ),
    (
        "花开了",
        "窗台上的花开了第一朵。",
        4,
    ),
    (
        "长出新叶",
        "阳台的绿植冒出一片新叶。",
        3,
    ),
    (
        "新菜成功",
        "照着食谱做了一道新菜，味道居然不错。",
        3,
    ),
    (
        "烤了一盘饼干",
        "烤了一盘饼干，形状不太规整但很香。",
        3,
    ),
    (
        "茶泡浓了",
        "茶泡得太久，苦涩里带一点回甘。",
        1,
    ),
    (
        "咖啡洒了",
        "咖啡洒在桌角，擦了半天还是留一圈印。",
        -1,
    ),
    (
        "好梦",
        "昨晚做了个很轻的梦，醒来还记得一点。",
        2,
    ),
    (
        "失眠",
        "凌晨醒了两次，天快亮时才睡回去。",
        -2,
    ),
    (
        "午睡睡过头",
        "午睡睡过头，醒来天已经暗了。",
        -1,
    ),
    (
        "电子秤没电",
        "站上电子秤才发现没电，换电池时又把盖子掉进了柜子缝。",
        -1,
    ),
    (
        "外卖多送一份",
        "外卖多送了一份小菜，打电话过去对方说不用退。",
        2,
    ),
    (
        "邻居家的饭香",
        "邻居家飘来炖肉味，站在门口闻了两下才回屋。",
        1,
    ),
    (
        "阳台的风",
        "阳台风很大，晾着的衣服被吹得鼓起来。",
        1,
    ),
    (
        "信箱里的明信片",
        "信箱里躺着一张没署名的明信片，邮戳是外地。",
        3,
    ),
    (
        "旧外套的口袋",
        "穿上旧外套，口袋里摸出一张去年写的便签。",
        2,
    ),
    (
        "手工做坏了",
        "想做个手工，剪坏了三张纸才勉强成形。",
        -1,
    ),
    (
        "修好了小东西",
        "把松了很久的椅子腿重新拧紧，坐上去不晃了。",
        3,
    ),
    (
        "记错时间",
        "把约定时间记早了半小时，到了才发现没人。",
        -1,
    ),
    (
        "临时被约出门",
        "本来打算宅着，临时被人叫出门走了走。",
        1,
    ),
    (
        "拍了一张好照片",
        "随手拍了一张窗外的照片，光线比想的好。",
        3,
    ),
    (
        "手机快没电",
        "出门时手机只剩百分之三，一路省着用。",
        -2,
    ),
    (
        "钥匙找不到了",
        "出门前找不到钥匙，最后在昨天穿的外套里。",
        -1,
    ),
    (
        "排队排到一半",
        "排队排到一半发现忘带会员卡。",
        -1,
    ),
    (
        "捡到一块好看的石头",
        "路边捡到一块被水磨圆的石头，顺手带回家。",
        2,
    ),
    (
        "路面积水",
        "昨夜的雨让路口积了一小片水，绕了半圈。",
        -1,
    ),
    (
        "新开的奶茶店",
        "新开的奶茶店买一送一，队排到了街角。",
        1,
    ),
    (
        "久违的太阳",
        "连阴了几天，今天终于见到太阳。",
        4,
    ),
    (
        "晒过的被子",
        "晚上钻进白天晒过的被子，有太阳味。",
        3,
    ),
    (
        "半夜饿了",
        "半夜饿得睡不着，起来煮了一小碗面。",
        1,
    ),
    (
        "清晨的鸟叫",
        "天刚亮就被鸟叫醒，躺了会儿没再睡着。",
        0,
    ),
    (
        "手机内存满了",
        "手机提示内存满了，删照片删了半小时。",
        -2,
    ),
    (
        "收到手写信",
        "收到一封手写的信，字迹有点抖。",
        4,
    ),
    (
        "旧歌单随机",
        "翻到几年前建的一个歌单，一首接一首听下去。",
        2,
    ),
    (
        "被小孩搭话",
        "路上被一个小孩问时间，说完他还认真道了谢。",
        2,
    ),
    (
        "晚风",
        "晚上开窗，风把窗帘吹得慢慢鼓起来。",
        2,
    ),
    (
        "灯光很暖",
        "换了一盏暖色的小灯，屋里看着软和了不少。",
        3,
    ),
    (
        "杯子摔了",
        "杯子从桌边掉下去，碎成好几片。",
        -3,
    ),
    (
        "找回了走丢的袜子",
        "晾衣服时在洗衣机后面找到了那只走丢的袜子。",
        1,
    ),
)


def _path(data_dir: Path) -> Path:
    return Path(data_dir) / "world_events.json"


def _load(data_dir: Path) -> dict[str, Any]:
    path = _path(data_dir)
    if not path.exists():
        return {"schema_version": 1, "personas": {}}
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "personas": {}}
    if not isinstance(content, dict):
        return {"schema_version": 1, "personas": {}}
    content.setdefault("personas", {})
    return content


def _save(data_dir: Path, content: dict[str, Any]) -> None:
    path = _path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, content)


RECENT_AVOID_DAYS = 14


def _recent_titles(entries: dict[str, Any], day_text: str) -> set[str]:
    """Collect titles used on nearby days so the daily event does not repeat."""
    current = date.fromisoformat(day_text)
    titles: set[str] = set()
    for key, value in entries.items():
        if key == day_text or not isinstance(value, dict):
            continue
        try:
            used = date.fromisoformat(str(key))
        except ValueError:
            continue
        if 0 < (current - used).days <= RECENT_AVOID_DAYS:
            title = str(value.get("title") or "").strip()
            if title:
                titles.add(title)
    return titles


def _pick_event(
    rng: random.Random,
    day_text: str,
    entries: dict[str, Any],
) -> tuple[str, str, int]:
    recent_titles = _recent_titles(entries, day_text)
    candidates = [event for event in EVENTS if event[0] not in recent_titles]
    if not candidates:
        candidates = list(EVENTS)
    return rng.choice(candidates)


def get_or_create(
    data_dir: Path,
    persona: str,
    day: str,
) -> dict[str, Any]:
    day_text = str(day or date.today().isoformat())
    with LOCK:
        content = _load(data_dir)
        personas = content.setdefault("personas", {})
        entries = personas.setdefault(str(persona), {})
        existing = entries.get(day_text)
        if isinstance(existing, dict):
            return {**existing, "created": False}
        rng = random.Random(f"{persona}:{day_text}")
        title, summary, mood = _pick_event(rng, day_text, entries)
        entry = {
            "date": day_text,
            "title": title,
            "summary": summary,
            "mood": mood,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        entries[day_text] = entry
        content["personas"][str(persona)] = {
            key: value
            for key, value in entries.items()
            if isinstance(value, dict)
        }
        _save(data_dir, content)
        return {**entry, "created": True}


def reroll(
    data_dir: Path,
    persona: str,
    day: str,
) -> dict[str, Any]:
    """Replace one day's event, keeping the same anti-repeat rules."""
    day_text = str(day or date.today().isoformat())
    with LOCK:
        content = _load(data_dir)
        personas = content.setdefault("personas", {})
        entries = personas.setdefault(str(persona), {})
        entries.pop(day_text, None)
        rng = random.Random(f"{persona}:{day_text}:reroll")
        title, summary, mood = _pick_event(rng, day_text, entries)
        entry = {
            "date": day_text,
            "title": title,
            "summary": summary,
            "mood": mood,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        entries[day_text] = entry
        content["personas"][str(persona)] = {
            key: value
            for key, value in entries.items()
            if isinstance(value, dict)
        }
        _save(data_dir, content)
        return {**entry, "created": True}


def recent(
    data_dir: Path,
    persona: str,
    day: str,
) -> dict[str, Any] | None:
    with LOCK:
        entries = _load(data_dir).get("personas", {}).get(str(persona), {})
    entry = entries.get(str(day))
    return entry if isinstance(entry, dict) else None


def list_recent(
    data_dir: Path,
    persona: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    with LOCK:
        entries = _load(data_dir).get("personas", {}).get(str(persona), {})
    items = [
        entry
        for entry in entries.values()
        if isinstance(entry, dict) and entry.get("date")
    ]
    items.sort(key=lambda entry: str(entry.get("date") or ""), reverse=True)
    return items[: max(1, int(limit or 10))]
