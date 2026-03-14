"""Lazy provisioning for the PyTauri wheel-backed desktop runtime."""

from __future__ import annotations

import importlib
import shutil
import site
import subprocess
import sys
import tempfile
import zipfile
from importlib import metadata
from pathlib import Path
from sysconfig import get_platform

from trellis.bundler.utils import CACHE_DIR


def _current_ext_mod_entry_points() -> list[metadata.EntryPoint]:
    """Return visible PyTauri runtime providers."""
    return list(metadata.entry_points(group="pytauri", name="ext_mod"))


def _installed_pytauri_version() -> str:
    """Return the installed pytauri package version."""
    return metadata.version("pytauri")


def _python_version_display() -> str:
    """Return the current Python major.minor version."""
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def _download_wheel(version: str, download_dir: Path) -> Path:
    """Download the exact matching pytauri-wheel into the cache."""
    download_dir.mkdir(parents=True, exist_ok=True)

    platform_key = get_platform().replace("-", "_").replace(".", "_")
    cache_tag = sys.implementation.cache_tag or "py"
    version_dir = download_dir / f"{version}-{cache_tag}-{platform_key}"
    version_dir.mkdir(parents=True, exist_ok=True)

    existing_wheels = sorted(version_dir.glob("*.whl"))
    if len(existing_wheels) == 1:
        return existing_wheels[0]
    if len(existing_wheels) > 1:
        return max(existing_wheels, key=lambda wheel: wheel.stat().st_mtime)

    temp_download_dir = Path(tempfile.mkdtemp(prefix="download-", dir=version_dir))
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--only-binary=:all:",
                "--no-deps",
                "--dest",
                str(temp_download_dir),
                f"pytauri-wheel=={version}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        wheels = sorted(temp_download_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(
                f"Trellis could not find a published binary wheel for pytauri-wheel=={version}."
            )

        target_path = version_dir / wheels[0].name
        if not target_path.exists():
            shutil.move(str(wheels[0]), str(target_path))
        return target_path
    finally:
        shutil.rmtree(temp_download_dir, ignore_errors=True)


def _extract_wheel(wheel_path: Path, extract_dir: Path) -> Path:
    """Extract a wheel archive into a cache directory."""
    if extract_dir.exists():
        return extract_dir

    extract_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_extract_dir = Path(tempfile.mkdtemp(prefix=f"{extract_dir.name}-", dir=extract_dir.parent))
    try:
        with zipfile.ZipFile(wheel_path, "r") as zf:
            root = temp_extract_dir.resolve()
            for member in zf.infolist():
                target_path = (temp_extract_dir / member.filename).resolve()
                if not target_path.is_relative_to(root):
                    raise ValueError(f"Wheel contains path traversal: {member.filename}")
            zf.extractall(temp_extract_dir)

        temp_extract_dir.replace(extract_dir)
        return extract_dir
    except Exception:
        shutil.rmtree(temp_extract_dir, ignore_errors=True)
        raise


def _stage_wheel(extract_dir: Path) -> None:
    """Expose extracted wheel contents to importlib metadata and imports."""
    site.addsitedir(str(extract_dir))
    importlib.invalidate_caches()


def _format_provider(provider: metadata.EntryPoint) -> str:
    """Format a runtime provider for error messages."""
    dist = provider.dist
    if dist is None:
        dist_name = "UNKNOWN"
    else:
        dist_name = getattr(dist, "name", str(dist))
    return f"{dist_name}: {provider.value}"


def ensure_pytauri_runtime() -> None:
    """Ensure a PyTauri runtime provider is available in the current environment."""
    if getattr(sys, "_pytauri_standalone", False):
        return

    providers = _current_ext_mod_entry_points()
    if len(providers) == 1:
        return
    if len(providers) > 1:
        provider_list = "\n".join(f"- {_format_provider(provider)}" for provider in providers)
        raise RuntimeError(
            f"Exactly one `pytauri` runtime provider is expected, but found:\n{provider_list}"
        )

    version = _installed_pytauri_version()
    download_dir = CACHE_DIR / "pytauri-wheel" / "downloads"
    try:
        wheel_path = _download_wheel(version, download_dir)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Trellis could not provision a desktop runtime for "
            f"pytauri {version} on Python {_python_version_display()}.\n\n"
            f"It attempted to download pytauri-wheel=={version} for the current environment, "
            "but no compatible published binary wheel was available.\n\n"
            "Install pytauri-wheel manually in this environment, or provide your own "
            "compatible build."
        ) from exc

    extract_dir = CACHE_DIR / "pytauri-wheel" / wheel_path.stem
    _stage_wheel(_extract_wheel(wheel_path, extract_dir))

    providers = _current_ext_mod_entry_points()
    if len(providers) != 1:
        raise RuntimeError(
            "Trellis could not activate the downloaded PyTauri runtime. "
            "Install pytauri-wheel manually in this environment."
        )
