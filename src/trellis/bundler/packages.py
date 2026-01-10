"""NPM package management."""

from __future__ import annotations

import json
import shutil
import tarfile
from pathlib import Path

import httpx

from .utils import CACHE_DIR, PACKAGES_DIR, safe_extract

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
    "recharts": "3.6.0",
    # Recharts 3.x dependencies
    "@reduxjs/toolkit": "2.5.0",
    "redux": "5.0.1",
    "redux-thunk": "3.1.0",
    "clsx": "2.1.1",
    "decimal.js-light": "2.5.1",
    "es-toolkit": "1.43.0",
    "eventemitter3": "5.0.1",
    "immer": "10.1.1",
    "react-redux": "9.2.0",
    "reselect": "5.1.1",
    "tiny-invariant": "1.3.3",
    "use-sync-external-store": "1.4.0",
    "victory-vendor": "37.3.6",
    # victory-vendor re-exports from actual d3 packages
    "d3-array": "3.2.4",
    "d3-color": "3.1.0",
    "d3-ease": "3.0.1",
    "d3-format": "3.1.0",
    "d3-interpolate": "3.0.1",
    "d3-path": "3.1.0",
    "d3-scale": "4.0.2",
    "d3-shape": "3.2.0",
    "d3-time": "3.1.0",
    "d3-time-format": "4.1.0",
    "d3-timer": "3.0.1",
    "d3-voronoi": "1.1.4",
    "internmap": "2.0.3",
    # recharts dependency
    "react-is": "18.3.1",
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


def fetch_npm_package(name: str, version: str, client: httpx.Client) -> Path:
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
        safe_extract(tar, temp_dir)
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
            fetch_npm_package(name, version, client)

    return PACKAGES_DIR
