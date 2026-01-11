"""Bundle building with esbuild."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from .esbuild import ensure_esbuild
from .packages import ensure_packages
from .workspace import stage_workspace

if TYPE_CHECKING:
    from .registry import CollectedModules, ModuleRegistry


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
) -> None:
    """Build a bundle using the module registry.

    This is the new registry-based build function. It:
    - Collects all registered modules
    - Stages files into a workspace
    - Generates _registry.ts wiring file
    - Runs esbuild with path aliases for @trellis/ imports

    Args:
        registry: Module registry with registered modules
        entry_point: Path to entry point file (e.g., app.tsx or main.tsx)
        workspace: Workspace directory for staging and output
        force: Force rebuild even if up to date
    """
    dist_dir = workspace / "dist"
    bundle_path = dist_dir / "bundle.js"
    css_path = dist_dir / "bundle.css"
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

    # Ensure dependencies
    esbuild = ensure_esbuild()
    node_modules = ensure_packages(collected.packages)

    dist_dir.mkdir(parents=True, exist_ok=True)

    # Use NODE_PATH env var to resolve from our cached packages
    env = os.environ.copy()
    env["NODE_PATH"] = str(node_modules)

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
        "--entry-names=bundle",
        "--format=esm",
        "--platform=browser",
        "--target=es2022",
        "--jsx=automatic",
        "--loader:.tsx=tsx",
        "--loader:.ts=ts",
        "--loader:.worker-bundle=text",
    ]

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
            shutil.copy2(src_path, dst_path)

    # Write snippets hash for incremental builds
    snippets_hash_file.write_text(compute_snippets_hash(collected))
