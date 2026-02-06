"""BuildConfig dataclass for platform build configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from trellis.bundler.steps import BuildStep


@dataclass(frozen=True)
class BuildConfig:
    """Immutable build configuration provided by a platform.

    Attributes:
        entry_point: Path to the TypeScript entry point file
        steps: Ordered list of build steps to execute
    """

    entry_point: Path
    steps: list[BuildStep] = field(default_factory=list)
