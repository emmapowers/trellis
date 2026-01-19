"""Unit tests for browser platform build steps."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from trellis.bundler.registry import ModuleRegistry
from trellis.bundler.steps import BuildContext
from trellis.platforms.browser.build_steps import PyodideWorkerBuildStep


class TestPyodideWorkerBuildStep:
    """Tests for PyodideWorkerBuildStep."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing."""
        registry = ModuleRegistry()
        registry.register("test-mod")
        collected = registry.collect()

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        # Set up node_modules
        node_modules = workspace / "node_modules"
        node_modules.mkdir()
        (node_modules / ".bin").mkdir()

        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=dist_dir,
        )
        ctx.node_modules = node_modules
        ctx.env["NODE_PATH"] = str(node_modules)

        return ctx

    def test_has_name_pyodide_worker_build(self) -> None:
        """PyodideWorkerBuildStep.name is 'pyodide-worker-build'."""
        step = PyodideWorkerBuildStep()
        assert step.name == "pyodide-worker-build"

    def test_builds_worker_as_iife(self, build_context: BuildContext) -> None:
        """PyodideWorkerBuildStep builds pyodide worker as IIFE format."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = PyodideWorkerBuildStep()
            step.run(build_context)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "--format=iife" in cmd

    def test_outputs_worker_bundle_file(self, build_context: BuildContext) -> None:
        """PyodideWorkerBuildStep writes output as pyodide.worker-bundle."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = PyodideWorkerBuildStep()
            step.run(build_context)

        cmd = mock_run.call_args[0][0]
        cmd_str = " ".join(str(arg) for arg in cmd)
        assert "pyodide.worker-bundle" in cmd_str

    def test_adds_worker_bundle_loader(self, build_context: BuildContext) -> None:
        """PyodideWorkerBuildStep adds --loader:.worker-bundle=text to ctx.esbuild_args."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = PyodideWorkerBuildStep()
            step.run(build_context)

        assert "--loader:.worker-bundle=text" in build_context.esbuild_args

    def test_adds_worker_alias(self, build_context: BuildContext) -> None:
        """PyodideWorkerBuildStep adds alias for @trellis/browser/pyodide.worker-bundle."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = PyodideWorkerBuildStep()
            step.run(build_context)

        # Should add alias like --alias:@trellis/browser/pyodide.worker-bundle={workspace}/pyodide.worker-bundle
        alias_found = any(
            "--alias:@trellis/browser/pyodide.worker-bundle=" in arg
            for arg in build_context.esbuild_args
        )
        assert alias_found

    def test_raises_without_node_modules(self, build_context: BuildContext) -> None:
        """PyodideWorkerBuildStep raises RuntimeError if node_modules not set."""
        build_context.node_modules = None

        step = PyodideWorkerBuildStep()
        with pytest.raises(RuntimeError, match="requires node_modules"):
            step.run(build_context)
