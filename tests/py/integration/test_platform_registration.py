"""Integration tests for platform module registration."""

from __future__ import annotations

from tests.helpers import HAS_PYTAURI, requires_pytauri
from trellis.bundler import registry

# Import platforms that don't require pytauri
from trellis.platforms import browser, common, server  # noqa: F401

# Desktop requires pytauri which isn't available in CI
if HAS_PYTAURI:
    from trellis.platforms import desktop  # noqa: F401


class TestPlatformRegistration:
    """Tests for platform module registration with the bundler registry.

    Note: These tests verify that platform imports register modules.
    Since Python caches imports, we import all platforms at module load time
    and then verify the registry state.
    """

    def test_common_registers_trellis_core(self) -> None:
        """Importing common platform registers trellis-core module."""
        collected = registry.collect()
        module_names = [m.name for m in collected.modules]
        assert "trellis-core" in module_names

    def test_trellis_core_has_packages(self) -> None:
        """trellis-core module includes NPM packages."""
        collected = registry.collect()
        # Should have core packages like react
        assert "react" in collected.packages
        assert "react-dom" in collected.packages

    def test_trellis_core_has_base_path(self) -> None:
        """trellis-core module has base_path set for source resolution."""
        collected = registry.collect()
        core = next(m for m in collected.modules if m.name == "trellis-core")

        # Should have base_path set (used by bundler to resolve source files)
        assert core._base_path is not None
        assert core._base_path.exists()

    def test_server_registers_trellis_server(self) -> None:
        """Importing server platform registers trellis-server module."""
        collected = registry.collect()
        module_names = [m.name for m in collected.modules]
        assert "trellis-server" in module_names

    @requires_pytauri
    def test_desktop_registers_with_tauri_packages(self) -> None:
        """Importing desktop platform registers trellis-desktop with Tauri packages."""
        collected = registry.collect()
        desktop_module = next(m for m in collected.modules if m.name == "trellis-desktop")

        # Desktop should have Tauri packages
        assert "@tauri-apps/api" in desktop_module.packages

    def test_browser_registers_trellis_browser(self) -> None:
        """Importing browser platform registers trellis-browser module."""
        collected = registry.collect()
        module_names = [m.name for m in collected.modules]
        assert "trellis-browser" in module_names

    def test_all_platforms_no_package_conflicts(self) -> None:
        """All platforms can be imported without package version conflicts."""
        # Should not raise on collect (no version conflicts)
        collected = registry.collect()
        # 4 modules with pytauri (desktop), 3 without
        expected_count = 4 if HAS_PYTAURI else 3
        assert len(collected.modules) == expected_count
