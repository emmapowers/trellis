"""Toolchain management for Trellis packaging.

Downloads and manages external toolchain binaries (Rust, Tauri CLI,
Python standalone) needed for desktop app packaging.
"""

from trellis.toolchain.platform import get_rust_target
from trellis.toolchain.python_standalone import (
    PYTHON_STANDALONE_RELEASE,
    PYTHON_STANDALONE_VERSION,
    PythonStandalone,
    ensure_python_standalone,
)
from trellis.toolchain.rustup import MINIMUM_RUST_VERSION, RustToolchain, ensure_rustup
from trellis.toolchain.tauri_cli import TAURI_CLI_VERSION, ensure_tauri_cli

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
