"""Client bundler using esbuild + npm registry."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path

import httpx

ESBUILD_VERSION = "0.24.0"
CACHE_DIR = Path.home() / ".cache" / "trellis"
BIN_DIR = CACHE_DIR / "bin"
PACKAGES_DIR = CACHE_DIR / "node_modules"


def _safe_extract(tar: tarfile.TarFile, dest: Path) -> None:
    """Safely extract a tarball, preventing path traversal attacks.

    Validates that all extracted paths stay within the destination directory.
    This prevents malicious tarballs from writing files outside the intended
    directory via paths like "../../../etc/passwd".

    Args:
        tar: The tarfile to extract
        dest: The destination directory

    Raises:
        ValueError: If any member would extract outside the destination
    """
    dest = dest.resolve()
    for member in tar.getmembers():
        member_path = (dest / member.name).resolve()
        if not member_path.is_relative_to(dest):
            raise ValueError(f"Tarball contains path traversal: {member.name}")
    tar.extractall(dest)


# Core packages with pinned versions (and their transitive deps)
CORE_PACKAGES = {
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "scheduler": "0.23.2",  # react-dom dependency
    "@msgpack/msgpack": "3.0.0",
}

# Additional packages for desktop platform (PyTauri)
DESKTOP_PACKAGES = {
    "@tauri-apps/api": "2.8.0",
    "tauri-plugin-pytauri-api": "0.8.0",
}


def _get_platform() -> str:
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
    plat = _get_platform()
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
        _safe_extract(tar, extract_dir)

    tgz_path.unlink()
    binary_path.chmod(0o755)
    return binary_path


def _fetch_npm_package(name: str, version: str, client: httpx.Client) -> Path:
    """Download and extract an npm package if not cached.

    Returns the path to the extracted package directory.
    """
    # Handle scoped packages: @msgpack/msgpack -> @msgpack/msgpack
    if name.startswith("@"):
        scope, pkg_name = name.split("/", 1)
        pkg_dir = PACKAGES_DIR / scope / pkg_name
        tarball_name = f"{pkg_name}-{version}.tgz"
    else:
        pkg_dir = PACKAGES_DIR / name
        tarball_name = f"{name}-{version}.tgz"

    # Check if already cached
    pkg_json = pkg_dir / "package.json"
    if pkg_json.exists():
        with open(pkg_json) as f:
            cached_version = json.load(f).get("version")
        if cached_version == version:
            return pkg_dir

    # Get package metadata from npm registry
    meta_url = f"https://registry.npmjs.org/{name}/{version}"
    response = client.get(meta_url)
    response.raise_for_status()
    meta = response.json()

    tarball_url = meta["dist"]["tarball"]

    # Download tarball
    tgz_path = CACHE_DIR / tarball_name
    with client.stream("GET", tarball_url) as r:
        r.raise_for_status()
        with open(tgz_path, "wb") as f:
            f.writelines(r.iter_bytes())

    # Extract - npm tarballs have a "package/" prefix
    pkg_dir.parent.mkdir(parents=True, exist_ok=True)
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)

    with tarfile.open(tgz_path) as tar:
        # Extract to a temp location then rename
        temp_dir = CACHE_DIR / "temp_extract"
        temp_dir.mkdir(exist_ok=True)
        _safe_extract(tar, temp_dir)
        (temp_dir / "package").rename(pkg_dir)
        temp_dir.rmdir()

    tgz_path.unlink()
    return pkg_dir


def ensure_packages(packages: dict[str, str] | None = None) -> Path:
    """Fetch packages from npm registry if not cached.

    Returns path to node_modules directory.
    """
    packages = packages or CORE_PACKAGES
    PACKAGES_DIR.mkdir(parents=True, exist_ok=True)

    with httpx.Client(follow_redirects=True) as client:
        for name, version in packages.items():
            _fetch_npm_package(name, version, client)

    return PACKAGES_DIR


# =============================================================================
# Unified bundle building
# =============================================================================


@dataclass
class BundleConfig:
    """Configuration for building a client bundle."""

    name: str
    """Platform name for logging (e.g., 'server', 'desktop')."""

    src_dir: Path
    """Directory containing entry point (main.tsx)."""

    dist_dir: Path
    """Output directory for bundle.js."""

    packages: dict[str, str]
    """NPM packages to include."""

    static_files: dict[str, Path] | None = None
    """Static files to copy to dist_dir. Keys are output filenames, values are source paths."""

    extra_outputs: list[Path] | None = None
    """Additional output files that must exist for incremental build check."""

    worker_entries: dict[str, Path] | None = None
    """Worker entry points to build. Keys are output names (without extension),
    values are source paths. Workers are built as IIFE and can be imported as text
    via the .worker-bundle extension."""


def build_bundle(
    config: BundleConfig,
    common_src_dir: Path,
    force: bool = False,
    extra_packages: dict[str, str] | None = None,
) -> None:
    """Build a client bundle using esbuild.

    This is the unified build function used by all platforms. It handles:
    - Incremental build checking (skip if sources unchanged)
    - Ensuring esbuild and npm packages are available
    - Running esbuild with consistent options
    - Copying static files to dist directory

    Args:
        config: Bundle configuration
        common_src_dir: Path to shared client code (platforms/common/client/src)
        force: Force rebuild even if up to date
        extra_packages: Additional packages to include beyond config.packages
    """
    bundle_path = config.dist_dir / "bundle.js"

    # Check if rebuild needed
    if not force:
        # All outputs must exist
        outputs_exist = bundle_path.exists()
        if config.extra_outputs:
            outputs_exist = outputs_exist and all(p.exists() for p in config.extra_outputs)

        if outputs_exist:
            bundle_mtime = bundle_path.stat().st_mtime
            platform_changed = any(
                f.stat().st_mtime > bundle_mtime for f in config.src_dir.rglob("*.ts*")
            )
            common_changed = any(
                f.stat().st_mtime > bundle_mtime for f in common_src_dir.rglob("*.ts*")
            )
            # Check if static source files changed
            static_changed = False
            if config.static_files:
                static_changed = any(
                    src.stat().st_mtime > bundle_mtime for src in config.static_files.values()
                )
            if not platform_changed and not common_changed and not static_changed:
                return

    # Ensure dependencies
    esbuild = ensure_esbuild()

    all_packages = {**config.packages, **(extra_packages or {})}
    node_modules = ensure_packages(all_packages)

    config.dist_dir.mkdir(parents=True, exist_ok=True)

    # Use NODE_PATH env var to resolve from our cached packages
    env = os.environ.copy()
    env["NODE_PATH"] = str(node_modules)

    # Build worker entries first (as IIFE, imported as text by main bundle)
    if config.worker_entries:
        for name, entry_path in config.worker_entries.items():
            worker_output = config.src_dir / f"{name}.worker-bundle"
            worker_cmd = [
                str(esbuild),
                str(entry_path),
                "--bundle",
                f"--outfile={worker_output}",
                "--format=iife",
                "--platform=browser",
                "--target=es2022",
                "--loader:.tsx=tsx",
                "--loader:.ts=ts",
            ]
            subprocess.run(worker_cmd, check=True, env=env)

    # Build main bundle
    cmd = [
        str(esbuild),
        str(config.src_dir / "main.tsx"),
        "--bundle",
        f"--outfile={bundle_path}",
        "--format=esm",
        "--platform=browser",
        "--target=es2022",
        "--jsx=automatic",
        "--loader:.tsx=tsx",
        "--loader:.ts=ts",
    ]

    # Add text loader for worker bundles
    if config.worker_entries:
        cmd.append("--loader:.worker-bundle=text")

    subprocess.run(cmd, check=True, env=env)

    # Copy static files to dist
    if config.static_files:
        for output_name, src_path in config.static_files.items():
            dest_path = config.dist_dir / output_name
            shutil.copy2(src_path, dest_path)
