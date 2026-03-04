"""Tauri CLI binary management."""

from __future__ import annotations

import subprocess
import tarfile
import zipfile
from pathlib import Path

import httpx

from trellis.bundler.utils import BIN_DIR, safe_extract
from trellis.toolchain.platform import get_rust_target
from trellis.toolchain.rustup import RustToolchain

TAURI_CLI_VERSION = "2.10.0"


def ensure_tauri_cli(rust: RustToolchain) -> Path:
    """Download the Tauri CLI binary if not cached.

    Tries prebuilt binaries from GitHub releases first. Falls back to
    `cargo install` for platforms without prebuilt binaries (e.g. Linux ARM64).

    Args:
        rust: RustToolchain with paths to cargo/rustc

    Returns:
        Path to the cargo-tauri executable
    """
    target = get_rust_target()
    is_windows = target.endswith("-msvc")
    binary_name = "cargo-tauri.exe" if is_windows else "cargo-tauri"

    extract_dir = BIN_DIR / f"tauri-cli-{TAURI_CLI_VERSION}"
    binary_path = extract_dir / binary_name

    if binary_path.exists():
        return binary_path

    # Try prebuilt binary from GitHub releases
    ext = "zip" if is_windows else "tgz"
    url = (
        f"https://github.com/tauri-apps/tauri/releases/download/"
        f"tauri-cli-v{TAURI_CLI_VERSION}/cargo-tauri-{target}.{ext}"
    )

    BIN_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = BIN_DIR / f"cargo-tauri-{target}-{TAURI_CLI_VERSION}.{ext}"

    try:
        timeout = httpx.Timeout(60.0, connect=10.0)
        with httpx.stream("GET", url, follow_redirects=True, timeout=timeout) as r:
            r.raise_for_status()
            with open(archive_path, "wb") as f:
                f.writelines(r.iter_bytes())

        extract_dir.mkdir(parents=True, exist_ok=True)

        if is_windows:
            with zipfile.ZipFile(archive_path, "r") as zf:
                for member in zf.infolist():
                    member_path = (extract_dir / member.filename).resolve()
                    if not member_path.is_relative_to(extract_dir.resolve()):
                        raise ValueError(f"Zip contains path traversal: {member.filename}")
                zf.extractall(extract_dir)
        else:
            with tarfile.open(archive_path, "r:gz") as tf:
                safe_extract(tf, extract_dir)

        archive_path.unlink()

        if not binary_path.exists():
            raise RuntimeError(f"Tauri CLI binary missing after extraction: {binary_path}")

        binary_path.chmod(0o755)
        return binary_path

    except Exception:
        archive_path.unlink(missing_ok=True)
        # Fall back to cargo install
        return _cargo_install_tauri_cli(rust)


def _cargo_install_tauri_cli(rust: RustToolchain) -> Path:
    """Install Tauri CLI via cargo as a fallback."""
    subprocess.run(
        [str(rust.cargo_bin), "install", "tauri-cli", "--version", TAURI_CLI_VERSION],
        check=True,
        env=rust.env(),
    )

    binary_name = "cargo-tauri.exe" if str(rust.cargo_bin).endswith(".exe") else "cargo-tauri"
    installed_path = rust.cargo_home / "bin" / binary_name

    if not installed_path.exists():
        raise RuntimeError(f"Tauri CLI not found after cargo install: {installed_path}")

    return installed_path
