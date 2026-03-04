"""Toolchain management for Trellis packaging.

Downloads and manages external toolchain binaries (Rust, Tauri CLI,
Python standalone) needed for desktop app packaging.
"""

from trellis.toolchain.platform import get_rust_target
from trellis.toolchain.python_standalone import PythonStandalone, ensure_python_standalone
from trellis.toolchain.rustup import RustToolchain, ensure_rustup
from trellis.toolchain.tauri_cli import ensure_tauri_cli

MINIMUM_RUST_VERSION = "1.93.1"
TAURI_CLI_VERSION = "2.10.0"
PYTHON_STANDALONE_VERSION = "3.13.1"
# Release tag for python-build-standalone (contains the build date)
PYTHON_STANDALONE_RELEASE = "20250106"

__all__ = [
    "MINIMUM_RUST_VERSION",
    "PYTHON_STANDALONE_RELEASE",
    "PYTHON_STANDALONE_VERSION",
    "TAURI_CLI_VERSION",
    "PythonStandalone",
    "RustToolchain",
    "ensure_python_standalone",
    "ensure_rustup",
    "ensure_tauri_cli",
    "get_rust_target",
]
