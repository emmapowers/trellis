"""Toolchain management for Trellis packaging.

Downloads and manages external toolchain binaries (Rust, Tauri CLI,
Python standalone) needed for desktop app packaging.
"""

from trellis.packaging.toolchain.platform import get_rust_target
from trellis.packaging.toolchain.python_standalone import (
    PYTHON_STANDALONE_RELEASE,
    PYTHON_STANDALONE_VERSION,
    PythonStandalone,
    ensure_python_standalone,
)
from trellis.packaging.toolchain.rustup import MINIMUM_RUST_VERSION, RustToolchain, ensure_rustup
from trellis.packaging.toolchain.tauri_cli import TAURI_CLI_VERSION, ensure_tauri_cli

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
