"""Shared test helpers and markers."""

from __future__ import annotations

from importlib.metadata import entry_points
from importlib.util import find_spec

import pytest

# Check for optional dependencies
HAS_PYTAURI = find_spec("pytauri") is not None
HAS_PYTAURI_RUNTIME = HAS_PYTAURI and len(entry_points(group="pytauri", name="ext_mod")) == 1

# Skip marker for tests that require a working pytauri runtime (desktop platform)
requires_pytauri = pytest.mark.skipif(
    not HAS_PYTAURI_RUNTIME,
    reason="pytauri runtime not installed",
)
