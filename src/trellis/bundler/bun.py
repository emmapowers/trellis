"""Bun runtime binary management."""

from __future__ import annotations

import platform
import zipfile
from pathlib import Path

import httpx

from .utils import BIN_DIR, BUN_VERSION


def get_bun_platform() -> str:
    """Return Bun platform string like 'darwin-aarch64'.

    Bun uses different naming conventions than other tools:
    - ARM64 is called 'aarch64' (not 'arm64')
    - Windows is called 'windows' (not 'win32')
    - Windows ARM is not supported
    """
    system = platform.system().lower()
    machine = platform.machine().lower()

    os_map = {"darwin": "darwin", "linux": "linux", "windows": "windows"}

    # Bun uses aarch64 for ARM, x64 for Intel
    # Windows ARM is not supported by Bun
    arch_map = {
        "arm64": "aarch64",
        "aarch64": "aarch64",
        "x86_64": "x64",
        "amd64": "x64",
    }

    os_name = os_map.get(system)
    arch = arch_map.get(machine)

    # Windows ARM is not supported
    if os_name == "windows" and arch == "aarch64":
        raise RuntimeError(f"Unsupported platform: {system}-{machine} (Windows ARM not supported)")

    if not os_name or not arch:
        raise RuntimeError(f"Unsupported platform: {system}-{machine}")

    return f"{os_name}-{arch}"


def ensure_bun() -> Path:
    """Download Bun binary if not cached.

    Downloads from GitHub releases and extracts the ZIP archive.
    Returns the path to the bun executable.
    """
    plat = get_bun_platform()
    binary_name = "bun.exe" if plat.startswith("windows") else "bun"
    extract_dir = BIN_DIR / f"bun-{BUN_VERSION}-{plat}"
    # Bun ZIPs contain a folder like "bun-darwin-aarch64/bun"
    binary_path = extract_dir / f"bun-{plat}" / binary_name

    if binary_path.exists():
        return binary_path

    url = f"https://github.com/oven-sh/bun/releases/download/bun-v{BUN_VERSION}/bun-{plat}.zip"
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = BIN_DIR / f"bun-{plat}-{BUN_VERSION}.zip"

    timeout = httpx.Timeout(60.0, connect=10.0)
    with httpx.stream("GET", url, follow_redirects=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            f.writelines(r.iter_bytes())

    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Validate paths to prevent zip-slip attacks
        for member in zf.infolist():
            member_path = (extract_dir / member.filename).resolve()
            if not member_path.is_relative_to(extract_dir.resolve()):
                raise ValueError(f"Zip contains path traversal: {member.filename}")
        zf.extractall(extract_dir)

    zip_path.unlink()

    if not binary_path.exists():
        raise RuntimeError(f"Bun binary missing after extraction: {binary_path}")

    binary_path.chmod(0o755)
    return binary_path
