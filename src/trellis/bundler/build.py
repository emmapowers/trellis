"""Bundle building with esbuild."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from .packages import ensure_packages, get_bin
from .workspace import write_registry_ts

if TYPE_CHECKING:
    from .registry import ModuleRegistry

logger = logging.getLogger(__name__)


def is_rebuild_needed(inputs: Iterable[Path], outputs: Iterable[Path]) -> bool:
    """Check if outputs are stale relative to inputs.

    Returns True if any output is missing or older than any input.

    Args:
        inputs: Source files to check
        outputs: Output files that should be newer than inputs

    Returns:
        True if rebuild is needed, False if outputs are up to date
    """
    input_list = list(inputs)
    output_list = list(outputs)

    # No inputs means nothing to rebuild from
    if not input_list:
        return False

    # Check all outputs exist
    for output in output_list:
        if not output.exists():
            return True

    # Find oldest output mtime
    oldest_output = min(output.stat().st_mtime for output in output_list)

    # Check if any input is newer than oldest output
    for input_file in input_list:
        if input_file.exists() and input_file.stat().st_mtime > oldest_output:
            return True

    return False


def build_from_registry(
    registry: ModuleRegistry,
    entry_point: Path,
    workspace: Path,
    *,
    force: bool = False,
    typecheck: bool = True,
    output_dir: Path | None = None,
    library: bool = False,
) -> None:
    """Build a bundle using the module registry.

    This function:
    - Collects all registered modules
    - Generates _registry.ts wiring file
    - Optionally runs tsc for type-checking
    - Runs esbuild with path aliases pointing directly to source files

    Args:
        registry: Module registry with registered modules
        entry_point: Path to entry point file (e.g., app.tsx or main.tsx)
        workspace: Workspace directory for generated files and output
        force: Force rebuild even if up to date
        typecheck: Run TypeScript type-checking before bundling (default True)
        output_dir: Custom output directory for bundle files (default: workspace/dist)
        library: Build as library with exports and declarations (default False)
    """
    dist_dir = output_dir or (workspace / "dist")
    # Library mode outputs index.js, app mode outputs bundle.js
    output_name = "index" if library else "bundle"
    bundle_path = dist_dir / f"{output_name}.js"
    css_path = dist_dir / f"{output_name}.css"

    # Collect registered modules (need this for input file list)
    collected = registry.collect()

    # Check if rebuild needed
    if not force:
        # Collect all input files: entry point, module files, and static files
        input_files: list[Path] = [entry_point]
        for module in collected.modules:
            if module._base_path:
                input_files.extend(module._base_path / f for f in module.files)
            input_files.extend(module.static_files.values())

        outputs = [bundle_path, css_path]
        if not is_rebuild_needed(input_files, outputs):
            return

    # Generate _registry.ts wiring file
    registry_path = write_registry_ts(workspace, collected)

    # Ensure dependencies (installed directly in workspace)
    packages = dict(collected.packages)
    ensure_packages(packages, workspace)
    node_modules = workspace / "node_modules"
    esbuild = get_bin(node_modules, "esbuild")

    # Use NODE_PATH env var to resolve from our packages
    env = os.environ.copy()
    env["NODE_PATH"] = str(node_modules)

    # Note: Type-checking is currently disabled since we removed workspace staging.
    # The tsc needs a tsconfig.json to work, which we no longer generate.
    # TODO: Re-enable type-checking by using root tsconfig.json

    # Generate declarations for library mode
    if library:
        dist_dir.mkdir(parents=True, exist_ok=True)
        # Skip declaration generation for now - needs tsconfig setup
        pass

    dist_dir.mkdir(parents=True, exist_ok=True)

    # Build main bundle with esbuild aliases pointing to source files
    cmd = [
        str(esbuild),
        str(entry_point),
        "--bundle",
        f"--outdir={dist_dir}",
        f"--entry-names={output_name}",
        "--format=esm",
        "--platform=browser",
        "--target=es2022",
        "--jsx=automatic",
        "--loader:.tsx=tsx",
        "--loader:.ts=ts",
    ]

    # Note: In library mode, we intentionally bundle React rather than
    # externalizing it. The mount() API uses the bundled React instance,
    # avoiding version conflicts with the host application's React.

    # Add alias for each module - point directly to source paths
    cmd.extend(
        f"--alias:@trellis/{module.name}={module._base_path}"
        for module in collected.modules
        if module._base_path
    )

    # Add alias for generated _registry
    cmd.append(f"--alias:@trellis/_registry={registry_path}")

    subprocess.run(cmd, check=True, env=env)

    # Copy static files to dist
    for module in collected.modules:
        for static_name, src_path in module.static_files.items():
            dst_path = dist_dir / static_name
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
