"""Unit tests for browser platform build steps."""

from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from trellis.bundler.manifest import BuildManifest, StepManifest
from trellis.bundler.steps import BuildContext, ShouldBuild
from trellis.bundler.wheels import ResolvedDependencies
from trellis.platforms.browser.build_steps import (
    _PYODIDE_WORKER_PATH,
    DependencyResolveStep,
    PyodideWorkerBuildStep,
    WheelBuildStep,
    WheelBundleStep,
)


def _make_context(tmp_path: Path, **kwargs: object) -> BuildContext:
    """Create a BuildContext for testing."""
    mock_registry = MagicMock()
    mock_collected = MagicMock()
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    return BuildContext(
        registry=mock_registry,
        entry_point=tmp_path / "main.tsx",
        workspace=workspace,
        collected=mock_collected,
        dist_dir=dist_dir,
        manifest=BuildManifest(),
        **kwargs,
    )


def _make_wheel(tmp_path: Path, name: str, version: str) -> Path:
    """Create a minimal .whl file with RECORD."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    dist_info = f"{name}-{version}.dist-info"
    pkg_init = f"{name}/__init__.py"
    record_entries = [
        f"{pkg_init},sha256=abc123,42",
        f"{dist_info}/METADATA,sha256=def456,100",
        f"{dist_info}/RECORD,,",
    ]
    record_content = "\n".join(record_entries) + "\n"
    wheel_path = tmp_path / f"{name}-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr(f"{dist_info}/METADATA", f"Name: {name}\nVersion: {version}\n")
        zf.writestr(f"{dist_info}/RECORD", record_content)
        zf.writestr(pkg_init, "")
    return wheel_path


class TestWheelBuildStep:
    """Tests for WheelBuildStep."""

    def test_step_name(self) -> None:
        step = WheelBuildStep(Path("/fake"))
        assert step.name == "wheel-build"

    def test_stores_wheel_in_generated_files(self, tmp_path: Path) -> None:
        """run() stores the built wheel path in ctx.generated_files."""
        ctx = _make_context(tmp_path)
        app_root = tmp_path / "app"
        app_root.mkdir()
        built_wheel = _make_wheel(ctx.workspace / "wheels", "myapp", "0.1.0")

        step = WheelBuildStep(app_root)

        with patch("trellis.platforms.browser.build_steps.build_wheel", return_value=built_wheel):
            step.run(ctx)

        assert ctx.generated_files["app_wheel"] == built_wheel

    def test_populates_manifest(self, tmp_path: Path) -> None:
        """run() populates step manifest with individual source files from RECORD."""
        ctx = _make_context(tmp_path)
        app_root = tmp_path / "app"
        app_root.mkdir()
        # Create source files matching RECORD entries
        (app_root / "myapp").mkdir()
        (app_root / "myapp" / "__init__.py").write_text("# myapp")
        (app_root / "pyproject.toml").write_text("[project]\nname = 'myapp'\n")
        built_wheel = _make_wheel(ctx.workspace / "wheels", "myapp", "0.1.0")

        step = WheelBuildStep(app_root)

        with patch("trellis.platforms.browser.build_steps.build_wheel", return_value=built_wheel):
            step.run(ctx)

        sm = ctx.manifest.steps["wheel-build"]
        assert app_root / "myapp" / "__init__.py" in sm.source_paths
        assert app_root / "pyproject.toml" in sm.source_paths
        assert app_root not in sm.source_paths  # Should NOT include the whole directory
        assert built_wheel in sm.dest_files

    def test_should_build_restores_context_on_skip(self, tmp_path: Path) -> None:
        """should_build restores generated_files["app_wheel"] when skipping."""
        ctx = _make_context(tmp_path)
        wheel_path = _make_wheel(ctx.workspace / "wheels", "myapp", "0.1.0")

        # Create output file (newer than source)
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        (source_dir / "app.py").write_text("# app")
        time.sleep(0.01)
        wheel_path.touch()

        prev_manifest = StepManifest(
            source_paths={source_dir},
            dest_files={wheel_path},
            metadata={"wheel_path": str(wheel_path)},
        )

        step = WheelBuildStep(tmp_path / "app")
        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.SKIP
        assert ctx.generated_files["app_wheel"] == wheel_path


class TestDependencyResolveStep:
    """Tests for DependencyResolveStep."""

    def test_step_name(self) -> None:
        step = DependencyResolveStep()
        assert step.name == "dependency-resolve"

    def test_stores_resolved_deps_in_build_data(self, tmp_path: Path) -> None:
        """run() stores ResolvedDependencies in ctx.build_data."""
        ctx = _make_context(tmp_path)
        app_wheel = _make_wheel(tmp_path / "wheels", "myapp", "0.1.0")
        ctx.generated_files["app_wheel"] = app_wheel

        resolved = ResolvedDependencies(
            wheel_paths=[app_wheel],
            pyodide_packages=["numpy"],
        )

        step = DependencyResolveStep()

        with patch(
            "trellis.platforms.browser.build_steps.resolve_dependencies", return_value=resolved
        ):
            step.run(ctx)

        assert ctx.build_data["resolved_deps"] is resolved

    def test_populates_manifest(self, tmp_path: Path) -> None:
        """run() tracks only app_wheel as source and writes marker as dest."""
        ctx = _make_context(tmp_path)
        app_wheel = _make_wheel(tmp_path / "wheels", "myapp", "0.1.0")
        dep_wheel = _make_wheel(tmp_path / "wheels", "click", "8.0.0")
        ctx.generated_files["app_wheel"] = app_wheel

        resolved = ResolvedDependencies(
            wheel_paths=[app_wheel, dep_wheel],
            pyodide_packages=["numpy"],
        )

        step = DependencyResolveStep()

        with patch(
            "trellis.platforms.browser.build_steps.resolve_dependencies", return_value=resolved
        ):
            step.run(ctx)

        sm = ctx.manifest.steps["dependency-resolve"]
        assert app_wheel in sm.source_paths
        assert sm.metadata["pyodide_packages"] == ["numpy"]
        assert sm.metadata["wheel_paths"] == [str(app_wheel), str(dep_wheel)]
        # Marker file written as dest
        marker = ctx.workspace / ".dependency-resolve-marker"
        assert marker in sm.dest_files
        assert marker.exists()

    def test_should_build_returns_build_when_no_manifest(self, tmp_path: Path) -> None:
        """should_build returns BUILD when no previous manifest."""
        ctx = _make_context(tmp_path)
        step = DependencyResolveStep()
        assert step.should_build(ctx, step_manifest=None) == ShouldBuild.BUILD

    def test_should_build_skips_when_app_wheel_unchanged(self, tmp_path: Path) -> None:
        """should_build skips and restores resolved_deps when app wheel is unchanged."""
        ctx = _make_context(tmp_path)
        app_wheel = _make_wheel(tmp_path / "wheels", "myapp", "0.1.0")
        dep_wheel = _make_wheel(tmp_path / "wheels", "click", "8.0.0")

        # Create marker newer than app_wheel
        time.sleep(0.01)
        marker = ctx.workspace / ".dependency-resolve-marker"
        marker.touch()

        prev_manifest = StepManifest(
            source_paths={app_wheel},
            dest_files={marker},
            metadata={
                "wheel_paths": [str(app_wheel), str(dep_wheel)],
                "pyodide_packages": ["numpy"],
            },
        )

        step = DependencyResolveStep()
        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.SKIP
        resolved = ctx.build_data["resolved_deps"]
        assert isinstance(resolved, ResolvedDependencies)
        assert resolved.wheel_paths == [app_wheel, dep_wheel]
        assert resolved.pyodide_packages == ["numpy"]

    def test_should_build_returns_build_when_app_wheel_newer(self, tmp_path: Path) -> None:
        """should_build returns BUILD when app wheel is newer than marker."""
        ctx = _make_context(tmp_path)
        app_wheel = _make_wheel(tmp_path / "wheels", "myapp", "0.1.0")

        marker = ctx.workspace / ".dependency-resolve-marker"
        marker.touch()
        time.sleep(0.01)
        app_wheel.touch()

        prev_manifest = StepManifest(
            source_paths={app_wheel},
            dest_files={marker},
            metadata={
                "wheel_paths": [str(app_wheel)],
                "pyodide_packages": [],
            },
        )

        step = DependencyResolveStep()
        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.BUILD


class TestWheelBundleStep:
    """Tests for WheelBundleStep."""

    def test_step_name(self) -> None:
        step = WheelBundleStep(entry_module="myapp")
        assert step.name == "wheel-bundle"

    def test_creates_zip_and_manifest(self, tmp_path: Path) -> None:
        """run() creates site-packages zip and manifest JSON."""
        ctx = _make_context(tmp_path)
        app_wheel = _make_wheel(tmp_path / "wheels", "myapp", "0.1.0")

        resolved = ResolvedDependencies(
            wheel_paths=[app_wheel],
            pyodide_packages=["numpy"],
        )
        ctx.build_data["resolved_deps"] = resolved

        step = WheelBundleStep(entry_module="myapp")
        step.run(ctx)

        # Check zip was created
        zip_path = ctx.generated_files["wheel_bundle"]
        assert zip_path.exists()
        with zipfile.ZipFile(zip_path) as zf:
            assert "myapp/__init__.py" in zf.namelist()

        # Check manifest was created
        manifest_path = ctx.generated_files["wheel_manifest"]
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text())
        assert manifest["entryModule"] == "myapp"
        assert manifest["pyodidePackages"] == ["numpy"]

    def test_populates_step_manifest(self, tmp_path: Path) -> None:
        """run() populates step manifest with source and dest paths."""
        ctx = _make_context(tmp_path)
        app_wheel = _make_wheel(tmp_path / "wheels", "myapp", "0.1.0")

        resolved = ResolvedDependencies(wheel_paths=[app_wheel], pyodide_packages=[])
        ctx.build_data["resolved_deps"] = resolved

        step = WheelBundleStep(entry_module="myapp")
        step.run(ctx)

        sm = ctx.manifest.steps["wheel-bundle"]
        assert app_wheel in sm.source_paths
        assert ctx.generated_files["wheel_bundle"] in sm.dest_files
        assert ctx.generated_files["wheel_manifest"] in sm.dest_files

    def test_should_build_returns_build_when_no_manifest(self, tmp_path: Path) -> None:
        """should_build returns BUILD when no previous manifest."""
        ctx = _make_context(tmp_path)
        step = WheelBundleStep(entry_module="myapp")
        assert step.should_build(ctx, step_manifest=None) == ShouldBuild.BUILD

    def test_should_build_skips_when_inputs_unchanged(self, tmp_path: Path) -> None:
        """should_build skips and restores generated_files when inputs unchanged."""
        ctx = _make_context(tmp_path)
        app_wheel = _make_wheel(tmp_path / "wheels", "myapp", "0.1.0")

        # Create output files newer than input
        time.sleep(0.01)
        zip_path = ctx.workspace / "site-packages.wheel-bundle"
        zip_path.write_bytes(b"\x00")
        manifest_path = ctx.workspace / "wheel-manifest.json"
        manifest_path.write_text("{}")

        prev_manifest = StepManifest(
            source_paths={app_wheel},
            dest_files={zip_path, manifest_path},
            metadata={
                "wheel_bundle": str(zip_path),
                "wheel_manifest": str(manifest_path),
            },
        )

        step = WheelBundleStep(entry_module="myapp")
        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.SKIP
        assert ctx.generated_files["wheel_bundle"] == zip_path
        assert ctx.generated_files["wheel_manifest"] == manifest_path

    def test_should_build_returns_build_when_input_newer(self, tmp_path: Path) -> None:
        """should_build returns BUILD when input wheel is newer than outputs."""
        ctx = _make_context(tmp_path)
        zip_path = ctx.workspace / "site-packages.wheel-bundle"
        zip_path.write_bytes(b"\x00")
        manifest_path = ctx.workspace / "wheel-manifest.json"
        manifest_path.write_text("{}")
        time.sleep(0.01)
        app_wheel = _make_wheel(tmp_path / "wheels", "myapp", "0.1.0")

        prev_manifest = StepManifest(
            source_paths={app_wheel},
            dest_files={zip_path, manifest_path},
            metadata={
                "wheel_bundle": str(zip_path),
                "wheel_manifest": str(manifest_path),
            },
        )

        step = WheelBundleStep(entry_module="myapp")
        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.BUILD


class TestPyodideWorkerBuildStep:
    """Tests for PyodideWorkerBuildStep."""

    def _make_context_with_node_modules(self, tmp_path: Path, **kwargs: object) -> BuildContext:
        """Create a BuildContext with node_modules set up."""
        ctx = _make_context(tmp_path, **kwargs)
        node_modules = ctx.workspace / "node_modules"
        node_modules.mkdir(parents=True, exist_ok=True)
        (node_modules / ".bin").mkdir()
        return ctx

    def test_step_name(self) -> None:
        step = PyodideWorkerBuildStep()
        assert step.name == "pyodide-worker-build"

    def test_runs_esbuild_with_correct_arguments(self, tmp_path: Path) -> None:
        """Step runs esbuild with bundle, IIFE format, and browser platform."""
        ctx = self._make_context_with_node_modules(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            step.run(ctx)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]

        assert "esbuild" in str(cmd[0])
        assert str(_PYODIDE_WORKER_PATH) in cmd
        assert "--bundle" in cmd
        assert "--format=iife" in cmd
        assert "--platform=browser" in cmd
        assert "--target=es2022" in cmd
        assert "--loader:.ts=ts" in cmd

    def test_outputs_to_workspace_worker_bundle(self, tmp_path: Path) -> None:
        """Step outputs bundle to workspace/pyodide.worker-bundle."""
        ctx = self._make_context_with_node_modules(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            step.run(ctx)

        cmd = mock_run.call_args[0][0]
        expected_outfile = f"--outfile={ctx.workspace / 'pyodide.worker-bundle'}"
        assert expected_outfile in cmd

    def test_appends_text_loader_to_esbuild_args(self, tmp_path: Path) -> None:
        """Step appends --loader:.worker-bundle=text to ctx.esbuild_args."""
        ctx = self._make_context_with_node_modules(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run"):
            step.run(ctx)

        assert "--loader:.worker-bundle=text" in ctx.esbuild_args

    def test_appends_alias_to_esbuild_args(self, tmp_path: Path) -> None:
        """Step appends worker bundle alias to ctx.esbuild_args."""
        ctx = self._make_context_with_node_modules(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run"):
            step.run(ctx)

        expected_alias = (
            f"--alias:@trellis/trellis-browser/pyodide.worker-bundle="
            f"{ctx.workspace / 'pyodide.worker-bundle'}"
        )
        assert expected_alias in ctx.esbuild_args

    def test_adds_wheel_aliases_when_present(self, tmp_path: Path) -> None:
        """Step includes wheel bundle/manifest aliases in esbuild command when present."""
        ctx = self._make_context_with_node_modules(tmp_path)
        wheel_bundle = ctx.workspace / "site-packages.wheel-bundle"
        wheel_bundle.write_bytes(b"fake")
        wheel_manifest = ctx.workspace / "wheel-manifest.json"
        wheel_manifest.write_text("{}")
        ctx.generated_files["wheel_bundle"] = wheel_bundle
        ctx.generated_files["wheel_manifest"] = wheel_manifest

        step = PyodideWorkerBuildStep()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            step.run(ctx)

        cmd = mock_run.call_args[0][0]
        assert f"--alias:@trellis/wheel-bundle={wheel_bundle}" in cmd
        assert f"--alias:@trellis/wheel-manifest={wheel_manifest}" in cmd
        assert "--loader:.wheel-bundle=binary" in cmd

        # Also check context esbuild_args include the aliases
        assert any("@trellis/wheel-bundle" in arg for arg in ctx.esbuild_args)
        assert any("@trellis/wheel-manifest" in arg for arg in ctx.esbuild_args)

    def test_populates_step_manifest_source_paths(self, tmp_path: Path) -> None:
        """Step adds worker source directory to step manifest source_paths."""
        ctx = self._make_context_with_node_modules(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run"):
            step.run(ctx)

        step_manifest = ctx.manifest.steps["pyodide-worker-build"]
        assert _PYODIDE_WORKER_PATH.parent in step_manifest.source_paths

    def test_populates_step_manifest_dest_files(self, tmp_path: Path) -> None:
        """Step adds output bundle to step manifest dest_files."""
        ctx = self._make_context_with_node_modules(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run"):
            step.run(ctx)

        step_manifest = ctx.manifest.steps["pyodide-worker-build"]
        expected_output = ctx.workspace / "pyodide.worker-bundle"
        assert expected_output in step_manifest.dest_files

    def test_includes_wheel_bundle_in_source_paths(self, tmp_path: Path) -> None:
        """Step tracks wheel bundle and manifest as source inputs."""
        ctx = self._make_context_with_node_modules(tmp_path)
        wheel_bundle = ctx.workspace / "site-packages.wheel-bundle"
        wheel_bundle.write_bytes(b"fake")
        wheel_manifest = ctx.workspace / "wheel-manifest.json"
        wheel_manifest.write_text("{}")
        ctx.generated_files["wheel_bundle"] = wheel_bundle
        ctx.generated_files["wheel_manifest"] = wheel_manifest

        step = PyodideWorkerBuildStep()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            step.run(ctx)

        sm = ctx.manifest.steps["pyodide-worker-build"]
        assert wheel_bundle in sm.source_paths
        assert wheel_manifest in sm.source_paths

    def test_defines_pyodide_version_for_worker(self, tmp_path: Path) -> None:
        """Step passes --define:PYODIDE_VERSION to the worker esbuild command."""
        ctx = self._make_context_with_node_modules(tmp_path)
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            step.run(ctx)

        cmd = mock_run.call_args[0][0]
        define_args = [arg for arg in cmd if arg.startswith("--define:PYODIDE_VERSION=")]
        assert len(define_args) == 1
        # Value should be a quoted string for esbuild
        assert define_args[0].startswith('--define:PYODIDE_VERSION="')

    def test_passes_context_env_to_subprocess(self, tmp_path: Path) -> None:
        """Step passes ctx.env to subprocess.run."""
        ctx = self._make_context_with_node_modules(tmp_path)
        ctx.env["NODE_PATH"] = "/custom/node_modules"
        step = PyodideWorkerBuildStep()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            step.run(ctx)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["env"]["NODE_PATH"] == "/custom/node_modules"


class TestPyodideWorkerBuildStepShouldBuild:
    """Tests for PyodideWorkerBuildStep.should_build()."""

    def _make_context(self, tmp_path: Path, **kwargs: object) -> BuildContext:
        ctx = _make_context(tmp_path, **kwargs)
        node_modules = ctx.workspace / "node_modules"
        node_modules.mkdir(parents=True, exist_ok=True)
        (node_modules / ".bin").mkdir()
        return ctx

    def test_returns_build_when_no_previous_manifest(self, tmp_path: Path) -> None:
        ctx = self._make_context(tmp_path)
        step = PyodideWorkerBuildStep()
        assert step.should_build(ctx, step_manifest=None) == ShouldBuild.BUILD

    def test_returns_build_when_source_paths_empty(self, tmp_path: Path) -> None:
        ctx = self._make_context(tmp_path)
        prev = StepManifest(
            source_paths=set(),
            dest_files={ctx.workspace / "pyodide.worker-bundle"},
        )
        step = PyodideWorkerBuildStep()
        assert step.should_build(ctx, prev) == ShouldBuild.BUILD

    def test_returns_build_when_output_missing(self, tmp_path: Path) -> None:
        ctx = self._make_context(tmp_path)
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "worker.ts").write_text("// worker")

        prev = StepManifest(
            source_paths={source_dir},
            dest_files={ctx.workspace / "pyodide.worker-bundle"},
        )
        step = PyodideWorkerBuildStep()
        assert step.should_build(ctx, prev) == ShouldBuild.BUILD

    def test_returns_skip_when_outputs_up_to_date(self, tmp_path: Path) -> None:
        ctx = self._make_context(tmp_path)
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "worker.ts").write_text("// worker")
        time.sleep(0.01)

        output_file = ctx.workspace / "pyodide.worker-bundle"
        output_file.write_text("// worker bundle")

        prev = StepManifest(source_paths={source_dir}, dest_files={output_file})
        step = PyodideWorkerBuildStep()
        assert step.should_build(ctx, prev) == ShouldBuild.SKIP

    def test_restores_esbuild_args_when_skip(self, tmp_path: Path) -> None:
        ctx = self._make_context(tmp_path)
        output_file = ctx.workspace / "pyodide.worker-bundle"
        output_file.touch()

        prev = StepManifest(
            source_paths={_PYODIDE_WORKER_PATH.parent},
            dest_files={output_file},
        )
        step = PyodideWorkerBuildStep()
        result = step.should_build(ctx, prev)

        assert result == ShouldBuild.SKIP
        assert "--loader:.worker-bundle=text" in ctx.esbuild_args
        assert any("pyodide.worker-bundle" in arg for arg in ctx.esbuild_args)

    def test_restores_wheel_aliases_when_skip(self, tmp_path: Path) -> None:
        """should_build restores wheel bundle aliases when skipping."""
        ctx = self._make_context(tmp_path)
        output_file = ctx.workspace / "pyodide.worker-bundle"
        output_file.touch()

        wheel_bundle = ctx.workspace / "site-packages.wheel-bundle"
        wheel_bundle.write_bytes(b"fake")
        ctx.generated_files["wheel_bundle"] = wheel_bundle
        ctx.generated_files["wheel_manifest"] = ctx.workspace / "wheel-manifest.json"

        prev = StepManifest(
            source_paths={_PYODIDE_WORKER_PATH.parent},
            dest_files={output_file},
        )
        step = PyodideWorkerBuildStep()
        result = step.should_build(ctx, prev)

        assert result == ShouldBuild.SKIP
        assert any("@trellis/wheel-bundle" in arg for arg in ctx.esbuild_args)
        assert any("@trellis/wheel-manifest" in arg for arg in ctx.esbuild_args)
