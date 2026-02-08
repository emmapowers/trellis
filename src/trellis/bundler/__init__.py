"""Client bundler using esbuild + Bun package management."""

from trellis.bundler.build import build
from trellis.bundler.build_config import BuildConfig
from trellis.bundler.registry import (
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
    IndexHtmlRenderStep,
    PackageInstallStep,
    RegistryGenerationStep,
    StaticFileCopyStep,
    TsconfigStep,
    TypeCheckStep,
)

__all__ = [
    "BuildConfig",
    "BuildContext",
    "BuildStep",
    "BundleBuildStep",
    "CollectedModules",
    "DeclarationStep",
    "ExportKind",
    "IndexHtmlRenderStep",
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
