"""Unit tests for desktop E2E harness process management."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from tests.e2e.desktop_harness import E2E_RESULT_PREFIX, run_desktop_e2e_scenario


def test_parses_payload_from_custom_command(tmp_path: Path) -> None:
    script = (
        "print("
        + repr(f'{E2E_RESULT_PREFIX}{{"success": true, "scenario": "unit"}}')
        + ", flush=True)"
    )
    result = run_desktop_e2e_scenario(
        app_root=tmp_path,
        scenario="markdown_external_link",
        timeout_seconds=5,
        command=[sys.executable, "-c", script],
    )

    assert result.return_code == 0
    assert result.payload == {"success": True, "scenario": "unit"}


def test_sets_timeout_env_from_timeout_seconds(tmp_path: Path) -> None:
    script = (
        "import json, os;"
        f"print({E2E_RESULT_PREFIX!r} + json.dumps("
        '{"timeout": os.environ.get("TRELLIS_DESKTOP_E2E_TIMEOUT_SECONDS")}'
        "), flush=True)"
    )
    result = run_desktop_e2e_scenario(
        app_root=tmp_path,
        scenario="markdown_external_link",
        timeout_seconds=12.5,
        command=[sys.executable, "-c", script],
    )

    assert result.return_code == 0
    assert result.payload == {"timeout": "12.5"}


def test_timeout_terminates_spawned_child_process(tmp_path: Path) -> None:
    child_pid_file = tmp_path / "child.pid"
    script = (
        "import pathlib, subprocess, sys, time;"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']);"
        f"pathlib.Path({str(child_pid_file)!r}).write_text(str(child.pid));"
        "print('started', flush=True);"
        "time.sleep(60)"
    )

    result = run_desktop_e2e_scenario(
        app_root=tmp_path,
        scenario="markdown_external_link",
        timeout_seconds=0.6,
        command=[sys.executable, "-c", script],
    )

    assert result.return_code != 0
    assert child_pid_file.exists()
    child_pid = int(child_pid_file.read_text().strip())
    assert _wait_for_process_exit(child_pid, timeout_seconds=3.0)


def _wait_for_process_exit(pid: int, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _is_process_alive(pid):
            return True
        time.sleep(0.05)
    return not _is_process_alive(pid)


def _is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
