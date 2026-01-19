"""Build steps for the bundler.

Each step is a discrete, composable unit of work that can mutate a shared
BuildContext. Platforms configure which steps to run and in what order.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from trellis.bundler.metafile import get_metafile_path
from trellis.bundler.packages import ensure_packages, get_bin
from trellis.bundler.workspace import write_registry_ts

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from trellis.bundler.registry import CollectedModules, ModuleRegistry


@dataclass
class BuildContext:
    """Mutable context shared across all build steps.

    Attributes:
        registry: Module registry with registered modules
        entry_point: Path to entry point file (e.g., main.tsx)
        workspace: Workspace directory for generated files
        collected: Collected modules from registry
        dist_dir: Output directory for bundle files
        app_static_dir: Optional app-level static files directory
        python_entry_point: Optional Python app entry point for browser bundling
        esbuild_args: Additional esbuild arguments (steps can append)
        env: Environment variables for subprocess calls (steps can modify)
        generated_files: Map of generated file names to paths (steps set these)
        template_context: Template variables for IndexHtmlRenderStep (steps can add)
        node_modules: Path to node_modules directory (set by PackageInstallStep)
    """

    # Inputs (set before steps run)
    registry: ModuleRegistry
    entry_point: Path
    workspace: Path
    collected: CollectedModules
    dist_dir: Path
    app_static_dir: Path | None = None
    python_entry_point: Path | None = None

    # Mutable state (steps can modify)
    esbuild_args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    generated_files: dict[str, Path] = field(default_factory=dict)
    template_context: dict[str, Any] = field(default_factory=dict)

    # Step outputs
    node_modules: Path | None = None


class BuildStep(ABC):
    """Abstract base class for build steps.

    Each step performs a discrete piece of work and may mutate the BuildContext.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Step name for logging."""
        ...

    @abstractmethod
    def run(self, ctx: BuildContext) -> None:
        """Execute the step, may mutate ctx."""
        ...


def _get_module_aliases(collected: CollectedModules) -> dict[str, Path]:
    """Get module name to path mappings for @trellis/* aliases.

    Returns:
        Dict mapping module names to their base paths (e.g., {"core": Path(...)})
    """
    return {module.name: module._base_path for module in collected.modules if module._base_path}


class PackageInstallStep(BuildStep):
    """Install npm packages using ensure_packages().

    Sets ctx.node_modules and ctx.env["NODE_PATH"].
    """

    @property
    def name(self) -> str:
        return "package-install"

    def run(self, ctx: BuildContext) -> None:
        packages = dict(ctx.collected.packages)
        ensure_packages(packages, ctx.workspace)
        ctx.node_modules = ctx.workspace / "node_modules"
        ctx.env["NODE_PATH"] = str(ctx.node_modules)


class RegistryGenerationStep(BuildStep):
    """Generate _registry.ts wiring file.

    Sets ctx.generated_files["_registry"] and adds alias to ctx.esbuild_args.
    """

    @property
    def name(self) -> str:
        return "registry-generation"

    def run(self, ctx: BuildContext) -> None:
        registry_path = write_registry_ts(ctx.workspace, ctx.collected)
        ctx.generated_files["_registry"] = registry_path
        ctx.esbuild_args.append(f"--alias:@trellis/_registry={registry_path}")


class TsconfigStep(BuildStep):
    """Generate tsconfig.json with path aliases for type checking.

    Sets ctx.generated_files["tsconfig"].
    """

    @property
    def name(self) -> str:
        return "tsconfig"

    def run(self, ctx: BuildContext) -> None:
        # Build path mappings for modules
        aliases = _get_module_aliases(ctx.collected)
        paths: dict[str, list[str]] = {
            f"@trellis/{name}/*": [f"{path}/*"] for name, path in aliases.items()
        }

        # Add _registry alias if it exists
        if "_registry" in ctx.generated_files:
            paths["@trellis/_registry"] = [str(ctx.generated_files["_registry"])]

        # Set up typeRoots to find @types packages in workspace node_modules
        node_modules = str(ctx.workspace / "node_modules")
        type_roots = [f"{node_modules}/@types"]

        # Add wildcard path to resolve npm packages from node_modules
        paths["*"] = [f"{node_modules}/*", f"{node_modules}/@types/*"]

        tsconfig = {
            "compilerOptions": {
                "target": "ES2022",
                "module": "ESNext",
                # Use classic node resolution - simpler and finds node_modules reliably
                "moduleResolution": "node",
                "jsx": "react-jsx",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "noEmit": True,
                # baseUrl points to workspace so paths resolve correctly
                "baseUrl": str(ctx.workspace),
                # typeRoots tells tsc where to find type definitions
                "typeRoots": type_roots,
                "paths": paths,
            },
            "include": [str(ctx.entry_point.parent / "**/*")],
        }

        tsconfig_path = ctx.workspace / "tsconfig.json"
        tsconfig_path.write_text(json.dumps(tsconfig, indent=2))
        ctx.generated_files["tsconfig"] = tsconfig_path


class TypeCheckStep(BuildStep):
    """Run TypeScript type-checking with tsc --noEmit.

    Args:
        fail_on_error: If True, raise on type errors. If False (default), log warning.
    """

    def __init__(self, *, fail_on_error: bool = False) -> None:
        self.fail_on_error = fail_on_error

    @property
    def name(self) -> str:
        return "type-check"

    def run(self, ctx: BuildContext) -> None:
        if ctx.node_modules is None:
            raise RuntimeError("TypeCheckStep requires node_modules (run PackageInstallStep first)")

        tsc = get_bin(ctx.node_modules, "tsc")
        tsconfig_path = ctx.generated_files.get("tsconfig")

        cmd = [str(tsc), "--noEmit"]
        if tsconfig_path:
            cmd.extend(["--project", str(tsconfig_path)])

        result = subprocess.run(cmd, check=False, env={**ctx.env})

        if result.returncode != 0:
            if self.fail_on_error:
                raise subprocess.CalledProcessError(result.returncode, cmd)
            logger.warning("TypeScript type-checking failed (continuing anyway)")


class DeclarationStep(BuildStep):
    """Generate TypeScript declaration files (.d.ts).

    Runs tsc --declaration --emitDeclarationOnly, outputting to ctx.dist_dir.
    """

    @property
    def name(self) -> str:
        return "declaration"

    def run(self, ctx: BuildContext) -> None:
        if ctx.node_modules is None:
            raise RuntimeError(
                "DeclarationStep requires node_modules (run PackageInstallStep first)"
            )

        tsc = get_bin(ctx.node_modules, "tsc")
        tsconfig_path = ctx.generated_files.get("tsconfig")

        cmd = [
            str(tsc),
            "--declaration",
            "--emitDeclarationOnly",
            "--outDir",
            str(ctx.dist_dir),
        ]
        if tsconfig_path:
            cmd.extend(["--project", str(tsconfig_path)])

        subprocess.run(cmd, check=True, env={**ctx.env})


class BundleBuildStep(BuildStep):
    """Run esbuild to create the bundle.

    Args:
        output_name: Name for output files (default "bundle" -> bundle.js, bundle.css)
    """

    def __init__(self, *, output_name: str = "bundle") -> None:
        self.output_name = output_name

    @property
    def name(self) -> str:
        return "bundle-build"

    def run(self, ctx: BuildContext) -> None:
        if ctx.node_modules is None:
            raise RuntimeError(
                "BundleBuildStep requires node_modules (run PackageInstallStep first)"
            )

        esbuild = get_bin(ctx.node_modules, "esbuild")
        metafile_path = get_metafile_path(ctx.workspace)

        cmd = [
            str(esbuild),
            str(ctx.entry_point),
            "--bundle",
            f"--outdir={ctx.dist_dir}",
            f"--entry-names={self.output_name}",
            f"--metafile={metafile_path}",
            "--format=esm",
            "--platform=browser",
            "--target=es2022",
            "--jsx=automatic",
            "--loader:.tsx=tsx",
            "--loader:.ts=ts",
        ]

        # Add aliases for each module - point directly to source paths
        aliases = _get_module_aliases(ctx.collected)
        cmd.extend(f"--alias:@trellis/{name}={path}" for name, path in aliases.items())

        # Add additional args from context (including _registry alias from RegistryGenerationStep)
        cmd.extend(ctx.esbuild_args)

        subprocess.run(cmd, check=True, env={**ctx.env})


class StaticFileCopyStep(BuildStep):
    """Copy static files to the dist directory using convention-based discovery.

    Copies from:
    - module._base_path / "static" for each registered module
    - ctx.app_static_dir if provided (for app-level static files)
    """

    @property
    def name(self) -> str:
        return "static-file-copy"

    def run(self, ctx: BuildContext) -> None:
        # Copy from each module's static directory
        for module in ctx.collected.modules:
            if module._base_path is None:
                continue
            static_dir = module._base_path / "static"
            if static_dir.is_dir():
                shutil.copytree(static_dir, ctx.dist_dir, dirs_exist_ok=True)

        # Copy from app-level static directory
        if ctx.app_static_dir is not None and ctx.app_static_dir.is_dir():
            shutil.copytree(ctx.app_static_dir, ctx.dist_dir, dirs_exist_ok=True)


class IndexHtmlRenderStep(BuildStep):
    """Render index.html.j2 template to dist directory.

    Merges BuildContext.template_context with constructor context to build
    the final template variables. Constructor context takes precedence.

    Args:
        template_path: Path to the Jinja2 template file
        context: Template context variables (defaults to empty dict)
    """

    def __init__(self, template_path: Path, context: dict[str, Any] | None = None) -> None:
        self._template_path = template_path
        self._context = context or {}

    @property
    def name(self) -> str:
        return "index-html-render"

    def run(self, ctx: BuildContext) -> None:
        # Lazy import jinja2 to avoid import overhead when not used
        from jinja2 import Environment, FileSystemLoader  # noqa: PLC0415

        # Merge contexts: BuildContext.template_context first, then constructor (overrides)
        merged_context = {**ctx.template_context, **self._context}

        template_dir = self._template_path.parent
        template_name = self._template_path.name

        env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        template = env.get_template(template_name)
        html_content = template.render(**merged_context)

        output_path = ctx.dist_dir / "index.html"
        output_path.write_text(html_content)
