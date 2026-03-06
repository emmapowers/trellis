"""Client bundler using esbuild + Bun package management."""

from trellis.bundler.build import build
from trellis.bundler.build_config import BuildConfig
from trellis.bundler.steps import (
    BuildContext,
    BuildStep,
    BundleBuildStep,
    DeclarationStep,
    IconAssetStep,
    IndexHtmlRenderStep,
    PackageInstallStep,
    RegistryGenerationStep,
    StaticFileCopyStep,
    TailwindBuildStep,
    TsconfigStep,
    TypeCheckStep,
)

__all__ = [
    "BuildConfig",
    "BuildContext",
    "BuildStep",
    "BundleBuildStep",
    "DeclarationStep",
    "IconAssetStep",
    "IndexHtmlRenderStep",
    "PackageInstallStep",
    "RegistryGenerationStep",
    "StaticFileCopyStep",
    "TailwindBuildStep",
    "TsconfigStep",
    "TypeCheckStep",
    "build",
]
