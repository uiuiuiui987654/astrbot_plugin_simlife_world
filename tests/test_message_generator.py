"""Proactive message writing: provider choice, the "no reply yet" hint, and history records."""

import asyncio
import unittest
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from astrbot_plugin_simlife_world.core.message_generator import ProactiveMessageGenerator
from astrbot_plugin_simlife_world.core.persona import PersonaContext

FRIEND = "aiocqhttp:FriendMessage:42"
NOON = datetime(2026, 7, 14, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))


class Provider:
    def __init__(self):
        self.prompts = []

    async def text_chat(self, prompt, session_id):
        self.prompts.append(prompt)
        return SimpleNamespace(completion_text="主动消息")


class Conversations:
    def __init__(self, current=None):
        self.current, self.created, self.pairs = current, [], []

    async def get_curr_conversation_id(self, umo):
        return self.current

    async def new_conversation(self, umo, persona_id=None):
        self.created.append((umo, persona_id))
        self.current = "created-conversation"
        return self.current

    async def add_message_pair(self, **pair):
        self.pairs.append(pair)


class Context:
    def __init__(self, default=None, selected=None, conversations=None):
        self.default, self.selected, self.asked_for = default or Provider(), selected, []
        self.conversation_manager = conversations or Conversations()

    def get_provider_by_id(self, provider_id):
        self.asked_for.append(provider_id)
        return self.selected

    def get_using_provider(self):
        return self.default


def write(context, delivery=None, schedule=None, unanswered=0):
    config = {"delivery_settings": {"recent_chat_messages": 0, **(delivery or {})}, "schedule_settings": schedule or {}}
    return asyncio.run(
        ProactiveMessageGenerator(context, config).generate(
            umo=FRIEND,
            persona=PersonaContext("alice", "persona"),
            current_time=NOON,
            current_state="吃午饭",
            intent="分享午饭",
            unanswered_count=unanswered,
        )
    )


def record(conversations, delivery=None):
    generator = ProactiveMessageGenerator(Context(conversations=conversations), {"delivery_settings": delivery or {}})
    return asyncio.run(generator.record_conversation(umo=FRIEND, persona_id="alice", intent="分享午饭", assistant_text="今天的午饭很好吃。"))


def texts(pair):
    return [pair[key].model_dump()["content"][0]["text"] for key in ("user_message", "assistant_message")]


class Providers(unittest.TestCase):
    PROMPT = {"proactive_prompt": "{current_time} {current_state} {intent} {unanswered_count}"}

    def test_proactive_provider_is_separate_from_the_schedule_one(self):
        context = Context(selected=Provider())
        schedule = {"schedule_llm_provider": "schedule-provider", "proactive_llm_provider": "proactive-provider"}
        self.assertEqual(write(context, self.PROMPT, schedule), "主动消息")
        self.assertEqual(context.asked_for, ["proactive-provider"])
        self.assertEqual((len(context.selected.prompts), len(context.default.prompts)), (1, 0))

    def test_old_llm_provider_key_is_ignored(self):
        context = Context(selected=Provider())
        write(context, self.PROMPT, {"llm_provider": "legacy-provider"})
        self.assertEqual((context.asked_for, len(context.default.prompts)), ([], 1))


class UnansweredHint(unittest.TestCase):
    hint = staticmethod(ProactiveMessageGenerator._parse_unanswered_hint)
    build = staticmethod(ProactiveMessageGenerator._build_unanswered_hint)

    def test_threshold_lines(self):
        template = "0: 正常\n2: 收敛\n3: 明显收敛"
        for count, expected in ((0, "正常"), (1, "正常"), (2, "收敛"), (5, "明显收敛")):
            self.assertEqual(self.hint(template, count), expected)
        for template, count in (("", 2), ("2: 收敛", 0), ("不加数字的文本", 3)):
            self.assertEqual(self.hint(template, count), "")

    def test_methods(self):
        both = {"unanswered_hint_placeholder_template": "已连续 {unanswered_count} 次未回应", "unanswered_hint_template": "0: 正常\n3: 收敛"}
        self.assertEqual(self.build({**both, "unanswered_hint_method": "placeholder"}, 2), "已连续 2 次未回应")
        self.assertEqual(self.build({**both, "unanswered_hint_method": "segmented"}, 5), "收敛")
        self.assertEqual(self.build({"unanswered_hint_template": "0: 正常\n3: 收敛"}, 0), "正常")  # segmented by default
        self.assertEqual(self.build({}, 3), "")

    def test_hint_reaches_the_prompt(self):
        context = Context()
        write(context, {"proactive_prompt": "hint={unanswered_hint}", "unanswered_hint_template": "0: 正常热络\n2: 多次未回应，请收敛"}, unanswered=3)
        self.assertIn("多次未回应，请收敛", context.default.prompts[0])
        context = Context()
        write(context, {"proactive_prompt": "hint=[{unanswered_hint}]"}, unanswered=3)
        self.assertIn("hint=[]", context.default.prompts[0])


class History(unittest.TestCase):
    def test_pair_is_added_to_the_current_conversation(self):
        conversations = Conversations("conversation-1")
        self.assertTrue(record(conversations))
        (pair,) = conversations.pairs
        note, reply = texts(pair)
        self.assertEqual((pair["cid"], conversations.created, reply), ("conversation-1", [], "今天的午饭很好吃。"))
        self.assertIn("你自己主动发的", note)
        self.assertIn("分享午饭", note)
        self.assertNotIn("系统事件", note)

    def test_custom_note(self):
        conversations = Conversations("conversation-1")
        record(conversations, {"proactive_history_note_template": "（你想起关于{intent}的事）"})
        self.assertIn("你想起关于分享午饭的事", texts(conversations.pairs[0])[0])

    def test_missing_conversation_is_created(self):
        conversations = Conversations()
        self.assertTrue(record(conversations))
        self.assertEqual(conversations.created, [(FRIEND, "alice")])
        self.assertEqual(conversations.pairs[0]["cid"], "created-conversation")


if __name__ == "__main__":
    unittest.main()
