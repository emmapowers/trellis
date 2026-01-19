"""Utilities for reading and parsing esbuild metafile."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Metafile:
    """Parsed esbuild metafile with resolved paths.

    Attributes:
        inputs: Absolute paths to input files (source files only, no node_modules)
        outputs: Absolute paths to output files
    """

    inputs: list[Path]
    outputs: list[Path]


def get_metafile_path(workspace: Path) -> Path:
    """Get the path where metafile.json should be stored.

    Args:
        workspace: Workspace directory

    Returns:
        Path to metafile.json
    """
    return workspace / "metafile.json"


def read_metafile(workspace: Path) -> Metafile:
    """Read and parse an esbuild metafile from the workspace.

    Parses the metafile and returns resolved absolute paths for inputs
    and outputs. Filters out node_modules from inputs since those are
    managed separately and don't trigger rebuilds.

    Args:
        workspace: Workspace directory containing metafile.json

    Returns:
        Parsed Metafile with absolute paths

    Raises:
        FileNotFoundError: If metafile.json doesn't exist
        ValueError: If metafile.json contains invalid JSON
    """
    metafile_path = get_metafile_path(workspace)

    try:
        data = json.loads(metafile_path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in metafile: {metafile_path}") from e

    # Parse inputs - paths are relative to workspace, filter out node_modules
    inputs: list[Path] = []
    for rel_path in data["inputs"]:
        if "node_modules" not in rel_path:
            abs_path = (workspace / rel_path).resolve()
            inputs.append(abs_path)

    # Parse outputs - paths are relative to workspace
    outputs: list[Path] = []
    for rel_path in data["outputs"]:
        abs_path = (workspace / rel_path).resolve()
        outputs.append(abs_path)

    return Metafile(inputs=inputs, outputs=outputs)
