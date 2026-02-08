"""Unit tests for BuildManifest."""

from __future__ import annotations

import json
from pathlib import Path

from trellis.bundler.manifest import (
    BuildManifest,
    StepManifest,
    get_manifest_path,
    load_manifest,
    save_manifest,
)


class TestStepManifest:
    """Tests for StepManifest dataclass."""

    def test_creates_with_defaults(self) -> None:
        """StepManifest can be created with default empty values."""
        manifest = StepManifest()

        assert manifest.source_paths == set()
        assert manifest.dest_files == set()
        assert manifest.metadata == {}

    def test_adds_source_path(self) -> None:
        """StepManifest tracks source paths."""
        manifest = StepManifest()

        manifest.source_paths.add(Path("/some/source/file.ts"))
        manifest.source_paths.add(Path("/some/other/file.py"))

        assert Path("/some/source/file.ts") in manifest.source_paths
        assert Path("/some/other/file.py") in manifest.source_paths

    def test_adds_dest_file(self) -> None:
        """StepManifest tracks destination files."""
        manifest = StepManifest()

        manifest.dest_files.add(Path("/dist/bundle.js"))
        manifest.dest_files.add(Path("/dist/bundle.css"))

        assert Path("/dist/bundle.js") in manifest.dest_files
        assert Path("/dist/bundle.css") in manifest.dest_files

    def test_stores_metadata(self) -> None:
        """StepManifest stores arbitrary metadata."""
        manifest = StepManifest()

        manifest.metadata["packages"] = {"react": "18.2.0"}
        manifest.metadata["version"] = "1.0.0"

        assert manifest.metadata["packages"] == {"react": "18.2.0"}
        assert manifest.metadata["version"] == "1.0.0"


class TestBuildManifest:
    """Tests for BuildManifest dataclass with per-step structure."""

    def test_creates_with_empty_steps(self) -> None:
        """BuildManifest can be created with empty steps dict."""
        manifest = BuildManifest()

        assert manifest.steps == {}

    def test_adds_step_manifest(self) -> None:
        """BuildManifest can add step manifests."""
        manifest = BuildManifest()

        step_manifest = StepManifest(
            source_paths={Path("/src/file.ts")},
            dest_files={Path("/dist/bundle.js")},
            metadata={"key": "value"},
        )
        manifest.steps["bundle-build"] = step_manifest

        assert "bundle-build" in manifest.steps
        assert manifest.steps["bundle-build"] is step_manifest


class TestManifestPath:
    """Tests for get_manifest_path."""

    def test_returns_build_manifest_json_in_workspace(self, tmp_path: Path) -> None:
        """get_manifest_path returns workspace/build_manifest.json."""
        workspace = tmp_path / "workspace"

        path = get_manifest_path(workspace)

        assert path == workspace / "build_manifest.json"


class TestManifestSerialization:
    """Tests for save_manifest and load_manifest with per-step format."""

    def test_save_manifest_writes_per_step_data(self, tmp_path: Path) -> None:
        """save_manifest writes version and per-step data."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        manifest = BuildManifest()
        manifest.steps["bundle-build"] = StepManifest(
            source_paths={workspace / "src" / "file.ts"},
            dest_files={workspace / "dist" / "bundle.js"},
            metadata={"key": "value"},
        )

        save_manifest(workspace, manifest)

        manifest_path = workspace / "build_manifest.json"
        assert manifest_path.exists()

        data = json.loads(manifest_path.read_text())
        assert data["version"] == 3
        assert "steps" in data
        assert "bundle-build" in data["steps"]

    def test_load_manifest_reads_per_step_data(self, tmp_path: Path) -> None:
        """load_manifest reads per-step data from JSON."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        manifest_path = workspace / "build_manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "version": 3,
                    "steps": {
                        "step1": {
                            "source_paths": ["src/a.ts"],
                            "dest_files": ["dist/a.js"],
                            "metadata": {"foo": "bar"},
                        }
                    },
                }
            )
        )

        manifest = load_manifest(workspace)

        assert manifest is not None
        assert "step1" in manifest.steps
        assert (workspace / "src" / "a.ts") in manifest.steps["step1"].source_paths
        assert (workspace / "dist" / "a.js") in manifest.steps["step1"].dest_files
        assert manifest.steps["step1"].metadata == {"foo": "bar"}

    def test_round_trip_preserves_step_data(self, tmp_path: Path) -> None:
        """Data survives a save/load round trip."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        source_path = workspace / "src" / "file.ts"
        dest_path = workspace / "dist" / "bundle.js"

        original = BuildManifest()
        original.steps["bundle-build"] = StepManifest(
            source_paths={source_path},
            dest_files={dest_path},
            metadata={"packages": {"react": "18.2.0"}},
        )

        save_manifest(workspace, original)
        loaded = load_manifest(workspace)

        assert loaded is not None
        assert "bundle-build" in loaded.steps
        assert loaded.steps["bundle-build"].source_paths == {source_path}
        assert loaded.steps["bundle-build"].dest_files == {dest_path}
        assert loaded.steps["bundle-build"].metadata == {"packages": {"react": "18.2.0"}}

    def test_load_manifest_returns_none_for_old_format(self, tmp_path: Path) -> None:
        """load_manifest returns None for old format (triggers full rebuild)."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        manifest_path = workspace / "build_manifest.json"
        # Old format without version field
        manifest_path.write_text(
            json.dumps(
                {
                    "source_paths": ["file.ts"],
                    "dest_files": ["bundle.js"],
                    "other": {},
                }
            )
        )

        manifest = load_manifest(workspace)

        assert manifest is None

    def test_load_manifest_returns_none_for_invalid_json(self, tmp_path: Path) -> None:
        """load_manifest returns None for invalid JSON."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        manifest_path = workspace / "build_manifest.json"
        manifest_path.write_text("not valid json {")

        manifest = load_manifest(workspace)

        assert manifest is None

    def test_load_manifest_returns_none_if_missing(self, tmp_path: Path) -> None:
        """load_manifest returns None if manifest file doesn't exist."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        manifest = load_manifest(workspace)

        assert manifest is None

    def test_paths_stored_relative_to_workspace(self, tmp_path: Path) -> None:
        """Paths are stored as relative paths in JSON."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        source_path = workspace / "src" / "file.ts"
        dest_path = workspace / "dist" / "bundle.js"

        manifest = BuildManifest()
        manifest.steps["step1"] = StepManifest(
            source_paths={source_path},
            dest_files={dest_path},
        )

        save_manifest(workspace, manifest)

        manifest_path = workspace / "build_manifest.json"
        data = json.loads(manifest_path.read_text())

        step_data = data["steps"]["step1"]
        assert "src/file.ts" in step_data["source_paths"]
        assert "dist/bundle.js" in step_data["dest_files"]

    def test_handles_paths_outside_workspace(self, tmp_path: Path) -> None:
        """Paths outside workspace are stored with ../ prefix."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        external_file = tmp_path / "external" / "file.ts"

        manifest = BuildManifest()
        manifest.steps["step1"] = StepManifest(
            source_paths={external_file},
        )

        save_manifest(workspace, manifest)

        manifest_path = workspace / "build_manifest.json"
        data = json.loads(manifest_path.read_text())

        step_data = data["steps"]["step1"]
        assert len(step_data["source_paths"]) == 1
        assert step_data["source_paths"][0].startswith("../")

        # Round trip should preserve the path
        loaded = load_manifest(workspace)
        assert loaded is not None
        assert external_file in loaded.steps["step1"].source_paths
