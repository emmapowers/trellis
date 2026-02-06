"""Tests for BuildConfig dataclass and platform get_build_config() methods."""

from __future__ import annotations

from pathlib import Path

import pytest

from trellis.bundler.build_config import BuildConfig
from trellis.bundler.steps import PackageInstallStep


class TestBuildConfig:
    """Tests for BuildConfig dataclass."""

    def test_creation(self) -> None:
        """BuildConfig can be created with entry_point and steps."""
        config = BuildConfig(
            entry_point=Path("/some/main.tsx"),
            steps=[PackageInstallStep()],
        )
        assert config.entry_point == Path("/some/main.tsx")
        assert len(config.steps) == 1

    def test_frozen(self) -> None:
        """BuildConfig is immutable (frozen)."""
        config = BuildConfig(
            entry_point=Path("/some/main.tsx"),
            steps=[],
        )
        with pytest.raises(AttributeError):
            config.entry_point = Path("/other.tsx")  # type: ignore[misc]
