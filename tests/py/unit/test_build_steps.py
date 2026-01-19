"""Unit tests for build steps."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from trellis.bundler.build import build, is_rebuild_needed
from trellis.bundler.registry import ModuleRegistry
from trellis.bundler.steps import (
    BuildContext,
    BuildStep,
    BundleBuildStep,
    DeclarationStep,
    PackageInstallStep,
    RegistryGenerationStep,
    StaticFileCopyStep,
    TsconfigStep,
    TypeCheckStep,
)


class TestBuildContext:
    """Tests for BuildContext dataclass."""

    def test_creates_with_required_fields(self, tmp_path: Path) -> None:
        """BuildContext requires registry, entry_point, workspace, collected, dist_dir."""
        registry = ModuleRegistry()
        collected = registry.collect()
        entry_point = tmp_path / "main.tsx"
        workspace = tmp_path / "workspace"
        dist_dir = tmp_path / "dist"

        ctx = BuildContext(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            collected=collected,
            dist_dir=dist_dir,
        )

        assert ctx.registry is registry
        assert ctx.entry_point == entry_point
        assert ctx.workspace == workspace
        assert ctx.collected is collected
        assert ctx.dist_dir == dist_dir

    def test_has_mutable_esbuild_args(self, tmp_path: Path) -> None:
        """BuildContext has empty esbuild_args list by default."""
        registry = ModuleRegistry()
        collected = registry.collect()

        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=collected,
            dist_dir=tmp_path / "dist",
        )

        assert ctx.esbuild_args == []
        # Should be mutable
        ctx.esbuild_args.append("--minify")
        assert ctx.esbuild_args == ["--minify"]

    def test_has_mutable_env(self, tmp_path: Path) -> None:
        """BuildContext has empty env dict by default."""
        registry = ModuleRegistry()
        collected = registry.collect()

        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=collected,
            dist_dir=tmp_path / "dist",
        )

        assert ctx.env == {}
        ctx.env["NODE_PATH"] = "/some/path"
        assert ctx.env["NODE_PATH"] == "/some/path"

    def test_has_mutable_generated_files(self, tmp_path: Path) -> None:
        """BuildContext has empty generated_files dict by default."""
        registry = ModuleRegistry()
        collected = registry.collect()

        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=collected,
            dist_dir=tmp_path / "dist",
        )

        assert ctx.generated_files == {}
        ctx.generated_files["_registry"] = tmp_path / "_registry.ts"
        assert ctx.generated_files["_registry"] == tmp_path / "_registry.ts"

    def test_node_modules_defaults_to_none(self, tmp_path: Path) -> None:
        """BuildContext node_modules defaults to None."""
        registry = ModuleRegistry()
        collected = registry.collect()

        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=collected,
            dist_dir=tmp_path / "dist",
        )

        assert ctx.node_modules is None


class TestBuildStep:
    """Tests for BuildStep abstract base class."""

    def test_is_abstract_class(self) -> None:
        """BuildStep cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BuildStep()  # type: ignore[abstract]

    def test_requires_name_property(self, tmp_path: Path) -> None:
        """BuildStep subclass must implement name property."""

        class IncompleteStep(BuildStep):
            def run(self, ctx: BuildContext) -> None:
                pass

        with pytest.raises(TypeError):
            IncompleteStep()  # type: ignore[abstract]

    def test_requires_run_method(self, tmp_path: Path) -> None:
        """BuildStep subclass must implement run method."""

        class IncompleteStep(BuildStep):
            @property
            def name(self) -> str:
                return "incomplete"

        with pytest.raises(TypeError):
            IncompleteStep()  # type: ignore[abstract]

    def test_concrete_subclass_can_be_instantiated(self, tmp_path: Path) -> None:
        """Concrete BuildStep subclass can be instantiated."""

        class NoopStep(BuildStep):
            @property
            def name(self) -> str:
                return "noop"

            def run(self, ctx: BuildContext) -> None:
                pass

        step = NoopStep()
        assert step.name == "noop"


class TestPackageInstallStep:
    """Tests for PackageInstallStep."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing."""
        registry = ModuleRegistry()
        registry.register("test-mod", packages={"react": "18.2.0"})
        collected = registry.collect()

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        return BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=tmp_path / "dist",
        )

    def test_has_name_package_install(self) -> None:
        """PackageInstallStep.name is 'package-install'."""
        step = PackageInstallStep()
        assert step.name == "package-install"

    def test_sets_node_modules_path(self, build_context: BuildContext) -> None:
        """PackageInstallStep sets ctx.node_modules to workspace/node_modules."""
        with patch("trellis.bundler.steps.ensure_packages"):
            step = PackageInstallStep()
            step.run(build_context)

        assert build_context.node_modules == build_context.workspace / "node_modules"

    def test_sets_node_path_env(self, build_context: BuildContext) -> None:
        """PackageInstallStep sets ctx.env['NODE_PATH'] to node_modules path."""
        with patch("trellis.bundler.steps.ensure_packages"):
            step = PackageInstallStep()
            step.run(build_context)

        expected = str(build_context.workspace / "node_modules")
        assert build_context.env["NODE_PATH"] == expected

    def test_calls_ensure_packages_with_collected_packages(
        self, build_context: BuildContext
    ) -> None:
        """PackageInstallStep calls ensure_packages with packages from collected modules."""
        with patch("trellis.bundler.steps.ensure_packages") as mock_ensure:
            step = PackageInstallStep()
            step.run(build_context)

        mock_ensure.assert_called_once_with({"react": "18.2.0"}, build_context.workspace)


class TestRegistryGenerationStep:
    """Tests for RegistryGenerationStep."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing."""
        registry = ModuleRegistry()
        collected = registry.collect()

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        return BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=tmp_path / "dist",
        )

    def test_has_name_registry_generation(self) -> None:
        """RegistryGenerationStep.name is 'registry-generation'."""
        step = RegistryGenerationStep()
        assert step.name == "registry-generation"

    def test_generates_registry_ts_file(self, build_context: BuildContext) -> None:
        """RegistryGenerationStep writes _registry.ts to workspace."""
        step = RegistryGenerationStep()
        step.run(build_context)

        registry_path = build_context.workspace / "_registry.ts"
        assert registry_path.exists()
        assert "initRegistry" in registry_path.read_text()

    def test_sets_generated_files_registry(self, build_context: BuildContext) -> None:
        """RegistryGenerationStep sets ctx.generated_files['_registry']."""
        step = RegistryGenerationStep()
        step.run(build_context)

        expected = build_context.workspace / "_registry.ts"
        assert build_context.generated_files["_registry"] == expected

    def test_adds_registry_alias_to_esbuild_args(self, build_context: BuildContext) -> None:
        """RegistryGenerationStep adds @trellis/_registry alias to ctx.esbuild_args."""
        step = RegistryGenerationStep()
        step.run(build_context)

        registry_path = build_context.workspace / "_registry.ts"
        expected_alias = f"--alias:@trellis/_registry={registry_path}"
        assert expected_alias in build_context.esbuild_args


class TestTsconfigStep:
    """Tests for TsconfigStep."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing."""
        registry = ModuleRegistry()
        # Register module with a base path
        registry.register("test-mod")
        registry._modules["test-mod"]._base_path = tmp_path / "test-mod"

        collected = registry.collect()

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        return BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=tmp_path / "dist",
        )

    def test_has_name_tsconfig(self) -> None:
        """TsconfigStep.name is 'tsconfig'."""
        step = TsconfigStep()
        assert step.name == "tsconfig"

    def test_generates_tsconfig_json_file(self, build_context: BuildContext) -> None:
        """TsconfigStep writes tsconfig.json to workspace."""
        step = TsconfigStep()
        step.run(build_context)

        tsconfig_path = build_context.workspace / "tsconfig.json"
        assert tsconfig_path.exists()

        tsconfig = json.loads(tsconfig_path.read_text())
        assert "compilerOptions" in tsconfig

    def test_sets_generated_files_tsconfig(self, build_context: BuildContext) -> None:
        """TsconfigStep sets ctx.generated_files['tsconfig']."""
        step = TsconfigStep()
        step.run(build_context)

        expected = build_context.workspace / "tsconfig.json"
        assert build_context.generated_files["tsconfig"] == expected

    def test_includes_module_path_aliases(self, build_context: BuildContext) -> None:
        """TsconfigStep includes path aliases for registered modules."""
        step = TsconfigStep()
        step.run(build_context)

        tsconfig_path = build_context.workspace / "tsconfig.json"
        tsconfig = json.loads(tsconfig_path.read_text())

        paths = tsconfig["compilerOptions"]["paths"]
        assert "@trellis/test-mod/*" in paths


class TestTypeCheckStep:
    """Tests for TypeCheckStep."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing."""
        registry = ModuleRegistry()
        collected = registry.collect()

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Set up node_modules (simulates PackageInstallStep ran)
        node_modules = workspace / "node_modules"
        node_modules.mkdir()
        (node_modules / ".bin").mkdir()

        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=tmp_path / "dist",
        )
        ctx.node_modules = node_modules
        ctx.generated_files["tsconfig"] = workspace / "tsconfig.json"

        return ctx

    def test_has_name_type_check(self) -> None:
        """TypeCheckStep.name is 'type-check'."""
        step = TypeCheckStep()
        assert step.name == "type-check"

    def test_defaults_to_fail_on_error_false(self) -> None:
        """TypeCheckStep defaults to fail_on_error=False."""
        step = TypeCheckStep()
        assert step.fail_on_error is False

    def test_can_set_fail_on_error_true(self) -> None:
        """TypeCheckStep can be created with fail_on_error=True."""
        step = TypeCheckStep(fail_on_error=True)
        assert step.fail_on_error is True

    def test_runs_tsc_noEmit(self, build_context: BuildContext) -> None:
        """TypeCheckStep runs tsc --noEmit."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = TypeCheckStep()
            step.run(build_context)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "--noEmit" in cmd

    def test_warns_on_type_errors_when_fail_on_error_false(
        self, build_context: BuildContext, caplog: pytest.LogCaptureFixture
    ) -> None:
        """TypeCheckStep logs warning when tsc fails and fail_on_error=False."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1  # Type error

            step = TypeCheckStep(fail_on_error=False)
            with caplog.at_level(logging.WARNING):
                step.run(build_context)  # Should not raise

        assert "type-check" in caplog.text.lower() or "type" in caplog.text.lower()

    def test_raises_on_type_errors_when_fail_on_error_true(
        self, build_context: BuildContext
    ) -> None:
        """TypeCheckStep raises when tsc fails and fail_on_error=True."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1  # Type error

            step = TypeCheckStep(fail_on_error=True)
            with pytest.raises(subprocess.CalledProcessError):
                step.run(build_context)


class TestDeclarationStep:
    """Tests for DeclarationStep."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing."""
        registry = ModuleRegistry()
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
        ctx.generated_files["tsconfig"] = workspace / "tsconfig.json"

        return ctx

    def test_has_name_declaration(self) -> None:
        """DeclarationStep.name is 'declaration'."""
        step = DeclarationStep()
        assert step.name == "declaration"

    def test_runs_tsc_with_declaration_flags(self, build_context: BuildContext) -> None:
        """DeclarationStep runs tsc with --declaration and --emitDeclarationOnly."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = DeclarationStep()
            step.run(build_context)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "--declaration" in cmd
        assert "--emitDeclarationOnly" in cmd

    def test_outputs_to_dist_dir(self, build_context: BuildContext) -> None:
        """DeclarationStep outputs .d.ts files to ctx.dist_dir."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = DeclarationStep()
            step.run(build_context)

        cmd = mock_run.call_args[0][0]
        outdir_flag = "--outDir"
        assert outdir_flag in cmd
        # Find the outDir value
        outdir_idx = cmd.index("--outDir")
        assert cmd[outdir_idx + 1] == str(build_context.dist_dir)


class TestBundleBuildStep:
    """Tests for BundleBuildStep."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing."""
        registry = ModuleRegistry()
        registry.register("test-mod")
        registry._modules["test-mod"]._base_path = tmp_path / "test-mod"
        collected = registry.collect()

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        # Set up node_modules
        node_modules = workspace / "node_modules"
        node_modules.mkdir()
        (node_modules / ".bin").mkdir()

        ctx = BuildContext(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            collected=collected,
            dist_dir=dist_dir,
        )
        ctx.node_modules = node_modules
        ctx.env["NODE_PATH"] = str(node_modules)

        return ctx

    def test_has_name_bundle_build(self) -> None:
        """BundleBuildStep.name is 'bundle-build'."""
        step = BundleBuildStep()
        assert step.name == "bundle-build"

    def test_defaults_output_name_to_bundle(self) -> None:
        """BundleBuildStep defaults to output_name='bundle'."""
        step = BundleBuildStep()
        assert step.output_name == "bundle"

    def test_can_set_output_name(self) -> None:
        """BundleBuildStep can be created with custom output_name."""
        step = BundleBuildStep(output_name="index")
        assert step.output_name == "index"

    def test_runs_esbuild(self, build_context: BuildContext) -> None:
        """BundleBuildStep runs esbuild."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = BundleBuildStep()
            step.run(build_context)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "esbuild" in str(cmd[0])

    def test_includes_entry_point(self, build_context: BuildContext) -> None:
        """BundleBuildStep includes entry point in esbuild command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = BundleBuildStep()
            step.run(build_context)

        cmd = mock_run.call_args[0][0]
        assert str(build_context.entry_point) in cmd

    def test_uses_entry_names_from_output_name(self, build_context: BuildContext) -> None:
        """BundleBuildStep uses --entry-names with output_name."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = BundleBuildStep(output_name="index")
            step.run(build_context)

        cmd = mock_run.call_args[0][0]
        assert "--entry-names=index" in cmd

    def test_includes_module_aliases(self, build_context: BuildContext) -> None:
        """BundleBuildStep includes aliases for registered modules."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = BundleBuildStep()
            step.run(build_context)

        cmd = mock_run.call_args[0][0]
        cmd_str = " ".join(str(arg) for arg in cmd)
        assert "--alias:@trellis/test-mod=" in cmd_str

    def test_includes_ctx_esbuild_args(self, build_context: BuildContext) -> None:
        """BundleBuildStep includes args from ctx.esbuild_args."""
        build_context.esbuild_args.append("--minify")
        build_context.esbuild_args.append("--alias:@trellis/_registry=/some/path")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = BundleBuildStep()
            step.run(build_context)

        cmd = mock_run.call_args[0][0]
        assert "--minify" in cmd
        assert "--alias:@trellis/_registry=/some/path" in cmd


class TestStaticFileCopyStep:
    """Tests for StaticFileCopyStep."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing with static files."""
        registry = ModuleRegistry()

        # Create a source file
        src_file = tmp_path / "src" / "static" / "data.json"
        src_file.parent.mkdir(parents=True)
        src_file.write_text('{"key": "value"}')

        # Register module with static file
        registry.register(
            "test-mod",
            static_files={"data.json": src_file},
        )
        collected = registry.collect()

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        return BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=dist_dir,
        )

    def test_has_name_static_file_copy(self) -> None:
        """StaticFileCopyStep.name is 'static-file-copy'."""
        step = StaticFileCopyStep()
        assert step.name == "static-file-copy"

    def test_copies_static_files_to_dist(self, build_context: BuildContext) -> None:
        """StaticFileCopyStep copies static files to dist directory."""
        step = StaticFileCopyStep()
        step.run(build_context)

        copied_file = build_context.dist_dir / "data.json"
        assert copied_file.exists()
        assert copied_file.read_text() == '{"key": "value"}'

    def test_creates_subdirectories_for_nested_files(self, tmp_path: Path) -> None:
        """StaticFileCopyStep creates subdirectories for nested static files."""
        registry = ModuleRegistry()

        # Create nested source file
        src_file = tmp_path / "src" / "assets" / "images" / "logo.png"
        src_file.parent.mkdir(parents=True)
        src_file.write_bytes(b"PNG data")

        registry.register(
            "test-mod",
            static_files={"assets/images/logo.png": src_file},
        )
        collected = registry.collect()

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=dist_dir,
        )

        step = StaticFileCopyStep()
        step.run(ctx)

        copied_file = dist_dir / "assets" / "images" / "logo.png"
        assert copied_file.exists()
        assert copied_file.read_bytes() == b"PNG data"


class TestBuildOrchestration:
    """Tests for the build() orchestration function."""

    def test_runs_steps_in_order(self, tmp_path: Path) -> None:
        """build() runs steps in the order provided."""
        registry = ModuleRegistry()

        workspace = tmp_path / "workspace"
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        run_order: list[str] = []

        class Step1(BuildStep):
            @property
            def name(self) -> str:
                return "step1"

            def run(self, ctx: BuildContext) -> None:
                run_order.append("step1")

        class Step2(BuildStep):
            @property
            def name(self) -> str:
                return "step2"

            def run(self, ctx: BuildContext) -> None:
                run_order.append("step2")

        class Step3(BuildStep):
            @property
            def name(self) -> str:
                return "step3"

            def run(self, ctx: BuildContext) -> None:
                run_order.append("step3")

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[Step1(), Step2(), Step3()],
            force=True,
        )

        assert run_order == ["step1", "step2", "step3"]

    def test_creates_dist_directory(self, tmp_path: Path) -> None:
        """build() creates the dist directory."""
        registry = ModuleRegistry()
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")
        workspace = tmp_path / "workspace"

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[],
            force=True,
        )

        assert (workspace / "dist").is_dir()

    def test_uses_custom_output_dir(self, tmp_path: Path) -> None:
        """build() uses custom output_dir when provided."""
        registry = ModuleRegistry()
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")
        workspace = tmp_path / "workspace"
        custom_output = tmp_path / "custom_dist"

        captured_dist: list[Path] = []

        class CaptureStep(BuildStep):
            @property
            def name(self) -> str:
                return "capture"

            def run(self, ctx: BuildContext) -> None:
                captured_dist.append(ctx.dist_dir)

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[CaptureStep()],
            output_dir=custom_output,
            force=True,
        )

        assert captured_dist[0] == custom_output
        assert custom_output.is_dir()

    def test_passes_collected_modules_to_context(self, tmp_path: Path) -> None:
        """build() passes collected modules to BuildContext."""
        registry = ModuleRegistry()
        registry.register("test-mod", packages={"react": "18.0.0"})
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")
        workspace = tmp_path / "workspace"

        captured_collected: list = []

        class CaptureStep(BuildStep):
            @property
            def name(self) -> str:
                return "capture"

            def run(self, ctx: BuildContext) -> None:
                captured_collected.append(ctx.collected)

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[CaptureStep()],
            force=True,
        )

        assert len(captured_collected[0].modules) == 1
        assert captured_collected[0].modules[0].name == "test-mod"
        assert captured_collected[0].packages == {"react": "18.0.0"}


class TestIsRebuildNeeded:
    """Tests for is_rebuild_needed helper function."""

    def test_returns_false_when_no_inputs(self, tmp_path: Path) -> None:
        """is_rebuild_needed returns False when no inputs provided."""
        output = tmp_path / "output.js"
        output.write_text("output")

        result = is_rebuild_needed(inputs=[], outputs=[output])

        assert result is False

    def test_returns_true_when_output_missing(self, tmp_path: Path) -> None:
        """is_rebuild_needed returns True when any output is missing."""
        input_file = tmp_path / "input.ts"
        input_file.write_text("input")
        output = tmp_path / "output.js"  # Does not exist

        result = is_rebuild_needed(inputs=[input_file], outputs=[output])

        assert result is True

    def test_returns_true_when_input_newer_than_output(self, tmp_path: Path) -> None:
        """is_rebuild_needed returns True when input is newer than output."""
        output = tmp_path / "output.js"
        output.write_text("output")

        # Wait to ensure different mtime
        time.sleep(0.01)

        input_file = tmp_path / "input.ts"
        input_file.write_text("input")  # Created after output

        result = is_rebuild_needed(inputs=[input_file], outputs=[output])

        assert result is True

    def test_returns_false_when_outputs_up_to_date(self, tmp_path: Path) -> None:
        """is_rebuild_needed returns False when outputs are newer than inputs."""
        input_file = tmp_path / "input.ts"
        input_file.write_text("input")

        # Wait to ensure different mtime
        time.sleep(0.01)

        output = tmp_path / "output.js"
        output.write_text("output")  # Created after input

        result = is_rebuild_needed(inputs=[input_file], outputs=[output])

        assert result is False

    def test_checks_all_outputs_exist(self, tmp_path: Path) -> None:
        """is_rebuild_needed returns True if any output is missing."""
        input_file = tmp_path / "input.ts"
        input_file.write_text("input")

        output1 = tmp_path / "output.js"
        output1.write_text("output1")
        output2 = tmp_path / "output.css"  # Does not exist

        result = is_rebuild_needed(inputs=[input_file], outputs=[output1, output2])

        assert result is True

    def test_uses_oldest_output_for_comparison(self, tmp_path: Path) -> None:
        """is_rebuild_needed uses oldest output mtime for comparison."""
        # Create input
        input_file = tmp_path / "input.ts"
        input_file.write_text("input")
        time.sleep(0.01)

        # Create old output
        old_output = tmp_path / "old.js"
        old_output.write_text("old")
        time.sleep(0.01)

        # Modify input (now newer than old output)
        input_file.write_text("modified input")
        time.sleep(0.01)

        # Create new output (newer than input)
        new_output = tmp_path / "new.js"
        new_output.write_text("new")

        # Should return True because input is newer than old_output
        result = is_rebuild_needed(inputs=[input_file], outputs=[old_output, new_output])

        assert result is True


class TestBuildCaching:
    """Tests for build() caching behavior."""

    def test_skips_steps_when_outputs_up_to_date(self, tmp_path: Path) -> None:
        """build() skips steps when outputs are newer than inputs."""
        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        dist_dir = workspace / "dist"
        dist_dir.mkdir()

        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        # Wait then create output
        time.sleep(0.01)
        output_js = dist_dir / "bundle.js"
        output_js.write_text("// built")

        # Create metafile (required for cache checking)
        # Paths in metafile are relative to workspace - use ../ to navigate to tmp_path
        metafile_content = {
            "inputs": {"../main.tsx": {"bytes": 8}},
            "outputs": {"dist/bundle.js": {"bytes": 100}},
        }
        (workspace / "metafile.json").write_text(json.dumps(metafile_content))

        step_ran = []

        class TrackingStep(BuildStep):
            @property
            def name(self) -> str:
                return "tracking"

            def run(self, ctx: BuildContext) -> None:
                step_ran.append(True)

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[TrackingStep()],
            force=False,
        )

        assert step_ran == [], "Step should not have run when outputs up to date"

    def test_runs_steps_when_force_true(self, tmp_path: Path) -> None:
        """build() runs steps when force=True even if outputs up to date."""
        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        dist_dir = workspace / "dist"
        dist_dir.mkdir()

        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        # Wait then create output (newer than input)
        time.sleep(0.01)
        output_js = dist_dir / "bundle.js"
        output_js.write_text("// built")

        step_ran = []

        class TrackingStep(BuildStep):
            @property
            def name(self) -> str:
                return "tracking"

            def run(self, ctx: BuildContext) -> None:
                step_ran.append(True)

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[TrackingStep()],
            force=True,
        )

        assert step_ran == [True], "Step should run when force=True"

    def test_runs_steps_when_output_missing(self, tmp_path: Path) -> None:
        """build() runs steps when output files are missing."""
        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        step_ran = []

        class TrackingStep(BuildStep):
            @property
            def name(self) -> str:
                return "tracking"

            def run(self, ctx: BuildContext) -> None:
                step_ran.append(True)

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[TrackingStep()],
            force=False,
        )

        assert step_ran == [True], "Step should run when output missing"

    def test_runs_steps_when_input_newer_than_output(self, tmp_path: Path) -> None:
        """build() runs steps when input files are newer than outputs."""
        registry = ModuleRegistry()
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        dist_dir = workspace / "dist"
        dist_dir.mkdir()

        # Create output first
        output_js = dist_dir / "bundle.js"
        output_js.write_text("// built")

        # Wait then create input (newer than output)
        time.sleep(0.01)
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        # Create metafile with input - use relative path from workspace
        metafile_content = {
            "inputs": {"../main.tsx": {"bytes": 8}},
            "outputs": {"dist/bundle.js": {"bytes": 100}},
        }
        (workspace / "metafile.json").write_text(json.dumps(metafile_content))

        step_ran = []

        class TrackingStep(BuildStep):
            @property
            def name(self) -> str:
                return "tracking"

            def run(self, ctx: BuildContext) -> None:
                step_ran.append(True)

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[TrackingStep()],
            force=False,
        )

        assert step_ran == [True], "Step should run when input newer than output"

    def test_considers_module_source_files_as_inputs(self, tmp_path: Path) -> None:
        """build() treats module source files as inputs for caching via metafile."""
        registry = ModuleRegistry()

        # Create module source file
        mod_dir = tmp_path / "my_mod"
        mod_dir.mkdir()
        mod_source = mod_dir / "index.ts"
        mod_source.write_text("// module source")
        registry.register("my-mod")
        registry._modules["my-mod"]._base_path = mod_dir

        workspace = tmp_path / "workspace"
        workspace.mkdir()
        dist_dir = workspace / "dist"
        dist_dir.mkdir()

        # Create output before module source update
        output_js = dist_dir / "bundle.js"
        output_js.write_text("// built")

        # Create metafile with module source as input
        # (metafile is created by esbuild and lists actual inputs from the bundle)
        # Path is relative from workspace - use ../ to navigate to tmp_path then to module
        metafile_content = {
            "inputs": {"../my_mod/index.ts": {"bytes": 16}},
            "outputs": {"dist/bundle.js": {"bytes": 100}},
        }
        (workspace / "metafile.json").write_text(json.dumps(metafile_content))

        # Wait then update module source (newer than output)
        time.sleep(0.01)
        mod_source.write_text("// updated module source")

        step_ran = []

        class TrackingStep(BuildStep):
            @property
            def name(self) -> str:
                return "tracking"

            def run(self, ctx: BuildContext) -> None:
                step_ran.append(True)

        build(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            steps=[TrackingStep()],
            force=False,
        )

        assert step_ran == [True], "Step should run when module source is newer"
