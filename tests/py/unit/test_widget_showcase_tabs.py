"""Unit tests for widget showcase tab resolution."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

import pytest

from trellis.platforms.common.base import PlatformType


def _import_showcase_app(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    app_root = Path(__file__).resolve().parents[3] / "examples" / "widget_showcase"
    monkeypatch.syspath_prepend(str(app_root))
    return importlib.import_module("widget_showcase.app")


@pytest.fixture
def showcase_app(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    return _import_showcase_app(monkeypatch)


def test_desktop_tab_absent_on_server_and_browser(showcase_app: ModuleType) -> None:
    server_tabs = showcase_app.resolve_tabs(PlatformType.SERVER)
    browser_tabs = showcase_app.resolve_tabs(PlatformType.BROWSER)

    assert all(tab_id != "desktop" for tab_id, *_ in server_tabs)
    assert all(tab_id != "desktop" for tab_id, *_ in browser_tabs)


def test_desktop_tab_present_on_desktop(showcase_app: ModuleType) -> None:
    tabs = showcase_app.resolve_tabs(PlatformType.DESKTOP)
    tab_ids = [tab_id for tab_id, *_ in tabs]

    assert "desktop" in tab_ids
    assert tab_ids.index("desktop") == tab_ids.index("forms") + 1


def test_platform_detection_falls_back_to_non_desktop(
    monkeypatch: pytest.MonkeyPatch,
    showcase_app: ModuleType,
) -> None:
    monkeypatch.setattr(showcase_app, "get_config", lambda: None)
    tabs = showcase_app.resolve_tabs()
    assert all(tab_id != "desktop" for tab_id, *_ in tabs)


@pytest.mark.parametrize(
    "platform", [PlatformType.SERVER, PlatformType.BROWSER, PlatformType.DESKTOP]
)
def test_tab_order_and_uniqueness(showcase_app: ModuleType, platform: PlatformType) -> None:
    tabs = showcase_app.resolve_tabs(platform)
    tab_ids = [tab_id for tab_id, *_ in tabs]

    assert tab_ids[0] == "layout"
    assert len(tab_ids) == len(set(tab_ids))
