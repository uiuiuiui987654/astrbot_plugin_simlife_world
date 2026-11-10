"""Only real chat counts as conversation activity; commands and regex triggers don't."""

import unittest
from types import SimpleNamespace

from astrbot.core.star.filter.command import CommandFilter
from astrbot.core.star.filter.command_group import CommandGroupFilter
from astrbot.core.star.filter.regex import RegexFilter

from astrbot_plugin_simlife_world.main import ProactiveVirtualDailyPlugin


def event(**extras):
    return SimpleNamespace(get_extra=lambda key, default=None: extras.get(key, default))


def handled_by(*filters):
    return event(handlers_parsed_params=None, activated_handlers=[SimpleNamespace(event_filters=list(filters))])


class ConversationDetection(unittest.TestCase):
    plugin = object.__new__(ProactiveVirtualDailyPlugin)

    def test_conversation(self):
        for name, ev in {
            "plain message": event(handlers_parsed_params=None, activated_handlers=[]),
            "other plugin's handler": handled_by(),
            "no extras at all": event(),
        }.items():
            with self.subTest(name):
                self.assertTrue(self.plugin._is_conversation_event(ev))

    def test_not_conversation(self):
        for name, ev in {
            "parsed command": event(handlers_parsed_params={"handler": {}}),
            "command": handled_by(CommandFilter(command_name="状态")),
            "command group": handled_by(CommandGroupFilter(group_name="虚拟人生")),
            "regex": handled_by(RegexFilter(r"签到")),
        }.items():
            with self.subTest(name):
                self.assertFalse(self.plugin._is_conversation_event(ev))


if __name__ == "__main__":
    unittest.main()
