"""Tests for DesktopPlatform runtime behavior."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


class TestDesktopPlatform:
    """Tests for DesktopPlatform runtime behavior."""

    def test_name_returns_desktop(self) -> None:
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        platform = DesktopPlatform()
        assert platform.name == "desktop"

    def test_get_build_config_raises_in_standalone_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from trellis.app.config import Config  # noqa: PLC0415
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        monkeypatch.setattr(sys, "_pytauri_standalone", True, raising=False)
        platform = DesktopPlatform()
        config = Config(name="test", module="test")

        with pytest.raises(NotImplementedError, match="standalone mode"):
            platform.get_build_config(config)

    def test_get_config_override_returns_none_in_standalone_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        monkeypatch.setattr(sys, "_pytauri_standalone", True, raising=False)
        platform = DesktopPlatform()
        assert platform._get_config_override() is None  # INTERNAL TEST: verifying hook method

    def test_is_standalone_reflects_runtime_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        monkeypatch.setattr(sys, "_pytauri_standalone", True, raising=False)
        assert DesktopPlatform().is_standalone is True

    def test_get_config_override_returns_dev_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        if hasattr(sys, "_pytauri_standalone"):
            monkeypatch.delattr(sys, "_pytauri_standalone")

        with patch(
            "trellis.platforms.desktop.platform.get_dist_dir", return_value=Path("/tmp/dist")
        ):
            platform = DesktopPlatform()
            config = platform._get_config_override(
                window_title="App",
                window_width=640,
                window_height=480,
            )
        assert config is not None
        assert config["app"]["windows"][0]["title"] == "App"


class TestDesktopPlatformImports:
    """Tests for platform import-time/runtime behavior."""

    def test_importing_platform_module_does_not_provision_runtime(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        module_name = "trellis.platforms.desktop.platform"
        original = sys.modules.pop(module_name, None)

        ensure_runtime = MagicMock()
        fake_toolchain = ModuleType("trellis.packaging.toolchain.pytauri_wheel")
        fake_toolchain.ensure_pytauri_runtime = ensure_runtime

        monkeypatch.setitem(
            sys.modules, "trellis.packaging.toolchain.pytauri_wheel", fake_toolchain
        )

        try:
            importlib.import_module(module_name)
        finally:
            sys.modules.pop(module_name, None)
            if original is not None:
                sys.modules[module_name] = original

        ensure_runtime.assert_not_called()

    def test_load_pytauri_runtime_provisions_before_import(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        module_name = "trellis.platforms.desktop.platform"
        original = sys.modules.pop(module_name, None)

        ensure_runtime = MagicMock()
        fake_toolchain = ModuleType("trellis.packaging.toolchain.pytauri_wheel")
        fake_toolchain.ensure_pytauri_runtime = ensure_runtime
        fake_pytauri = ModuleType("pytauri")
        fake_pytauri.AppHandle = object
        fake_pytauri.Commands = object
        fake_pytauri.Manager = object
        fake_pytauri.builder_factory = object()
        fake_pytauri.context_factory = object()
        fake_ipc = ModuleType("pytauri.ipc")
        fake_ipc.Channel = object
        fake_ipc.JavaScriptChannelId = object
        fake_webview = ModuleType("pytauri.webview")
        fake_webview.WebviewWindow = object

        monkeypatch.setitem(
            sys.modules, "trellis.packaging.toolchain.pytauri_wheel", fake_toolchain
        )
        monkeypatch.setitem(sys.modules, "pytauri", fake_pytauri)
        monkeypatch.setitem(sys.modules, "pytauri.ipc", fake_ipc)
        monkeypatch.setitem(sys.modules, "pytauri.webview", fake_webview)

        try:
            platform_module = importlib.import_module(module_name)
            runtime = platform_module.DesktopPlatform()._load_pytauri_runtime()
        finally:
            sys.modules.pop(module_name, None)
            if original is not None:
                sys.modules[module_name] = original

        ensure_runtime.assert_called_once_with()
        assert runtime.builder_factory is fake_pytauri.builder_factory
