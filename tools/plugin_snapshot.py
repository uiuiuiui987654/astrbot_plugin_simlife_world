"""Import the plugin against stub astrbot/3rd-party modules and dump a structural snapshot.

Snapshot = registered handlers (decorator kind + args, in registration order per kind)
         + every attribute of the plugin class (resolved through the MRO) with an AST hash
           of its function body, so moved code can be proven unchanged.
Usage: python tools/plugin_snapshot.py <repo_dir> <out.json>
"""
import ast, hashlib, importlib, importlib.abc, importlib.machinery, inspect, json, sys, textwrap, types
from pathlib import Path

REG = []
STUB_ROOTS = ("astrbot", "apscheduler", "holidays", "lunar_python", "aiohttp")


class _Any:
    def __init__(self, *a, **k):
        pass
    def __call__(self, *a, **k):
        return _Any()
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _Any()
    def __iter__(self):
        return iter(())
    def __mro_entries__(self, bases):
        return (object,)


def _rec(kind):
    def factory(*args, **kwargs):
        def deco(fn):
            REG.append([kind, [repr(a) for a in args], sorted((k, repr(v)) for k, v in kwargs.items()), getattr(fn, "__name__", repr(fn))])
            return fn
        return deco
    return factory


class _Group:
    def __init__(self, name):
        self.name = name
    def command(self, *args, **kwargs):
        return _rec("group:%s/command" % self.name)(*args, **kwargs)
    def group(self, *args, **kwargs):
        return _rec("group:%s/group" % self.name)(*args, **kwargs)


class _Filter:
    class EventMessageType:
        PRIVATE_MESSAGE = "PRIVATE_MESSAGE"; GROUP_MESSAGE = "GROUP_MESSAGE"; ALL = "ALL"
    class PermissionType:
        ADMIN = "ADMIN"; MEMBER = "MEMBER"
    def command_group(self, *args, **kwargs):
        def deco(fn):
            REG.append(["command_group", [repr(a) for a in args], [], fn.__name__])
            return _Group(args[0])
        return deco
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _rec(name)


class Star:
    def __init__(self, *a, **k):
        pass


class _StubModule(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "filter":
            return _Filter()
        if name == "Star":
            return Star
        return _Any


class _Finder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path, target=None):
        if fullname.split(".")[0] in STUB_ROOTS:
            return importlib.machinery.ModuleSpec(fullname, self, is_package=True)
        return None
    def create_module(self, spec):
        m = _StubModule(spec.name)
        m.__path__ = []
        return m
    def exec_module(self, module):
        pass


def body_hash(obj):
    fn = inspect.unwrap(obj)
    if isinstance(fn, (staticmethod, classmethod)):
        fn = fn.__func__
    try:
        src = textwrap.dedent(inspect.getsource(fn))
    except (TypeError, OSError):
        return "nosrc:" + type(fn).__name__
    node = ast.parse(src).body[0]
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        node.decorator_list = []
    return hashlib.sha1(ast.dump(node, include_attributes=False).encode()).hexdigest()[:16]


def main():
    repo = Path(sys.argv[1]).resolve()
    sys.meta_path.insert(0, _Finder())
    sys.path.insert(0, str(repo.parent))
    mod = importlib.import_module(repo.name + ".main")
    cls = getattr(mod, "SimLifeWorldPlugin")
    attrs = {}
    for name in dir(cls):
        if name.startswith("__") and name.endswith("__") and name != "__init__":
            continue
        raw = inspect.getattr_static(cls, name)
        if isinstance(raw, (staticmethod, classmethod)) or inspect.isfunction(raw):
            kind = type(raw).__name__
            attrs[name] = kind + ":" + body_hash(raw)
        elif isinstance(raw, _Group):
            attrs[name] = "group:" + raw.name
        else:
            attrs[name] = "value:" + type(raw).__name__
    out = {"handlers": REG, "attrs": attrs, "mro": [c.__name__ for c in cls.__mro__]}
    Path(sys.argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print("handlers", len(REG), "attrs", len(attrs))


if __name__ == "__main__":
    main()
