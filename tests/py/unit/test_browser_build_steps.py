"""Unit tests for browser platform build steps."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from trellis.bundler.manifest import BuildManifest, StepManifest
from trellis.bundler.steps import BuildContext, ShouldBuild
from trellis.platforms.browser.build_steps import (
    _PYODIDE_WORKER_PATH,
    PyodideWorkerBuildStep,
    PythonSourceBundleStep,
    WheelCopyStep,
    build_source_config,
)


class TestPythonSourceBundleStep:
    """Tests for PythonSourceBundleStep."""

    def _make_context(self, tmp_path: Path, **kwargs) -> BuildContext:
        """Create a BuildContext for testing."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()
        return BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
            **kwargs,
        )

    def test_skips_when_no_entry_point(self, tmp_path: Path) -> None:
        """Step is a no-op when python_entry_point is None."""
        ctx = self._make_context(tmp_path)
        step = PythonSourceBundleStep()

        step.run(ctx)

        # template_context should remain empty
        assert "source_json" not in ctx.template_context

    def test_adds_source_json_for_single_file(self, tmp_path: Path) -> None:
        """Step adds source_json to template_context for single file."""
        # Create a single Python file
        app_file = tmp_path / "app.py"
        app_file.write_text("print('hello')")

        ctx = self._make_context(tmp_path, python_entry_point=app_file)
        step = PythonSourceBundleStep()

        step.run(ctx)

        assert "source_json" in ctx.template_context
        source_json = ctx.template_context["source_json"]
        assert '"type": "code"' in source_json
        assert "print('hello')" in source_json

    def test_adds_source_json_for_package(self, tmp_path: Path) -> None:
        """Step adds source_json to template_context for package."""
        # Create a package
        pkg = tmp_path / "myapp"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("# init")
        (pkg / "__main__.py").write_text("print('main')")

        ctx = self._make_context(tmp_path, python_entry_point=pkg / "__main__.py")
        step = PythonSourceBundleStep()

        step.run(ctx)

        assert "source_json" in ctx.template_context
        source_json = ctx.template_context["source_json"]
        assert '"type": "module"' in source_json
        assert '"moduleName": "myapp"' in source_json

    def test_adds_routing_mode_to_context(self, tmp_path: Path) -> None:
        """Step adds routing_mode to template_context."""
        app_file = tmp_path / "app.py"
        app_file.write_text("x = 1")

        ctx = self._make_context(tmp_path, python_entry_point=app_file)
        step = PythonSourceBundleStep()

        step.run(ctx)

        assert ctx.template_context["routing_mode"] == "hash_url"

    def test_escapes_script_tags_in_source(self, tmp_path: Path) -> None:
        """Step escapes </script> in source to prevent XSS."""
        app_file = tmp_path / "app.py"
        app_file.write_text('x = "</script><script>alert(1)</script>"')

        ctx = self._make_context(tmp_path, python_entry_point=app_file)
        step = PythonSourceBundleStep()

        step.run(ctx)

        source_json = ctx.template_context["source_json"]
        # Should escape </ to <\/
        assert "</script>" not in source_json
        assert r"<\/script>" in source_json

    def test_step_name(self) -> None:
        """Step has correct name."""
        step = PythonSourceBundleStep()
        assert step.name == "python-source-bundle"


class TestPyodideWorkerBuildStep:
    """Tests for PyodideWorkerBuildStep."""

    def _make_context(self, tmp_path: Path, **kwargs) -> BuildContext:
        """Create a BuildContext for testing."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        # Set up node_modules
        node_modules = workspace / "node_modules"
        node_modules.mkdir(parents=True, exist_ok=True)
        (node_modules / ".bin").mkdir()

        return BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=mock_collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
            **kwargs,
        )

    def test_step_name(self) -> None:
        """Step has correct name."""
        step = PyodideWorkerBuildStep()
        assert step.name == "pyodide-worker-build"

    def test_runs_esbuild_with_correct_arguments(self, tmp_path: Path) -> None:
        """Step runs esbuild with bundle, IIFE format, and browser platform."""
        ctx = self._make_context(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            step.run(ctx)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]

        # Verify key esbuild flags
        assert "esbuild" in str(cmd[0])
        assert str(_PYODIDE_WORKER_PATH) in cmd
        assert "--bundle" in cmd
        assert "--format=iife" in cmd
        assert "--platform=browser" in cmd
        assert "--target=es2022" in cmd
        assert "--loader:.ts=ts" in cmd

    def test_outputs_to_workspace_worker_bundle(self, tmp_path: Path) -> None:
        """Step outputs bundle to workspace/pyodide.worker-bundle."""
        ctx = self._make_context(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            step.run(ctx)

        cmd = mock_run.call_args[0][0]
        expected_outfile = f"--outfile={ctx.workspace / 'pyodide.worker-bundle'}"
        assert expected_outfile in cmd

    def test_appends_text_loader_to_esbuild_args(self, tmp_path: Path) -> None:
        """Step appends --loader:.worker-bundle=text to ctx.esbuild_args."""
        ctx = self._make_context(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run"):
            step.run(ctx)

        assert "--loader:.worker-bundle=text" in ctx.esbuild_args

    def test_appends_alias_to_esbuild_args(self, tmp_path: Path) -> None:
        """Step appends worker bundle alias to ctx.esbuild_args."""
        ctx = self._make_context(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run"):
            step.run(ctx)

        expected_alias = (
            f"--alias:@trellis/trellis-browser/pyodide.worker-bundle="
            f"{ctx.workspace / 'pyodide.worker-bundle'}"
        )
        assert expected_alias in ctx.esbuild_args

    def test_populates_step_manifest_source_paths(self, tmp_path: Path) -> None:
        """Step adds worker source directory to step manifest source_paths."""
        ctx = self._make_context(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run"):
            step.run(ctx)

        step_manifest = ctx.manifest.steps["pyodide-worker-build"]
        # Should track the parent directory of the worker source file
        assert _PYODIDE_WORKER_PATH.parent in step_manifest.source_paths

    def test_populates_step_manifest_dest_files(self, tmp_path: Path) -> None:
        """Step adds output bundle to step manifest dest_files."""
        ctx = self._make_context(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run"):
            step.run(ctx)

        step_manifest = ctx.manifest.steps["pyodide-worker-build"]
        expected_output = ctx.workspace / "pyodide.worker-bundle"
        assert expected_output in step_manifest.dest_files

    def test_passes_context_env_to_subprocess(self, tmp_path: Path) -> None:
        """Step passes ctx.env to subprocess.run."""
        ctx = self._make_context(tmp_path)
        ctx.env["NODE_PATH"] = "/custom/node_modules"
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            step.run(ctx)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["env"]["NODE_PATH"] == "/custom/node_modules"


class TestWheelCopyStep:
    """Tests for WheelCopyStep."""

    def _make_context(self, tmp_path: Path, **kwargs) -> BuildContext:
        """Create a BuildContext for testing."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()
        dist_dir = tmp_path / "build_dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        return BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=dist_dir,
            manifest=BuildManifest(),
            **kwargs,
        )

    def test_copies_wheel_to_dist(self, tmp_path: Path) -> None:
        """Step copies trellis wheel from project dist/ to build dist_dir."""
        # Create a fake project dist with wheel
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)
        wheel_file = project_dist / "trellis-0.1.0-py3-none-any.whl"
        wheel_file.write_text("fake wheel content")

        ctx = self._make_context(tmp_path)
        step = WheelCopyStep(project_dist)

        step.run(ctx)

        # Wheel should be copied to build dist_dir
        copied_wheel = ctx.dist_dir / "trellis-0.1.0-py3-none-any.whl"
        assert copied_wheel.exists()
        assert copied_wheel.read_text() == "fake wheel content"

    def test_raises_when_no_wheel_found(self, tmp_path: Path) -> None:
        """Step raises RuntimeError when no wheel is found."""
        # Empty project dist
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)

        ctx = self._make_context(tmp_path)
        step = WheelCopyStep(project_dist)

        with pytest.raises(RuntimeError, match=r"trellis wheel not found"):
            step.run(ctx)

    def test_raises_when_dist_dir_not_exists(self, tmp_path: Path) -> None:
        """Step raises RuntimeError when project dist/ doesn't exist."""
        project_dist = tmp_path / "nonexistent" / "dist"

        ctx = self._make_context(tmp_path)
        step = WheelCopyStep(project_dist)

        with pytest.raises(RuntimeError, match=r"trellis wheel not found"):
            step.run(ctx)

    def test_uses_latest_wheel_when_multiple(self, tmp_path: Path) -> None:
        """Step uses most recent wheel when multiple exist."""
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)

        # Create older wheel
        old_wheel = project_dist / "trellis-0.1.0-py3-none-any.whl"
        old_wheel.write_text("old wheel")

        # Small delay to ensure different mtime
        time.sleep(0.01)

        # Create newer wheel
        new_wheel = project_dist / "trellis-0.2.0-py3-none-any.whl"
        new_wheel.write_text("new wheel")

        ctx = self._make_context(tmp_path)
        step = WheelCopyStep(project_dist)

        step.run(ctx)

        # Should copy the newer wheel
        wheels = list(ctx.dist_dir.glob("*.whl"))
        assert len(wheels) == 1
        assert wheels[0].read_text() == "new wheel"

    def test_step_name(self) -> None:
        """Step has correct name."""
        step = WheelCopyStep(Path("/fake"))
        assert step.name == "wheel-copy"


class TestBuildSourceConfig:
    """Tests for build_source_config function."""

    def test_single_file_returns_code_type(self, tmp_path: Path) -> None:
        """Returns type='code' config for single file outside package."""
        source = tmp_path / "script.py"
        source.write_text("print('hello')")

        result = build_source_config(source)

        assert result["type"] == "code"
        assert result["code"] == "print('hello')"

    def test_package_returns_module_type(self, tmp_path: Path) -> None:
        """Returns type='module' config for file inside package."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("# init")
        source = pkg / "main.py"
        source.write_text("# main")

        result = build_source_config(source)

        assert result["type"] == "module"
        assert "files" in result
        assert "mypkg/__init__.py" in result["files"]
        assert "mypkg/main.py" in result["files"]

    def test_package_uses_explicit_module_name(self, tmp_path: Path) -> None:
        """Uses explicit module_name when provided."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        source = pkg / "__main__.py"
        source.write_text("# main")

        result = build_source_config(source, module_name="mypkg")

        assert result["type"] == "module"
        assert result["moduleName"] == "mypkg"

    def test_package_infers_module_name_from_file(self, tmp_path: Path) -> None:
        """Infers module name from file path when not provided."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        source = pkg / "app.py"
        source.write_text("# app")

        result = build_source_config(source)

        # Should infer mypkg.app from the file path
        assert result["moduleName"] == "mypkg.app"

    def test_package_with_main_infers_package_name(self, tmp_path: Path) -> None:
        """Infers package name when __main__.py is the entry point."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        source = pkg / "__main__.py"
        source.write_text("# main")

        result = build_source_config(source)

        # __main__.py means run as package, so moduleName is just the package
        assert result["moduleName"] == "mypkg"

    def test_nested_package_infers_full_module_path(self, tmp_path: Path) -> None:
        """Infers full dotted module path for nested packages."""
        foo = tmp_path / "foo"
        foo.mkdir()
        (foo / "__init__.py").write_text("")

        bar = foo / "bar"
        bar.mkdir()
        (bar / "__init__.py").write_text("")

        source = bar / "baz.py"
        source.write_text("# baz")

        result = build_source_config(source)

        assert result["moduleName"] == "foo.bar.baz"


class TestPythonSourceBundleStepManifest:
    """Tests for PythonSourceBundleStep manifest population."""

    def _make_context(self, tmp_path: Path, **kwargs) -> BuildContext:
        """Create a BuildContext for testing."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()
        return BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
            **kwargs,
        )

    def test_adds_single_file_to_source_paths(self, tmp_path: Path) -> None:
        """Step adds single Python file to step manifest source_paths."""
        app_file = tmp_path / "app.py"
        app_file.write_text("print('hello')")

        ctx = self._make_context(tmp_path, python_entry_point=app_file)
        step = PythonSourceBundleStep()

        step.run(ctx)

        step_manifest = ctx.manifest.steps["python-source-bundle"]
        assert app_file in step_manifest.source_paths

    def test_adds_package_directory_to_source_paths(self, tmp_path: Path) -> None:
        """Step adds package directory to step manifest source_paths for modules."""
        pkg = tmp_path / "myapp"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("# init")
        (pkg / "__main__.py").write_text("print('main')")

        ctx = self._make_context(tmp_path, python_entry_point=pkg / "__main__.py")
        step = PythonSourceBundleStep()

        step.run(ctx)

        # Package directory should be tracked (enables recursive mtime checking)
        step_manifest = ctx.manifest.steps["python-source-bundle"]
        assert pkg in step_manifest.source_paths

    def test_skips_manifest_when_no_entry_point(self, tmp_path: Path) -> None:
        """Step does not create step manifest when python_entry_point is None."""
        ctx = self._make_context(tmp_path)
        step = PythonSourceBundleStep()

        step.run(ctx)

        # Step should not create a manifest entry when no-op
        assert "python-source-bundle" not in ctx.manifest.steps


class TestWheelCopyStepManifest:
    """Tests for WheelCopyStep manifest population and should_build with new API."""

    def _make_context(self, tmp_path: Path, **kwargs) -> BuildContext:
        """Create a BuildContext for testing."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()
        dist_dir = tmp_path / "build_dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        return BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=dist_dir,
            manifest=BuildManifest(),
            **kwargs,
        )

    def test_adds_wheel_to_source_paths(self, tmp_path: Path) -> None:
        """Step adds wheel file to step manifest source_paths."""
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)
        wheel_file = project_dist / "trellis-0.1.0-py3-none-any.whl"
        wheel_file.write_text("fake wheel content")

        ctx = self._make_context(tmp_path)
        step = WheelCopyStep(project_dist)

        step.run(ctx)

        step_manifest = ctx.manifest.steps["wheel-copy"]
        assert wheel_file in step_manifest.source_paths

    def test_adds_copied_wheel_to_dest_files(self, tmp_path: Path) -> None:
        """Step adds copied wheel to step manifest dest_files."""
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)
        wheel_file = project_dist / "trellis-0.1.0-py3-none-any.whl"
        wheel_file.write_text("fake wheel content")

        ctx = self._make_context(tmp_path)
        step = WheelCopyStep(project_dist)

        step.run(ctx)

        step_manifest = ctx.manifest.steps["wheel-copy"]
        dest_wheel = ctx.dist_dir / "trellis-0.1.0-py3-none-any.whl"
        assert dest_wheel in step_manifest.dest_files

    def test_stores_wheel_name_in_step_manifest_metadata(self, tmp_path: Path) -> None:
        """Step stores wheel name in step manifest metadata."""
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)
        wheel_file = project_dist / "trellis-0.1.0-py3-none-any.whl"
        wheel_file.write_text("fake wheel content")

        ctx = self._make_context(tmp_path)
        step = WheelCopyStep(project_dist)

        step.run(ctx)

        step_manifest = ctx.manifest.steps["wheel-copy"]
        assert step_manifest.metadata["wheel_name"] == "trellis-0.1.0-py3-none-any.whl"

    def test_stores_wheel_mtime_in_step_manifest_metadata(self, tmp_path: Path) -> None:
        """Step stores wheel mtime in step manifest metadata for change detection."""
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)
        wheel_file = project_dist / "trellis-0.1.0-py3-none-any.whl"
        wheel_file.write_text("fake wheel content")
        expected_mtime = wheel_file.stat().st_mtime

        ctx = self._make_context(tmp_path)
        step = WheelCopyStep(project_dist)

        step.run(ctx)

        step_manifest = ctx.manifest.steps["wheel-copy"]
        assert step_manifest.metadata["wheel_mtime"] == expected_mtime

    def test_should_build_returns_build_when_wheel_changed(self, tmp_path: Path) -> None:
        """should_build returns BUILD when wheel name differs from previous."""
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)
        wheel_file = project_dist / "trellis-0.2.0-py3-none-any.whl"
        wheel_file.write_text("new wheel")

        ctx = self._make_context(tmp_path)

        prev_step_manifest = StepManifest(metadata={"wheel_name": "trellis-0.1.0-py3-none-any.whl"})

        step = WheelCopyStep(project_dist)

        assert step.should_build(ctx, prev_step_manifest) == ShouldBuild.BUILD

    def test_should_build_returns_skip_when_wheel_unchanged(self, tmp_path: Path) -> None:
        """should_build returns SKIP when wheel name and mtime match previous."""
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)
        wheel_file = project_dist / "trellis-0.1.0-py3-none-any.whl"
        wheel_file.write_text("wheel content")
        wheel_mtime = wheel_file.stat().st_mtime

        ctx = self._make_context(tmp_path)

        # Create the dest file that should_build checks for
        dest_wheel = ctx.dist_dir / "trellis-0.1.0-py3-none-any.whl"
        dest_wheel.write_text("wheel content")

        prev_step_manifest = StepManifest(
            metadata={"wheel_name": "trellis-0.1.0-py3-none-any.whl", "wheel_mtime": wheel_mtime}
        )

        step = WheelCopyStep(project_dist)

        assert step.should_build(ctx, prev_step_manifest) == ShouldBuild.SKIP

    def test_should_build_returns_build_when_no_previous_manifest(self, tmp_path: Path) -> None:
        """should_build returns BUILD when no previous step manifest exists."""
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)
        wheel_file = project_dist / "trellis-0.1.0-py3-none-any.whl"
        wheel_file.write_text("wheel content")

        ctx = self._make_context(tmp_path)

        step = WheelCopyStep(project_dist)

        assert step.should_build(ctx, None) == ShouldBuild.BUILD

    def test_should_build_returns_build_when_wheel_content_changed(self, tmp_path: Path) -> None:
        """should_build returns BUILD when wheel content changed even if name is same.

        This catches the case where pyproject.toml dependencies change but version
        stays the same - the wheel is rebuilt with new content but same filename.
        """
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)
        wheel_file = project_dist / "trellis-0.1.0-py3-none-any.whl"
        wheel_file.write_text("old wheel content")
        old_mtime = wheel_file.stat().st_mtime

        # Simulate rebuild with new content (e.g., added pygments dependency)
        time.sleep(0.01)  # Ensure different mtime
        wheel_file.write_text("new wheel content with pygments")

        ctx = self._make_context(tmp_path)

        # Previous manifest has same name but old mtime
        prev_step_manifest = StepManifest(
            metadata={"wheel_name": "trellis-0.1.0-py3-none-any.whl", "wheel_mtime": old_mtime}
        )

        step = WheelCopyStep(project_dist)

        assert step.should_build(ctx, prev_step_manifest) == ShouldBuild.BUILD


class TestPyodideWorkerBuildStepShouldBuild:
    """Tests for PyodideWorkerBuildStep.should_build()."""

    def _make_context(self, tmp_path: Path, **kwargs) -> BuildContext:
        """Create a BuildContext for testing."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        # Set up node_modules
        node_modules = workspace / "node_modules"
        node_modules.mkdir(parents=True, exist_ok=True)
        (node_modules / ".bin").mkdir()

        ctx = BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=mock_collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
            **kwargs,
        )
        return ctx

    def test_returns_build_when_no_previous_manifest(self, tmp_path: Path) -> None:
        """should_build returns BUILD when no previous step manifest."""
        ctx = self._make_context(tmp_path)

        step = PyodideWorkerBuildStep()
        result = step.should_build(ctx, step_manifest=None)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_source_paths_empty(self, tmp_path: Path) -> None:
        """should_build returns BUILD when previous manifest has empty source_paths."""
        ctx = self._make_context(tmp_path)
        prev_manifest = StepManifest(
            source_paths=set(),
            dest_files={ctx.workspace / "pyodide.worker-bundle"},
        )

        step = PyodideWorkerBuildStep()
        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_output_missing(self, tmp_path: Path) -> None:
        """should_build returns BUILD when output file doesn't exist."""
        ctx = self._make_context(tmp_path)
        # Create a fake source directory
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "worker.ts").write_text("// worker")

        prev_manifest = StepManifest(
            source_paths={source_dir},
            dest_files={ctx.workspace / "pyodide.worker-bundle"},  # Doesn't exist
        )

        step = PyodideWorkerBuildStep()
        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_source_newer(self, tmp_path: Path) -> None:
        """should_build returns BUILD when source is newer than output."""
        ctx = self._make_context(tmp_path)

        # Create output first
        output_file = ctx.workspace / "pyodide.worker-bundle"
        output_file.write_text("// old worker bundle")

        time.sleep(0.01)  # Ensure different mtime

        # Create source directory (newer)
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "worker.ts").write_text("// modified worker")

        prev_manifest = StepManifest(
            source_paths={source_dir},
            dest_files={output_file},
        )

        step = PyodideWorkerBuildStep()
        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_skip_when_outputs_up_to_date(self, tmp_path: Path) -> None:
        """should_build returns SKIP when outputs are newer than sources."""
        ctx = self._make_context(tmp_path)

        # Create source directory first
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "worker.ts").write_text("// worker")

        time.sleep(0.01)  # Ensure different mtime

        # Create output (newer than source)
        output_file = ctx.workspace / "pyodide.worker-bundle"
        output_file.write_text("// worker bundle")

        prev_manifest = StepManifest(
            source_paths={source_dir},
            dest_files={output_file},
        )

        step = PyodideWorkerBuildStep()
        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.SKIP

    def test_restores_esbuild_args_when_skip(self, tmp_path: Path) -> None:
        """should_build restores esbuild_args when returning SKIP."""
        ctx = self._make_context(tmp_path)
        step = PyodideWorkerBuildStep()

        # Create previous manifest with source/dest - make output newer than source
        output_file = ctx.workspace / "pyodide.worker-bundle"
        output_file.touch()

        prev_manifest = StepManifest(
            source_paths={_PYODIDE_WORKER_PATH.parent},
            dest_files={output_file},
        )

        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.SKIP
        assert "--loader:.worker-bundle=text" in ctx.esbuild_args
        assert any("pyodide.worker-bundle" in arg for arg in ctx.esbuild_args)


class TestPythonSourceBundleStepShouldBuild:
    """Tests for PythonSourceBundleStep.should_build()."""

    def _make_context(self, tmp_path: Path, **kwargs) -> BuildContext:
        """Create a BuildContext for testing."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()
        return BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
            **kwargs,
        )

    def test_returns_skip_when_no_python_entry_point(self, tmp_path: Path) -> None:
        """should_build returns SKIP when python_entry_point is None."""
        ctx = self._make_context(tmp_path)

        step = PythonSourceBundleStep()
        result = step.should_build(ctx, step_manifest=None)

        assert result == ShouldBuild.SKIP

    def test_returns_build_when_no_previous_manifest(self, tmp_path: Path) -> None:
        """should_build returns BUILD when no previous step manifest."""
        app_file = tmp_path / "app.py"
        app_file.write_text("print('hello')")

        ctx = self._make_context(tmp_path, python_entry_point=app_file)

        step = PythonSourceBundleStep()
        result = step.should_build(ctx, step_manifest=None)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_source_mtime_newer(self, tmp_path: Path) -> None:
        """should_build returns BUILD when source mtime is newer than stored."""
        app_file = tmp_path / "app.py"
        app_file.write_text("print('hello')")

        ctx = self._make_context(tmp_path, python_entry_point=app_file)

        # Previous manifest stores an older mtime
        prev_manifest = StepManifest(
            source_paths={app_file},
            metadata={"source_mtime": 0.0},  # Very old
        )

        step = PythonSourceBundleStep()
        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_skip_when_source_unchanged(self, tmp_path: Path) -> None:
        """should_build returns SKIP when source mtime matches stored."""
        app_file = tmp_path / "app.py"
        app_file.write_text("print('hello')")

        ctx = self._make_context(tmp_path, python_entry_point=app_file)

        # Get current mtime
        current_mtime = app_file.stat().st_mtime

        prev_manifest = StepManifest(
            source_paths={app_file},
            metadata={"source_mtime": current_mtime},
        )

        step = PythonSourceBundleStep()
        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.SKIP

    def test_returns_build_for_package_when_file_modified(self, tmp_path: Path) -> None:
        """should_build returns BUILD when any file in package is modified."""
        pkg = tmp_path / "myapp"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("# init")
        (pkg / "__main__.py").write_text("print('main')")

        ctx = self._make_context(tmp_path, python_entry_point=pkg / "__main__.py")

        # Previous manifest stores an older mtime
        prev_manifest = StepManifest(
            source_paths={pkg},
            metadata={"source_mtime": 0.0},  # Very old
        )

        step = PythonSourceBundleStep()
        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_restores_template_context_when_skip(self, tmp_path: Path) -> None:
        """should_build restores template_context when returning SKIP."""
        entry = tmp_path / "app.py"
        entry.write_text("print('hello')")

        ctx = self._make_context(tmp_path, python_entry_point=entry)
        step = PythonSourceBundleStep()
        step.run(ctx)
        mtime = ctx.manifest.steps["python-source-bundle"].metadata["source_mtime"]

        # Fresh context - template_context is empty
        fresh_ctx = self._make_context(tmp_path, python_entry_point=entry)
        prev_manifest = StepManifest(
            source_paths={entry},
            metadata={"source_mtime": mtime},
        )

        result = step.should_build(fresh_ctx, prev_manifest)

        assert result == ShouldBuild.SKIP
        assert "source_json" in fresh_ctx.template_context
        assert fresh_ctx.template_context["routing_mode"] == "hash_url"
