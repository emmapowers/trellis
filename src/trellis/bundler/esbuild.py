"""Esbuild binary management."""

from __future__ import annotations

import platform
import tarfile
from pathlib import Path

import httpx

from .utils import BIN_DIR, ESBUILD_VERSION, safe_extract


def get_platform() -> str:
    """Return esbuild platform string like 'darwin-arm64'."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    os_map = {"darwin": "darwin", "linux": "linux", "windows": "win32"}
    arch_map = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64", "amd64": "x64"}

    os_name = os_map.get(system)
    arch = arch_map.get(machine)
    if not os_name or not arch:
        raise RuntimeError(f"Unsupported platform: {system}-{machine}")
    return f"{os_name}-{arch}"


def ensure_esbuild() -> Path:
    """Download esbuild binary if not cached."""
    plat = get_platform()
    binary_name = "esbuild.exe" if plat.startswith("win32") else "esbuild"
    extract_dir = BIN_DIR / f"esbuild-{ESBUILD_VERSION}-{plat}"
    binary_path = extract_dir / "package" / "bin" / binary_name

    if binary_path.exists():
        return binary_path

    url = f"https://registry.npmjs.org/@esbuild/{plat}/-/{plat}-{ESBUILD_VERSION}.tgz"
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    tgz_path = BIN_DIR / f"{plat}-{ESBUILD_VERSION}.tgz"

    with httpx.stream("GET", url, follow_redirects=True) as r:
        r.raise_for_status()
        with open(tgz_path, "wb") as f:
            f.writelines(r.iter_bytes())

    extract_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tgz_path) as tar:
        safe_extract(tar, extract_dir)

    tgz_path.unlink()
    binary_path.chmod(0o755)
    return binary_path
