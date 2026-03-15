from __future__ import annotations

import importlib
import sys
from pathlib import Path

from trellis.app import App

REPO_ROOT = Path(__file__).resolve().parents[3]


def _import_example_module(example_dir: str, module_name: str) -> object:
    example_root = REPO_ROOT / "examples" / example_dir
    sys.path.insert(0, str(example_root))
    try:
        importlib.invalidate_caches()
        stale = [
            name
            for name in sys.modules
            if name == module_name or name.startswith(f"{module_name}.")
        ]
        for name in stale:
            sys.modules.pop(name, None)
        package_name = module_name.split(".", 1)[0]
        sys.modules.pop(package_name, None)
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(str(example_root))


def test_widget_showcase_no_longer_exposes_css_tab() -> None:
    module = _import_example_module("widget_showcase", "widget_showcase.app")

    tabs = module.resolve_tabs()  # type: ignore[attr-defined]

    assert all(tab_id != "css" for tab_id, *_rest in tabs)


def test_html_studio_example_imports_cleanly() -> None:
    module = _import_example_module("html_studio", "html_studio.app")

    assert isinstance(module.app, App)  # type: ignore[attr-defined]
