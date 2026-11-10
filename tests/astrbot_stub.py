"""A minimal stand-in for the ``astrbot`` package so the plugin can be imported and
unit-tested without installing AstrBot.

Only what the plugin touches at import time and what the tests exercise is modelled;
any other ``astrbot.*`` attribute resolves to a permissive dummy class. Decorators
from ``filter`` return the decorated function unchanged and record the registration
in ``REGISTRY`` so tests can check which handlers the plugin declares.
"""
from __future__ import annotations

import asyncio
import contextlib
import importlib.abc
import importlib.machinery
import logging
import sys
import tempfile
import types
from pathlib import Path

REGISTRY: list[tuple[str, tuple, dict, str]] = []
STUB_ROOTS = ("astrbot",)
OPTIONAL_ROOTS = ("apscheduler", "holidays", "lunar_python", "aiohttp")


class Dummy:
    """Accepts any constructor arguments and any attribute access."""

    def __init__(self, *args, **kwargs):
        self.args = args
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __call__(self, *args, **kwargs):
        return Dummy()

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return Dummy()


def _recorder(kind):
    def factory(*args, **kwargs):
        def decorator(fn):
            REGISTRY.append((kind, args, kwargs, getattr(fn, "__name__", repr(fn))))
            return fn

        return decorator

    return factory


class CommandGroup:
    def __init__(self, name):
        self.name = name

    def command(self, *args, **kwargs):
        return _recorder("group:%s/command" % self.name)(*args, **kwargs)

    def group(self, *args, **kwargs):
        return _recorder("group:%s/group" % self.name)(*args, **kwargs)


class _Filter:
    class EventMessageType:
        PRIVATE_MESSAGE = "PRIVATE_MESSAGE"
        GROUP_MESSAGE = "GROUP_MESSAGE"
        ALL = "ALL"

    class PermissionType:
        ADMIN = "ADMIN"
        MEMBER = "MEMBER"

    def command_group(self, *args, **kwargs):
        def decorator(fn):
            REGISTRY.append(("command_group", args, kwargs, fn.__name__))
            return CommandGroup(args[0])

        return decorator

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _recorder(name)


class Star:
    def __init__(self, context=None, *args, **kwargs):
        self.context = context

    async def html_render(self, *args, **kwargs):
        return ""


class StarTools:
    _root: Path | None = None

    @classmethod
    def get_data_dir(cls, name: str) -> Path:
        if cls._root is None:
            cls._root = Path(tempfile.mkdtemp(prefix="astrbot-stub-"))
        path = cls._root / name
        path.mkdir(parents=True, exist_ok=True)
        return path


class CommandFilter:
    def __init__(self, command_name="", *args, **kwargs):
        self.command_name = command_name


class CommandGroupFilter:
    def __init__(self, group_name="", *args, **kwargs):
        self.group_name = group_name


class RegexFilter:
    def __init__(self, regex="", *args, **kwargs):
        self.regex = regex


class GreedyStr(str):
    pass


class _SessionLockManager:
    def __init__(self):
        self._locks: dict[str, asyncio.Lock] = {}

    @contextlib.asynccontextmanager
    async def acquire_lock(self, key):
        # one lock per (event loop, key): unittest's IsolatedAsyncioTestCase uses a fresh loop per test
        lock = self._locks.setdefault((id(asyncio.get_running_loop()), key), asyncio.Lock())
        async with lock:
            yield


class MessageChain(list):
    def __init__(self, chain=None, **_kwargs):
        super().__init__(chain or [])
        self.chain = self

    def message(self, text):
        self.append(Plain(text))
        return self


class _Component(Dummy):
    pass


class Plain(_Component):
    def __init__(self, text="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text


class Image(_Component):
    @classmethod
    def fromFileSystem(cls, path):
        return cls(file=str(path))

    @classmethod
    def fromURL(cls, url):
        return cls(url=url)

    @classmethod
    def fromBase64(cls, data):
        return cls(base64=data)


class Record(_Component):
    pass


class Reply(_Component):
    pass


class TextPart(Dummy):
    def __init__(self, text="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "text"
        self.text = text

    def model_dump(self):
        return {"type": self.type, "text": self.text}


class _MessageSegment:
    role = ""

    def __init__(self, content=None, **kwargs):
        self.content = list(content or [])
        self.__dict__.update(kwargs)

    def model_dump(self):
        return {
            "role": self.role,
            "content": [part.model_dump() if hasattr(part, "model_dump") else part for part in self.content],
        }


class UserMessageSegment(_MessageSegment):
    role = "user"


class AssistantMessageSegment(_MessageSegment):
    role = "assistant"


SPECIFIC = {
    "astrbot.api": {"logger": logging.getLogger("astrbot")},
    "astrbot.api.event": {"filter": _Filter(), "MessageChain": MessageChain},
    "astrbot.api.message_components": {"Plain": Plain, "Image": Image, "Record": Record, "Reply": Reply},
    "astrbot.api.star": {"Star": Star, "StarTools": StarTools},
    "astrbot.core.agent.message": {
        "TextPart": TextPart,
        "UserMessageSegment": UserMessageSegment,
        "AssistantMessageSegment": AssistantMessageSegment,
    },
    "astrbot.core.star.filter.command": {"CommandFilter": CommandFilter, "GreedyStr": GreedyStr},
    "astrbot.core.star.filter.command_group": {"CommandGroupFilter": CommandGroupFilter},
    "astrbot.core.star.filter.regex": {"RegexFilter": RegexFilter},
    "astrbot.core.utils.session_lock": {"session_lock_manager": _SessionLockManager()},
}


class _StubModule(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        value = type(name, (Dummy,), {})
        setattr(self, name, value)
        return value


class _Finder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, roots):
        self.roots = roots

    def find_spec(self, fullname, path, target=None):
        if fullname.split(".")[0] in self.roots:
            return importlib.machinery.ModuleSpec(fullname, self, is_package=True)
        return None

    def create_module(self, spec):
        module = _StubModule(spec.name)
        module.__path__ = []
        module.__dict__.update(SPECIFIC.get(spec.name, {}))
        return module

    def exec_module(self, module):
        pass


STUBBED: set[str] = set()


def is_stubbed(name: str) -> bool:
    """True when ``name`` is served by this stub instead of the real package."""
    return name in STUBBED


def install() -> None:
    """Install the stub; real third-party packages are used when they are installed."""
    roots = list(STUB_ROOTS)
    for name in OPTIONAL_ROOTS:
        try:
            __import__(name)
        except ImportError:
            roots.append(name)
    STUBBED.update(roots)
    if not any(isinstance(f, _Finder) for f in sys.meta_path):
        sys.meta_path.insert(0, _Finder(tuple(roots)))
