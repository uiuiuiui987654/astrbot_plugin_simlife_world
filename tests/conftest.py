"""Test bootstrap: stub out AstrBot and import the plugin as a package named
``astrbot_plugin_simlife_world`` no matter what the checkout directory is called."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "astrbot_plugin_simlife_world"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests import astrbot_stub  # noqa: E402

astrbot_stub.install()

if PACKAGE not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        PACKAGE, ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE] = module
    spec.loader.exec_module(module)
