"""E2E test for SSR hydration — checks for React hydration mismatch warnings.

Starts a minimal Trellis server with SSR enabled, loads the page in a
headless browser via Playwright, and verifies no hydration warnings
appear in the console.

Requires: Playwright browsers installed (``npx playwright install chromium``).
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from trellis.platforms.common import find_available_port

# Mark as slow + e2e — needs server + browser
pytestmark = [pytest.mark.slow, pytest.mark.e2e]

_SCRIPT = Path(__file__).parent / "check_hydration.js"
_STARTUP_TIMEOUT = 30


def _wait_for_server(url: str, timeout: float) -> bool:
    """Poll until the server responds with 200."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(url, timeout=2.0)
            if resp.status_code == 200:
                return True
        except (httpx.ConnectError, httpx.TimeoutException, OSError):
            pass
        time.sleep(0.5)
    return False


@pytest.fixture(scope="module")
def server_url() -> str:
    """Start a minimal Trellis server with SSR and return its URL."""
    host = "127.0.0.1"
    port = find_available_port(host=host)
    url = f"http://{host}:{port}"

    # Start the server in a subprocess so it gets its own event loop
    server_script = Path(__file__).parent / "_run_test_server.py"
    proc = subprocess.Popen(
        [sys.executable, str(server_script), host, str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env={**os.environ, "TRELLIS_HOT_RELOAD": "false"},
    )

    if not _wait_for_server(url, _STARTUP_TIMEOUT):
        proc.kill()
        stdout, _ = proc.communicate(timeout=5)
        output = stdout.decode() if stdout else ""
        pytest.skip(f"Test server did not start in time:\n{output}")

    yield url

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_no_hydration_warnings(server_url: str) -> None:
    """Load the SSR page in Playwright and verify no hydration mismatch warnings."""
    result = subprocess.run(
        ["node", str(_SCRIPT), server_url],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode == 2:
        stderr = result.stderr.strip()
        if "Playwright not installed" in stderr or "Cannot find module" in stderr:
            pytest.skip(f"Playwright not available: {stderr}")
        pytest.fail(f"Hydration check script error:\nstdout: {result.stdout}\nstderr: {stderr}")

    assert result.returncode == 0, f"Hydration warnings detected:\n{result.stdout}\n{result.stderr}"
