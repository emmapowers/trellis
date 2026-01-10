"""Bundle building with esbuild."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .esbuild import ensure_esbuild
from .packages import ensure_packages


@dataclass
class BundleConfig:
    """Configuration for building a client bundle."""

    name: str
    """Platform name for logging (e.g., 'server', 'desktop')."""

    src_dir: Path
    """Directory containing entry point (main.tsx)."""

    dist_dir: Path
    """Output directory for bundle.js."""

    packages: dict[str, str]
    """NPM packages to include."""

    static_files: dict[str, Path] | None = None
    """Static files to copy to dist_dir. Keys are output filenames, values are source paths."""

    extra_outputs: list[Path] | None = None
    """Additional output files that must exist for incremental build check."""

    worker_entries: dict[str, Path] | None = None
    """Worker entry points to build. Keys are output names (without extension),
    values are source paths. Workers are built as IIFE and can be imported as text
    via the .worker-bundle extension."""


def build_bundle(
    config: BundleConfig,
    common_src_dir: Path,
    force: bool = False,
    extra_packages: dict[str, str] | None = None,
) -> None:
    """Build a client bundle using esbuild.

    This is the unified build function used by all platforms. It handles:
    - Incremental build checking (skip if sources unchanged)
    - Ensuring esbuild and npm packages are available
    - Running esbuild with consistent options
    - Copying static files to dist directory

    Args:
        config: Bundle configuration
        common_src_dir: Path to shared client code (platforms/common/client/src)
        force: Force rebuild even if up to date
        extra_packages: Additional packages to include beyond config.packages
    """
    bundle_path = config.dist_dir / "bundle.js"

    css_path = config.dist_dir / "bundle.css"

    # Check if rebuild needed
    if not force:
        # All outputs must exist (JS and CSS)
        outputs_exist = bundle_path.exists() and css_path.exists()
        if config.extra_outputs:
            outputs_exist = outputs_exist and all(p.exists() for p in config.extra_outputs)

        if outputs_exist:
            bundle_mtime = bundle_path.stat().st_mtime
            platform_changed = any(
                f.stat().st_mtime > bundle_mtime for f in config.src_dir.rglob("*.ts*")
            )
            common_changed = any(
                f.stat().st_mtime > bundle_mtime
                for pattern in ("*.ts", "*.tsx", "*.css")
                for f in common_src_dir.rglob(pattern)
            )
            # Check if static source files changed
            static_changed = False
            if config.static_files:
                static_changed = any(
                    src.stat().st_mtime > bundle_mtime for src in config.static_files.values()
                )
            if not platform_changed and not common_changed and not static_changed:
                return

    # Ensure dependencies
    esbuild = ensure_esbuild()

    all_packages = {**config.packages, **(extra_packages or {})}
    node_modules = ensure_packages(all_packages)

    config.dist_dir.mkdir(parents=True, exist_ok=True)

    # Use NODE_PATH env var to resolve from our cached packages
    env = os.environ.copy()
    env["NODE_PATH"] = str(node_modules)

    # Build worker entries first (as IIFE, imported as text by main bundle)
    if config.worker_entries:
        for name, entry_path in config.worker_entries.items():
            worker_output = config.src_dir / f"{name}.worker-bundle"
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

    # Build main bundle (outputs bundle.js and bundle.css if CSS is imported)
    cmd = [
        str(esbuild),
        str(config.src_dir / "main.tsx"),
        "--bundle",
        f"--outdir={config.dist_dir}",
        "--entry-names=bundle",
        "--format=esm",
        "--platform=browser",
        "--target=es2022",
        "--jsx=automatic",
        "--loader:.tsx=tsx",
        "--loader:.ts=ts",
    ]

    # Add text loader for worker bundles
    if config.worker_entries:
        cmd.append("--loader:.worker-bundle=text")

    subprocess.run(cmd, check=True, env=env)

    # Copy static files to dist
    if config.static_files:
        for output_name, src_path in config.static_files.items():
            dest_path = config.dist_dir / output_name
            shutil.copy2(src_path, dest_path)
