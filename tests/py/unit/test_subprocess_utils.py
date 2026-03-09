"""Tests for cross-platform subprocess utilities."""

from __future__ import annotations

import signal
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from trellis.utils.subprocess import start_child_process, stop_child_process


class TestStartChildProcess:
    """Tests for start_child_process platform-specific behavior."""

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX only")
    def test_posix_sets_start_new_session(self) -> None:
        """On POSIX, start_new_session=True is passed to Popen."""
        with patch("trellis.utils.subprocess.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            start_child_process(["echo", "hello"])
            kwargs = mock_popen.call_args[1]
            assert kwargs["start_new_session"] is True

    @pytest.mark.skipif(sys.platform != "linux", reason="Linux only")
    def test_linux_sets_preexec_fn(self) -> None:
        """On Linux, a preexec_fn is set for prctl."""
        with patch("trellis.utils.subprocess.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            start_child_process(["echo", "hello"])
            kwargs = mock_popen.call_args[1]
            assert kwargs["preexec_fn"] is not None

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
    def test_macos_no_preexec_fn(self) -> None:
        """On macOS, no preexec_fn is set (no prctl equivalent)."""
        with patch("trellis.utils.subprocess.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            start_child_process(["echo", "hello"])
            kwargs = mock_popen.call_args[1]
            assert "preexec_fn" not in kwargs

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
    def test_windows_sets_creation_flags(self) -> None:
        """On Windows, CREATE_NEW_PROCESS_GROUP is set."""
        with patch("trellis.utils.subprocess.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 1234
            mock_popen.return_value = mock_proc
            start_child_process(["echo", "hello"])
            kwargs = mock_popen.call_args[1]
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            assert kwargs["creationflags"] & CREATE_NEW_PROCESS_GROUP

    def test_passes_extra_kwargs(self) -> None:
        """Extra kwargs are forwarded to Popen."""
        with patch("trellis.utils.subprocess.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 1234
            mock_popen.return_value = mock_proc
            start_child_process(
                ["echo", "hello"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            kwargs = mock_popen.call_args[1]
            assert kwargs["stdout"] == subprocess.PIPE
            assert kwargs["stderr"] == subprocess.PIPE


class TestStopChildProcess:
    """Tests for stop_child_process behavior."""

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX only")
    def test_posix_sends_sigterm_to_group(self) -> None:
        """On POSIX, sends SIGTERM to the process group."""
        mock_proc = MagicMock()
        mock_proc.pid = 1234

        with (
            patch("trellis.utils.subprocess.os.getpgid", return_value=1234) as mock_getpgid,
            patch("trellis.utils.subprocess.os.killpg") as mock_killpg,
        ):
            stop_child_process(mock_proc)
            mock_getpgid.assert_called_with(1234)
            mock_killpg.assert_called_with(1234, signal.SIGTERM)
            mock_proc.wait.assert_called_once()

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX only")
    def test_posix_escalates_to_sigkill_on_timeout(self) -> None:
        """On POSIX, escalates to SIGKILL when SIGTERM times out."""
        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_proc.wait.side_effect = [subprocess.TimeoutExpired("cmd", 5), None]

        with (
            patch("trellis.utils.subprocess.os.getpgid", return_value=1234),
            patch("trellis.utils.subprocess.os.killpg") as mock_killpg,
        ):
            stop_child_process(mock_proc, timeout=1.0)
            calls = mock_killpg.call_args_list
            assert len(calls) == 2
            assert calls[0].args == (1234, signal.SIGTERM)
            assert calls[1].args == (1234, signal.SIGKILL)

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
    def test_windows_calls_terminate(self) -> None:
        """On Windows, calls process.terminate()."""
        mock_proc = MagicMock()
        stop_child_process(mock_proc)
        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_once()

    def test_handles_already_dead_process(self) -> None:
        """Does not raise when process is already dead."""
        mock_proc = MagicMock()
        mock_proc.pid = 1234

        if sys.platform == "win32":
            mock_proc.terminate.side_effect = ProcessLookupError
        else:
            with (
                patch(
                    "trellis.utils.subprocess.os.getpgid",
                    side_effect=ProcessLookupError,
                ),
            ):
                # Should not raise
                stop_child_process(mock_proc)
                return

        # Windows path
        stop_child_process(mock_proc)
