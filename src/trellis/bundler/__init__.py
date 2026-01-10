"""Client bundler using esbuild + Bun package management."""

from .build import BundleConfig, build_bundle
from .bun import ensure_bun, get_bun_platform
from .esbuild import ensure_esbuild, get_platform
from .packages import (
    DESKTOP_PACKAGES,
    PACKAGES,
    ensure_packages,
    generate_package_json,
    get_packages_hash,
)
from .utils import (
    BIN_DIR,
    BUN_VERSION,
    CACHE_DIR,
    ESBUILD_VERSION,
    safe_extract,
)

# Backward compatibility aliases
_safe_extract = safe_extract
_get_platform = get_platform
CORE_PACKAGES = PACKAGES  # Renamed to PACKAGES

__all__ = [
    "BIN_DIR",
    "BUN_VERSION",
    "CACHE_DIR",
    "CORE_PACKAGES",
    "DESKTOP_PACKAGES",
    "ESBUILD_VERSION",
    "PACKAGES",
    "BundleConfig",
    "_get_platform",
    "_safe_extract",
    "build_bundle",
    "ensure_bun",
    "ensure_esbuild",
    "ensure_packages",
    "generate_package_json",
    "get_bun_platform",
    "get_packages_hash",
    "get_platform",
    "safe_extract",
]
