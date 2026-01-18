"""Shared test helpers and markers."""

from __future__ import annotations

from importlib.util import find_spec

import pytest

# Check for optional dependencies
HAS_PYTAURI = find_spec("pytauri") is not None

# Skip marker for tests that require pytauri (desktop platform)
requires_pytauri = pytest.mark.skipif(not HAS_PYTAURI, reason="pytauri not installed")
