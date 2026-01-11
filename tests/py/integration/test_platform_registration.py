"""Integration tests for platform module registration."""

from __future__ import annotations

# Import all platforms once at module level to trigger registrations
# This avoids issues with Python's import caching
from trellis.platforms import browser, common, desktop, server  # noqa: F401


class TestPlatformRegistration:
    """Tests for platform module registration with the bundler registry.

    Note: These tests verify that platform imports register modules.
    Since Python caches imports, we import all platforms at module load time
    and then verify the registry state.
    """

    def test_common_registers_trellis_core(self) -> None:
        """Importing common platform registers trellis-core module."""
        from trellis.bundler import registry

        collected = registry.collect()
        module_names = [m.name for m in collected.modules]
        assert "trellis-core" in module_names

    def test_trellis_core_has_packages(self) -> None:
        """trellis-core module includes NPM packages."""
        from trellis.bundler import registry

        collected = registry.collect()
        # Should have core packages like react
        assert "react" in collected.packages
        assert "react-dom" in collected.packages

    def test_trellis_core_has_widget_files(self) -> None:
        """trellis-core module includes widget TypeScript files."""
        from trellis.bundler import registry

        collected = registry.collect()
        core = next(m for m in collected.modules if m.name == "trellis-core")

        # Should have widget files
        widget_files = [f for f in core.files if "widgets/" in f]
        assert len(widget_files) > 0
        assert any("Button" in f for f in widget_files)

    def test_server_registers_trellis_server(self) -> None:
        """Importing server platform registers trellis-server module."""
        from trellis.bundler import registry

        collected = registry.collect()
        module_names = [m.name for m in collected.modules]
        assert "trellis-server" in module_names

    def test_desktop_registers_with_tauri_packages(self) -> None:
        """Importing desktop platform registers trellis-desktop with Tauri packages."""
        from trellis.bundler import registry

        collected = registry.collect()
        desktop_module = next(m for m in collected.modules if m.name == "trellis-desktop")

        # Desktop should have Tauri packages
        assert "@tauri-apps/api" in desktop_module.packages

    def test_browser_registers_with_worker(self) -> None:
        """Importing browser platform registers trellis-browser with worker entry."""
        from trellis.bundler import registry

        collected = registry.collect()
        browser_module = next(m for m in collected.modules if m.name == "trellis-browser")

        # Browser should have pyodide worker
        assert "pyodide" in browser_module.worker_entries

    def test_all_platforms_no_package_conflicts(self) -> None:
        """All platforms can be imported without package version conflicts."""
        from trellis.bundler import registry

        # Should not raise on collect (no version conflicts)
        collected = registry.collect()
        assert len(collected.modules) == 4
