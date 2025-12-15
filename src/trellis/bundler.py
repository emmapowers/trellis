"""Client bundler using esbuild + npm registry."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import tarfile
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


def build_client(
    force: bool = False,
    extra_packages: dict[str, str] | None = None,
) -> None:
    """Build the client bundle if needed.

    Bundles the server platform's client code, which imports common code
    from platforms/common/client/src/.
    """
    platforms_dir = Path(__file__).parent / "platforms"
    server_client_dir = platforms_dir / "server" / "client"
    common_client_dir = platforms_dir / "common" / "client"
    src_dir = server_client_dir / "src"
    dist_dir = server_client_dir / "dist"
    bundle_path = dist_dir / "bundle.js"

    # Check if rebuild needed - check both server and common source
    if not force and bundle_path.exists():
        bundle_mtime = bundle_path.stat().st_mtime
        server_changed = any(f.stat().st_mtime > bundle_mtime for f in src_dir.rglob("*.ts*"))
        common_changed = any(
            f.stat().st_mtime > bundle_mtime for f in (common_client_dir / "src").rglob("*.ts*")
        )
        if not server_changed and not common_changed:
            return

    # Ensure dependencies
    esbuild = ensure_esbuild()

    all_packages = {**CORE_PACKAGES, **(extra_packages or {})}
    node_modules = ensure_packages(all_packages)

    dist_dir.mkdir(parents=True, exist_ok=True)

    # Build command
    # esbuild bundles all files reachable from the entry point via imports.
    # No need to list individual source files - the import graph from main.tsx
    # includes all .ts/.tsx files in src/ (core/, widgets/, etc.)
    cmd = [
        str(esbuild),
        str(src_dir / "main.tsx"),
        "--bundle",
        f"--outfile={bundle_path}",
        "--format=esm",
        "--platform=browser",
        "--target=es2022",
        "--jsx=automatic",
        "--loader:.tsx=tsx",
        "--loader:.ts=ts",
    ]

    # Use NODE_PATH env var to resolve from our cached packages
    env = os.environ.copy()
    env["NODE_PATH"] = str(node_modules)

    subprocess.run(cmd, check=True, env=env)
