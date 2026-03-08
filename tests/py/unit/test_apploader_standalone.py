"""Tests for apploader standalone platform selection."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from tests.helpers import requires_pytauri

if TYPE_CHECKING:
    from tests.conftest import WriteTrellisConfig


class TestStandalonePlatformSelection:
    """Tests that apploader selects correct platform based on sys._pytauri_standalone."""

    @requires_pytauri
    def test_selects_standalone_when_flag_set(
        self, write_trellis_config: WriteTrellisConfig, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With sys._pytauri_standalone=True, selects DesktopStandalonePlatform."""
        from trellis.app.apploader import AppLoader  # noqa: PLC0415
        from trellis.platforms.desktop.standalone_platform import (  # noqa: PLC0415
            DesktopStandalonePlatform,
        )

        app_root = write_trellis_config(module="test", platform="DESKTOP")
        apploader = AppLoader(app_root)
        apploader.load_config()

        monkeypatch.setattr(sys, "_pytauri_standalone", True, raising=False)

        assert type(apploader.platform) is DesktopStandalonePlatform

    @requires_pytauri
    def test_selects_dev_when_flag_not_set(
        self, write_trellis_config: WriteTrellisConfig, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without sys._pytauri_standalone, selects DesktopPlatform."""
        from trellis.app.apploader import AppLoader  # noqa: PLC0415
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        app_root = write_trellis_config(module="test", platform="DESKTOP")
        apploader = AppLoader(app_root)
        apploader.load_config()

        # Ensure the flag is not set
        if hasattr(sys, "_pytauri_standalone"):
            monkeypatch.delattr(sys, "_pytauri_standalone")

        assert isinstance(apploader.platform, DesktopPlatform)
