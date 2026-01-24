"""Unit tests for BuildManifest."""

from __future__ import annotations

import json
import time
from pathlib import Path

from trellis.bundler.build import build
from trellis.bundler.manifest import (
    BuildManifest,
    StepManifest,
    get_manifest_path,
    load_manifest,
    save_manifest,
)
from trellis.bundler.registry import ModuleRegistry
from trellis.bundler.steps import BuildContext, BuildStep, ShouldBuild
from trellis.bundler.utils import is_rebuild_needed


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
        assert data["version"] == 2
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
                    "version": 2,
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


class TestBuildWithPartialSteps:
    """Tests for build() with per-step staleness decisions."""

    def test_skips_step_when_should_build_returns_skip(self, tmp_path: Path) -> None:
        """build() skips step when should_build returns SKIP and previous manifest exists."""

        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        # Create previous manifest so SKIP has something to skip to
        prev_manifest = BuildManifest()
        prev_manifest.steps["skip-step"] = StepManifest(metadata={"previous": True})
        save_manifest(workspace, prev_manifest)

        step_ran = []

        class SkipStep(BuildStep):
            @property
            def name(self) -> str:
                return "skip-step"

            def run(self, ctx: BuildContext) -> None:
                step_ran.append(True)

            def should_build(
                self, ctx: BuildContext, step_manifest: StepManifest | None
            ) -> ShouldBuild | None:
                return ShouldBuild.SKIP

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[SkipStep()],
            force=False,
        )

        assert step_ran == [], "Step should not run when should_build returns SKIP"

    def test_runs_step_when_should_build_returns_build(self, tmp_path: Path) -> None:
        """build() runs step when should_build returns BUILD."""

        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        step_ran = []

        class BuildAlwaysStep(BuildStep):
            @property
            def name(self) -> str:
                return "build-always"

            def run(self, ctx: BuildContext) -> None:
                step_ran.append(True)

            def should_build(
                self, ctx: BuildContext, step_manifest: StepManifest | None
            ) -> ShouldBuild | None:
                return ShouldBuild.BUILD

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[BuildAlwaysStep()],
            force=False,
        )

        assert step_ran == [True], "Step should run when should_build returns BUILD"

    def test_runs_step_when_should_build_returns_none(self, tmp_path: Path) -> None:
        """build() runs step when should_build returns None (always run)."""

        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        step_ran = []

        class DefaultStep(BuildStep):
            @property
            def name(self) -> str:
                return "default-step"

            def run(self, ctx: BuildContext) -> None:
                step_ran.append(True)

            # Uses default should_build which returns None

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[DefaultStep()],
            force=False,
        )

        assert step_ran == [True], "Step should run when should_build returns None"

    def test_preserves_manifest_for_skipped_steps(self, tmp_path: Path) -> None:
        """build() preserves previous manifest section for skipped steps."""

        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        # Create previous manifest with data for the step
        prev_manifest = BuildManifest()
        prev_manifest.steps["skip-step"] = StepManifest(
            source_paths={tmp_path / "old_source.ts"},
            dest_files={tmp_path / "old_output.js"},
            metadata={"preserved": True},
        )
        save_manifest(workspace, prev_manifest)

        class SkipStep(BuildStep):
            @property
            def name(self) -> str:
                return "skip-step"

            def run(self, ctx: BuildContext) -> None:
                pass  # Should not be called

            def should_build(
                self, ctx: BuildContext, step_manifest: StepManifest | None
            ) -> ShouldBuild | None:
                return ShouldBuild.SKIP

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[SkipStep()],
            force=False,
        )

        # Load the new manifest and verify old data was preserved
        new_manifest = load_manifest(workspace)
        assert new_manifest is not None
        assert "skip-step" in new_manifest.steps
        assert new_manifest.steps["skip-step"].metadata == {"preserved": True}

    def test_force_flag_runs_all_steps(self, tmp_path: Path) -> None:
        """build() runs all steps when force=True, ignoring should_build."""

        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        step_ran = []

        class SkipStep(BuildStep):
            @property
            def name(self) -> str:
                return "skip-step"

            def run(self, ctx: BuildContext) -> None:
                step_ran.append(True)

            def should_build(
                self, ctx: BuildContext, step_manifest: StepManifest | None
            ) -> ShouldBuild | None:
                return ShouldBuild.SKIP  # Would normally skip

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[SkipStep()],
            force=True,  # Force runs all
        )

        assert step_ran == [True], "Step should run when force=True"

    def test_full_rebuild_when_no_previous_manifest(self, tmp_path: Path) -> None:
        """build() runs all steps when no previous manifest exists."""

        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"
        # Don't create workspace yet - no manifest exists
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        step_ran = []
        received_manifest = []

        class TestStep(BuildStep):
            @property
            def name(self) -> str:
                return "test-step"

            def run(self, ctx: BuildContext) -> None:
                step_ran.append(True)

            def should_build(
                self, ctx: BuildContext, step_manifest: StepManifest | None
            ) -> ShouldBuild | None:
                received_manifest.append(step_manifest)
                # Return SKIP but it should still run because no previous manifest
                return ShouldBuild.SKIP

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[TestStep()],
            force=False,
        )

        # Step should receive None for step_manifest (no previous)
        assert received_manifest == [None]
        # With no previous manifest, step runs even if SKIP (nothing to skip to)
        assert step_ran == [True]


class TestIsRebuildNeededWithDirectories:
    """Tests for is_rebuild_needed() with directory inputs."""

    def test_detects_new_file_in_directory(self, tmp_path: Path) -> None:
        """is_rebuild_needed detects new files added to a directory input."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        (static_dir / "existing.txt").write_text("existing")

        # Create output after the directory contents
        time.sleep(0.01)
        output = tmp_path / "bundle.js"
        output.write_text("output")

        # Initially should be up to date
        assert is_rebuild_needed([static_dir], [output]) is False

        # Add a new file to the directory
        time.sleep(0.01)
        (static_dir / "new.txt").write_text("new file")

        # Now should need rebuild
        assert is_rebuild_needed([static_dir], [output]) is True

    def test_detects_modified_file_in_nested_dir(self, tmp_path: Path) -> None:
        """is_rebuild_needed detects modified files in nested directories."""
        static_dir = tmp_path / "static"
        nested_dir = static_dir / "assets" / "images"
        nested_dir.mkdir(parents=True)
        nested_file = nested_dir / "logo.png"
        nested_file.write_bytes(b"original")

        # Create output after the directory contents
        time.sleep(0.01)
        output = tmp_path / "bundle.js"
        output.write_text("output")

        # Initially should be up to date
        assert is_rebuild_needed([static_dir], [output]) is False

        # Modify the nested file
        time.sleep(0.01)
        nested_file.write_bytes(b"modified")

        # Now should need rebuild
        assert is_rebuild_needed([static_dir], [output]) is True

    def test_detects_deleted_file_in_directory(self, tmp_path: Path) -> None:
        """is_rebuild_needed detects when a file is deleted from directory.

        Note: Deletion typically updates the directory's mtime, which triggers rebuild.
        """
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        to_delete = static_dir / "deleteme.txt"
        to_delete.write_text("will be deleted")

        # Create output after the directory contents
        time.sleep(0.01)
        output = tmp_path / "bundle.js"
        output.write_text("output")

        # Initially should be up to date
        assert is_rebuild_needed([static_dir], [output]) is False

        # Delete the file (this updates directory mtime)
        time.sleep(0.01)
        to_delete.unlink()

        # Should need rebuild because directory was modified
        assert is_rebuild_needed([static_dir], [output]) is True

    def test_handles_mixed_files_and_directories(self, tmp_path: Path) -> None:
        """is_rebuild_needed handles a mix of file and directory inputs."""
        # Create a regular file
        source_file = tmp_path / "main.ts"
        source_file.write_text("// source")

        # Create a directory
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        (static_dir / "data.json").write_text("{}")

        # Create output after inputs
        time.sleep(0.01)
        output = tmp_path / "bundle.js"
        output.write_text("output")

        # Initially should be up to date
        assert is_rebuild_needed([source_file, static_dir], [output]) is False

        # Modify the source file
        time.sleep(0.01)
        source_file.write_text("// modified source")

        # Should need rebuild
        assert is_rebuild_needed([source_file, static_dir], [output]) is True
