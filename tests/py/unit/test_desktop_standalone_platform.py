"""Tests for DesktopStandalonePlatform."""

from __future__ import annotations

import importlib

import pytest

from tests.helpers import requires_pytauri


@requires_pytauri
class TestDesktopStandalonePlatform:
    """Tests for DesktopStandalonePlatform runtime behavior."""

    def test_uses_pytauri_builder_and_context_factories(self) -> None:
        pytauri = importlib.import_module("pytauri")
        standalone_platform = importlib.import_module(
            "trellis.platforms.desktop.standalone_platform"
        )

        assert standalone_platform.builder_factory is pytauri.builder_factory
        assert standalone_platform.context_factory is pytauri.context_factory

    def test_name_returns_desktop(self) -> None:
        from trellis.platforms.desktop.standalone_platform import (  # noqa: PLC0415
            DesktopStandalonePlatform,
        )

        platform = DesktopStandalonePlatform()
        assert platform.name == "desktop"

    def test_get_build_config_raises(self) -> None:
        from trellis.app.config import Config  # noqa: PLC0415
        from trellis.platforms.desktop.standalone_platform import (  # noqa: PLC0415
            DesktopStandalonePlatform,
        )

        platform = DesktopStandalonePlatform()
        config = Config(name="test", module="test")

        with pytest.raises(NotImplementedError, match="DesktopStandalonePlatform"):
            platform.get_build_config(config)

    def test_get_config_override_returns_none(self) -> None:
        from trellis.platforms.desktop.standalone_platform import (  # noqa: PLC0415
            DesktopStandalonePlatform,
        )

        platform = DesktopStandalonePlatform()
        assert platform._get_config_override() is None  # INTERNAL TEST: verifying hook method


@requires_pytauri
class TestDesktopPlatformInheritance:
    """Tests that DesktopPlatform correctly inherits from DesktopStandalonePlatform."""

    def test_desktop_platform_is_subclass(self) -> None:
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415
        from trellis.platforms.desktop.standalone_platform import (  # noqa: PLC0415
            DesktopStandalonePlatform,
        )

        assert issubclass(DesktopPlatform, DesktopStandalonePlatform)

    def test_desktop_platform_name(self) -> None:
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        platform = DesktopPlatform()
        assert platform.name == "desktop"
