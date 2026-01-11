"""Module registry for bundle building.

Modules register themselves at import time, declaring packages, files, snippets,
and exports. At build time, the registry is collected and used to stage files
and generate the bundle.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from enum import StrEnum, auto
from pathlib import Path

from wcmatch import glob as wcglob

# Supported source file types for bundling
SUPPORTED_SOURCE_TYPES: frozenset[str] = frozenset({".ts", ".tsx", ".css", ".js", ".jsx"})


def _is_glob_pattern(path: str) -> bool:
    """Check if a path contains glob pattern characters."""
    return any(c in path for c in "*?[{")


def _make_source_glob(directory: str) -> str:
    """Create a glob pattern for source files in a directory."""
    extensions = ",".join(ext.lstrip(".") for ext in sorted(SUPPORTED_SOURCE_TYPES))
    return f"{directory}/**/*.{{{extensions}}}"


def _validate_source_files(files: list[str]) -> None:
    """Validate that all files have supported source types.

    Args:
        files: List of file paths to validate

    Raises:
        ValueError: If any file has an unsupported extension
    """
    for file_path in files:
        ext = Path(file_path).suffix.lower()
        if ext and ext not in SUPPORTED_SOURCE_TYPES:
            raise ValueError(
                f"Unsupported source file type '{ext}' in '{file_path}'. "
                f"Supported types: {', '.join(sorted(SUPPORTED_SOURCE_TYPES))}"
            )


def _expand_globs(base_path: Path, patterns: list[str]) -> list[str]:
    """Expand glob patterns relative to base_path.

    Uses wcmatch for extended glob support including brace expansion.
    For example: "src/**/*.{ts,tsx,css}" expands to all .ts, .tsx, and .css files.

    Directories are expanded to include all supported source types:
    - "src" becomes "src/**/*.{css,js,jsx,ts,tsx}"

    Args:
        base_path: Directory to glob from
        patterns: List of paths, glob patterns, or directories

    Returns:
        List of expanded file paths (relative to base_path)

    Raises:
        ValueError: If any expanded file has an unsupported extension
    """
    result: list[str] = []
    for pattern in patterns:
        full_path = base_path / pattern
        expanded_pattern = pattern
        if full_path.is_dir():
            # Directory - expand to all supported source types
            expanded_pattern = _make_source_glob(pattern)

        if _is_glob_pattern(expanded_pattern):
            # Expand glob pattern using wcmatch (supports brace expansion)
            flags = wcglob.BRACE | wcglob.GLOBSTAR
            matched = wcglob.glob(expanded_pattern, root_dir=base_path, flags=flags)
            result.extend(match for match in matched if (base_path / match).is_file())
        else:
            # Literal path - keep as-is
            result.append(pattern)

    # Validate all files have supported extensions
    _validate_source_files(result)
    return result


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

    files: list[str] = field(default_factory=list)
    """Files to copy (paths relative to registering Python file)."""

    snippets: dict[str, str] = field(default_factory=dict)
    """Inline code snippets (filename -> code)."""

    static_files: dict[str, Path] = field(default_factory=dict)
    """Static files to copy (output name -> source path)."""

    exports: list[ModuleExport] = field(default_factory=list)
    """Exports from this module."""

    worker_entries: dict[str, str] = field(default_factory=dict)
    """Worker entry points (name -> relative path)."""

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
        files: list[str] | None = None,
        snippets: dict[str, str] | None = None,
        static_files: dict[str, Path] | None = None,
        exports: list[tuple[str, ExportKind, str]] | None = None,
        worker_entries: dict[str, str] | None = None,
    ) -> None:
        """Register a module.

        Args:
            name: Unique module name
            packages: NPM packages (name -> version)
            files: Files to copy (paths relative to calling Python file)
            snippets: Inline code (filename -> code)
            static_files: Static files (output name -> source path)
            exports: Exports as (name, kind, source) tuples
            worker_entries: Worker entry points (name -> relative path)

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

        # Expand glob patterns in files
        expanded_files: list[str] = []
        if files:
            if base_path is not None:
                expanded_files = _expand_globs(base_path, files)
            else:
                expanded_files = files

        # Expand directories in static_files
        expanded_static: dict[str, Path] = {}
        if static_files:
            expanded_static = _expand_static_files(static_files)

        module = Module(
            name=name,
            packages=packages or {},
            files=expanded_files,
            snippets=snippets or {},
            static_files=expanded_static,
            exports=module_exports,
            worker_entries=worker_entries or {},
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
