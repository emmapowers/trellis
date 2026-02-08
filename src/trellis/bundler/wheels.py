"""Wheel building, dependency resolution, and bundle creation for browser platform.

Resolves Python dependencies for the emscripten/Pyodide target at build time.
Uses the `packaging` library to evaluate PEP 508 markers against the target
environment, since pip's --platform flag does NOT evaluate markers.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from packaging.requirements import Requirement

logger = logging.getLogger(__name__)

PYODIDE_VERSION = "0.29.0"
PYODIDE_LOCKFILE_URL = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/pyodide-lock.json"


@dataclass
class ResolvedDependencies:
    """Result of dependency resolution for the browser target."""

    wheel_paths: list[Path] = field(default_factory=list)
    pyodide_packages: list[str] = field(default_factory=list)


def build_emscripten_env(python_version: str) -> dict[str, str]:
    """Build PEP 508 environment dict for emscripten/Pyodide target.

    Args:
        python_version: Full Python version string from Pyodide lockfile (e.g. "3.12.7")
    """
    parts = python_version.split(".")
    major, minor = parts[0], parts[1]
    return {
        "os_name": "posix",
        "sys_platform": "emscripten",
        "platform_system": "Emscripten",
        "platform_machine": "wasm32",
        "platform_release": "",
        "implementation_name": "cpython",
        "python_version": f"{major}.{minor}",
        "python_full_version": python_version,
        "platform_version": "",
        "implementation_version": python_version,
    }


def filter_requirements(requirements: list[Requirement], env: dict[str, str]) -> list[Requirement]:
    """Evaluate PEP 508 markers and return applicable requirements.

    Args:
        requirements: List of parsed requirements
        env: PEP 508 environment dict (from build_emscripten_env)

    Returns:
        Requirements that apply to the target environment
    """
    result = []
    for req in requirements:
        if req.marker is None:
            result.append(req)
        elif req.marker.evaluate(env):
            result.append(req)
    return result


def read_wheel_requirements(wheel_path: Path) -> list[str]:
    """Read Requires-Dist entries from a wheel's METADATA.

    Args:
        wheel_path: Path to .whl file

    Returns:
        List of requirement strings
    """
    with zipfile.ZipFile(wheel_path) as zf:
        for name in zf.namelist():
            if name.endswith(".dist-info/METADATA"):
                metadata = zf.read(name).decode("utf-8")
                return [
                    line[len("Requires-Dist: ") :]
                    for line in metadata.splitlines()
                    if line.startswith("Requires-Dist: ")
                ]
    return []


def read_wheel_record(wheel_path: Path) -> list[str]:
    """Read file paths from a wheel's RECORD, excluding .dist-info entries.

    Args:
        wheel_path: Path to .whl file

    Returns:
        List of package file paths (e.g. ["mypkg/__init__.py", "mypkg/core.py"])
    """
    with zipfile.ZipFile(wheel_path) as zf:
        for name in zf.namelist():
            if name.endswith(".dist-info/RECORD"):
                data = zf.read(name).decode("utf-8")
                if not data.strip():
                    return []
                reader = csv.reader(io.StringIO(data))
                return [row[0] for row in reader if row and ".dist-info/" not in row[0]]
    return []


def get_pyodide_package_names(lockfile: dict[str, Any]) -> set[str]:
    """Extract package names from Pyodide lockfile.

    Args:
        lockfile: Parsed pyodide-lock.json

    Returns:
        Set of normalized package names available in Pyodide
    """
    return set(lockfile.get("packages", {}).keys())


def get_pyodide_python_version(lockfile: dict[str, Any]) -> str:
    """Extract Python version from Pyodide lockfile.

    Args:
        lockfile: Parsed pyodide-lock.json

    Returns:
        Python version string (e.g. "3.12.7")
    """
    version: str = lockfile["info"]["python"]
    return version


def fetch_pyodide_lockfile(cache_dir: Path) -> dict[str, Any]:
    """Download and cache the Pyodide lockfile.

    Caches the lockfile keyed by Pyodide version to avoid repeated downloads.

    Args:
        cache_dir: Directory for caching downloaded files

    Returns:
        Parsed pyodide-lock.json dict
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"pyodide-lock-{PYODIDE_VERSION}.json"

    if cache_file.exists():
        result: dict[str, Any] = json.loads(cache_file.read_text())
        return result

    import httpx  # noqa: PLC0415 — deferred to avoid import cost when cached

    logger.info("Downloading Pyodide lockfile from %s", PYODIDE_LOCKFILE_URL)
    response = httpx.get(PYODIDE_LOCKFILE_URL, follow_redirects=True)
    response.raise_for_status()

    lockfile: dict[str, Any] = response.json()
    cache_file.write_text(json.dumps(lockfile))
    return lockfile


def build_wheel(project_dir: Path, output_dir: Path) -> Path:
    """Build a wheel from a Python project directory.

    Args:
        project_dir: Directory containing pyproject.toml
        output_dir: Directory to write the built wheel

    Returns:
        Path to the built wheel file

    Raises:
        RuntimeError: If the build fails or no wheel is produced
    """
    pyproject = project_dir / "pyproject.toml"
    if not pyproject.exists():
        raise FileNotFoundError(
            f"No pyproject.toml found in {project_dir}. "
            f"A pyproject.toml is required to build the browser platform bundle."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "-w",
            str(output_dir),
            str(project_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to build wheel for {project_dir}:\n{result.stderr}")

    wheels = list(output_dir.glob("*.whl"))
    if not wheels:
        raise RuntimeError(f"No wheel produced for {project_dir}")

    return max(wheels, key=lambda p: p.stat().st_mtime)


def _get_host_python_version() -> str:
    """Get the host Python version string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _normalize_name(name: str) -> str:
    """Normalize a package name for comparison (PEP 503)."""
    return name.lower().replace("-", "_").replace(".", "_")


def _download_wheel(req: Requirement, python_version: str, cache_dir: Path) -> Path:
    """Download a pure-Python wheel for a requirement.

    Args:
        req: The requirement to download
        python_version: Target Python version (e.g. "3.12")
        cache_dir: Directory for downloads

    Returns:
        Path to the downloaded wheel

    Raises:
        RuntimeError: If download fails
    """
    download_dir = cache_dir / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)

    # Build version spec string
    version_spec = str(req)
    # Strip markers for pip download
    name_and_version = version_spec.split(";")[0].strip()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--no-deps",
            "--only-binary=:all:",
            f"--python-version={python_version}",
            "--platform=any",
            "--abi=none",
            "-d",
            str(download_dir),
            name_and_version,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to download {req.name}: {result.stderr.strip()}")

    # Find the downloaded wheel
    norm_name = _normalize_name(req.name)
    for whl in download_dir.glob("*.whl"):
        if _normalize_name(whl.name.split("-")[0]) == norm_name:
            return whl

    raise RuntimeError(f"Downloaded wheel not found for {req.name} in {download_dir}")


def resolve_dependencies(app_wheel: Path, cache_dir: Path) -> ResolvedDependencies:
    """Recursively resolve dependencies for the browser/emscripten target.

    Algorithm:
    1. Read app wheel's Requires-Dist, filter by emscripten markers
    2. For each requirement:
       - Already resolved -> skip
       - In Pyodide built-in set -> add to pyodide_packages
       - Has @ file:// URL -> build_wheel() from that path, add to queue
       - Otherwise -> pip download --no-deps
    3. Recursively process each downloaded/built wheel's requirements

    Args:
        app_wheel: Path to the app's wheel file
        cache_dir: Directory for caching lockfile and downloads

    Returns:
        ResolvedDependencies with wheel_paths and pyodide_packages
    """
    lockfile = fetch_pyodide_lockfile(cache_dir)
    pyodide_packages = get_pyodide_package_names(lockfile)
    python_version = get_pyodide_python_version(lockfile)
    env = build_emscripten_env(python_version)

    # Check for minor version mismatch
    host_version = _get_host_python_version()
    host_parts = host_version.split(".")
    pyodide_parts = python_version.split(".")
    if host_parts[:2] != pyodide_parts[:2]:
        logger.warning(
            "Host Python %s.%s does not match Pyodide Python %s.%s — "
            "dependency resolution may be inaccurate",
            host_parts[0],
            host_parts[1],
            pyodide_parts[0],
            pyodide_parts[1],
        )

    major_minor = f"{pyodide_parts[0]}.{pyodide_parts[1]}"

    result = ResolvedDependencies()
    result.wheel_paths.append(app_wheel)

    resolved_names: set[str] = set()
    queue: list[Path] = [app_wheel]
    normalized_pyodide_names = {_normalize_name(p) for p in pyodide_packages}

    while queue:
        wheel = queue.pop(0)
        raw_reqs = read_wheel_requirements(wheel)
        parsed_reqs = [Requirement(r) for r in raw_reqs]
        filtered = filter_requirements(parsed_reqs, env)

        for req in filtered:
            norm = _normalize_name(req.name)
            if norm in resolved_names:
                continue
            resolved_names.add(norm)

            # Check for Pyodide built-in
            if norm in normalized_pyodide_names:
                result.pyodide_packages.append(req.name)
                continue

            # Check for direct reference (@ file://)
            if req.url and req.url.startswith("file://"):
                parsed = urlparse(req.url)
                project_path = Path(parsed.path)
                built = build_wheel(project_path, cache_dir / "built")
                result.wheel_paths.append(built)
                queue.append(built)
                continue

            # Download pure-Python wheel
            downloaded = _download_wheel(req, major_minor, cache_dir)
            result.wheel_paths.append(downloaded)
            queue.append(downloaded)

    return result


def create_site_packages_zip(wheel_paths: list[Path], output_path: Path) -> None:
    """Pre-extract all wheels into a flat zip for Pyodide's unpackArchive.

    Each wheel's contents are extracted directly into the zip root,
    so the zip contains package dirs and .dist-info dirs at the top level.

    Args:
        wheel_paths: List of .whl files to extract
        output_path: Path for the output zip file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as out_zip:
        for wheel_path in wheel_paths:
            with zipfile.ZipFile(wheel_path) as whl:
                for item in whl.namelist():
                    data = whl.read(item)
                    out_zip.writestr(item, data)
