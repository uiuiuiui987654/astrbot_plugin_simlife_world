"""插件联动控制台：集中展示已安装插件与虚拟人生的接入状态。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# 只登记已知插件的展示信息；未知插件仍会自动出现在控制台里。
INTEGRATION_CATALOG: dict[str, dict[str, Any]] = {
    "astrbot_plugin_simlife_world": {
        "title": "虚拟人生",
        "emoji": "🏠",
        "category": "核心",
        "capabilities": ["日程", "家具", "拍照", "互动"],
        "note": "当前视图与生活模拟核心",
    },
    "astrbot_plugin_qzone": {
        "title": "QQ空间",
        "emoji": "🌌",
        "category": "社交",
        "capabilities": ["说说", "自动发布", "评论"],
        "note": "已接入调度看门狗，自动发说说不再静默停摆",
    },
    "astrbot_plugin_omnidraw": {
        "title": "OmniDraw",
        "emoji": "🎨",
        "category": "创作",
        "capabilities": ["绘图", "自拍", "视频"],
        "note": "虚拟人生自拍联动已启用，画面会读取当前活动与场景",
    },
    "astrbot_plugin_livingmemory": {
        "title": "LivingMemory",
        "emoji": "🧠",
        "category": "记忆",
        "capabilities": ["长期记忆", "回忆检索"],
        "note": "长期记忆能力，可与虚拟人生长期时间线配合",
    },
    "astrbot_plugin_proactive_chat": {
        "title": "Proactive Chat",
        "emoji": "💬",
        "category": "主动消息",
        "capabilities": ["主动问候", "定时消息"],
        "note": "与虚拟人生主动消息并行；请避免两套日程同时打扰",
    },
    "astrbot_plugin_bilibili_ai_bot": {
        "title": "B站 AI Bot",
        "emoji": "📺",
        "category": "社交",
        "capabilities": ["评论", "私信", "直播弹幕", "动态"],
        "note": "独立 B 站账号能力，可在插件页管理",
    },
    "astrbot_plugin_group_chat_plus": {
        "title": "群聊增强",
        "emoji": "👥",
        "category": "群聊",
        "capabilities": ["群聊增强", "上下文"],
        "note": "群聊行为增强；虚拟人生仍有群聊隐私规则",
    },
    "astrbot_plugin_qqprofile": {
        "title": "QQ资料",
        "emoji": "🪪",
        "category": "社交",
        "capabilities": ["资料查询", "头像"],
        "note": "QQ 资料与头像查询能力",
    },
    "meme_manager": {
        "title": "表情包管理",
        "emoji": "😼",
        "category": "媒体",
        "capabilities": ["表情包", "图片"],
        "note": "表情包素材库，可在聊天与媒体回复中使用",
    },
    "astrbot_plugin_media_reply_filter": {
        "title": "媒体回复过滤",
        "emoji": "🧹",
        "category": "媒体",
        "capabilities": ["媒体过滤", "回复清理"],
        "note": "清理媒体消息里的多余内容",
    },
    "astrbot_plugin_dafeiyu_clean": {
        "title": "文本清理",
        "emoji": "✨",
        "category": "文本",
        "capabilities": ["发送前清理"],
        "note": "清理模型偶发漏出的内部文本",
    },
    "astrbot_plugin_dafeiyu_signature": {
        "title": "签名",
        "emoji": "✍️",
        "category": "文本",
        "capabilities": ["个性签名"],
        "note": "发送签名 / 落款类内容",
    },
}

_CATALOG_ORDER = {name: index for index, name in enumerate(INTEGRATION_CATALOG)}


def _clean(value: Any, limit: int = 300) -> str:
    return str(value or "").strip()[:limit]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, TypeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _config_path(config_dir: Path, name: str, root_dir_name: str) -> Path | None:
    for stem in (name, root_dir_name):
        candidate = config_dir / f"{stem}_config.json"
        if candidate.is_file():
            return candidate
    return None


def _safe_config_summary(name: str, config: dict[str, Any]) -> dict[str, Any]:
    """只返回控制台展示用的安全摘要，不输出 token、cookie 或密钥。"""
    if name == "astrbot_plugin_qzone":
        trigger = config.get("trigger") if isinstance(config.get("trigger"), dict) else {}
        return {
            "publish_cron": _clean(trigger.get("publish_cron"), 60),
            "comment_cron": _clean(trigger.get("comment_cron"), 60),
            "publish_offset": trigger.get("publish_offset"),
        }
    if name == "astrbot_plugin_omnidraw":
        link = (
            config.get("virtual_life_link")
            if isinstance(config.get("virtual_life_link"), dict)
            else {}
        )
        return {
            "selfie_link": bool(link.get("enable", False)),
            "private_only": bool(link.get("private_only", False)),
            "cooldown_minutes": link.get("cooldown_minutes"),
            "max_per_day": link.get("max_per_day"),
        }
    if name == "astrbot_plugin_proactive_chat":
        for key in ("trigger_probability", "probability", "enable"):
            if key in config:
                return {key: config.get(key)}
    return {}


def _meta_value(meta: Any, key: str, default: Any = None) -> Any:
    return getattr(meta, key, default)


def _installed_plugin_dirs(plugin_dir: Path) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    try:
        directories = sorted(plugin_dir.iterdir())
    except OSError:
        return found
    for directory in directories:
        if not directory.is_dir():
            continue
        metadata_path = directory / "metadata.yaml"
        if not metadata_path.is_file():
            continue
        name = directory.name
        version = ""
        desc = ""
        try:
            for line in metadata_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("version:"):
                    version = line.split(":", 1)[1].strip().strip("\"'")
                elif line.startswith("desc:"):
                    desc = line.split(":", 1)[1].strip().strip("\"'")[:240]
        except OSError:
            continue
        found[name] = {
            "name": name,
            "root_dir_name": name,
            "display_name": name,
            "version": version,
            "desc": desc,
            "activated": False,
            "reserved": False,
            "from_filesystem": True,
        }
    return found


def collect_integrations(plugin: Any) -> dict[str, Any]:
    """读取 AstrBot 已加载插件列表，并合并目录中尚未加载的插件。"""
    context = getattr(plugin, "context", None)
    metas: list[Any] = []
    if context is not None and hasattr(context, "get_all_stars"):
        try:
            metas = list(context.get_all_stars() or [])
        except Exception:
            metas = []

    data_dir = Path(getattr(plugin, "data_dir", "."))
    plugin_dir = data_dir.parent.parent / "plugins"
    config_dir = data_dir.parent.parent / "config"

    by_name: dict[str, dict[str, Any]] = {}
    for meta in metas:
        if bool(_meta_value(meta, "reserved", False)):
            continue
        name = _clean(_meta_value(meta, "name"), 120)
        if not name:
            continue
        root_dir_name = _clean(_meta_value(meta, "root_dir_name"), 120) or name
        catalog = INTEGRATION_CATALOG.get(name) or INTEGRATION_CATALOG.get(root_dir_name, {})
        item = {
            "name": name,
            "root_dir_name": root_dir_name,
            "display_name": _clean(_meta_value(meta, "display_name"), 80) or name,
            "version": _clean(_meta_value(meta, "version"), 40),
            "author": _clean(_meta_value(meta, "author"), 80),
            "desc": _clean(_meta_value(meta, "desc"), 240),
            "activated": bool(_meta_value(meta, "activated", True)),
            "reserved": bool(_meta_value(meta, "reserved", False)),
            "title": catalog.get("title") or name,
            "emoji": catalog.get("emoji", "🧩"),
            "category": catalog.get("category", "其他"),
            "capabilities": list(catalog.get("capabilities") or []),
            "note": catalog.get("note", "已安装的 AstrBot 插件"),
            "from_filesystem": False,
            "config_summary": {},
        }
        config_path = _config_path(config_dir, name, root_dir_name)
        if config_path is not None:
            item["config_present"] = True
            item["config_summary"] = _safe_config_summary(
                name, _read_json(config_path)
            )
        else:
            item["config_present"] = False
        by_name[name] = item

    for name, fallback in _installed_plugin_dirs(plugin_dir).items():
        if name in by_name:
            continue
        catalog = INTEGRATION_CATALOG.get(name, {})
        fallback.update(
            {
                "title": catalog.get("title") or name,
                "emoji": catalog.get("emoji", "🧩"),
                "category": catalog.get("category", "其他"),
                "capabilities": list(catalog.get("capabilities") or []),
                "note": catalog.get("note", "已安装但当前未加载"),
                "config_summary": {},
            }
        )
        config_path = _config_path(config_dir, name, name)
        fallback["config_present"] = config_path is not None
        by_name[name] = fallback

    def sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
        known = _CATALOG_ORDER.get(item.get("name") or "")
        if known is None:
            known = 999
        return (0 if item.get("activated") else 1, known, item.get("name") or "")

    items = sorted(by_name.values(), key=sort_key)
    active = sum(1 for item in items if item.get("activated"))
    return {
        "ok": True,
        "counts": {
            "total": len(items),
            "active": active,
            "inactive": len(items) - active,
        },
        "items": items,
    }
