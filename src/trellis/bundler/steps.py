"""Build steps for the bundler.

Each step is a discrete, composable unit of work that can mutate a shared
BuildContext. Platforms configure which steps to run and in what order.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any

from trellis.bundler.manifest import BuildManifest, StepManifest
from trellis.bundler.metafile import get_metafile_path, read_metafile
from trellis.bundler.packages import ensure_packages, get_bin
from trellis.bundler.utils import is_rebuild_needed
from trellis.bundler.workspace import node_modules_path, write_registry_ts

logger = logging.getLogger(__name__)


def collect_ts_source_files(base_path: Path) -> set[Path]:
    """Collect TypeScript/TSX source files recursively from a directory.

    Args:
        base_path: Directory to search for source files

    Returns:
        Set of paths to .ts and .tsx files
    """
    return {f for f in base_path.rglob("*") if f.suffix in {".ts", ".tsx"}}


class ShouldBuild(StrEnum):
    """Enum indicating whether a step should build or skip."""

    SKIP = auto()  # Step is up to date, preserve manifest
    BUILD = auto()  # Step needs to run


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
        manifest: Build manifest tracking inputs and outputs
        app_static_dir: Optional app-level static files directory
        python_entry_point: Optional Python app entry point for browser bundling
        esbuild_args: Additional esbuild arguments (steps can append)
        env: Environment variables for subprocess calls (steps can modify)
        generated_files: Map of generated file names to paths (steps set these)
        template_context: Template variables for IndexHtmlRenderStep (steps can add)
    """

    # Inputs (set before steps run)
    registry: ModuleRegistry
    entry_point: Path
    workspace: Path
    collected: CollectedModules
    dist_dir: Path
    manifest: BuildManifest
    app_static_dir: Path | None = None
    python_entry_point: Path | None = None

    # Mutable state (steps can modify)
    esbuild_args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    generated_files: dict[str, Path] = field(default_factory=dict)
    template_context: dict[str, Any] = field(default_factory=dict)

    def exec_in_build_env(
        self, cmd: list[str], *, check: bool = True
    ) -> subprocess.CompletedProcess[bytes]:
        """Execute a command in the build environment.

        Runs the command with:
        - cwd set to workspace (ensures consistent path resolution)
        - env set to the build environment (includes NODE_PATH, etc.)

        Args:
            cmd: Command and arguments to execute
            check: If True, raise CalledProcessError on non-zero exit

        Returns:
            CompletedProcess instance with return code and output
        """
        return subprocess.run(cmd, check=check, cwd=self.workspace, env=self.env)


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

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if this step should build, skip, or defer.

        Override this in subclasses to implement per-step staleness checking.

        Args:
            ctx: Current build context
            step_manifest: Manifest from previous build for this step, or None

        Returns:
            SKIP: Step is up to date, copy old manifest section to new
            BUILD: Step needs to run
            None: Step always runs (same as BUILD)
        """
        return None


def _get_module_aliases(collected: CollectedModules) -> dict[str, Path]:
    """Get module name to path mappings for @trellis/* aliases.

    Returns:
        Dict mapping module names to their base paths (e.g., {"core": Path(...)})
    """
    return {module.name: module._base_path for module in collected.modules if module._base_path}


class PackageInstallStep(BuildStep):
    """Install npm packages using ensure_packages().

    Stores packages in manifest metadata for change detection.
    """

    @property
    def name(self) -> str:
        return "package-install"

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if packages have changed since last build.

        Returns SKIP if packages unchanged, BUILD if different or no previous.
        """
        if step_manifest is None:
            return ShouldBuild.BUILD

        prev_packages = step_manifest.metadata.get("packages")
        current_packages = dict(ctx.collected.packages)

        if prev_packages != current_packages:
            return ShouldBuild.BUILD
        return ShouldBuild.SKIP

    def run(self, ctx: BuildContext) -> None:
        packages = dict(ctx.collected.packages)
        ensure_packages(packages, ctx.workspace)

        # Store packages in step manifest for next build's comparison
        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        step_manifest.metadata["packages"] = packages


class RegistryGenerationStep(BuildStep):
    """Generate _registry.ts wiring file.

    Sets ctx.generated_files["_registry"] and adds alias to ctx.esbuild_args.
    """

    @property
    def name(self) -> str:
        return "registry-generation"

    def _compute_collected_hash(self, ctx: BuildContext) -> str:
        """Compute stable hash of collected modules structure."""
        modules_data = [
            {"name": m.name, "exports": [(e.name, e.kind, e.source) for e in m.exports]}
            for m in ctx.collected.modules
        ]
        data_str = json.dumps(modules_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if registry needs regenerating based on collected modules.

        When skipping, restores context fields that run() would have set.
        """
        if step_manifest is None:
            return ShouldBuild.BUILD

        current_hash = self._compute_collected_hash(ctx)
        if step_manifest.metadata.get("collected_hash") != current_hash:
            return ShouldBuild.BUILD

        # Verify output file exists - rebuild if deleted
        registry_path = ctx.workspace / "_registry.ts"
        if not registry_path.exists():
            return ShouldBuild.BUILD

        # Skipping - restore context fields that run() would have set
        ctx.generated_files["_registry"] = registry_path
        ctx.esbuild_args.append(f"--alias:@trellis/_registry={registry_path}")

        return ShouldBuild.SKIP

    def run(self, ctx: BuildContext) -> None:
        registry_path = write_registry_ts(ctx.workspace, ctx.collected)
        ctx.generated_files["_registry"] = registry_path
        ctx.esbuild_args.append(f"--alias:@trellis/_registry={registry_path}")

        # Store hash for next build's comparison
        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        step_manifest.metadata["collected_hash"] = self._compute_collected_hash(ctx)


class TsconfigStep(BuildStep):
    """Generate tsconfig.json with path aliases for type checking.

    Sets ctx.generated_files["tsconfig"].
    """

    @property
    def name(self) -> str:
        return "tsconfig"

    def _compute_inputs_hash(self, ctx: BuildContext) -> str:
        """Compute stable hash of inputs that determine tsconfig content."""
        aliases = sorted((m.name, str(m._base_path)) for m in ctx.collected.modules if m._base_path)
        inputs_data = {
            "aliases": aliases,
            "entry_point": str(ctx.entry_point),
            "has_registry": "_registry" in ctx.generated_files,
        }
        data_str = json.dumps(inputs_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if tsconfig needs regenerating based on inputs.

        When skipping, restores context fields that run() would have set.
        """
        if step_manifest is None:
            return ShouldBuild.BUILD

        # Verify output file exists - rebuild if deleted
        tsconfig_path = ctx.workspace / "tsconfig.json"
        if not tsconfig_path.exists():
            return ShouldBuild.BUILD

        current_hash = self._compute_inputs_hash(ctx)
        if step_manifest.metadata.get("inputs_hash") != current_hash:
            return ShouldBuild.BUILD

        # Restore context fields that run() would have set
        ctx.generated_files["tsconfig"] = tsconfig_path

        return ShouldBuild.SKIP

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

        # Store hash for next build's comparison
        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        step_manifest.metadata["inputs_hash"] = self._compute_inputs_hash(ctx)


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

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if type check needs rerunning based on source/marker mtimes."""
        if step_manifest is None:
            return ShouldBuild.BUILD
        if not step_manifest.source_paths or not step_manifest.dest_files:
            return ShouldBuild.BUILD
        if is_rebuild_needed(step_manifest.source_paths, step_manifest.dest_files):
            return ShouldBuild.BUILD
        return ShouldBuild.SKIP

    def run(self, ctx: BuildContext) -> None:
        tsc = get_bin(node_modules_path(ctx.workspace), "tsc")
        tsconfig_path = ctx.generated_files.get("tsconfig")

        cmd = [str(tsc), "--noEmit"]
        if tsconfig_path:
            cmd.extend(["--project", str(tsconfig_path)])

        result = ctx.exec_in_build_env(cmd, check=False)

        if result.returncode != 0:
            if self.fail_on_error:
                raise subprocess.CalledProcessError(result.returncode, cmd)
            logger.warning("TypeScript type-checking failed (continuing anyway)")

        # Touch marker and track sources
        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        marker = ctx.workspace / ".tsc-check"
        marker.touch()
        step_manifest.dest_files.add(marker)

        # Track source files
        step_manifest.source_paths.update(collect_ts_source_files(ctx.entry_point.parent))

        # Track generated files as inputs
        for gen_file in ctx.generated_files.values():
            if gen_file.exists():
                step_manifest.source_paths.add(gen_file)


class DeclarationStep(BuildStep):
    """Generate a bundled TypeScript declaration file (.d.ts).

    Uses dts-bundle-generator to create a single declaration file from the
    entry point, with tree-shaking of unused types.
    """

    @property
    def name(self) -> str:
        return "declaration"

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if declarations need regenerating based on source/output mtimes."""
        if step_manifest is None:
            return ShouldBuild.BUILD
        if not step_manifest.source_paths or not step_manifest.dest_files:
            return ShouldBuild.BUILD
        if is_rebuild_needed(step_manifest.source_paths, step_manifest.dest_files):
            return ShouldBuild.BUILD
        return ShouldBuild.SKIP

    def run(self, ctx: BuildContext) -> None:
        dts_generator = get_bin(node_modules_path(ctx.workspace), "dts-bundle-generator")
        tsconfig_path = ctx.generated_files.get("tsconfig")

        # Output file name matches the entry point (index.ts -> index.d.ts)
        output_name = ctx.entry_point.stem + ".d.ts"
        output_file = ctx.dist_dir / output_name

        cmd = [
            str(dts_generator),
            "-o",
            str(output_file),
            str(ctx.entry_point),
            "--no-banner",  # Don't add "Generated by dts-bundle-generator" comment
        ]
        if tsconfig_path:
            cmd.extend(["--project", str(tsconfig_path)])

        ctx.exec_in_build_env(cmd)

        # Track sources and outputs
        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        step_manifest.source_paths.update(collect_ts_source_files(ctx.entry_point.parent))
        step_manifest.dest_files.add(output_file)

        # Track generated files as inputs
        for gen_file in ctx.generated_files.values():
            if gen_file.exists():
                step_manifest.source_paths.add(gen_file)


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

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if bundle needs rebuilding based on source/output mtimes."""
        if step_manifest is None:
            return ShouldBuild.BUILD
        if not step_manifest.source_paths or not step_manifest.dest_files:
            return ShouldBuild.BUILD
        if is_rebuild_needed(step_manifest.source_paths, step_manifest.dest_files):
            return ShouldBuild.BUILD
        return ShouldBuild.SKIP

    def run(self, ctx: BuildContext) -> None:
        esbuild = get_bin(node_modules_path(ctx.workspace), "esbuild")
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

        ctx.exec_in_build_env(cmd)

        # Populate step manifest from metafile
        metafile = read_metafile(ctx.workspace)
        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        step_manifest.source_paths.update(metafile.inputs)
        step_manifest.dest_files.update(metafile.outputs)


class StaticFileCopyStep(BuildStep):
    """Copy static files to the dist directory using convention-based discovery.

    Copies from:
    - module._base_path / "static" for each registered module
    - ctx.app_static_dir if provided (for app-level static files)
    """

    @property
    def name(self) -> str:
        return "static-file-copy"

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if static files need copying based on source/output mtimes."""
        if step_manifest is None:
            return ShouldBuild.BUILD
        if not step_manifest.source_paths or not step_manifest.dest_files:
            return ShouldBuild.BUILD
        if is_rebuild_needed(step_manifest.source_paths, step_manifest.dest_files):
            return ShouldBuild.BUILD
        return ShouldBuild.SKIP

    def run(self, ctx: BuildContext) -> None:
        # Copy from each module's static directory
        for module in ctx.collected.modules:
            if module._base_path is None:
                continue
            static_dir = module._base_path / "static"
            if static_dir.is_dir():
                self._copy_and_track(static_dir, ctx.dist_dir, ctx)

        # Copy from app-level static directory
        if ctx.app_static_dir is not None and ctx.app_static_dir.is_dir():
            self._copy_and_track(ctx.app_static_dir, ctx.dist_dir, ctx)

    def _copy_and_track(self, src_dir: Path, dest_dir: Path, ctx: BuildContext) -> None:
        """Copy directory and track in step manifest.

        Args:
            src_dir: Source directory (added as directory input)
            dest_dir: Destination directory
            ctx: Build context
        """
        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())

        # Add source directory (not individual files) - enables recursive mtime checking
        step_manifest.source_paths.add(src_dir)

        # Copy entire tree
        shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)

        # Build files list with glob
        for dest_file in dest_dir.glob("**/*"):
            if dest_file.is_file():
                step_manifest.dest_files.add(dest_file)


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

    def _compute_context_hash(self, ctx: BuildContext) -> str:
        """Compute hash of merged template context."""
        merged_context = {**ctx.template_context, **self._context}
        context_str = json.dumps(merged_context, sort_keys=True, default=str)
        return hashlib.sha256(context_str.encode()).hexdigest()

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if index.html needs regenerating based on template/context."""
        if step_manifest is None:
            return ShouldBuild.BUILD
        if not step_manifest.source_paths or not step_manifest.dest_files:
            return ShouldBuild.BUILD

        # Check template mtime
        if is_rebuild_needed(step_manifest.source_paths, step_manifest.dest_files):
            return ShouldBuild.BUILD

        # Check context hash
        current_hash = self._compute_context_hash(ctx)
        if step_manifest.metadata.get("context_hash") != current_hash:
            return ShouldBuild.BUILD

        return ShouldBuild.SKIP

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

        # Populate step manifest
        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        step_manifest.source_paths.add(self._template_path)
        step_manifest.dest_files.add(output_path)
        step_manifest.metadata["context_hash"] = self._compute_context_hash(ctx)
