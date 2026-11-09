from __future__ import annotations

import json
import re
from datetime import datetime

from astrbot.api import logger
from astrbot.core.agent.message import (
    AssistantMessageSegment,
    TextPart,
    UserMessageSegment,
)

from .human_style import CURRENT_STATE_RULE, HUMAN_PROACTIVE_RULE
from .persona import PersonaContext


class ProactiveMessageGenerator:
    def __init__(self, context, config):
        self.context = context
        self.config = config

    async def generate(
        self,
        *,
        umo: str,
        persona: PersonaContext,
        current_time: datetime,
        current_state: str,
        intent: str,
        unanswered_count: int,
        relationship_context: str = "",
        timeline_context: str = "",
        recent_sent: list[str] | None = None,
        retry_note: str = "",
        decide: bool = False,
        include_history: bool = True,
        group_mode: bool = False,
    ) -> str:
        settings = self.config.get("delivery_settings", {}) or {}
        template = str(settings.get("proactive_prompt", ""))
        unanswered_hint = self._build_unanswered_hint(settings, unanswered_count)
        task_prompt = template.format(
            current_time=current_time.strftime("%Y-%m-%d %H:%M"),
            current_state=current_state,
            intent=intent,
            unanswered_count=unanswered_count,
            unanswered_hint=unanswered_hint,
        )
        history = (
            await self._recent_history(
                umo, int(settings.get("recent_chat_messages", 8))
            )
            if include_history
            else "无"
        )
        prompt = (
            f"<persona>\n{persona.prompt}\n</persona>\n\n"
            f"<recent_conversation>\n{history}\n</recent_conversation>\n\n{task_prompt}"
            + HUMAN_PROACTIVE_RULE
        )
        if history and history.strip() != "无":
            prompt += (
                "\n\n【衔接要求】上面是你们最近的对话：如果最后几轮里对方说了具体的事"
                "（在忙什么、刚聊到的话题、提到的东西），优先接着那件事说；"
                "不要凭空开一个和上文无关的新话题，也不要重复你上一次主动说过的状态。"
            )
        if recent_sent:
            prompt += (
                "\n\n<recent_proactive>\n你最近已经主动说过的话（不要重复这些内容、场景和句式）：\n"
                + "\n".join(f"- {line}" for line in recent_sent[:8])
                + "\n</recent_proactive>\n"
                "这次必须换一个真正的角度：不要复述同一件家务、同一个动作、同一个数字、同一种比喻；"
                "如果上面最近几条都属于同一个主题或同一个场景（例如都在说起床、早饭、换衣服、天气、出门），"
                "这次不要再用同类问候、同一种开场和收尾，必须换成一个完全不同的主题或由头；"
                "可以聊对方的事、刚发生的小变化、一件具体的见闻，或者一件新进展；"
                "如果实在没有新的东西可说，就保持沉默。"
            )
        if retry_note:
            prompt += "\n\n【重写要求】" + retry_note
        if decide:
            prompt += (
                "\n\n【先决定要不要开口】这次不是必须说话。先掂量此刻开口是否自然："
                "对方刚说完话/正在聊天、你正忙或专注、刚主动说过、没什么具体由头时，"
                "就应该选择不说；只有真的想说（有具体的事、确实想他、有明确由头）才开口。"
                "不要为了刷存在感而说话。"
                '只输出 JSON：{"decision":"send" 或 "silent",'
                '"reason":"一句话理由","text":"要说的话，silent 时留空"}'
            )
            if group_mode:
                prompt += (
                    "\n\n【群聊补充】这是群聊，不是一对一私聊。群聊安静、没人接话时，"
                    "可以更主动地打破冷场：有具体见闻、想分享的小事、或一句自然的吐槽，"
                    "就优先选择 send；不要因为怕打扰而习惯性沉默，也不要为了活跃而硬开话题。"
                )
        if timeline_context:
            prompt += "\n\n" + timeline_context
            illness_hint = self.illness_hint(timeline_context)
            if illness_hint:
                prompt += "\n\n" + illness_hint
            weather_hint = self.weather_hint(timeline_context)
            if weather_hint:
                prompt += "\n\n" + weather_hint
            rain_hint = self.rain_hint(timeline_context)
            if rain_hint:
                prompt += "\n\n" + rain_hint
            sunny_hint = self.sunny_hint(timeline_context)
            if sunny_hint:
                prompt += "\n\n" + sunny_hint
            season_hint = self.season_hint(timeline_context)
            if season_hint:
                prompt += "\n\n" + season_hint
            social_hint = self.social_hint(timeline_context)
            if social_hint:
                prompt += "\n\n" + social_hint
            thirst_hint = self.thirst_hint(timeline_context)
            if thirst_hint:
                prompt += "\n\n" + thirst_hint
            hangover_hint = self.hangover_hint(timeline_context)
            if hangover_hint:
                prompt += "\n\n" + hangover_hint
            tipsy_hint = self.tipsy_hint(timeline_context)
            if tipsy_hint:
                prompt += "\n\n" + tipsy_hint
            stress_hint = self.stress_hint(timeline_context)
            if stress_hint:
                prompt += "\n\n" + stress_hint
            afterglow_hint = self.afterglow_hint(timeline_context)
            if afterglow_hint:
                prompt += "\n\n" + afterglow_hint
            appetite_hint = self.appetite_hint(timeline_context)
            if appetite_hint:
                prompt += "\n\n" + appetite_hint
            eye_hint = self.eye_hint(timeline_context)
            if eye_hint:
                prompt += "\n\n" + eye_hint
            heat_hint = self.heat_hint(timeline_context)
            if heat_hint:
                prompt += "\n\n" + heat_hint
            stomach_hint = self.stomach_hint(timeline_context)
            if stomach_hint:
                prompt += "\n\n" + stomach_hint
            late_meal_hint = self.late_meal_hint(timeline_context)
            if late_meal_hint:
                prompt += "\n\n" + late_meal_hint
            breakfast_hint = self.breakfast_hint(timeline_context)
            if breakfast_hint:
                prompt += "\n\n" + breakfast_hint
            commute_hint = self.commute_hint(timeline_context)
            if commute_hint:
                prompt += "\n\n" + commute_hint
            dehydration_hint = self.dehydration_hint(timeline_context)
            if dehydration_hint:
                prompt += "\n\n" + dehydration_hint
            nap_hint = self.nap_hint(timeline_context)
            if nap_hint:
                prompt += "\n\n" + nap_hint
            music_hint = self.music_hint(timeline_context)
            if music_hint:
                prompt += "\n\n" + music_hint
            temperature_hint = self.temperature_hint(timeline_context)
            if temperature_hint:
                prompt += "\n\n" + temperature_hint
            lunch_hint = self.lunch_hint(timeline_context)
            if lunch_hint:
                prompt += "\n\n" + lunch_hint
            meal_time_hint = self.meal_time_hint(timeline_context)
            if meal_time_hint:
                prompt += "\n\n" + meal_time_hint
            reading_hint = self.reading_hint(timeline_context)
            if reading_hint:
                prompt += "\n\n" + reading_hint
            instrument_hint = self.instrument_hint(timeline_context)
            if instrument_hint:
                prompt += "\n\n" + instrument_hint
            cooking_hint = self.cooking_hint(timeline_context)
            if cooking_hint:
                prompt += "\n\n" + cooking_hint
            tooth_hint = self.tooth_hint(timeline_context)
            if tooth_hint:
                prompt += "\n\n" + tooth_hint
            movie_hint = self.movie_hint(timeline_context)
            if movie_hint:
                prompt += "\n\n" + movie_hint
            hygiene_hint = self.hygiene_hint(timeline_context)
            if hygiene_hint:
                prompt += "\n\n" + hygiene_hint
            cozy_hint = self.cozy_hint(timeline_context)
            if cozy_hint:
                prompt += "\n\n" + cozy_hint
            stiff_hint = self.stiff_hint(timeline_context)
            if stiff_hint:
                prompt += "\n\n" + stiff_hint
            overtraining_hint = self.overtraining_hint(timeline_context)
            if overtraining_hint:
                prompt += "\n\n" + overtraining_hint
            monday_hint = self.monday_hint(timeline_context)
            if monday_hint:
                prompt += "\n\n" + monday_hint
            solitude_hint = self.solitude_hint(timeline_context)
            if solitude_hint:
                prompt += "\n\n" + solitude_hint
            social_hangover_hint = self.social_hangover_hint(timeline_context)
            if social_hangover_hint:
                prompt += "\n\n" + social_hangover_hint
            wind_down_hint = self.wind_down_hint(timeline_context)
            if wind_down_hint:
                prompt += "\n\n" + wind_down_hint
            soreness_hint = self.soreness_hint(timeline_context)
            if soreness_hint:
                prompt += "\n\n" + soreness_hint
            sedentary_hint = self.sedentary_hint(timeline_context)
            if sedentary_hint:
                prompt += "\n\n" + sedentary_hint
            afternoon_hint = self.afternoon_dip_hint(timeline_context)
            if afternoon_hint:
                prompt += "\n\n" + afternoon_hint
            morning_hint = self.morning_grogginess_hint(timeline_context)
            if morning_hint:
                prompt += "\n\n" + morning_hint
            evening_hint = self.evening_sleepiness_hint(timeline_context)
            if evening_hint:
                prompt += "\n\n" + evening_hint
        if relationship_context:
            prompt += "\n\n" + relationship_context
        if timeline_context:
            prompt += CURRENT_STATE_RULE
        schedule_settings = self.config.get("schedule_settings", {}) or {}
        provider_id = str(schedule_settings.get("proactive_llm_provider") or "").strip()
        provider = self.context.get_provider_by_id(provider_id) if provider_id else None
        provider = provider or self.context.get_using_provider()
        if not provider:
            raise RuntimeError("no LLM provider available")
        response = await provider.text_chat(prompt, session_id=f"proactive_message::{umo}")
        for key in ("completion_text", "completion", "text", "content"):
            value = getattr(response, key, None)
            if not isinstance(value, str) or not value.strip():
                continue
            raw = value.strip()
            if not decide:
                return raw
            payload = self.parse_decision(raw)
            if not payload:
                return raw
            if payload["decision"] != "send":
                logger.info(
                    "[虚拟人生] 这次决定不开口 umo=%s 理由=%s",
                    umo,
                    payload["reason"] or "无",
                )
                return ""
            return payload["text"].strip()
        raise RuntimeError("LLM returned empty proactive message")

    @staticmethod
    def weather_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in (
                "坏天气",
                "阴雨",
                "下雨",
                "小雨",
                "中雨",
                "大雨",
                "暴雨",
                "温差",
                "降温",
                "风大",
            )
        ):
            return ""
        return (
            "【天气影响】最近天气不太好，语气可以安静、慵懒一点，"
            "不要约对方去户外或远的地方；可以聊天气、宅在家的小事，"
            "或者轻轻提醒对方带伞、别着凉。"
        )

    @staticmethod
    def evening_sleepiness_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "这个点有点困了" not in text and "想早点睡" not in text:
            return ""
        return (
            "【晚上困了】这个点你有点困了。主动消息可以短一点、语气软一点，"
            "适合说想早点洗澡睡觉、想安静下来；不要约熬夜或继续玩。"
        )

    @staticmethod
    def morning_grogginess_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "昨晚没睡够" not in text and "早上有点懵" not in text:
            return ""
        return (
            "【早上没睡醒】你昨晚没睡够，早上有点懵。主动消息可以慢一点、"
            "短一点，适合说想喝点热水、想缓一缓；不要约早起高强度活动。"
        )

    @staticmethod
    def afternoon_dip_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "午后有点犯困" not in text:
            return ""
        return (
            "【午后犯困】你午后有点犯困，效率不太高。主动消息可以短一点、"
            "语气懒一点，适合说想喝点水、想活动一下或想早点休息；"
            "不要约高强度活动。"
        )

    @staticmethod
    def sedentary_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("没怎么运动", "身体有点发懒", "久坐")
        ):
            return ""
        return (
            "【久坐状态】你最近一周都没怎么运动，身体有点发懒。"
            "主动消息可以提想站起来走走、伸个懒腰、晒晒太阳；"
            "不要一开口就约高强度运动，先从轻活动开始。"
        )

    @staticmethod
    def soreness_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("腿有点酸", "昨天运动完", "腿没那么酸")
        ):
            return ""
        return (
            "【运动酸痛】你昨天运动完，今天腿有点酸。主动消息可以提想泡热水澡、"
            "拉伸一下、少走动；不要约跑步、爬山或高强度运动，也别硬撑着说没事。"
        )

    @staticmethod
    def wind_down_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "晚上有点难入睡" not in text and "聊得太兴奋" not in text:
            return ""
        return (
            "【社交后难入睡】你聊得太兴奋，晚上有点睡不着。主动消息可以"
            "说想洗个热水澡、听会儿轻音乐、早点安静下来；不要约继续聊天。"
        )

    @staticmethod
    def social_hangover_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "昨天聊太久" not in text and "还没缓过来" not in text:
            return ""
        return (
            "【社交后劲】你昨天聊得太久，今天还有点没缓过来。主动消息可以"
            "短一点、少约活动；适合说今天想静一静、还没回血。"
        )

    @staticmethod
    def solitude_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "社交电量用完" not in text and "想一个人待会儿" not in text:
            return ""
        return (
            "【社交电量】你今天聊了很久，社交电量用完了。主动消息可以短一点，"
            "说想安静待会儿、想回家；不要约下一场社交。"
        )

    @staticmethod
    def monday_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "周一又要上班" not in text and "提不起劲" not in text:
            return ""
        return (
            "【周一状态】你今天有点周一低落，提不起劲。主动消息可以短一点、"
            "语气懒一点；适合说不想上班、想再歇一天，但不用一直抱怨。"
        )

    @staticmethod
    def overtraining_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("运动量有点大", "练得太狠", "练太猛", "肌肉有点发酸")
        ):
            return ""
        return (
            "【运动过量】你今天练得有点狠，肌肉发酸。主动消息可以提想休息、"
            "想拉伸放松；不要约继续高强度训练。"
        )

    @staticmethod
    def stiff_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in (
                "肩颈有点发僵",
                "肩颈发僵",
                "睡不安稳",
                "昨天久坐没活动",
                "今天肩颈还紧",
            )
        ):
            return ""
        return (
            "【肩颈发僵】你坐太久没活动，肩颈有点僵。主动消息可以提想站起来"
            "拉伸、想活动一下；不要约继续久坐或高强度运动。"
        )

    @staticmethod
    def cozy_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "香薰、轻音乐和热茶" not in text and "睡意来得更快" not in text:
            return ""
        return (
            "【睡前三件套】你现在香薰、轻音乐、热茶配着书，整个人很松。"
            "主动消息可以很轻、很短，适合说有点困了、想早点睡；不要约熬夜。"
        )

    @staticmethod
    def hygiene_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "身上有点味道" not in text:
            return ""
        return (
            "【身上有味道】你觉得自己身上有点味道，不太想凑近人。"
            "主动消息可以提想先洗澡、换衣服；不要约见面或出门社交。"
        )

    @staticmethod
    def movie_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "昨晚电影看太晚" in text:
            return (
                "【昨晚看太晚】你昨晚电影看太晚，今天有点困。主动消息可以"
                "短一点、慢一点；不要约今天再熬夜看片。"
            )
        if "电影看得有点晚" in text or "睡意被拖后" in text:
            return (
                "【晚场电影】电影看得有点晚，睡意被拖后了。主动消息可以提"
                "想喝水、想早点睡；不要约下一部或熬夜刷剧。"
            )
        if "爆米花" in text and "渴" in text:
            return (
                "【爆米花口渴】爆米花有点咸，嘴里发渴。主动消息可以提"
                "想喝水、想泡杯茶；不要继续吃咸的。"
            )
        return ""

    @staticmethod
    def tooth_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("牙有点酸", "牙齿有点吃不消", "吃甜食没刷牙")
        ):
            return ""
        return (
            "【牙齿不适】你最近甜食吃多了，牙齿有点酸。主动消息可以提想刷牙、"
            "想少吃点甜的；不要约奶茶蛋糕或夜宵。"
        )

    @staticmethod
    def cooking_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("自己做了顿饭", "烤了点甜点", "满屋香味")
        ):
            return ""
        return (
            "【下厨】你自己做了饭/烤了甜点，心情不错。主动消息可以提想拍照"
            "分享、想让人尝尝；语气可以带点小得意，但不要报数值。"
        )

    @staticmethod
    def instrument_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "弹了会儿琴" not in text and "工作上的烦心事淡了点" not in text:
            return ""
        return (
            "【练琴放松】你刚弹了会儿琴，心情松下来一些。主动消息可以轻一点，"
            "适合分享刚弹的曲子或说手指有点酸；不要马上又安排高强度工作。"
        )

    @staticmethod
    def reading_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "快歌有点分心" in text:
            return (
                "【看书分心】你快歌有点吵，书没看进去。主动消息可以提想换首"
                "轻音乐或干脆关掉；语气可以有点无奈。"
            )
        if "看书看太久" in text:
            return (
                "【看书久了】你看书看太久，眼睛有点酸。主动消息可以提想合上书"
                "歇一会儿、看看远处；不要约继续长时间用眼。"
            )
        if "看了会儿书" in text:
            return (
                "【看书放松】你刚看了会儿书，心静下来了。主动消息可以轻一点，"
                "适合说想早点睡或想再翻几页。"
            )
        return ""

    @staticmethod
    def meal_time_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "吃饭时间忽早忽晚" not in text and "饭点太乱" not in text:
            return ""
        return (
            "【饭点乱】你最近吃饭时间忽早忽晚，肠胃有点不适应。"
            "主动消息可以提想吃点热的、想固定饭点、想早点吃晚饭；"
            "不要约夜宵或重口。"
        )

    @staticmethod
    def lunch_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("没吃午饭", "下午有点饿", "下午总有点虚")
        ):
            return ""
        return (
            "【没吃午饭】你今天错过了午饭，下午有点饿。主动消息可以提想找点吃的、"
            "想喝点热的垫一下；不要硬撑到晚上，也别约太费体力的活动。"
        )

    @staticmethod
    def temperature_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "晚上温度不太舒服" not in text:
            return ""
        return (
            "【夜间温度】晚上温度不太舒服，你睡得有点沉不下去。"
            "主动消息可以提想开空调/风扇、想加床被子、想早点调好房间温度；"
            "不要约熬夜或出门吹风。"
        )

    @staticmethod
    def music_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "睡前听了快歌" in text:
            return (
                "【睡前音乐】你刚听了快歌，人有点兴奋。主动消息可以提想听点"
                "轻音乐缓缓、想早点静下来；不要约继续嗨或熬夜。"
            )
        if "睡前听了会儿音乐" in text:
            return (
                "【睡前音乐】你听了会儿音乐，人放松下来了。主动消息语气可以"
                "轻一点、慢一点，适合说困了或想早点睡。"
            )
        return ""

    @staticmethod
    def nap_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("午睡睡太久", "起来有点懵", "人清醒一点")
        ):
            return ""
        return (
            "【午睡后】你午睡睡久了，刚起来有点懵。主动消息可以慢一点，"
            "说想洗把脸、喝口水、缓一缓；不要马上安排费脑子或剧烈活动。"
        )

    @staticmethod
    def dehydration_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("水喝太少了", "嘴巴很干", "头有点疼", "有点口渴")
        ):
            return ""
        return (
            "【缺水状态】你今天水喝得太少，有点口渴甚至头疼。主动消息可以提想喝水、"
            "喝温水；不要硬撑着，也不要约剧烈运动。"
        )

    @staticmethod
    def commute_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("通勤约", "路上有点累", "通勤有点久")
        ):
            return ""
        return (
            "【通勤疲劳】你今天路上折腾得有点久，人有点累。主动消息可以提想歇一会儿、"
            "想早点到家；不要约再跑远路或安排紧凑的下一场。"
        )

    @staticmethod
    def breakfast_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("没吃早饭", "上午有点没力气", "上午总有点虚")
        ):
            return ""
        return (
            "【没吃早饭】你今天没吃早饭，上午有点虚。主动消息可以提想找点吃的、"
            "喝点热的；不要硬撑到中午，也不要约太费体力的活动。"
        )

    @staticmethod
    def late_meal_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("睡前吃夜宵", "胃有点胀", "吃了夜宵")
        ):
            return ""
        return (
            "【夜宵影响】你睡前吃了夜宵，胃有点胀。主动消息可以提想站起来走走、"
            "喝点温水、晚点再躺；不要约继续吃夜宵或喝酒。"
        )

    @staticmethod
    def stomach_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("胃里有点烧", "吃得太重口", "胃里好受一些")
        ):
            return ""
        return (
            "【肠胃不适】你吃得太重口，胃里有点烧。主动消息可以提想喝粥、"
            "喝温水、吃点清淡的；不要约火锅、烧烤、酒或夜宵。"
        )

    @staticmethod
    def heat_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in (
                "太阳有点毒",
                "晒得头有点晕",
                "有点中暑",
                "中暑刚缓",
                "怕晒",
                "肩膀被晒得有点红",
                "昨天晒伤",
                "还红着",
            )
        ):
            return ""
        return (
            "【高温暴晒】你被太阳晒得有点晕，可能还有点缺水。主动消息短一点，"
            "可以说想躲阴凉、想喝水、想早点回家；不要约中午出门或户外运动。"
        )

    @staticmethod
    def eye_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("眼睛有点酸", "盯屏幕久了", "眼睛舒服一点")
        ):
            return ""
        return (
            "【用眼疲劳】你盯屏幕有点久，眼睛发酸。主动消息短一点，"
            "可以说想闭眼休息、想看看远处、想站起来走走；"
            "不要约继续打游戏或刷剧。"
        )

    @staticmethod
    def appetite_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("没什么胃口", "吃几口就饱", "胃口稍微好一点")
        ):
            return ""
        return (
            "【胃口状态】你现在胃口不太好，主动消息短一点；"
            "可以提想吃点粥、汤或清淡的，不要约火锅、烧烤、酒或重口味。"
            "如果已经吃了点粥汤，语气可以松一点，别一直说吃不下。"
        )

    @staticmethod
    def afterglow_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("昨天和人聊过天", "心情还留着一点暖")
        ):
            return ""
        return (
            "【社交余温】你昨天和人聊得还不错，今天心情还留着一点暖。"
            "可以自然地提起昨天聊过的一件小事，或者轻轻分享一个今天的细节；"
            "不要刻意煽情，也不要重复昨天说过的话。"
        )

    @staticmethod
    def stress_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("工作有点久", "加班", "肩颈发紧", "脑子也累了", "工作压力")
        ):
            return ""
        return (
            "【工作疲惫】你今天工作很久，语气可以有点累，但不要长篇抱怨。"
            "可以说想休息、想喝点热的、想找人聊两句；不要约高强度活动，"
            "也不要硬撑着说自己没事。"
        )

    @staticmethod
    def tipsy_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if "微醺" not in text:
            return ""
        return (
            "【微醺状态】你现在有点微醺，话可以比平时多一点、软一点，"
            "可以分享一件小事或说真心话；但不要鼓励对方喝酒，也不要开车或出门冒险。"
        )

    @staticmethod
    def hangover_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in (
                "宿醉",
                "昨晚喝了酒",
                "昨晚喝了点酒",
                "今天头有点沉",
                "头很沉",
                "喝得有点多",
            )
        ):
            return ""
        if any(marker in text for marker in ("头很沉", "喝得有点多", "重度")):
            return (
                "【重度宿醉】你现在宿醉得很厉害，主动消息要非常短、很虚弱，"
                "可以直接说头沉、想躺着、想喝水；不要聊天太久，不要约任何事，"
                "也不要逞强说自己没事。"
            )
        if "好受一些" in text:
            return (
                "【宿醉缓解】你喝了水、吃了点东西，宿醉缓过来一点。"
                "语气可以稍微回暖，愿意正常聊几句，但不要约酒或重口味，"
                "也不用一直强调自己不舒服。"
            )
        return (
            "【轻度宿醉】你昨晚喝了点酒，今天有点没精神，主动消息短一点、慢一点，"
            "可以提到想喝水、吃清淡的；不要约喝酒或重口味，也不用反复解释自己喝多了。"
        )

    @staticmethod
    def thirst_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(marker in text for marker in ("口渴", "嘴巴很干", "想喝水")):
            return ""
        return (
            "【口渴状态】你现在有点缺水，可以提到想喝水、嘴巴干，"
            "主动消息短一点，不要约吃重口或喝酒；顺手喝杯水会更舒服。"
        )

    @staticmethod
    def social_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("没怎么和人说话", "很久没和人", "有点闷")
        ):
            return ""
        return (
            "【孤独状态】你最近有点闷，想和人说话。可以主动一点，"
            "但不要一次倒太多情绪；可以轻轻问对方在做什么，"
            "或者说一句“最近有点安静”，不要强行卖惨。"
        )

    @staticmethod
    def season_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if any(marker in text for marker in ("冬天", "冬季")):
            return (
                "【冬季影响】现在是冬天，语气可以更想宅家、喝热饮、注意保暖，"
                "不要约对方去太远或太冷的地方；可以聊热汤、被窝、窗外的天色。"
            )
        if any(marker in text for marker in ("夏天", "夏季")):
            return (
                "【夏季影响】现在是夏天，语气可以轻快一点，可以提冷饮、空调、"
                "傍晚散步，但避免约对方中午暴晒或长时间户外。"
            )
        return ""

    @staticmethod
    def rain_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("淋得有点狼狈", "没带伞", "衣服湿了", "洗了热水澡")
        ):
            return ""
        if "洗了热水澡" in text or "暖和过来了" in text:
            return (
                "【淋雨恢复】你刚淋了雨，但已经洗了热水澡或喝了热茶，缓过来一点。"
                "语气可以从狼狈转成松一口气，可以说“总算暖和了”，"
                "顺手提醒对方雨天带伞；不要一直抱怨。"
            )
        return (
            "【淋雨状态】你刚在坏天气里淋了一阵，可以有点狼狈地抱怨一句"
            "没带伞、衣服湿了，想赶紧回去换衣服或泡热水澡，但不要夸张卖惨；"
            "也可以顺手提醒对方出门带伞。"
        )

    @staticmethod
    def sunny_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("天气不错", "晴天")
        ):
            return ""
        return (
            "【好天气影响】最近天气很好，语气可以轻快一点，"
            "可以提晒太阳、散步、公园、开窗通风这类小事；"
            "但不要每句都聊天气，也不要强行邀约。"
        )

    @staticmethod
    def illness_hint(timeline_context: str) -> str:
        text = str(timeline_context or "")
        if not any(
            marker in text
            for marker in ("生病中", "生病第", "恢复期", "恢复中", "症状：", "病程第", "养病记录", "刚退烧")
        ):
            return ""
        if "刚退烧" in text:
            return (
                "【退烧恢复】你刚退烧，身体还虚，胃口也没完全回来。"
                "主动消息要短、慢、轻，可以说想喝点粥、想吃清淡的，"
                "不要约运动或出门，也不要硬撑着说自己好了。"
            )
        if "发烧" in text:
            return (
                "【发烧状态】你现在在发烧，主动消息要非常短、虚弱、慢一点；"
                "不要逞强，不要约出门或运动，也不要报数值。可以只说想躺着、"
                "想喝水、想喝点粥，或轻轻说一句“今天有点没力气”。"
            )
        return (
            "【生病/恢复期要求】你现在身体不舒服或还在恢复。主动消息要短、轻、慢，"
            "语气可以有点虚弱；不要约对方出门、运动或聚会，不要逞强，也不要报身体数值。"
            "可以只说身体感受、想安静休息，或轻轻问一句对方在做什么。"
        )

    @staticmethod
    def parse_decision(raw: str) -> dict:
        """解析「要不要开口」的 JSON；解析失败返回空字典。"""
        match = re.search(r"\{.*\}", str(raw or ""), re.S)
        if not match:
            return {}
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        decision = str(data.get("decision") or "").strip().lower()
        if decision not in {"send", "silent", "skip", "no", "yes"}:
            return {}
        return {
            "decision": "send" if decision in {"send", "yes"} else "silent",
            "reason": str(data.get("reason") or "").strip()[:120],
            "text": str(data.get("text") or "").strip(),
        }

    @staticmethod
    def _build_unanswered_hint(settings: dict, count: int) -> str:
        method = str(
            settings.get("unanswered_hint_method", "segmented") or "segmented"
        ).strip().lower()
        if method == "placeholder":
            placeholder = str(
                settings.get("unanswered_hint_placeholder_template", "") or ""
            ).strip()
            if placeholder:
                try:
                    return placeholder.format(unanswered_count=max(0, int(count)))
                except (KeyError, IndexError, ValueError, TypeError):
                    return ""
            return ""
        return ProactiveMessageGenerator._parse_unanswered_hint(
            settings.get("unanswered_hint_template", ""), count
        )

    @staticmethod
    def _parse_unanswered_hint(template: object, count: int) -> str:
        """Parse a segmented unanswered hint template.

        Every line has the form ``<threshold>: <text>`` and applies when the
        unanswered count is at least ``threshold``. The segment with the largest
        threshold not exceeding the count wins; unparseable or empty templates
        produce an empty hint.
        """
        try:
            count = max(0, int(count))
        except (TypeError, ValueError):
            count = 0
        segments: list[tuple[int, str]] = []
        for line in str(template).splitlines():
            match = re.match(r"^\s*(\d+)\s*[:：]\s*(.+?)\s*$", line)
            if not match:
                continue
            text = match.group(2).strip()
            if text:
                segments.append((int(match.group(1)), text))
        if not segments:
            return ""
        segments.sort(key=lambda item: item[0])
        selected = ""
        for threshold, text in segments:
            if threshold <= count:
                selected = text
            else:
                break
        return selected

    async def record_conversation(
        self,
        *,
        umo: str,
        persona_id: str,
        intent: str,
        assistant_text: str,
    ) -> bool:
        manager = self.context.conversation_manager
        try:
            conversation_id = await manager.get_curr_conversation_id(umo)
            if not conversation_id:
                conversation_id = await manager.new_conversation(umo, persona_id=persona_id)
            if not conversation_id:
                logger.warning("[虚拟人生] 主动消息未写入上下文：无法创建对话 umo=%s", umo)
                return False
            user_message = UserMessageSegment(content=[TextPart(text=self._history_note(intent))])
            assistant_message = AssistantMessageSegment(content=[TextPart(text=assistant_text)])
            await manager.add_message_pair(
                cid=conversation_id,
                user_message=user_message,
                assistant_message=assistant_message,
            )
            logger.info("[虚拟人生] 主动消息已写入对话上下文 umo=%s conversation=%s", umo, conversation_id)
            return True
        except Exception as exc:
            logger.error("[虚拟人生] 主动消息写入对话上下文失败 umo=%s: %s", umo, exc)
            return False

    def _history_note(self, intent: str) -> str:
        settings = self.config.get("delivery_settings", {}) or {}
        template = str(settings.get("proactive_history_note_template", "")).strip()
        default = f"（你主动发起的消息）\n背景：{intent}"
        if not template:
            return default
        try:
            return template.format(intent=intent)
        except (KeyError, IndexError, ValueError):
            return default

    async def recent_proactive_texts(self, umo: str, limit: int = 5) -> list[str]:
        """取最近几条「你主动发起的消息」正文，按时间从新到旧。"""
        if limit <= 0:
            return []
        try:
            manager = self.context.conversation_manager
            conversation_id = await manager.get_curr_conversation_id(umo)
            if not conversation_id:
                return []
            conversation = await manager.get_conversation(umo, conversation_id)
            raw = getattr(conversation, "history", "[]")
            history = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(history, list):
                return []
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("[虚拟人生] 读取主动消息历史失败 %s: %s", umo, exc)
            return []
        texts: list[str] = []
        previous_user = ""
        for item in history:
            if not isinstance(item, dict):
                continue
            role = item.get("role", "")
            content = item.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    str(part.get("text", ""))
                    for part in content
                    if isinstance(part, dict) and part.get("type") == "text"
                )
            text = str(content or "").strip()
            if role == "user":
                previous_user = text
                continue
            if role == "assistant":
                if previous_user.startswith("（你主动发起的消息）") and text:
                    texts.append(text)
                previous_user = ""
        return list(reversed(texts[-limit:]))

    async def _recent_history(self, umo: str, count: int) -> str:
        if count <= 0:
            return "无"
        try:
            conversation_id = await self.context.conversation_manager.get_curr_conversation_id(umo)
            if not conversation_id:
                return "无"
            conversation = await self.context.conversation_manager.get_conversation(umo, conversation_id)
            raw = getattr(conversation, "history", "[]")
            history = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(history, list):
                return "无"
            lines = []
            for item in history[-count:]:
                if not isinstance(item, dict):
                    continue
                role = item.get("role", "unknown")
                content = item.get("content", "")
                if isinstance(content, list):
                    content = " ".join(
                        str(part.get("text", "")) for part in content if isinstance(part, dict) and part.get("type") == "text"
                    )
                lines.append(f"{role}: {content}")
            return "\n".join(lines) or "无"
        except Exception as exc:
            logger.debug("[虚拟人生] 读取历史失败 %s: %s", umo, exc)
            return "无"
