"""Desktop E2E harness utilities."""

from __future__ import annotations

import json
import os
import signal
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
    command: list[str] | None = None,
) -> DesktopE2ERunResult:
    """Run a desktop app with an E2E scenario and parse harness output."""
    env = dict(os.environ)
    env["TRELLIS_DESKTOP_E2E_SCENARIO"] = scenario
    env["TRELLIS_DESKTOP_E2E_TIMEOUT_SECONDS"] = str(timeout_seconds)
    env["TRELLIS_DESKTOP_E2E_INITIAL_DELAY_SECONDS"] = "0.8"

    runner_command = command or [
        sys.executable,
        "-m",
        "trellis.cli",
        "--app-root",
        str(app_root),
        "run",
        "--desktop",
    ]

    process = subprocess.Popen(
        runner_command,
        cwd=app_root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=os.name == "posix",
    )

    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = _coerce_output(exc.stdout)
        stderr = _coerce_output(exc.stderr)
        _terminate_process_tree(process, force=False)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _terminate_process_tree(process, force=True)
            process.wait(timeout=3)

    return_code = process.returncode if process.returncode is not None else 124
    if timed_out and return_code == 0:
        return_code = 124

    payload = _parse_e2e_payload(stdout)
    return DesktopE2ERunResult(
        return_code=return_code,
        stdout=stdout,
        stderr=stderr,
        payload=payload,
    )


def _parse_e2e_payload(stdout: str) -> dict[str, object] | None:
    for line in stdout.splitlines():
        if line.startswith(E2E_RESULT_PREFIX):
            return json.loads(line.removeprefix(E2E_RESULT_PREFIX))
    return None


def _coerce_output(output: str | bytes | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode(errors="replace")
    return output


def _terminate_process_tree(process: subprocess.Popen[str], *, force: bool) -> None:
    if process.poll() is not None:
        return

    if os.name == "posix":
        _terminate_posix_process_group(process, force=force)
        return

    if force:
        process.kill()
    else:
        process.terminate()


def _terminate_posix_process_group(process: subprocess.Popen[str], *, force: bool) -> None:
    try:
        process_group = os.getpgid(process.pid)
    except ProcessLookupError:
        return

    termination_signal = signal.SIGKILL if force else signal.SIGTERM
    try:
        os.killpg(process_group, termination_signal)
    except ProcessLookupError:
        return
