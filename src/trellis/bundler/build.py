"""Bundle building with esbuild."""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from .bun import ensure_bun
from .esbuild import ensure_esbuild
from .packages import ensure_packages
from .workspace import stage_workspace

if TYPE_CHECKING:
    from .registry import CollectedModules, ModuleRegistry

logger = logging.getLogger(__name__)

# TypeScript version for type-checking (build-time dependency)
TYPESCRIPT_VERSION = "5.7.3"


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


def compute_snippets_hash(collected: CollectedModules) -> str:
    """Compute a hash of all snippet content for change detection.

    The hash is computed deterministically by sorting modules and snippets.

    Args:
        collected: Collected modules containing snippets

    Returns:
        SHA-256 hex digest of all snippet content
    """
    h = hashlib.sha256()
    for module in sorted(collected.modules, key=lambda m: m.name):
        for name, content in sorted(module.snippets.items()):
            h.update(f"{module.name}:{name}:{content}".encode())
    return h.hexdigest()


def snippets_changed(collected: CollectedModules, hash_file: Path) -> bool:
    """Check if snippets have changed since last build.

    Args:
        collected: Collected modules containing snippets
        hash_file: Path to stored hash file

    Returns:
        True if snippets have changed or hash file doesn't exist
    """
    current_hash = compute_snippets_hash(collected)
    if not hash_file.exists():
        return True
    return hash_file.read_text() != current_hash


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

    This is the new registry-based build function. It:
    - Collects all registered modules
    - Stages files into a workspace
    - Generates _registry.ts wiring file
    - Optionally runs tsc for type-checking
    - Runs esbuild with path aliases for @trellis/ imports

    Args:
        registry: Module registry with registered modules
        entry_point: Path to entry point file (e.g., app.tsx or main.tsx)
        workspace: Workspace directory for staging and output
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
    staged_dir = workspace / "staged"
    snippets_hash_file = workspace / ".snippets-hash"

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
        files_changed = is_rebuild_needed(input_files, outputs)
        snippets_differ = snippets_changed(collected, snippets_hash_file)

        if not files_changed and not snippets_differ:
            return

    # Stage workspace (copies files, writes snippets, generates _registry.ts)
    stage_workspace(workspace, collected, entry_point)

    # Add typescript to packages if type-checking is enabled
    packages = dict(collected.packages)
    if typecheck:
        packages["typescript"] = TYPESCRIPT_VERSION

    # Ensure dependencies
    esbuild = ensure_esbuild()
    node_modules = ensure_packages(packages)

    # Use NODE_PATH env var to resolve from our cached packages
    env = os.environ.copy()
    env["NODE_PATH"] = str(node_modules)

    # Symlink node_modules into workspace for tsc type resolution
    workspace_node_modules = workspace / "node_modules"
    if workspace_node_modules.is_symlink():
        workspace_node_modules.unlink()
    if not workspace_node_modules.exists():
        workspace_node_modules.symlink_to(node_modules)

    # Run TypeScript type-checking before bundling
    bun = ensure_bun()
    if typecheck:
        tsc_result = subprocess.run(
            [str(bun), "x", "tsc", "--noEmit"],
            check=False,
            cwd=workspace,
            env=env,
        )
        if tsc_result.returncode != 0:
            logger.warning("TypeScript type-checking failed (see errors above)")

    # Generate declarations for library mode
    if library:
        dist_dir.mkdir(parents=True, exist_ok=True)
        # Use absolute path for outDir since we run from workspace directory
        abs_dist_dir = dist_dir.resolve()
        decl_result = subprocess.run(
            [
                str(bun),
                "x",
                "tsc",
                "--emitDeclarationOnly",
                "--declaration",
                "--outDir",
                str(abs_dist_dir),
            ],
            check=False,
            cwd=workspace,
            env=env,
        )
        if decl_result.returncode != 0:
            logger.warning("Declaration generation failed (see errors above)")
        else:
            # Rename entry.d.ts to index.d.ts to match bundle name
            entry_decl = abs_dist_dir / "entry.d.ts"
            index_decl = abs_dist_dir / "index.d.ts"
            if entry_decl.exists():
                entry_decl.rename(index_decl)

    dist_dir.mkdir(parents=True, exist_ok=True)

    # Build worker entries first (as IIFE, imported as text by main bundle)
    # Worker bundle is placed next to the worker source file so relative imports work
    for module in collected.modules:
        if module.worker_entries and module._base_path:
            for name, relative_path in module.worker_entries.items():
                entry_path = staged_dir / module.name / relative_path
                # Place worker bundle next to the source file (same directory)
                worker_dir = entry_path.parent
                worker_output = worker_dir / f"{name}.worker-bundle"
                worker_cmd = [
                    str(esbuild),
                    str(entry_path),
                    "--bundle",
                    f"--outfile={worker_output}",
                    "--format=iife",
                    "--platform=browser",
                    "--target=es2022",
                    "--loader:.tsx=tsx",
                    "--loader:.ts=ts",
                ]
                subprocess.run(worker_cmd, check=True, env=env)

    # Build main bundle with esbuild aliases for @trellis/ imports
    cmd = [
        str(esbuild),
        str(workspace / "entry.tsx"),
        "--bundle",
        f"--outdir={dist_dir}",
        f"--entry-names={output_name}",
        "--format=esm",
        "--platform=browser",
        "--target=es2022",
        "--jsx=automatic",
        "--loader:.tsx=tsx",
        "--loader:.ts=ts",
        "--loader:.worker-bundle=text",
    ]

    # Note: In library mode, we intentionally bundle React rather than
    # externalizing it. The mount() API uses the bundled React instance,
    # avoiding version conflicts with the host application's React.

    # Add alias for each module
    cmd.extend(
        f"--alias:@trellis/{module.name}={staged_dir / module.name}" for module in collected.modules
    )

    # Add alias for _registry
    cmd.append(f"--alias:@trellis/_registry={staged_dir / '_registry.ts'}")

    subprocess.run(cmd, check=True, env=env)

    # Copy static files to dist
    for module in collected.modules:
        for output_name, src_path in module.static_files.items():
            dst_path = dist_dir / output_name
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)

    # Write snippets hash for incremental builds
    snippets_hash_file.write_text(compute_snippets_hash(collected))
