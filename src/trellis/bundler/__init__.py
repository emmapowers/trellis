"""Client bundler using esbuild + Bun package management."""

from .build import TYPESCRIPT_VERSION, build_from_registry
from .bun import ensure_bun, get_bun_platform
from .esbuild import ensure_esbuild, get_platform
from .packages import (
    DESKTOP_PACKAGES,
    PACKAGES,
    ensure_packages,
    generate_package_json,
    get_packages_hash,
)
from .registry import (
    SUPPORTED_SOURCE_TYPES,
    CollectedModules,
    ExportKind,
    Module,
    ModuleExport,
    ModuleRegistry,
    registry,
)
from .utils import (
    BIN_DIR,
    BUN_VERSION,
    CACHE_DIR,
    ESBUILD_VERSION,
    safe_extract,
)
from .workspace import (
    generate_registry_ts,
    generate_tsconfig,
    get_project_hash,
    get_project_workspace,
    stage_workspace,
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
    "SUPPORTED_SOURCE_TYPES",
    "TYPESCRIPT_VERSION",
    "CollectedModules",
    "ExportKind",
    "Module",
    "ModuleExport",
    "ModuleRegistry",
    "_get_platform",
    "_safe_extract",
    "build_from_registry",
    "ensure_bun",
    "ensure_esbuild",
    "ensure_packages",
    "generate_package_json",
    "generate_registry_ts",
    "generate_tsconfig",
    "get_bun_platform",
    "get_packages_hash",
    "get_platform",
    "get_project_hash",
    "get_project_workspace",
    "registry",
    "safe_extract",
    "stage_workspace",
]
