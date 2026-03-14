"""Python standalone build management for packaging."""

from __future__ import annotations

import tarfile
from dataclasses import dataclass
from pathlib import Path

import httpx

from trellis.bundler.utils import BIN_DIR, safe_extract
from trellis.packaging.toolchain.platform import get_rust_target

PYTHON_STANDALONE_VERSION = "3.13.1"
PYTHON_STANDALONE_RELEASE = "20250106"


@dataclass
class PythonStandalone:
    """Paths to a standalone Python installation."""

    python_bin: Path
    base_dir: Path


def ensure_python_standalone() -> PythonStandalone:
    """Download a standalone Python build if not cached.

    Downloads from indygreg/python-build-standalone GitHub releases.
    Windows uses the `-shared` variant for embedding.

    Returns:
        PythonStandalone with paths to python binary and base directory
    """
    target = get_rust_target()
    is_windows = target.endswith("-msvc")

    install_dir = BIN_DIR / f"python-standalone-{PYTHON_STANDALONE_VERSION}-{target}"

    if is_windows:
        python_bin = install_dir / "python" / "python.exe"
    else:
        python_bin = install_dir / "python" / "bin" / "python3"
    base_dir = install_dir / "python"

    if python_bin.exists():
        return PythonStandalone(python_bin=python_bin, base_dir=base_dir)

    # Build download URL
    variant = "shared-install_only_stripped" if is_windows else "install_only_stripped"
    url = (
        f"https://github.com/indygreg/python-build-standalone/releases/download/"
        f"{PYTHON_STANDALONE_RELEASE}/"
        f"cpython-{PYTHON_STANDALONE_VERSION}+{PYTHON_STANDALONE_RELEASE}-"
        f"{target}-{variant}.tar.gz"
    )

    BIN_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = BIN_DIR / f"python-standalone-{PYTHON_STANDALONE_VERSION}-{target}.tar.gz"

    timeout = httpx.Timeout(60.0, connect=10.0)
    with httpx.stream("GET", url, follow_redirects=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(archive_path, "wb") as f:
            f.writelines(r.iter_bytes())

    install_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as tf:
        safe_extract(tf, install_dir)

    archive_path.unlink()

    if not python_bin.exists():
        raise RuntimeError(f"Python binary missing after extraction: {python_bin}")

    python_bin.chmod(0o755)
    return PythonStandalone(python_bin=python_bin, base_dir=base_dir)
