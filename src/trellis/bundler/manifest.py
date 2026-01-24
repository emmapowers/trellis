"""Build manifest for tracking inputs and outputs across build steps."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Manifest format version - increment when changing the serialization format
MANIFEST_VERSION = 2


@dataclass
class StepManifest:
    """Tracks inputs and outputs for a single build step.

    Attributes:
        source_paths: Set of source file paths (inputs to the step)
        dest_files: Set of destination file paths (outputs of the step)
        metadata: Arbitrary metadata for the step (e.g., package versions)
    """

    source_paths: set[Path] = field(default_factory=set)
    dest_files: set[Path] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildManifest:
    """Tracks all inputs and outputs for a build with per-step granularity.

    Each step stores its own StepManifest in the steps dict. The source_paths
    and dest_files properties aggregate data from all steps for backwards
    compatibility with existing code.

    Attributes:
        steps: Dict mapping step name to its StepManifest
    """

    steps: dict[str, StepManifest] = field(default_factory=dict)

    @property
    def source_paths(self) -> set[Path]:
        """All source paths across all steps (backwards compat)."""
        return {p for s in self.steps.values() for p in s.source_paths}

    @property
    def dest_files(self) -> set[Path]:
        """All dest files across all steps (backwards compat)."""
        return {p for s in self.steps.values() for p in s.dest_files}


def get_manifest_path(workspace: Path) -> Path:
    """Get the path where build_manifest.json should be stored.

    Args:
        workspace: Workspace directory

    Returns:
        Path to build_manifest.json
    """
    return workspace / "build_manifest.json"


def save_manifest(workspace: Path, manifest: BuildManifest) -> None:
    """Save a BuildManifest to the workspace as JSON.

    Paths are stored relative to the workspace for portability.
    Uses version 2 format with per-step data.

    Args:
        workspace: Workspace directory
        manifest: Manifest to save
    """
    steps_data: dict[str, Any] = {}
    for step_name, step_manifest in manifest.steps.items():
        steps_data[step_name] = {
            "source_paths": sorted(
                str(p.relative_to(workspace, walk_up=True)) for p in step_manifest.source_paths
            ),
            "dest_files": sorted(
                str(p.relative_to(workspace, walk_up=True)) for p in step_manifest.dest_files
            ),
            "metadata": step_manifest.metadata,
        }

    data = {
        "version": MANIFEST_VERSION,
        "steps": steps_data,
    }

    manifest_path = get_manifest_path(workspace)
    manifest_path.write_text(json.dumps(data, indent=2))


def load_manifest(workspace: Path) -> BuildManifest | None:
    """Load a BuildManifest from the workspace.

    Paths are converted from relative to absolute using the workspace.
    Returns None if file is missing, invalid JSON, or old format (version != 2).

    Args:
        workspace: Workspace directory

    Returns:
        Loaded manifest, or None if missing/invalid/old format (triggers full rebuild)
    """
    manifest_path = get_manifest_path(workspace)

    if not manifest_path.exists():
        return None

    try:
        data = json.loads(manifest_path.read_text())
    except json.JSONDecodeError:
        return None

    # Check for current manifest format version
    if data.get("version") != MANIFEST_VERSION:
        return None

    if "steps" not in data:
        return None

    manifest = BuildManifest()

    for step_name, step_data in data["steps"].items():
        source_paths = {(workspace / p).resolve() for p in step_data.get("source_paths", [])}
        dest_files = {(workspace / p).resolve() for p in step_data.get("dest_files", [])}
        metadata = step_data.get("metadata", {})

        manifest.steps[step_name] = StepManifest(
            source_paths=source_paths,
            dest_files=dest_files,
            metadata=metadata,
        )

    return manifest
