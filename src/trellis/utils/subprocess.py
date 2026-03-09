"""Cross-platform child process management with process group cleanup.

Ensures child processes die when the parent dies, using platform-specific
mechanisms:
- Linux: prctl(PR_SET_PDEATHSIG) for automatic child death on parent exit
- macOS: Process groups with killpg for graceful cleanup
- Windows: Job Objects with KILL_ON_JOB_CLOSE for automatic cleanup
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import typing as tp

logger = logging.getLogger(__name__)

_IS_WINDOWS = sys.platform == "win32"
_IS_LINUX = sys.platform == "linux"


def start_child_process(cmd: list[str], **popen_kwargs: tp.Any) -> subprocess.Popen[bytes]:
    """Start a child process with platform-specific cleanup guarantees.

    On Linux, sets PR_SET_PDEATHSIG so the child receives SIGTERM when the
    parent dies (survives even SIGKILL of parent).

    On macOS, starts in a new session for killpg-based cleanup.

    On Windows, creates a Job Object with KILL_ON_JOB_CLOSE and assigns the
    process to it. The job handle is stored on process._job_handle.

    Args:
        cmd: Command and arguments to execute
        **popen_kwargs: Additional arguments passed to subprocess.Popen

    Returns:
        The started Popen process
    """
    if _IS_WINDOWS:
        return _start_windows(cmd, **popen_kwargs)
    return _start_posix(cmd, **popen_kwargs)


def stop_child_process(process: subprocess.Popen[bytes], timeout: float = 5.0) -> None:
    """Stop a child process gracefully, with escalation to SIGKILL.

    On POSIX, sends SIGTERM to the process group, then SIGKILL on timeout.
    On Windows, calls terminate() then kill() on timeout, and closes the
    job handle if present.

    Args:
        process: The process to stop
        timeout: Seconds to wait after SIGTERM before escalating to SIGKILL
    """
    if _IS_WINDOWS:
        _stop_windows(process, timeout)
    else:
        _stop_posix(process, timeout)


def _start_posix(cmd: list[str], **popen_kwargs: tp.Any) -> subprocess.Popen[bytes]:
    """Start a child process on POSIX with process group isolation."""
    import signal  # noqa: PLC0415 — only needed on POSIX

    popen_kwargs["start_new_session"] = True

    if _IS_LINUX:
        # On Linux, use prctl to auto-kill child when parent dies
        original_preexec = popen_kwargs.pop("preexec_fn", None)

        def _preexec() -> None:
            _set_pdeathsig(signal.SIGTERM)
            if original_preexec is not None:
                original_preexec()

        popen_kwargs["preexec_fn"] = _preexec

    return subprocess.Popen(cmd, **popen_kwargs)


def _set_pdeathsig(sig: int) -> None:
    """Set parent death signal via prctl (Linux only)."""
    import ctypes  # noqa: PLC0415 — only needed on Linux
    import ctypes.util  # noqa: PLC0415

    PR_SET_PDEATHSIG = 1
    libc_name = ctypes.util.find_library("c")
    libc = ctypes.CDLL(libc_name or None, use_errno=True)
    result = libc.prctl(PR_SET_PDEATHSIG, sig, 0, 0, 0)
    if result != 0:
        errno = ctypes.get_errno()
        logger.warning("prctl(PR_SET_PDEATHSIG) failed with errno %d", errno)


def _stop_posix(process: subprocess.Popen[bytes], timeout: float) -> None:
    """Stop a POSIX process group gracefully."""
    import signal  # noqa: PLC0415 — only needed on POSIX

    # If the process has already been reaped, its PID may have been recycled.
    # Calling killpg would signal an unrelated process group.
    if process.returncode is not None:
        return

    try:
        pgid = os.getpgid(process.pid)
        os.killpg(pgid, signal.SIGTERM)
        process.wait(timeout=timeout)
    except ProcessLookupError:
        pass  # Already dead
    except subprocess.TimeoutExpired:
        try:
            pgid = os.getpgid(process.pid)
            os.killpg(pgid, signal.SIGKILL)
            process.wait(timeout=2)
        except (ProcessLookupError, OSError):
            pass
    except OSError:
        pass  # Process already gone


def _start_windows(cmd: list[str], **popen_kwargs: tp.Any) -> subprocess.Popen[bytes]:
    """Start a child process on Windows with Job Object cleanup."""
    import ctypes  # noqa: PLC0415 — only needed on Windows
    import ctypes.wintypes  # noqa: PLC0415

    CREATE_NEW_PROCESS_GROUP = 0x00000200
    popen_kwargs.setdefault("creationflags", 0)
    popen_kwargs["creationflags"] |= CREATE_NEW_PROCESS_GROUP

    process = subprocess.Popen(cmd, **popen_kwargs)

    # Create a Job Object and assign the process to it
    get_last_error = ctypes.get_last_error  # type: ignore[attr-defined]
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        kernel32.CreateJobObjectW.restype = ctypes.wintypes.HANDLE
        kernel32.SetInformationJobObject.restype = ctypes.wintypes.BOOL
        kernel32.OpenProcess.restype = ctypes.wintypes.HANDLE
        kernel32.AssignProcessToJobObject.restype = ctypes.wintypes.BOOL
        kernel32.CloseHandle.restype = ctypes.wintypes.BOOL

        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            logger.warning("CreateJobObjectW failed (error %d)", get_last_error())
            return process

        try:
            # Set JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
                _fields_ = [  # noqa: RUF012 — ctypes API
                    ("PerProcessUserTimeLimit", ctypes.c_int64),
                    ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", ctypes.wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", ctypes.wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", ctypes.wintypes.DWORD),
                    ("SchedulingClass", ctypes.wintypes.DWORD),
                ]

            class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
                _fields_ = [  # noqa: RUF012 — ctypes API
                    ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                    ("IoInfo", ctypes.c_byte * 48),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t),
                ]

            JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
            JobObjectExtendedLimitInformation = 9

            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

            if not kernel32.SetInformationJobObject(
                job,
                JobObjectExtendedLimitInformation,
                ctypes.byref(info),
                ctypes.sizeof(info),
            ):
                logger.warning("SetInformationJobObject failed (error %d)", get_last_error())
                kernel32.CloseHandle(job)
                return process

            # PROCESS_SET_QUOTA | PROCESS_TERMINATE for AssignProcessToJobObject
            proc_handle = kernel32.OpenProcess(0x100 | 0x1, False, process.pid)
            if not proc_handle:
                logger.warning("OpenProcess failed (error %d)", get_last_error())
                kernel32.CloseHandle(job)
                return process

            try:
                if not kernel32.AssignProcessToJobObject(job, proc_handle):
                    logger.warning(
                        "AssignProcessToJobObject failed (error %d)",
                        get_last_error(),
                    )
                    kernel32.CloseHandle(job)
                    return process
            finally:
                kernel32.CloseHandle(proc_handle)

            process._job_handle = job  # type: ignore[attr-defined]
        except Exception:
            kernel32.CloseHandle(job)
            raise
    except Exception:
        logger.warning("Failed to create Windows Job Object", exc_info=True)

    return process


def _stop_windows(process: subprocess.Popen[bytes], timeout: float) -> None:
    """Stop a Windows process gracefully."""
    try:
        process.terminate()
        process.wait(timeout=timeout)
    except ProcessLookupError:
        pass  # Already dead
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=2)
        except (ProcessLookupError, OSError):
            pass
    except OSError:
        pass  # Process already gone
    finally:
        # Close the Job Object handle if present
        job_handle = getattr(process, "_job_handle", None)
        if job_handle is not None:
            try:
                import ctypes  # noqa: PLC0415

                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
                kernel32.CloseHandle.restype = ctypes.wintypes.BOOL
                kernel32.CloseHandle(job_handle)
            except Exception:
                pass
