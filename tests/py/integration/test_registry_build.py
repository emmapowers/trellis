"""Integration tests for registry-based bundle building."""

from __future__ import annotations

from trellis.bundler.packages import SYSTEM_PACKAGES


class TestSystemPackages:
    """Tests for system package configuration."""

    def test_typescript_included_via_system_packages(self) -> None:
        """TypeScript is included via SYSTEM_PACKAGES (always installed)."""
        assert "typescript" in SYSTEM_PACKAGES
        assert "esbuild" in SYSTEM_PACKAGES
