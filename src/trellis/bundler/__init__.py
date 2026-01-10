"""Client bundler using esbuild + npm registry."""

from .build import BundleConfig, build_bundle
from .esbuild import ensure_esbuild, get_platform
from .packages import (
    CORE_PACKAGES,
    DESKTOP_PACKAGES,
    ensure_packages,
    fetch_npm_package,
)
from .utils import (
    BIN_DIR,
    CACHE_DIR,
    ESBUILD_VERSION,
    PACKAGES_DIR,
    safe_extract,
)

# Backward compatibility aliases for underscore-prefixed names
_safe_extract = safe_extract
_get_platform = get_platform
_fetch_npm_package = fetch_npm_package

__all__ = [
    "BIN_DIR",
    "CACHE_DIR",
    "CORE_PACKAGES",
    "DESKTOP_PACKAGES",
    "ESBUILD_VERSION",
    "PACKAGES_DIR",
    "BundleConfig",
    "_fetch_npm_package",
    "_get_platform",
    "_safe_extract",
    "build_bundle",
    "ensure_esbuild",
    "ensure_packages",
    "fetch_npm_package",
    "get_platform",
    "safe_extract",
]
