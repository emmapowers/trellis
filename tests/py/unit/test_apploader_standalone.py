"""Tests for apploader standalone platform selection."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from trellis.platforms.common.base import PlatformType

if TYPE_CHECKING:
    from tests.conftest import WriteTrellisConfig


class TestStandalonePlatformSelection:
    """Tests that desktop platform mode follows sys._pytauri_standalone."""

    def test_selects_standalone_when_flag_set(
        self, write_trellis_config: WriteTrellisConfig, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With sys._pytauri_standalone=True, DesktopPlatform runs in standalone mode."""
        from trellis.app.apploader import AppLoader  # noqa: PLC0415
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        app_root = write_trellis_config(module="test", platform="DESKTOP")
        apploader = AppLoader(app_root)
        apploader.load_config()

        monkeypatch.setattr(sys, "_pytauri_standalone", True, raising=False)

        assert isinstance(apploader.platform, DesktopPlatform)
        assert apploader.platform.is_standalone is True

    def test_selects_dev_when_flag_not_set(
        self, write_trellis_config: WriteTrellisConfig, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without sys._pytauri_standalone, DesktopPlatform runs in dev mode."""
        from trellis.app.apploader import AppLoader  # noqa: PLC0415
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        app_root = write_trellis_config(module="test", platform="DESKTOP")
        apploader = AppLoader(app_root)
        apploader.load_config()

        # Ensure the flag is not set
        if hasattr(sys, "_pytauri_standalone"):
            monkeypatch.delattr(sys, "_pytauri_standalone")

        assert isinstance(apploader.platform, DesktopPlatform)
        assert apploader.platform.is_standalone is False

    def test_standalone_entry_overrides_platform_to_desktop(
        self,
        write_trellis_config: WriteTrellisConfig,
        monkeypatch: pytest.MonkeyPatch,
        reset_apploader: None,
    ) -> None:
        """Standalone entry forces DESKTOP even when config says SERVER."""
        from trellis.app.apploader import AppLoader, get_apploader  # noqa: PLC0415

        app_root = write_trellis_config(module="test", platform="SERVER")
        monkeypatch.setenv("TRELLIS_APP_ROOT", str(app_root))

        # standalone_entry.main() calls load_app and asyncio.run which we
        # can't run in a test. Patch both, then reload the module to trigger
        # main() inside the patch context.
        monkeypatch.delitem(sys.modules, "trellis.app.standalone_entry", raising=False)

        def fake_load_app(self: AppLoader) -> None:
            self.app = MagicMock()
            self.app.top = MagicMock()

        with (
            patch("asyncio.run"),
            patch.object(AppLoader, "load_app", fake_load_app),
        ):
            import importlib  # noqa: PLC0415

            importlib.import_module("trellis.app.standalone_entry")

        config = get_apploader().config
        assert config is not None
        assert config.platform == PlatformType.DESKTOP
