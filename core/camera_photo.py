"""观察窗相机：根据用户拍到的目标 + 当前虚拟人生状态生成照片。

提示词的拼装在 ``camera_prompt``；这里负责调用绘图接口和处理返回的图片。
"""

from __future__ import annotations

import base64
import logging
import mimetypes
from pathlib import Path
from typing import Any

import aiohttp

# re-exported for callers that still use camera_photo.<name>
from .camera_prompt import (  # noqa: F401
    ACTIVITY_EN,
    ANIME_STYLE,
    COMFY_PROXY_URL,
    DEFAULT_CHARACTER,
    DEFAULT_CHARACTER_PROMPT,
    DEFAULT_NEGATIVE_PROMPT,
    DEFAULT_STYLE_PROMPT,
    ITEM_EN,
    OUTDOOR_MARKERS,
    OUTDOOR_SCENES,
    OUTFIT_EN,
    ROOM_EN,
    ROOM_ENV_EN,
    TARGET_CHARACTER,
    TARGET_ITEM,
    TARGET_ROOM,
    _at_home,
    _clean,
    _english_activity,
    _english_item_name,
    _english_outfit,
    _english_pose,
    _english_room,
    _english_room_name,
    _english_time_light,
    _english_weather,
    _furniture_environment,
    _is_bathing,
    _is_napping,
    _is_outdoor,
    _is_sleeping,
    _is_workout,
    _item_description_for_weather,
    _outdoor_context,
    _scene_from_snapshot_location,
    _snapshot_is_home,
    _time_negative_prompt,
    _time_period,
    build_anime_prompt,
    build_anime_scene_prompt,
    build_environment,
    build_prompt,
    camera_settings,
    compose_style_prompt,
    persona_visual_from_prompt,
    pose_hint_for_snapshot,
)

logger = logging.getLogger("astrbot")


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
            logger.debug("[虚拟人生] _materialize_image 出错，已忽略", exc_info=True)
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
            logger.debug("[虚拟人生] _generate_via_proxy 出错，已忽略", exc_info=True)
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
    return {
        "ok": False,
        "error": "相机显影失败，请检查插件相机设置里的绘图接口、模型和提示词",
    }
