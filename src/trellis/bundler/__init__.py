"""Client bundler using esbuild + Bun package management."""

from trellis.bundler.build import build
from trellis.bundler.registry import (
    SUPPORTED_SOURCE_TYPES,
    CollectedModules,
    ExportKind,
    Module,
    ModuleExport,
    ModuleRegistry,
    registry,
)
from trellis.bundler.steps import (
    BuildContext,
    BuildStep,
    BundleBuildStep,
    DeclarationStep,
    PackageInstallStep,
    RegistryGenerationStep,
    StaticFileCopyStep,
    TsconfigStep,
    TypeCheckStep,
)

__all__ = [
    "SUPPORTED_SOURCE_TYPES",
    "BuildContext",
    "BuildStep",
    "BundleBuildStep",
    "CollectedModules",
    "DeclarationStep",
    "ExportKind",
    "Module",
    "ModuleExport",
    "ModuleRegistry",
    "PackageInstallStep",
    "RegistryGenerationStep",
    "StaticFileCopyStep",
    "TsconfigStep",
    "TypeCheckStep",
    "build",
    "registry",
]
