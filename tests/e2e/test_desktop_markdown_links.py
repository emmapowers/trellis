"""Desktop E2E tests for markdown link behavior."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.e2e.desktop_harness import run_desktop_e2e_scenario
from tests.helpers import requires_pytauri

_RUN_DESKTOP_E2E = os.environ.get("TRELLIS_RUN_DESKTOP_E2E") == "1"
requires_desktop_e2e = pytest.mark.skipif(
    not _RUN_DESKTOP_E2E, reason="set TRELLIS_RUN_DESKTOP_E2E=1 to run desktop E2E tests"
)


@requires_pytauri
@requires_desktop_e2e
@pytest.mark.slow
def test_markdown_external_link_opens_via_desktop_external_handler() -> None:
    app_root = Path("examples/widget_showcase").resolve()
    result = run_desktop_e2e_scenario(
        app_root=app_root,
        scenario="markdown_external_link",
    )

    assert result.payload is not None, f"missing E2E payload\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert result.return_code == 0, f"desktop E2E exited {result.return_code}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert result.payload["success"] is True
    assert result.payload["scenario"] == "markdown_external_link"
    assert result.payload["external_url"] in {
        "https://github.com/emmapowers/trellis",
        "https://github.com/emmapowers/trellis/",
    }
