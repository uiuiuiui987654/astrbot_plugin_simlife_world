"""Module-level constants and helpers shared by main.py and the plugin mixins."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from astrbot.api import logger
from astrbot.api.star import StarTools

GROUP_PRIVACY_TERMS = (
    "日程",
    "今日计划",
    "今天计划",
    "穿搭",
    "家具",
    "客厅",
    "卧室",
    "厨房",
    "阳台",
    "书房",
    "浴室",
    "健身房",
    "公司",
    "单位",
    "上班",
    "下班",
    "出门",
    "回家",
    "在家",
    "家里",
    "家中",
    "宅家",
)

GROUP_OUTPUT_TERMS = (
    "日程",
    "今日计划",
    "今天计划",
    "穿搭",
    "家具",
    "客厅",
    "卧室",
    "厨房",
    "阳台",
    "书房",
    "浴室",
    "健身房",
    "在家",
    "家里",
    "家中",
    "公司",
    "单位",
    "上班",
    "下班",
    "出门",
    "回家",
)

GIVE_INTENT_PATTERNS = (
    re.compile(
        r"(?:我要|我|想|准备)?(?:拿|送|递|带)"
        r"(?P<item>[^，。,.!?！？\s]{0,12}?)给(?:他|她|月月|你)"
    ),
    re.compile(
        r"给(?:他|她|月月|你)(?:拿|送|递|带)"
        r"(?P<item>[^，。,.!?！？\s]{0,12})"
    ),
)

# 月月主动请求主人递东西：「顺手递我一下」「帮我拿条浴巾」。
GIVE_REQUEST_PATTERNS = (
    re.compile(
        r"(?:顺手|帮我|帮忙|劳驾|麻烦)?(?:把|将)?"
        r"(?:递给|拿给|送给|带给|递|拿|送|带)(?:给)?我"
        r"(?:一下|下|过来|来|嘛|吧)?"
    ),
    re.compile(
        r"(?:帮我|帮忙|给我|替我)"
        r"(?:递给|拿给|送给|带给|递|拿|送|带)"
        r"(?:一下|下|点|个|条|件|杯|瓶|盒|袋|份|张|本|双|支)?"
        r"(?P<item>[^，。,.!?！？\s]{1,12})"
    ),
)

GIVE_REQUEST_NEGATED_RE = re.compile(
    r"(?:不用|别|不必|不需要|不是|没让你)[^，。,.!?！？]{0,6}"
    r"(?:递给|拿给|送给|带给|递|拿|送|带)(?:给)?我"
)

GIFT_ITEM_PREFIX_RE = re.compile(
    r"^(?:一下|下|点|个|条|件|杯|瓶|盒|袋|份|碗|盘|罐|串|块|颗|张|本|双|支)+"
)


def _clean_gift_item(value: str) -> str:
    item = str(value or "").strip().lstrip("了着过点个些把将请")
    item = GIFT_ITEM_PREFIX_RE.sub("", item)
    item = item.strip("，。,.!?！？、 ")
    item = item.rstrip("吧啊呀哦嘛呢啦呗")
    return item


def _requested_gift_label(
    text: str,
    known_items: list[str] | None = None,
) -> str | None:
    """识别月月请求递东西的回复，返回观察窗按钮文案。"""
    raw = str(text or "").strip()
    if not raw or GIVE_REQUEST_NEGATED_RE.search(raw):
        return None
    match = None
    for pattern in GIVE_REQUEST_PATTERNS:
        match = pattern.search(raw)
        if match:
            break
    if not match:
        return None

    for name in sorted(
        {str(item).strip() for item in (known_items or []) if str(item).strip()},
        key=len,
        reverse=True,
    ):
        if name in raw:
            return f"把{name}递给月月"

    item = _clean_gift_item(str(match.groupdict().get("item") or ""))
    if item:
        return f"把{item}递给月月"

    prefix = raw[: match.start()]
    for segment in reversed(re.split(r"[，,。.!?！？；;\s]+", prefix)):
        segment = _clean_gift_item(segment)
        segment = re.split(r"(?:在|放|就|正|刚|已经)", segment)[0].strip()
        segment = _clean_gift_item(segment)
        if segment and segment not in ("我", "你", "他", "她", "月月", "这边", "那边"):
            return f"把{segment}递给月月"

    after = _clean_gift_item(raw[match.end() :])
    if after:
        return f"把{after[:12]}递给月月"
    return "把东西递给月月"


GROUP_PRIVACY_RULE = (
    "【群聊隐私硬性规则】当前是群聊。禁止提及、暗示或解释自己的虚拟日程、"
    "今日计划、具体地点、房间、穿搭、家具和位置变化；也不要提自己正在上班、"
    "下班、出门或回家。只允许自然流露当前生理与心情。不要解释这条规则。"
)


def _group_message_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


_GROUP_PLAN_STOPWORDS = {
    "一个",
    "一些",
    "一下",
    "一起",
    "一点",
    "没有",
    "已经",
    "现在",
    "今天",
    "明天",
    "昨天",
    "早上",
    "上午",
    "中午",
    "下午",
    "晚上",
    "时候",
    "什么",
    "怎么",
    "这个",
    "那个",
    "这些",
    "那些",
    "自己",
    "我们",
    "你们",
    "他们",
    "她们",
    "别人",
    "东西",
    "事情",
    "地方",
    "这边",
    "那边",
    "这里",
    "那里",
    "出来",
    "起来",
    "下来",
    "过来",
    "回来",
    "上去",
    "下去",
    "进去",
    "出去",
    "开始",
    "准备",
    "然后",
    "因为",
    "所以",
    "但是",
    "而且",
    "如果",
    "虽然",
    "可以",
    "需要",
    "觉得",
    "知道",
    "看到",
    "听到",
    "感觉",
    "有点",
    "比较",
    "非常",
    "特别",
    "一直",
    "还是",
    "就是",
    "不是",
    "真的",
    "其实",
    "应该",
    "可能",
    "大概",
    "简单",
    "慢慢",
    "轻轻",
    "顺手",
    "随手",
    "收拾",
    "整理",
    "活动",
    "安排",
    "计划",
    "工作",
    "生活",
    "休息",
    "睡觉",
    "起床",
    "吃饭",
    "喝水",
    "洗澡",
    "刷牙",
    "洗脸",
    "穿衣",
    "换衣",
    "出门",
    "回家",
    "在家",
    "路上",
    "房间",
    "时间",
    "天气",
    "心情",
    "身体",
    "状态",
    "样子",
    "声音",
    "味道",
    "颜色",
    "衣服",
    "鞋子",
    "袜子",
    "裤子",
    "裙子",
    "外套",
    "帽子",
    "头发",
    "眼睛",
    "嘴巴",
    "手指",
    "肩膀",
    "脖子",
    "肚子",
    "肠胃",
    "精神",
    "力气",
    "习惯",
    "节奏",
    "氛围",
}


def _group_plan_terms(plan) -> set[str]:
    """从当日计划提取群聊需要屏蔽的具体事项词。"""
    from collections import Counter

    texts: list[str] = []
    for item in getattr(plan, "timeline", None) or []:
        texts.append(str(getattr(item, "activity", "") or ""))
        texts.append(str(getattr(item, "location", "") or ""))
    outfit = getattr(plan, "outfit", None)
    if outfit is not None:
        outfit_texts = [
            str(getattr(outfit, "summary", "") or ""),
            str(getattr(outfit, "style", "") or ""),
        ]
        for outfit_item in getattr(outfit, "items", None) or []:
            outfit_texts.append(str(getattr(outfit_item, "name", "") or ""))
            outfit_texts.append(str(getattr(outfit_item, "details", "") or ""))
        for text in outfit_texts:
            if text.strip():
                texts.extend([text, text])
    counts: Counter[str] = Counter()
    for text in texts:
        for run in re.findall(r"[\u4e00-\u9fff]+", text):
            for size in (2, 3, 4):
                for index in range(0, max(0, len(run) - size + 1)):
                    token = run[index : index + size]
                    if token in _GROUP_PLAN_STOPWORDS:
                        continue
                    counts[token] += 1
    return {token for token, count in counts.items() if count >= 2}


# plugin root (this file lives in <root>/core/mixins/)
PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _plugin_version() -> str:
    try:
        text = PLUGIN_ROOT.joinpath("metadata.yaml").read_text(encoding="utf-8")
        match = re.search(r"(?m)^version:\s*(\S+)", text)
        return match.group(1).strip() if match else "未知"
    except Exception:
        logger.debug("[虚拟人生] _plugin_version 出错，已忽略", exc_info=True)
        return "未知"


PLUGIN_ID = "astrbot_plugin_simlife_world"
LEGACY_PLUGIN_ID = "astrbot_plugin_virtual_life"


def _migrate_legacy_data(data_dir: Path) -> None:
    """Copy data from the pre-rename plugin id when the new data dir is empty."""
    try:
        legacy_dir = StarTools.get_data_dir(LEGACY_PLUGIN_ID)
        if legacy_dir == data_dir or not legacy_dir.is_dir():
            return
        if any(data_dir.iterdir()):
            return
        shutil.copytree(legacy_dir, data_dir, dirs_exist_ok=True)
        logger.info(
            "[虚拟人生] 已从旧插件标识迁移数据目录 %s -> %s",
            legacy_dir,
            data_dir,
        )
    except Exception as exc:
        logger.warning("[虚拟人生] 旧插件数据迁移失败: %s", exc)


def _frontend_ui_version() -> str:
    try:
        text = (
            PLUGIN_ROOT.joinpath("views")
            .joinpath("life", "index.html")
            .read_text(encoding="utf-8")
        )
        match = re.search(r"app\.js\?v=([^\"'&<>]+)", text)
        return match.group(1).strip() if match else "未知"
    except Exception:
        logger.debug("[虚拟人生] _frontend_ui_version 出错，已忽略", exc_info=True)
        return "未知"
