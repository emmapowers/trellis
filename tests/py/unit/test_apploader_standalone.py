"""Tests for apploader standalone platform selection."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

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
