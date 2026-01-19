"""Module registry for bundle building.

Modules register themselves at import time, declaring packages, static files,
and exports. At build time, the registry is collected and used to generate
the bundle.
"""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass, field
from enum import StrEnum, auto
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported source file types for bundling
SUPPORTED_SOURCE_TYPES: frozenset[str] = frozenset({".ts", ".tsx", ".css", ".js", ".jsx"})


def _expand_static_files(static_files: dict[str, Path]) -> dict[str, Path]:
    """Expand directories in static_files to individual files.

    Directories are expanded to include all files EXCEPT source types.
    Single files are kept as-is.

    Args:
        static_files: Dict of output_name -> source_path

    Returns:
        Expanded dict with directories replaced by their contents
    """
    result: dict[str, Path] = {}
    for output_name, source_path in static_files.items():
        if source_path.is_dir():
            # Expand directory - include all files except source types
            for file_path in source_path.rglob("*"):
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if ext not in SUPPORTED_SOURCE_TYPES:
                        # Use relative path from the directory as the output key
                        rel_path = file_path.relative_to(source_path)
                        result[f"{output_name}/{rel_path}"] = file_path
        else:
            # Single file - keep as-is
            result[output_name] = source_path
    return result


class ExportKind(StrEnum):
    """Kind of export from a module."""

    component = auto()
    """React component - will be registered via registerWidget()."""

    function = auto()
    """Utility function - exported for use by other modules."""

    initializer = auto()
    """Side-effect code - called at startup."""

    stylesheet = auto()
    """CSS file - imported for side effects, keeps .css extension."""


@dataclass
class ModuleExport:
    """An export from a module."""

    name: str
    """Export name (must match actual TypeScript export name)."""

    kind: ExportKind
    """How this export should be handled."""

    source: str
    """Source file relative to module base path."""


@dataclass
class Module:
    """A registered module that contributes to the bundle."""

    name: str
    """Unique module name (e.g., 'trellis-core', 'my-widget')."""

    packages: dict[str, str] = field(default_factory=dict)
    """NPM packages required by this module (name -> version)."""

    static_files: dict[str, Path] = field(default_factory=dict)
    """Static files to copy (output name -> source path)."""

    exports: list[ModuleExport] = field(default_factory=list)
    """Exports from this module."""

    _base_path: Path | None = None
    """Base path for resolving relative file paths. Set during registration."""


@dataclass
class CollectedModules:
    """Result of collecting all registered modules."""

    modules: list[Module]
    """All registered modules in registration order."""

    packages: dict[str, str]
    """Merged packages from all modules."""


class ModuleRegistry:
    """Registry for modules that contribute to the bundle."""

    def __init__(self) -> None:
        self._modules: dict[str, Module] = {}

    def register(
        self,
        name: str,
        *,
        packages: dict[str, str] | None = None,
        static_files: dict[str, Path] | None = None,
        exports: list[tuple[str, ExportKind, str]] | None = None,
    ) -> None:
        """Register a module.

        Args:
            name: Unique module name
            packages: NPM packages (name -> version)
            static_files: Static files (output name -> source path)
            exports: Exports as (name, kind, source) tuples

        Raises:
            ValueError: If module name is already registered
        """
        if name in self._modules:
            raise ValueError(f"Module '{name}' already registered")

        # Get the caller's file path for resolving relative paths
        frame = inspect.currentframe()
        if frame is not None and frame.f_back is not None:
            caller_file = frame.f_back.f_code.co_filename
            base_path = Path(caller_file).parent.resolve()
        else:
            base_path = None

        # Convert export tuples to ModuleExport objects
        module_exports = []
        if exports:
            for export_name, kind, source in exports:
                module_exports.append(ModuleExport(name=export_name, kind=kind, source=source))

        # Expand directories in static_files
        expanded_static: dict[str, Path] = {}
        if static_files:
            expanded_static = _expand_static_files(static_files)

        module = Module(
            name=name,
            packages=packages or {},
            static_files=expanded_static,
            exports=module_exports,
            _base_path=base_path,
        )
        self._modules[name] = module

    def collect(self) -> CollectedModules:
        """Collect all registered modules.

        Returns:
            CollectedModules with all modules and merged packages

        Raises:
            ValueError: If package version conflicts exist
        """
        modules = list(self._modules.values())

        # Merge packages, checking for conflicts
        packages: dict[str, str] = {}
        for module in modules:
            for pkg_name, pkg_version in module.packages.items():
                if pkg_name in packages:
                    if packages[pkg_name] != pkg_version:
                        raise ValueError(
                            f"Package version conflict for '{pkg_name}': "
                            f"'{packages[pkg_name]}' vs '{pkg_version}'"
                        )
                else:
                    packages[pkg_name] = pkg_version

        return CollectedModules(modules=modules, packages=packages)

    def clear(self) -> None:
        """Remove all registered modules."""
        self._modules.clear()


# Global registry singleton
registry = ModuleRegistry()
