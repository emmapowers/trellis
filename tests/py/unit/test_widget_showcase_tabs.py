"""Unit tests for widget showcase tab resolution."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from trellis.platforms.common.base import PlatformType


def _import_showcase_app(monkeypatch: pytest.MonkeyPatch):
    app_root = Path(__file__).resolve().parents[3] / "examples" / "widget_showcase"
    monkeypatch.syspath_prepend(str(app_root))
    return importlib.import_module("widget_showcase.app")


class TestWidgetShowcaseTabs:
    """Tests for platform-aware widget showcase tabs."""

    def test_desktop_tab_absent_on_server_and_browser(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        app_module = _import_showcase_app(monkeypatch)

        server_tabs = app_module.resolve_tabs(PlatformType.SERVER)
        browser_tabs = app_module.resolve_tabs(PlatformType.BROWSER)

        assert all(tab_id != "desktop" for tab_id, *_ in server_tabs)
        assert all(tab_id != "desktop" for tab_id, *_ in browser_tabs)

    def test_desktop_tab_present_on_desktop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        app_module = _import_showcase_app(monkeypatch)

        tabs = app_module.resolve_tabs(PlatformType.DESKTOP)
        tab_ids = [tab_id for tab_id, *_ in tabs]

        assert "desktop" in tab_ids
        assert tab_ids.index("desktop") == tab_ids.index("forms") + 1

    def test_platform_detection_falls_back_to_non_desktop(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        app_module = _import_showcase_app(monkeypatch)

        monkeypatch.setattr(app_module, "get_config", lambda: None)
        tabs = app_module.resolve_tabs()
        assert all(tab_id != "desktop" for tab_id, *_ in tabs)

    @pytest.mark.parametrize(
        "platform", [PlatformType.SERVER, PlatformType.BROWSER, PlatformType.DESKTOP]
    )
    def test_tab_order_and_uniqueness(
        self, monkeypatch: pytest.MonkeyPatch, platform: PlatformType
    ) -> None:
        app_module = _import_showcase_app(monkeypatch)

        tabs = app_module.resolve_tabs(platform)
        tab_ids = [tab_id for tab_id, *_ in tabs]

        assert tab_ids[0] == "layout"
        assert len(tab_ids) == len(set(tab_ids))
