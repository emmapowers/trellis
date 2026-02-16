"""Unit tests for desktop runtime Tauri config overrides."""

from __future__ import annotations

from tests.helpers import requires_pytauri

pytestmark = requires_pytauri


class TestBuildTauriConfigOverride:
    def test_includes_window_title_and_size(self) -> None:
        from trellis.platforms.desktop.platform import (  # noqa: PLC0415
            _build_tauri_config_override,
        )

        override = _build_tauri_config_override(
            dist_path="/tmp/app/.dist",
            window_title="My Desktop App",
            window_width=1440,
            window_height=900,
        )

        assert override["build"]["frontendDist"] == "/tmp/app/.dist"
        assert override["app"]["windows"] == [
            {"title": "My Desktop App", "width": 1440, "height": 900}
        ]
