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
    # Icons
    "lucide-react": "0.468.0",
    # Charts
    "uplot": "1.6.31",
    "recharts": "2.15.0",
    # Recharts dependencies
    "@babel/runtime": "7.26.0",
    "clsx": "2.1.1",
    "d3-array": "3.2.4",
    "dom-helpers": "5.2.1",
    "d3-color": "3.1.0",
    "d3-format": "3.1.0",
    "d3-interpolate": "3.0.1",
    "d3-path": "3.1.0",
    "d3-scale": "4.0.2",
    "d3-shape": "3.2.0",
    "d3-time": "3.1.0",
    "d3-time-format": "4.1.0",
    "decimal.js-light": "2.5.1",
    "eventemitter3": "4.0.7",
    "fast-equals": "5.2.2",
    "internmap": "2.0.3",
    "lodash": "4.17.21",
    "object-assign": "4.1.1",
    "prop-types": "15.8.1",
    "react-is": "18.3.1",
    "react-smooth": "4.0.4",
    "react-transition-group": "4.4.5",
    "recharts-scale": "0.4.5",
    "tiny-invariant": "1.3.3",
    "victory-vendor": "36.9.2",
    # React Aria (accessibility) - umbrella packages
    "react-aria": "3.35.0",
    "react-stately": "3.33.0",
    # React Aria internal packages (required by umbrella)
    "@react-aria/breadcrumbs": "3.5.17",
    "@react-aria/button": "3.10.0",
    "@react-aria/calendar": "3.5.12",
    "@react-aria/checkbox": "3.14.7",
    "@react-aria/color": "3.0.0",
    "@react-aria/combobox": "3.10.4",
    "@react-aria/datepicker": "3.11.3",
    "@react-aria/dialog": "3.5.18",
    "@react-aria/dnd": "3.7.3",
    "@react-aria/focus": "3.18.3",
    "@react-aria/gridlist": "3.9.4",
    "@react-aria/i18n": "3.12.3",
    "@react-aria/interactions": "3.22.3",
    "@react-aria/label": "3.7.12",
    "@react-aria/link": "3.7.5",
    "@react-aria/listbox": "3.13.4",
    "@react-aria/menu": "3.15.4",
    "@react-aria/meter": "3.4.17",
    "@react-aria/numberfield": "3.11.7",
    "@react-aria/overlays": "3.23.3",
    "@react-aria/progress": "3.4.17",
    "@react-aria/radio": "3.10.8",
    "@react-aria/searchfield": "3.7.9",
    "@react-aria/select": "3.14.10",
    "@react-aria/selection": "3.20.0",
    "@react-aria/separator": "3.4.3",
    "@react-aria/slider": "3.7.12",
    "@react-aria/ssr": "3.9.6",
    "@react-aria/switch": "3.6.8",
    "@react-aria/table": "3.15.4",
    "@react-aria/tabs": "3.9.6",
    "@react-aria/tag": "3.4.6",
    "@react-aria/textfield": "3.14.9",
    "@react-aria/tooltip": "3.7.8",
    "@react-aria/utils": "3.25.3",
    "@react-aria/visually-hidden": "3.8.16",
    "@react-aria/toolbar": "3.0.0-beta.9",
    "@react-aria/toggle": "3.10.8",
    "@react-aria/spinbutton": "3.6.9",
    "@react-aria/form": "3.0.9",
    "@react-aria/grid": "3.10.4",
    "@react-aria/live-announcer": "3.4.0",
    # React Stately internal packages (required by umbrella)
    "@react-stately/calendar": "3.5.5",
    "@react-stately/checkbox": "3.6.9",
    "@react-stately/collections": "3.11.0",
    "@react-stately/color": "3.8.0",
    "@react-stately/combobox": "3.10.0",
    "@react-stately/data": "3.11.7",
    "@react-stately/datepicker": "3.10.3",
    "@react-stately/dnd": "3.4.3",
    "@react-stately/form": "3.0.6",
    "@react-stately/list": "3.11.0",
    "@react-stately/menu": "3.8.3",
    "@react-stately/numberfield": "3.9.7",
    "@react-stately/overlays": "3.6.11",
    "@react-stately/radio": "3.10.8",
    "@react-stately/searchfield": "3.5.7",
    "@react-stately/select": "3.6.8",
    "@react-stately/selection": "3.17.0",
    "@react-stately/slider": "3.5.8",
    "@react-stately/table": "3.12.3",
    "@react-stately/tabs": "3.6.10",
    "@react-stately/toggle": "3.7.8",
    "@react-stately/tooltip": "3.4.13",
    "@react-stately/tree": "3.8.5",
    "@react-stately/utils": "3.10.4",
    "@react-stately/flags": "3.0.4",
    "@react-stately/virtualizer": "4.1.0",
    "@react-stately/grid": "3.9.3",
    # Shared types and utilities
    "@react-types/shared": "3.25.0",
    "@react-types/button": "3.10.0",
    "@react-types/checkbox": "3.8.4",
    "@react-types/calendar": "3.4.10",
    "@react-types/color": "3.0.0",
    "@react-types/combobox": "3.13.0",
    "@react-types/datepicker": "3.8.3",
    "@react-types/dialog": "3.5.13",
    "@react-types/grid": "3.2.9",
    "@react-types/label": "3.9.6",
    "@react-types/link": "3.5.8",
    "@react-types/listbox": "3.5.2",
    "@react-types/menu": "3.9.12",
    "@react-types/meter": "3.4.4",
    "@react-types/numberfield": "3.8.6",
    "@react-types/overlays": "3.8.10",
    "@react-types/progress": "3.5.7",
    "@react-types/radio": "3.8.4",
    "@react-types/searchfield": "3.5.9",
    "@react-types/select": "3.9.7",
    "@react-types/slider": "3.7.6",
    "@react-types/switch": "3.5.6",
    "@react-types/table": "3.10.2",
    "@react-types/tabs": "3.3.10",
    "@react-types/textfield": "3.9.7",
    "@react-types/tooltip": "3.4.12",
    # Internationalization packages
    "@internationalized/date": "3.5.6",
    "@internationalized/message": "3.1.5",
    "@internationalized/number": "3.5.4",
    "@internationalized/string": "3.2.4",
    "intl-messageformat": "10.7.3",
    # intl-messageformat dependencies
    "@formatjs/icu-messageformat-parser": "2.9.3",
    "@formatjs/fast-memoize": "2.2.3",
    "@formatjs/icu-skeleton-parser": "1.8.5",
    "@formatjs/intl-localematcher": "0.5.7",
    "tslib": "2.8.1",
    # Additional React Aria dependencies
    "@swc/helpers": "0.5.13",
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
