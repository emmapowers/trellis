"""Platform detection for Rust target triples."""

from __future__ import annotations

import platform


def get_rust_target() -> str:
    """Return the Rust target triple for the current platform.

    Maps platform.system() + platform.machine() to Rust target triples
    like 'aarch64-apple-darwin' or 'x86_64-unknown-linux-gnu'.

    Raises:
        RuntimeError: If the current platform is not supported.
    """
    system = platform.system().lower()
    machine = platform.machine().lower()

    targets: dict[tuple[str, str], str] = {
        ("darwin", "arm64"): "aarch64-apple-darwin",
        ("darwin", "aarch64"): "aarch64-apple-darwin",
        ("darwin", "x86_64"): "x86_64-apple-darwin",
        ("linux", "x86_64"): "x86_64-unknown-linux-gnu",
        ("linux", "amd64"): "x86_64-unknown-linux-gnu",
        ("linux", "aarch64"): "aarch64-unknown-linux-gnu",
        ("linux", "arm64"): "aarch64-unknown-linux-gnu",
        ("windows", "amd64"): "x86_64-pc-windows-msvc",
        ("windows", "x86_64"): "x86_64-pc-windows-msvc",
        ("windows", "arm64"): "aarch64-pc-windows-msvc",
        ("windows", "aarch64"): "aarch64-pc-windows-msvc",
    }

    target = targets.get((system, machine))
    if target is None:
        raise RuntimeError(f"Unsupported platform: {system}-{machine}")

    return target
