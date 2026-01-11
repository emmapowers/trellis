"""Integration tests for registry-based bundle building."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from trellis.bundler.build import compute_snippets_hash
from trellis.bundler.registry import CollectedModules, ModuleRegistry


class TestRegistryBuildBundle:
    """Tests for registry-based build_bundle function."""

    @pytest.fixture
    def mock_esbuild_env(self):
        """Mock esbuild and package fetching."""
        with patch("trellis.bundler.build.ensure_esbuild") as mock_esbuild:
            with patch("trellis.bundler.build.ensure_packages") as mock_packages:
                with patch("subprocess.run") as mock_run:
                    mock_esbuild.return_value = Path("/fake/esbuild")
                    mock_packages.return_value = Path("/fake/node_modules")
                    mock_run.return_value = MagicMock(returncode=0)
                    yield {
                        "esbuild": mock_esbuild,
                        "packages": mock_packages,
                        "run": mock_run,
                    }

    def test_creates_dist_directory(self, tmp_path: Path, mock_esbuild_env) -> None:
        """build_bundle creates the dist directory."""
        from trellis.bundler.build import build_from_registry

        # Set up entry point
        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        # Set up registry
        registry = ModuleRegistry()
        registry.register("test-module", packages={"react": "18.2.0"})

        workspace = tmp_path / "workspace"

        # Simulate esbuild creating output files
        def create_outputs(*args, **kwargs):
            dist = workspace / "dist"
            dist.mkdir(parents=True, exist_ok=True)
            (dist / "bundle.js").write_text("// bundle")
            (dist / "bundle.css").write_text("/* css */")
            return MagicMock(returncode=0)

        mock_esbuild_env["run"].side_effect = create_outputs

        build_from_registry(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            force=True,
        )

        assert (workspace / "dist").is_dir()

    def test_produces_bundle_js(self, tmp_path: Path, mock_esbuild_env) -> None:
        """build_bundle produces bundle.js in dist directory."""
        from trellis.bundler.build import build_from_registry

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        registry = ModuleRegistry()

        workspace = tmp_path / "workspace"

        # Simulate esbuild creating output
        def create_outputs(*args, **kwargs):
            dist = workspace / "dist"
            dist.mkdir(parents=True, exist_ok=True)
            (dist / "bundle.js").write_text("// bundle")
            (dist / "bundle.css").write_text("/* css */")
            return MagicMock(returncode=0)

        mock_esbuild_env["run"].side_effect = create_outputs

        build_from_registry(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            force=True,
        )

        assert (workspace / "dist" / "bundle.js").exists()

    def test_uses_esbuild_aliases(self, tmp_path: Path, mock_esbuild_env) -> None:
        """build_bundle passes correct esbuild aliases for modules."""
        from trellis.bundler.build import build_from_registry

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        registry = ModuleRegistry()
        registry.register("my-widgets")
        registry.register("trellis-core")

        workspace = tmp_path / "workspace"

        # Simulate esbuild creating output
        def create_outputs(*args, **kwargs):
            dist = workspace / "dist"
            dist.mkdir(parents=True, exist_ok=True)
            (dist / "bundle.js").write_text("// bundle")
            (dist / "bundle.css").write_text("/* css */")
            return MagicMock(returncode=0)

        mock_esbuild_env["run"].side_effect = create_outputs

        build_from_registry(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            force=True,
        )

        # Check esbuild was called with alias flags
        call_args = mock_esbuild_env["run"].call_args
        cmd = call_args[0][0]  # First positional arg is the command list

        # Should have alias for each module
        cmd_str = " ".join(str(arg) for arg in cmd)
        assert "--alias:@trellis/my-widgets=" in cmd_str
        assert "--alias:@trellis/trellis-core=" in cmd_str

    def test_handles_worker_entries(self, tmp_path: Path, mock_esbuild_env) -> None:
        """build_bundle builds worker entries as IIFE."""
        from trellis.bundler.build import build_from_registry

        # Set up module with worker
        module_src = tmp_path / "src"
        module_src.mkdir()
        (module_src / "service-worker.ts").write_text("// worker code")

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        registry = ModuleRegistry()
        registry.register(
            "browser-module",
            files=["service-worker.ts"],
            worker_entries={"service": "service-worker.ts"},
        )
        # Manually set base path since we're not registering from the module's location
        registry._modules["browser-module"]._base_path = module_src

        workspace = tmp_path / "workspace"

        # Track esbuild calls
        calls = []

        def track_calls(*args, **kwargs):
            calls.append(args[0])
            # Create expected outputs
            dist = workspace / "dist"
            dist.mkdir(parents=True, exist_ok=True)
            (dist / "bundle.js").write_text("// bundle")
            (dist / "bundle.css").write_text("/* css */")
            # Create worker bundle in staged dir
            staged = workspace / "staged" / "browser-module"
            staged.mkdir(parents=True, exist_ok=True)
            (staged / "service.worker-bundle").write_text("// worker")
            return MagicMock(returncode=0)

        mock_esbuild_env["run"].side_effect = track_calls

        build_from_registry(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            force=True,
        )

        # Should have at least 2 esbuild calls: worker + main bundle
        assert len(calls) >= 2

        # First call(s) should be worker builds with --format=iife
        worker_calls = [c for c in calls if "--format=iife" in [str(a) for a in c]]
        assert len(worker_calls) >= 1

    def test_skips_rebuild_when_up_to_date(self, tmp_path: Path, mock_esbuild_env) -> None:
        """build_bundle skips rebuild if outputs exist and sources unchanged."""
        from trellis.bundler.build import build_from_registry

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        registry = ModuleRegistry()

        workspace = tmp_path / "workspace"

        # Pre-create outputs
        dist = workspace / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "bundle.js").write_text("// existing bundle")
        (dist / "bundle.css").write_text("/* existing css */")

        # Create staged dir so it looks like a previous build
        staged = workspace / "staged"
        staged.mkdir(parents=True, exist_ok=True)
        (workspace / "entry.tsx").write_text("// entry")

        # Create snippets hash file (empty registry has no snippets)
        empty_collected = CollectedModules(modules=[], packages={})
        (workspace / ".snippets-hash").write_text(compute_snippets_hash(empty_collected))

        # Build without force - should skip
        build_from_registry(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            force=False,
        )

        # esbuild should not have been called
        mock_esbuild_env["run"].assert_not_called()

    def test_rebuilds_when_force_true(self, tmp_path: Path, mock_esbuild_env) -> None:
        """build_bundle rebuilds even if up to date when force=True."""
        from trellis.bundler.build import build_from_registry

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        registry = ModuleRegistry()

        workspace = tmp_path / "workspace"

        # Pre-create outputs
        dist = workspace / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "bundle.js").write_text("// existing bundle")
        (dist / "bundle.css").write_text("/* existing css */")

        # Create staged dir
        staged = workspace / "staged"
        staged.mkdir(parents=True, exist_ok=True)
        (workspace / "entry.tsx").write_text("// entry")

        def create_outputs(*args, **kwargs):
            (dist / "bundle.js").write_text("// new bundle")
            (dist / "bundle.css").write_text("/* new css */")
            return MagicMock(returncode=0)

        mock_esbuild_env["run"].side_effect = create_outputs

        # Build with force - should rebuild
        build_from_registry(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            force=True,
        )

        # esbuild should have been called
        mock_esbuild_env["run"].assert_called()

    def test_stages_modules_before_build(self, tmp_path: Path, mock_esbuild_env) -> None:
        """build_bundle stages all module files before running esbuild."""
        from trellis.bundler.build import build_from_registry

        # Set up module with files
        module_src = tmp_path / "src"
        module_src.mkdir()
        (module_src / "Widget.tsx").write_text("export const Widget = () => null;")

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        registry = ModuleRegistry()
        registry.register("my-module", files=["Widget.tsx"])
        registry._modules["my-module"]._base_path = module_src

        workspace = tmp_path / "workspace"

        def create_outputs(*args, **kwargs):
            dist = workspace / "dist"
            dist.mkdir(parents=True, exist_ok=True)
            (dist / "bundle.js").write_text("// bundle")
            (dist / "bundle.css").write_text("/* css */")
            return MagicMock(returncode=0)

        mock_esbuild_env["run"].side_effect = create_outputs

        build_from_registry(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            force=True,
        )

        # Module files should be staged
        staged_widget = workspace / "staged" / "my-module" / "Widget.tsx"
        assert staged_widget.exists()
        assert staged_widget.read_text() == "export const Widget = () => null;"
