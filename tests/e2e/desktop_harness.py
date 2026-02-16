"""Desktop E2E harness utilities."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

E2E_RESULT_PREFIX = "TRELLIS_DESKTOP_E2E_RESULT="


@dataclass(frozen=True, slots=True)
class DesktopE2ERunResult:
    """Outcome of a desktop E2E harness run."""

    return_code: int
    stdout: str
    stderr: str
    payload: dict[str, object] | None


def run_desktop_e2e_scenario(
    *,
    app_root: Path,
    scenario: str,
    timeout_seconds: float = 30.0,
) -> DesktopE2ERunResult:
    """Run a desktop app with an E2E scenario and parse harness output."""
    env = dict(os.environ)
    env["TRELLIS_DESKTOP_E2E_SCENARIO"] = scenario
    env["TRELLIS_DESKTOP_E2E_TIMEOUT_SECONDS"] = "8"
    env["TRELLIS_DESKTOP_E2E_INITIAL_DELAY_SECONDS"] = "0.8"

    process = subprocess.run(
        [sys.executable, "-m", "trellis.cli", "--app-root", str(app_root), "run", "--desktop"],
        cwd=app_root,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    payload = _parse_e2e_payload(process.stdout)
    return DesktopE2ERunResult(
        return_code=process.returncode,
        stdout=process.stdout,
        stderr=process.stderr,
        payload=payload,
    )


def _parse_e2e_payload(stdout: str) -> dict[str, object] | None:
    for line in stdout.splitlines():
        if line.startswith(E2E_RESULT_PREFIX):
            return json.loads(line.removeprefix(E2E_RESULT_PREFIX))
    return None
