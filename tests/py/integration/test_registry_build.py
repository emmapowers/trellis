"""Integration tests for registry-based bundle building."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from trellis.bundler.packages import SYSTEM_PACKAGES
from trellis.bundler.registry import ModuleRegistry


class TestRegistryBuildBundle:
    """Tests for registry-based build_bundle function."""

    @pytest.fixture
    def mock_esbuild_env(self):
        """Mock esbuild and package fetching."""
        with patch("trellis.bundler.build.ensure_packages") as mock_packages:
            with patch("trellis.bundler.build.get_bin") as mock_get_bin:
                with patch("subprocess.run") as mock_run:
                    mock_packages.return_value = Path("/fake/node_modules")
                    mock_get_bin.return_value = Path("/fake/esbuild")
                    mock_run.return_value = MagicMock(returncode=0)
                    yield {
                        "get_bin": mock_get_bin,
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

    def test_uses_esbuild_aliases_to_source(self, tmp_path: Path, mock_esbuild_env) -> None:
        """build_bundle passes esbuild aliases pointing to source paths."""
        from trellis.bundler.build import build_from_registry

        # Set up module source directories
        module_a_src = tmp_path / "module_a"
        module_a_src.mkdir()
        module_b_src = tmp_path / "module_b"
        module_b_src.mkdir()

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        registry = ModuleRegistry()
        registry.register("my-widgets")
        registry.register("trellis-core")
        # Set base paths to simulate real modules
        registry._modules["my-widgets"]._base_path = module_a_src
        registry._modules["trellis-core"]._base_path = module_b_src

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

        # Check esbuild was called with alias flags pointing to source paths
        call_args = mock_esbuild_env["run"].call_args
        cmd = call_args[0][0]  # First positional arg is the command list

        # Should have alias for each module pointing to source
        cmd_str = " ".join(str(arg) for arg in cmd)
        assert f"--alias:@trellis/my-widgets={module_a_src}" in cmd_str
        assert f"--alias:@trellis/trellis-core={module_b_src}" in cmd_str

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

    def test_generates_registry_file(self, tmp_path: Path, mock_esbuild_env) -> None:
        """build_bundle generates _registry.ts in workspace."""
        from trellis.bundler.build import build_from_registry

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        registry = ModuleRegistry()

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

        # _registry.ts should be generated in workspace
        registry_file = workspace / "_registry.ts"
        assert registry_file.exists()
        assert "initRegistry" in registry_file.read_text()


class TestTypescriptTypeChecking:
    """Tests for TypeScript type-checking with tsc."""

    @pytest.fixture
    def mock_build_env(self):
        """Mock esbuild, tsc, and package fetching."""
        with patch("trellis.bundler.build.ensure_packages") as mock_packages:
            with patch("trellis.bundler.build.get_bin") as mock_get_bin:
                with patch("subprocess.run") as mock_run:
                    mock_packages.return_value = Path("/fake/node_modules")
                    mock_get_bin.return_value = Path("/fake/esbuild")
                    mock_run.return_value = MagicMock(returncode=0)
                    yield {
                        "get_bin": mock_get_bin,
                        "packages": mock_packages,
                        "run": mock_run,
                    }

    @pytest.mark.skip(reason="Type checking temporarily disabled during bundler refactor")
    def test_runs_tsc_before_esbuild_by_default(self, tmp_path: Path, mock_build_env) -> None:
        """build_from_registry runs tsc --noEmit before esbuild when typecheck=True."""
        from trellis.bundler.build import build_from_registry

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"

        calls = []

        def track_calls(cmd, *args, **kwargs):
            calls.append(cmd)
            # Create outputs for esbuild
            dist = workspace / "dist"
            dist.mkdir(parents=True, exist_ok=True)
            (dist / "bundle.js").write_text("// bundle")
            (dist / "bundle.css").write_text("/* css */")
            return MagicMock(returncode=0)

        mock_build_env["run"].side_effect = track_calls

        build_from_registry(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            force=True,
        )

        # Should have at least 2 calls: tsc then esbuild
        assert len(calls) >= 2

        # Find the tsc call (check for "tsc" as an element, not substring)
        tsc_calls = [c for c in calls if "tsc" in c]
        assert len(tsc_calls) == 1, f"Expected 1 tsc call, got {len(tsc_calls)}: {calls}"

        tsc_cmd = tsc_calls[0]
        assert "--noEmit" in tsc_cmd

        # tsc should be called before esbuild
        tsc_index = calls.index(tsc_cmd)
        esbuild_calls = [c for c in calls if "esbuild" in str(c)]
        assert len(esbuild_calls) >= 1
        esbuild_index = calls.index(esbuild_calls[0])
        assert tsc_index < esbuild_index, "tsc should run before esbuild"

    def test_skips_tsc_when_typecheck_false(self, tmp_path: Path, mock_build_env) -> None:
        """build_from_registry skips tsc when typecheck=False."""
        from trellis.bundler.build import build_from_registry

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"

        calls = []

        def track_calls(cmd, *args, **kwargs):
            calls.append(cmd)
            dist = workspace / "dist"
            dist.mkdir(parents=True, exist_ok=True)
            (dist / "bundle.js").write_text("// bundle")
            (dist / "bundle.css").write_text("/* css */")
            return MagicMock(returncode=0)

        mock_build_env["run"].side_effect = track_calls

        build_from_registry(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            force=True,
            typecheck=False,
        )

        # Should not have any tsc calls (check for "tsc" as an element, not substring)
        tsc_calls = [c for c in calls if "tsc" in c]
        assert len(tsc_calls) == 0, f"Expected no tsc calls, got: {tsc_calls}"

    @pytest.mark.skip(reason="Type checking temporarily disabled during bundler refactor")
    def test_logs_warning_on_type_errors(
        self, tmp_path: Path, mock_build_env, caplog: pytest.LogCaptureFixture
    ) -> None:
        """build_from_registry logs warning when tsc finds type errors."""
        import logging

        from trellis.bundler.build import build_from_registry

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"

        def tsc_fails(cmd, *args, **kwargs):
            if "tsc" in str(cmd):
                result = MagicMock()
                result.returncode = 1
                return result
            return MagicMock(returncode=0)

        mock_build_env["run"].side_effect = tsc_fails

        with caplog.at_level(logging.WARNING):
            build_from_registry(
                registry=registry,
                entry_point=entry_point,
                workspace=workspace,
                force=True,
            )

        assert "TypeScript type-checking failed" in caplog.text

    def test_typescript_included_via_system_packages(self) -> None:
        """TypeScript is included via SYSTEM_PACKAGES (always installed)."""
        # Verify typescript is in SYSTEM_PACKAGES (build.py no longer passes it explicitly)
        assert "typescript" in SYSTEM_PACKAGES
        assert "esbuild" in SYSTEM_PACKAGES
