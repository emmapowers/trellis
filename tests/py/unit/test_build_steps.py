"""Unit tests for build steps."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from trellis.bundler.build import build
from trellis.bundler.manifest import BuildManifest, StepManifest, load_manifest, save_manifest
from trellis.bundler.registry import ModuleRegistry, registry
from trellis.bundler.steps import (
    BuildContext,
    BuildStep,
    BundleBuildStep,
    DeclarationStep,
    IndexHtmlRenderStep,
    PackageInstallStep,
    RegistryGenerationStep,
    ShouldBuild,
    StaticFileCopyStep,
    TsconfigStep,
    TypeCheckStep,
    collect_ts_source_files,
)


class TestCollectTsSourceFiles:
    """Tests for collect_ts_source_files() helper function."""

    def test_finds_ts_files(self, tmp_path: Path) -> None:
        """collect_ts_source_files finds .ts files recursively."""
        (tmp_path / "main.ts").write_text("// main")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "util.ts").write_text("// util")

        result = collect_ts_source_files(tmp_path)

        assert (tmp_path / "main.ts") in result
        assert (tmp_path / "sub" / "util.ts") in result

    def test_finds_tsx_files(self, tmp_path: Path) -> None:
        """collect_ts_source_files finds .tsx files recursively."""
        (tmp_path / "App.tsx").write_text("// app")
        (tmp_path / "components").mkdir()
        (tmp_path / "components" / "Button.tsx").write_text("// button")

        result = collect_ts_source_files(tmp_path)

        assert (tmp_path / "App.tsx") in result
        assert (tmp_path / "components" / "Button.tsx") in result

    def test_ignores_other_file_types(self, tmp_path: Path) -> None:
        """collect_ts_source_files ignores non-TypeScript files."""
        (tmp_path / "main.ts").write_text("// ts")
        (tmp_path / "util.js").write_text("// js")
        (tmp_path / "config.json").write_text("{}")
        (tmp_path / "README.md").write_text("# readme")
        (tmp_path / "data.txt").write_text("data")

        result = collect_ts_source_files(tmp_path)

        assert (tmp_path / "main.ts") in result
        assert (tmp_path / "util.js") not in result
        assert (tmp_path / "config.json") not in result
        assert (tmp_path / "README.md") not in result
        assert (tmp_path / "data.txt") not in result

    def test_returns_empty_set_for_empty_directory(self, tmp_path: Path) -> None:
        """collect_ts_source_files returns empty set for empty directory."""
        result = collect_ts_source_files(tmp_path)

        assert result == set()

    def test_returns_empty_set_for_directory_with_no_ts_files(self, tmp_path: Path) -> None:
        """collect_ts_source_files returns empty set when no TS/TSX files exist."""
        (tmp_path / "app.js").write_text("// js")
        (tmp_path / "styles.css").write_text("/* css */")

        result = collect_ts_source_files(tmp_path)

        assert result == set()


class TestBuildContext:
    """Tests for BuildContext dataclass."""

    def test_creates_with_required_fields(self, tmp_path: Path) -> None:
        """BuildContext requires registry, entry_point, workspace, collected, dist_dir, manifest."""
        registry = ModuleRegistry()
        collected = registry.collect()
        entry_point = tmp_path / "main.tsx"
        workspace = tmp_path / "workspace"
        dist_dir = tmp_path / "dist"
        manifest = BuildManifest()

        ctx = BuildContext(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            collected=collected,
            dist_dir=dist_dir,
            manifest=manifest,
        )

        assert ctx.registry is registry
        assert ctx.entry_point == entry_point
        assert ctx.workspace == workspace
        assert ctx.collected is collected
        assert ctx.dist_dir == dist_dir
        assert ctx.manifest is manifest

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
            manifest=BuildManifest(),
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
            manifest=BuildManifest(),
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
            manifest=BuildManifest(),
        )

        assert ctx.generated_files == {}
        ctx.generated_files["_registry"] = tmp_path / "_registry.ts"
        assert ctx.generated_files["_registry"] == tmp_path / "_registry.ts"

    def test_has_manifest_field(self, tmp_path: Path) -> None:
        """BuildContext has manifest field."""
        registry = ModuleRegistry()
        collected = registry.collect()
        manifest = BuildManifest()

        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=collected,
            dist_dir=tmp_path / "dist",
            manifest=manifest,
        )

        assert ctx.manifest is manifest

    def test_manifest_is_required(self, tmp_path: Path) -> None:
        """BuildContext requires manifest field."""
        registry = ModuleRegistry()
        collected = registry.collect()

        # This should fail at type checking level, but we verify the field exists
        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        assert hasattr(ctx, "manifest")

    @pytest.mark.slow
    def test_exec_in_build_env_sets_cwd_to_workspace(self, tmp_path: Path) -> None:
        """exec_in_build_env runs command with cwd set to workspace."""
        registry = ModuleRegistry()
        collected = registry.collect()
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        # Run pwd to verify cwd
        result = ctx.exec_in_build_env(["pwd"], check=True)
        # pwd output includes newline, workspace.resolve() handles symlinks
        assert result.returncode == 0

    @pytest.mark.slow
    def test_exec_in_build_env_uses_ctx_env(self, tmp_path: Path) -> None:
        """exec_in_build_env passes ctx.env to subprocess."""
        registry = ModuleRegistry()
        collected = registry.collect()
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
            env={"TEST_VAR": "test_value"},
        )

        # Create a script that checks the env var exists
        # printenv returns 0 if var exists, 1 if not
        result = ctx.exec_in_build_env(["printenv", "TEST_VAR"], check=False)
        assert result.returncode == 0, "TEST_VAR should be set in environment"

    @pytest.mark.slow
    def test_exec_in_build_env_raises_on_failure_when_check_true(self, tmp_path: Path) -> None:
        """exec_in_build_env raises CalledProcessError when check=True and command fails."""
        registry = ModuleRegistry()
        collected = registry.collect()
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        with pytest.raises(subprocess.CalledProcessError):
            ctx.exec_in_build_env(["false"], check=True)

    @pytest.mark.slow
    def test_exec_in_build_env_returns_result_when_check_false(self, tmp_path: Path) -> None:
        """exec_in_build_env returns CompletedProcess when check=False."""
        registry = ModuleRegistry()
        collected = registry.collect()
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        ctx = BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        result = ctx.exec_in_build_env(["false"], check=False)
        assert result.returncode != 0


class TestBuildContextDirectManifestAccess:
    """Tests for BuildContext - steps access manifest.steps directly."""

    def test_no_step_manifests_attribute(self, tmp_path: Path) -> None:
        """BuildContext should NOT have step_manifests attribute (removed)."""
        ctx = BuildContext(
            registry=ModuleRegistry(),
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=ModuleRegistry().collect(),
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        assert not hasattr(ctx, "step_manifests")

    def test_no_get_step_manifest_method(self, tmp_path: Path) -> None:
        """BuildContext should NOT have get_step_manifest method (removed)."""
        ctx = BuildContext(
            registry=ModuleRegistry(),
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=ModuleRegistry().collect(),
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        assert not hasattr(ctx, "get_step_manifest")

    def test_steps_write_to_manifest_steps_directly(self, tmp_path: Path) -> None:
        """Steps write to ctx.manifest.steps directly."""
        ctx = BuildContext(
            registry=ModuleRegistry(),
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=ModuleRegistry().collect(),
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        # Steps use setdefault to create/get their manifest entry
        step_manifest = ctx.manifest.steps.setdefault("test-step", StepManifest())
        step_manifest.metadata["foo"] = "bar"

        # The manifest should contain the step
        assert "test-step" in ctx.manifest.steps
        assert ctx.manifest.steps["test-step"].metadata["foo"] == "bar"

    def test_setdefault_returns_existing(self, tmp_path: Path) -> None:
        """setdefault returns existing StepManifest if present."""
        ctx = BuildContext(
            registry=ModuleRegistry(),
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=ModuleRegistry().collect(),
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        # First call creates
        first = ctx.manifest.steps.setdefault("bundle-build", StepManifest())
        first.metadata["foo"] = "bar"

        # Second call returns same instance
        second = ctx.manifest.steps.setdefault("bundle-build", StepManifest())

        assert second is first
        assert second.metadata["foo"] == "bar"


class TestBuildStep:
    """Tests for BuildStep abstract base class."""

    def test_is_abstract_class(self) -> None:
        """BuildStep cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BuildStep()  # type: ignore[abstract]

    def test_requires_name_property(self) -> None:
        """BuildStep subclass must implement name property."""

        class IncompleteStep(BuildStep):
            def run(self, ctx: BuildContext) -> None:
                pass

        with pytest.raises(TypeError):
            IncompleteStep()  # type: ignore[abstract]

    def test_requires_run_method(self) -> None:
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


class TestShouldBuildEnum:
    """Tests for ShouldBuild enum."""

    def test_has_skip_member(self) -> None:
        """ShouldBuild enum has SKIP member."""
        assert hasattr(ShouldBuild, "SKIP")
        assert ShouldBuild.SKIP.value == "skip"

    def test_has_build_member(self) -> None:
        """ShouldBuild enum has BUILD member."""
        assert hasattr(ShouldBuild, "BUILD")
        assert ShouldBuild.BUILD.value == "build"


class TestBuildStepShouldBuildSignature:
    """Tests for BuildStep.should_build() method with new signature."""

    def test_default_returns_none(self, tmp_path: Path) -> None:
        """BuildStep.should_build() returns None by default (always run)."""
        ctx = BuildContext(
            registry=ModuleRegistry(),
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=ModuleRegistry().collect(),
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        class NoopStep(BuildStep):
            @property
            def name(self) -> str:
                return "noop"

            def run(self, ctx: BuildContext) -> None:
                pass

        step = NoopStep()
        result = step.should_build(ctx, step_manifest=None)

        assert result is None

    def test_receives_step_manifest_parameter(self, tmp_path: Path) -> None:
        """BuildStep.should_build() receives step_manifest for comparison."""
        ctx = BuildContext(
            registry=ModuleRegistry(),
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=ModuleRegistry().collect(),
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        received_manifest: list[StepManifest | None] = []

        class CheckManifestStep(BuildStep):
            @property
            def name(self) -> str:
                return "check-manifest"

            def run(self, ctx: BuildContext) -> None:
                pass

            def should_build(
                self, ctx: BuildContext, step_manifest: StepManifest | None
            ) -> ShouldBuild | None:
                received_manifest.append(step_manifest)
                return None

        step = CheckManifestStep()
        prev_step_manifest = StepManifest(
            source_paths={Path("/some/file")},
            metadata={"key": "value"},
        )
        step.should_build(ctx, step_manifest=prev_step_manifest)

        assert len(received_manifest) == 1
        assert received_manifest[0] is prev_step_manifest

    def test_can_return_skip(self, tmp_path: Path) -> None:
        """BuildStep.should_build() can return SKIP."""
        ctx = BuildContext(
            registry=ModuleRegistry(),
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=ModuleRegistry().collect(),
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        class SkipStep(BuildStep):
            @property
            def name(self) -> str:
                return "skip-step"

            def run(self, ctx: BuildContext) -> None:
                pass

            def should_build(
                self, ctx: BuildContext, step_manifest: StepManifest | None
            ) -> ShouldBuild | None:
                return ShouldBuild.SKIP

        step = SkipStep()
        result = step.should_build(ctx, step_manifest=None)

        assert result == ShouldBuild.SKIP

    def test_can_return_build(self, tmp_path: Path) -> None:
        """BuildStep.should_build() can return BUILD."""
        ctx = BuildContext(
            registry=ModuleRegistry(),
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=ModuleRegistry().collect(),
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        class BuildAlwaysStep(BuildStep):
            @property
            def name(self) -> str:
                return "build-always"

            def run(self, ctx: BuildContext) -> None:
                pass

            def should_build(
                self, ctx: BuildContext, step_manifest: StepManifest | None
            ) -> ShouldBuild | None:
                return ShouldBuild.BUILD

        step = BuildAlwaysStep()
        result = step.should_build(ctx, step_manifest=None)

        assert result == ShouldBuild.BUILD


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
            manifest=BuildManifest(),
        )

    def test_has_name_package_install(self) -> None:
        """PackageInstallStep.name is 'package-install'."""
        step = PackageInstallStep()
        assert step.name == "package-install"

    def test_calls_ensure_packages_with_collected_packages(
        self, build_context: BuildContext
    ) -> None:
        """PackageInstallStep calls ensure_packages with packages from collected modules."""
        with patch("trellis.bundler.steps.ensure_packages") as mock_ensure:
            step = PackageInstallStep()
            step.run(build_context)

        mock_ensure.assert_called_once_with({"react": "18.2.0"}, build_context.workspace)


class TestPackageInstallStepShouldBuild:
    """Tests for PackageInstallStep.should_build() with new signature."""

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
            manifest=BuildManifest(),
        )

    def test_returns_skip_when_packages_unchanged(self, build_context: BuildContext) -> None:
        """should_build returns SKIP when packages match previous step manifest."""
        prev_step_manifest = StepManifest(
            metadata={"packages": {"react": "18.2.0"}},  # Same version
        )

        step = PackageInstallStep()
        result = step.should_build(build_context, prev_step_manifest)

        assert result == ShouldBuild.SKIP

    def test_returns_build_when_packages_changed(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when packages differ from previous manifest."""
        prev_step_manifest = StepManifest(
            metadata={"packages": {"react": "17.0.0"}},  # Different version
        )

        step = PackageInstallStep()
        result = step.should_build(build_context, prev_step_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_no_previous_manifest(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when no previous step manifest."""
        step = PackageInstallStep()
        result = step.should_build(build_context, step_manifest=None)

        assert result == ShouldBuild.BUILD

    def test_writes_packages_to_step_manifest_metadata(self, build_context: BuildContext) -> None:
        """PackageInstallStep stores packages in step manifest metadata."""
        with patch("trellis.bundler.steps.ensure_packages"):
            step = PackageInstallStep()
            step.run(build_context)

        step_manifest = build_context.manifest.steps["package-install"]
        expected_packages = {"react": "18.2.0"}
        assert step_manifest.metadata["packages"] == expected_packages


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
            manifest=BuildManifest(),
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


class TestRegistryGenerationStepShouldBuild:
    """Tests for RegistryGenerationStep.should_build()."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing."""
        registry = ModuleRegistry()
        registry.register("test-mod", packages={"react": "18.0.0"})
        collected = registry.collect()

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        return BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

    def test_returns_build_when_no_previous_manifest(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when no previous step manifest."""
        step = RegistryGenerationStep()
        result = step.should_build(build_context, step_manifest=None)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_collected_hash_missing(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when previous manifest has no collected_hash."""
        prev_manifest = StepManifest(metadata={})

        step = RegistryGenerationStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_modules_changed(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when modules have changed."""
        # Run once to get the hash
        step = RegistryGenerationStep()
        step.run(build_context)
        original_hash = build_context.manifest.steps["registry-generation"].metadata.get(
            "collected_hash"
        )

        # Create new context with different modules
        registry2 = ModuleRegistry()
        registry2.register("different-mod", packages={"lodash": "4.0.0"})
        build_context.collected = registry2.collect()

        prev_manifest = StepManifest(metadata={"collected_hash": original_hash})
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_skip_when_modules_unchanged(self, build_context: BuildContext) -> None:
        """should_build returns SKIP when modules are unchanged."""
        # Run once to get the hash
        step = RegistryGenerationStep()
        step.run(build_context)
        current_hash = build_context.manifest.steps["registry-generation"].metadata.get(
            "collected_hash"
        )

        # Use same hash in previous manifest
        prev_manifest = StepManifest(metadata={"collected_hash": current_hash})
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.SKIP


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
            manifest=BuildManifest(),
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


class TestTsconfigStepShouldBuild:
    """Tests for TsconfigStep.should_build()."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing."""
        registry = ModuleRegistry()
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
            manifest=BuildManifest(),
        )

    def test_returns_build_when_no_previous_manifest(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when no previous step manifest."""
        step = TsconfigStep()
        result = step.should_build(build_context, step_manifest=None)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_inputs_hash_missing(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when previous manifest has no inputs_hash."""
        prev_manifest = StepManifest(metadata={})

        step = TsconfigStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_module_paths_changed(
        self, build_context: BuildContext, tmp_path: Path
    ) -> None:
        """should_build returns BUILD when module paths have changed."""
        # Run once to get the hash
        step = TsconfigStep()
        step.run(build_context)
        original_hash = build_context.manifest.steps["tsconfig"].metadata.get("inputs_hash")

        # Change module path
        registry2 = ModuleRegistry()
        registry2.register("test-mod")
        registry2._modules["test-mod"]._base_path = tmp_path / "different-path"
        build_context.collected = registry2.collect()

        prev_manifest = StepManifest(metadata={"inputs_hash": original_hash})
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_skip_when_inputs_unchanged(self, build_context: BuildContext) -> None:
        """should_build returns SKIP when inputs are unchanged."""
        # Run once to get the hash
        step = TsconfigStep()
        step.run(build_context)
        current_hash = build_context.manifest.steps["tsconfig"].metadata.get("inputs_hash")

        # Use same hash in previous manifest
        prev_manifest = StepManifest(metadata={"inputs_hash": current_hash})
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.SKIP

    def test_restores_generated_files_when_skip(self, build_context: BuildContext) -> None:
        """should_build restores generated_files['tsconfig'] when returning SKIP."""
        step = TsconfigStep()
        step.run(build_context)

        inputs_hash = build_context.manifest.steps["tsconfig"].metadata["inputs_hash"]
        prev_manifest = StepManifest(metadata={"inputs_hash": inputs_hash})

        # Fresh context - generated_files is empty
        fresh_ctx = BuildContext(
            registry=build_context.registry,
            entry_point=build_context.entry_point,
            workspace=build_context.workspace,
            collected=build_context.collected,
            dist_dir=build_context.dist_dir,
            manifest=BuildManifest(),
        )
        result = step.should_build(fresh_ctx, prev_manifest)

        assert result == ShouldBuild.SKIP
        assert fresh_ctx.generated_files["tsconfig"] == fresh_ctx.workspace / "tsconfig.json"


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
            manifest=BuildManifest(),
        )
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


class TestTypeCheckStepShouldBuild:
    """Tests for TypeCheckStep.should_build()."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext with source files for testing."""
        registry = ModuleRegistry()
        collected = registry.collect()

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create entry point directory with a source file
        entry_dir = tmp_path / "src"
        entry_dir.mkdir()
        entry_point = entry_dir / "main.tsx"
        entry_point.write_text("// main")

        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        node_modules = workspace / "node_modules"
        node_modules.mkdir()
        (node_modules / ".bin").mkdir()

        ctx = BuildContext(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            collected=collected,
            dist_dir=dist_dir,
            manifest=BuildManifest(),
        )
        ctx.generated_files["tsconfig"] = workspace / "tsconfig.json"

        return ctx

    def test_returns_build_when_no_previous_manifest(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when no previous step manifest."""
        step = TypeCheckStep()
        result = step.should_build(build_context, step_manifest=None)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_source_paths_empty(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when previous manifest has empty source_paths."""
        prev_manifest = StepManifest(
            source_paths=set(),
            dest_files={build_context.workspace / ".tsc-check"},
        )

        step = TypeCheckStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_marker_missing(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when marker file doesn't exist."""
        prev_manifest = StepManifest(
            source_paths={build_context.entry_point},
            dest_files={build_context.workspace / ".tsc-check"},  # Doesn't exist
        )

        step = TypeCheckStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_source_newer(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when source is newer than marker."""
        # Create marker first
        marker = build_context.workspace / ".tsc-check"
        marker.write_text("")

        time.sleep(0.01)  # Ensure different mtime

        # Modify source (now newer)
        build_context.entry_point.write_text("// modified main")

        prev_manifest = StepManifest(
            source_paths={build_context.entry_point},
            dest_files={marker},
        )

        step = TypeCheckStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_skip_when_marker_up_to_date(self, build_context: BuildContext) -> None:
        """should_build returns SKIP when marker is newer than sources."""
        time.sleep(0.01)  # Ensure different mtime

        # Create marker (newer than source)
        marker = build_context.workspace / ".tsc-check"
        marker.write_text("")

        prev_manifest = StepManifest(
            source_paths={build_context.entry_point},
            dest_files={marker},
        )

        step = TypeCheckStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.SKIP


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
            manifest=BuildManifest(),
        )
        ctx.generated_files["tsconfig"] = workspace / "tsconfig.json"

        return ctx

    def test_has_name_declaration(self) -> None:
        """DeclarationStep.name is 'declaration'."""
        step = DeclarationStep()
        assert step.name == "declaration"

    def test_runs_dts_bundle_generator(self, build_context: BuildContext) -> None:
        """DeclarationStep runs dts-bundle-generator with correct flags."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = DeclarationStep()
            step.run(build_context)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "dts-bundle-generator" in cmd[0]
        assert "--no-banner" in cmd

    def test_outputs_to_dist_dir(self, build_context: BuildContext) -> None:
        """DeclarationStep outputs .d.ts file to ctx.dist_dir."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = DeclarationStep()
            step.run(build_context)

        cmd = mock_run.call_args[0][0]
        # dts-bundle-generator uses -o for output file
        assert "-o" in cmd
        output_idx = cmd.index("-o")
        output_path = cmd[output_idx + 1]
        assert output_path.startswith(str(build_context.dist_dir))
        assert output_path.endswith(".d.ts")


class TestDeclarationStepShouldBuild:
    """Tests for DeclarationStep.should_build()."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext with source files for testing."""
        registry = ModuleRegistry()
        collected = registry.collect()

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create entry point directory with source file
        entry_dir = tmp_path / "src"
        entry_dir.mkdir()
        entry_point = entry_dir / "main.tsx"
        entry_point.write_text("// main")

        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        node_modules = workspace / "node_modules"
        node_modules.mkdir()
        (node_modules / ".bin").mkdir()

        ctx = BuildContext(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            collected=collected,
            dist_dir=dist_dir,
            manifest=BuildManifest(),
        )
        ctx.generated_files["tsconfig"] = workspace / "tsconfig.json"

        return ctx

    def test_returns_build_when_no_previous_manifest(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when no previous step manifest."""
        step = DeclarationStep()
        result = step.should_build(build_context, step_manifest=None)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_source_paths_empty(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when previous manifest has empty source_paths."""
        prev_manifest = StepManifest(
            source_paths=set(),
            dest_files={build_context.dist_dir / "main.d.ts"},
        )

        step = DeclarationStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_output_missing(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when output file doesn't exist."""
        prev_manifest = StepManifest(
            source_paths={build_context.entry_point},
            dest_files={build_context.dist_dir / "main.d.ts"},  # Doesn't exist
        )

        step = DeclarationStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_source_newer(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when source is newer than output."""
        # Create output first
        output_file = build_context.dist_dir / "main.d.ts"
        output_file.write_text("// declarations")

        time.sleep(0.01)  # Ensure different mtime

        # Modify source (now newer)
        build_context.entry_point.write_text("// modified main")

        prev_manifest = StepManifest(
            source_paths={build_context.entry_point},
            dest_files={output_file},
        )

        step = DeclarationStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_skip_when_outputs_up_to_date(self, build_context: BuildContext) -> None:
        """should_build returns SKIP when outputs are newer than sources."""
        time.sleep(0.01)  # Ensure different mtime

        # Create output (newer than source)
        output_file = build_context.dist_dir / "main.d.ts"
        output_file.write_text("// declarations")

        prev_manifest = StepManifest(
            source_paths={build_context.entry_point},
            dest_files={output_file},
        )

        step = DeclarationStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.SKIP


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

        # Create a mock metafile for read_metafile()
        metafile_path = workspace / "metafile.json"
        metafile_path.write_text(
            json.dumps(
                {
                    "inputs": ["../main.tsx"],
                    "outputs": ["../dist/bundle.js"],
                }
            )
        )

        ctx = BuildContext(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            collected=collected,
            dist_dir=dist_dir,
            manifest=BuildManifest(),
        )
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


class TestBundleBuildStepManifest:
    """Tests for BundleBuildStep manifest population."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing."""
        registry = ModuleRegistry()
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
            manifest=BuildManifest(),
        )
        ctx.env["NODE_PATH"] = str(node_modules)

        return ctx

    def test_adds_metafile_inputs_to_step_manifest(self, build_context: BuildContext) -> None:
        """BundleBuildStep adds metafile inputs to step manifest source_paths."""
        # Create a metafile that esbuild would produce
        metafile_content = {
            "inputs": {"../main.tsx": {"bytes": 8}, "../util.ts": {"bytes": 16}},
            "outputs": {"dist/bundle.js": {"bytes": 100}},
        }
        (build_context.workspace / "metafile.json").write_text(json.dumps(metafile_content))

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = BundleBuildStep()
            step.run(build_context)

        # Check step manifest has input files (absolute paths)
        workspace = build_context.workspace
        expected_inputs = {
            (workspace / "../main.tsx").resolve(),
            (workspace / "../util.ts").resolve(),
        }
        step_manifest = build_context.manifest.steps["bundle-build"]
        assert step_manifest.source_paths == expected_inputs

    def test_adds_metafile_outputs_to_step_manifest(self, build_context: BuildContext) -> None:
        """BundleBuildStep adds metafile outputs to step manifest dest_files."""
        # Create a metafile that esbuild would produce
        metafile_content = {
            "inputs": {"../main.tsx": {"bytes": 8}},
            "outputs": {"dist/bundle.js": {"bytes": 100}, "dist/bundle.css": {"bytes": 50}},
        }
        (build_context.workspace / "metafile.json").write_text(json.dumps(metafile_content))

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            step = BundleBuildStep()
            step.run(build_context)

        # Check step manifest has output files (absolute paths)
        workspace = build_context.workspace
        expected_outputs = {
            (workspace / "dist/bundle.js").resolve(),
            (workspace / "dist/bundle.css").resolve(),
        }
        step_manifest = build_context.manifest.steps["bundle-build"]
        assert step_manifest.dest_files == expected_outputs


class TestBundleBuildStepShouldBuild:
    """Tests for BundleBuildStep.should_build()."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing."""
        registry = ModuleRegistry()
        collected = registry.collect()

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        return BuildContext(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            collected=collected,
            dist_dir=dist_dir,
            manifest=BuildManifest(),
        )

    def test_returns_build_when_no_previous_manifest(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when no previous step manifest."""
        step = BundleBuildStep()
        result = step.should_build(build_context, step_manifest=None)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_source_paths_empty(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when previous manifest has empty source_paths."""
        prev_manifest = StepManifest(
            source_paths=set(),
            dest_files={build_context.dist_dir / "bundle.js"},
        )

        step = BundleBuildStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_dest_files_empty(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when previous manifest has empty dest_files."""
        prev_manifest = StepManifest(
            source_paths={build_context.entry_point},
            dest_files=set(),
        )

        step = BundleBuildStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_output_missing(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when output file doesn't exist."""
        prev_manifest = StepManifest(
            source_paths={build_context.entry_point},
            dest_files={build_context.dist_dir / "bundle.js"},  # Doesn't exist
        )

        step = BundleBuildStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_source_newer(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when source is newer than output."""
        # Create output first
        output_file = build_context.dist_dir / "bundle.js"
        output_file.write_text("// old bundle")

        time.sleep(0.01)  # Ensure different mtime

        # Modify source (now newer)
        build_context.entry_point.write_text("// modified entry")

        prev_manifest = StepManifest(
            source_paths={build_context.entry_point},
            dest_files={output_file},
        )

        step = BundleBuildStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_skip_when_outputs_up_to_date(self, build_context: BuildContext) -> None:
        """should_build returns SKIP when outputs are newer than sources."""
        # Source file already exists from fixture

        time.sleep(0.01)  # Ensure different mtime

        # Create output (newer than source)
        output_file = build_context.dist_dir / "bundle.js"
        output_file.write_text("// bundle")

        prev_manifest = StepManifest(
            source_paths={build_context.entry_point},
            dest_files={output_file},
        )

        step = BundleBuildStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.SKIP


class TestIndexHtmlRenderStepManifest:
    """Tests for IndexHtmlRenderStep manifest population."""

    def test_adds_template_to_step_manifest_source_paths(self, tmp_path: Path) -> None:
        """IndexHtmlRenderStep adds template path to step manifest source_paths."""
        registry = ModuleRegistry()
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
            manifest=BuildManifest(),
        )

        # Create a template file
        template_path = tmp_path / "index.html.j2"
        template_path.write_text("<!DOCTYPE html><html><body>Hello</body></html>")

        step = IndexHtmlRenderStep(template_path=template_path)
        step.run(ctx)

        step_manifest = ctx.manifest.steps["index-html-render"]
        assert template_path in step_manifest.source_paths

    def test_adds_index_html_to_step_manifest_dest_files(self, tmp_path: Path) -> None:
        """IndexHtmlRenderStep adds index.html to step manifest dest_files."""
        registry = ModuleRegistry()
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
            manifest=BuildManifest(),
        )

        # Create a template file
        template_path = tmp_path / "index.html.j2"
        template_path.write_text("<!DOCTYPE html><html><body>Hello</body></html>")

        step = IndexHtmlRenderStep(template_path=template_path)
        step.run(ctx)

        step_manifest = ctx.manifest.steps["index-html-render"]
        expected_output = dist_dir / "index.html"
        assert expected_output in step_manifest.dest_files


class TestIndexHtmlRenderStepShouldBuild:
    """Tests for IndexHtmlRenderStep.should_build()."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext for testing."""
        registry = ModuleRegistry()
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
            manifest=BuildManifest(),
        )

    def test_returns_build_when_no_previous_manifest(
        self, build_context: BuildContext, tmp_path: Path
    ) -> None:
        """should_build returns BUILD when no previous step manifest."""
        template_path = tmp_path / "index.html.j2"
        template_path.write_text("<!DOCTYPE html><html><body>Hello</body></html>")

        step = IndexHtmlRenderStep(template_path=template_path)
        result = step.should_build(build_context, step_manifest=None)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_source_paths_empty(
        self, build_context: BuildContext, tmp_path: Path
    ) -> None:
        """should_build returns BUILD when previous manifest has empty source_paths."""
        template_path = tmp_path / "index.html.j2"
        template_path.write_text("<!DOCTYPE html>")

        prev_manifest = StepManifest(
            source_paths=set(),
            dest_files={build_context.dist_dir / "index.html"},
        )

        step = IndexHtmlRenderStep(template_path=template_path)
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_output_missing(
        self, build_context: BuildContext, tmp_path: Path
    ) -> None:
        """should_build returns BUILD when output file doesn't exist."""
        template_path = tmp_path / "index.html.j2"
        template_path.write_text("<!DOCTYPE html>")

        prev_manifest = StepManifest(
            source_paths={template_path},
            dest_files={build_context.dist_dir / "index.html"},  # Doesn't exist
        )

        step = IndexHtmlRenderStep(template_path=template_path)
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_template_newer(
        self, build_context: BuildContext, tmp_path: Path
    ) -> None:
        """should_build returns BUILD when template is newer than output."""
        template_path = tmp_path / "index.html.j2"

        # Create output first
        output_file = build_context.dist_dir / "index.html"
        output_file.write_text("<!DOCTYPE html><html><body>old</body></html>")

        time.sleep(0.01)  # Ensure different mtime

        # Create/modify template (now newer)
        template_path.write_text("<!DOCTYPE html><html><body>new</body></html>")

        prev_manifest = StepManifest(
            source_paths={template_path},
            dest_files={output_file},
            metadata={"context_hash": "same"},
        )

        step = IndexHtmlRenderStep(template_path=template_path)
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_context_changed(
        self, build_context: BuildContext, tmp_path: Path
    ) -> None:
        """should_build returns BUILD when context has changed."""
        template_path = tmp_path / "index.html.j2"
        template_path.write_text("<!DOCTYPE html>{{ title }}</html>")

        time.sleep(0.01)  # Ensure different mtime

        # Create output (newer than template)
        output_file = build_context.dist_dir / "index.html"
        output_file.write_text("<!DOCTYPE html>Old Title</html>")

        prev_manifest = StepManifest(
            source_paths={template_path},
            dest_files={output_file},
            metadata={"context_hash": "old_hash"},  # Different hash
        )

        step = IndexHtmlRenderStep(template_path=template_path, context={"title": "New Title"})
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_skip_when_template_and_context_unchanged(
        self, build_context: BuildContext, tmp_path: Path
    ) -> None:
        """should_build returns SKIP when template and context are unchanged."""
        template_path = tmp_path / "index.html.j2"
        template_path.write_text("<!DOCTYPE html>")

        time.sleep(0.01)  # Ensure different mtime

        # Create output (newer than template)
        output_file = build_context.dist_dir / "index.html"
        output_file.write_text("<!DOCTYPE html>")

        # Run step once to get the context hash
        step = IndexHtmlRenderStep(template_path=template_path, context={"key": "value"})
        step.run(build_context)
        current_hash = build_context.manifest.steps["index-html-render"].metadata.get(
            "context_hash"
        )

        prev_manifest = StepManifest(
            source_paths={template_path},
            dest_files={output_file},
            metadata={"context_hash": current_hash},
        )

        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.SKIP


class TestStaticFileCopyStep:
    """Tests for StaticFileCopyStep.

    StaticFileCopyStep uses convention-based discovery:
    - Copies from module._base_path / "static" for each module
    - Copies from ctx.app_static_dir if provided
    """

    def test_has_name_static_file_copy(self) -> None:
        """StaticFileCopyStep.name is 'static-file-copy'."""
        step = StaticFileCopyStep()
        assert step.name == "static-file-copy"

    def test_copies_files_from_module_static_directory(self, tmp_path: Path) -> None:
        """StaticFileCopyStep copies files from module._base_path / 'static'."""
        registry = ModuleRegistry()

        # Create module with static directory
        mod_dir = tmp_path / "my_mod"
        static_dir = mod_dir / "static"
        static_dir.mkdir(parents=True)
        (static_dir / "data.json").write_text('{"key": "value"}')
        (static_dir / "icon.png").write_bytes(b"PNG data")

        registry.register("my-mod")
        registry._modules["my-mod"]._base_path = mod_dir
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
            manifest=BuildManifest(),
        )

        step = StaticFileCopyStep()
        step.run(ctx)

        # Files should be copied to dist
        assert (dist_dir / "data.json").exists()
        assert (dist_dir / "data.json").read_text() == '{"key": "value"}'
        assert (dist_dir / "icon.png").exists()
        assert (dist_dir / "icon.png").read_bytes() == b"PNG data"

    def test_ignores_modules_without_static_directory(self, tmp_path: Path) -> None:
        """StaticFileCopyStep skips modules that have no static directory."""
        registry = ModuleRegistry()

        # Create module WITHOUT static directory
        mod_dir = tmp_path / "my_mod"
        mod_dir.mkdir()
        # No static folder created

        registry.register("my-mod")
        registry._modules["my-mod"]._base_path = mod_dir
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
            manifest=BuildManifest(),
        )

        step = StaticFileCopyStep()
        # Should not raise - just skip the module
        step.run(ctx)

        # dist should be empty (except what dist_dir.mkdir() created)
        assert list(dist_dir.iterdir()) == []

    def test_preserves_nested_directory_structure(self, tmp_path: Path) -> None:
        """StaticFileCopyStep preserves nested directories from static folder."""
        registry = ModuleRegistry()

        # Create module with nested static structure
        mod_dir = tmp_path / "my_mod"
        static_dir = mod_dir / "static"
        (static_dir / "assets" / "images").mkdir(parents=True)
        (static_dir / "assets" / "images" / "logo.png").write_bytes(b"PNG data")
        (static_dir / "assets" / "fonts").mkdir(parents=True)
        (static_dir / "assets" / "fonts" / "font.woff").write_bytes(b"WOFF data")

        registry.register("my-mod")
        registry._modules["my-mod"]._base_path = mod_dir
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
            manifest=BuildManifest(),
        )

        step = StaticFileCopyStep()
        step.run(ctx)

        # Nested structure should be preserved
        assert (dist_dir / "assets" / "images" / "logo.png").exists()
        assert (dist_dir / "assets" / "images" / "logo.png").read_bytes() == b"PNG data"
        assert (dist_dir / "assets" / "fonts" / "font.woff").exists()
        assert (dist_dir / "assets" / "fonts" / "font.woff").read_bytes() == b"WOFF data"

    def test_copies_app_level_static_files(self, tmp_path: Path) -> None:
        """StaticFileCopyStep copies from ctx.app_static_dir if provided."""
        registry = ModuleRegistry()
        collected = registry.collect()

        # Create app-level static directory
        app_static = tmp_path / "app_static"
        app_static.mkdir()
        (app_static / "favicon.ico").write_bytes(b"ICON data")
        (app_static / "robots.txt").write_text("User-agent: *")

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
            manifest=BuildManifest(),
            app_static_dir=app_static,
        )

        step = StaticFileCopyStep()
        step.run(ctx)

        # App-level static files should be copied
        assert (dist_dir / "favicon.ico").exists()
        assert (dist_dir / "favicon.ico").read_bytes() == b"ICON data"
        assert (dist_dir / "robots.txt").exists()
        assert (dist_dir / "robots.txt").read_text() == "User-agent: *"

    def test_copies_from_both_modules_and_app(self, tmp_path: Path) -> None:
        """StaticFileCopyStep copies from both module static dirs and app_static_dir."""
        registry = ModuleRegistry()

        # Create module with static directory
        mod_dir = tmp_path / "my_mod"
        static_dir = mod_dir / "static"
        static_dir.mkdir(parents=True)
        (static_dir / "module.css").write_text(".mod { }")

        registry.register("my-mod")
        registry._modules["my-mod"]._base_path = mod_dir
        collected = registry.collect()

        # Create app-level static directory
        app_static = tmp_path / "app_static"
        app_static.mkdir()
        (app_static / "app.css").write_text(".app { }")

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
            manifest=BuildManifest(),
            app_static_dir=app_static,
        )

        step = StaticFileCopyStep()
        step.run(ctx)

        # Both module and app static files should be copied
        assert (dist_dir / "module.css").exists()
        assert (dist_dir / "app.css").exists()


class TestStaticFileCopyStepManifest:
    """Tests for StaticFileCopyStep manifest population."""

    def test_adds_static_directories_to_source_paths(self, tmp_path: Path) -> None:
        """StaticFileCopyStep adds static directories to manifest.source_paths."""
        registry = ModuleRegistry()

        # Create module with static directory
        mod_dir = tmp_path / "my_mod"
        static_dir = mod_dir / "static"
        static_dir.mkdir(parents=True)
        (static_dir / "data.json").write_text("{}")

        registry.register("my-mod")
        registry._modules["my-mod"]._base_path = mod_dir
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
            manifest=BuildManifest(),
        )

        step = StaticFileCopyStep()
        step.run(ctx)

        # Static directory should be in source_paths (not individual files)
        step_manifest = ctx.manifest.steps["static-file-copy"]
        assert static_dir in step_manifest.source_paths

    def test_adds_app_static_dir_to_source_paths(self, tmp_path: Path) -> None:
        """StaticFileCopyStep adds app_static_dir to manifest.source_paths."""
        registry = ModuleRegistry()
        collected = registry.collect()

        # Create app-level static directory
        app_static = tmp_path / "app_static"
        app_static.mkdir()
        (app_static / "favicon.ico").write_bytes(b"ICON data")

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
            manifest=BuildManifest(),
            app_static_dir=app_static,
        )

        step = StaticFileCopyStep()
        step.run(ctx)

        step_manifest = ctx.manifest.steps["static-file-copy"]
        assert app_static in step_manifest.source_paths

    def test_adds_copied_files_to_dest_files(self, tmp_path: Path) -> None:
        """StaticFileCopyStep adds copied files to manifest.dest_files."""
        registry = ModuleRegistry()

        # Create module with static files
        mod_dir = tmp_path / "my_mod"
        static_dir = mod_dir / "static"
        (static_dir / "assets").mkdir(parents=True)
        (static_dir / "data.json").write_text("{}")
        (static_dir / "assets" / "logo.png").write_bytes(b"PNG")

        registry.register("my-mod")
        registry._modules["my-mod"]._base_path = mod_dir
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
            manifest=BuildManifest(),
        )

        step = StaticFileCopyStep()
        step.run(ctx)

        # All copied files should be in dest_files
        step_manifest = ctx.manifest.steps["static-file-copy"]
        assert (dist_dir / "data.json") in step_manifest.dest_files
        assert (dist_dir / "assets" / "logo.png") in step_manifest.dest_files


class TestStaticFileCopyStepShouldBuild:
    """Tests for StaticFileCopyStep.should_build()."""

    @pytest.fixture
    def build_context(self, tmp_path: Path) -> BuildContext:
        """Create a BuildContext with static directory for testing."""
        registry = ModuleRegistry()

        # Create module with static directory
        mod_dir = tmp_path / "my_mod"
        static_dir = mod_dir / "static"
        static_dir.mkdir(parents=True)
        (static_dir / "data.json").write_text('{"key": "value"}')

        registry.register("my-mod")
        registry._modules["my-mod"]._base_path = mod_dir
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
            manifest=BuildManifest(),
        )

    def test_returns_build_when_no_previous_manifest(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when no previous step manifest."""
        step = StaticFileCopyStep()
        result = step.should_build(build_context, step_manifest=None)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_source_paths_empty(self, build_context: BuildContext) -> None:
        """should_build returns BUILD when previous manifest has empty source_paths."""
        prev_manifest = StepManifest(
            source_paths=set(),
            dest_files={build_context.dist_dir / "data.json"},
        )

        step = StaticFileCopyStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_output_missing(
        self, build_context: BuildContext, tmp_path: Path
    ) -> None:
        """should_build returns BUILD when output file doesn't exist."""
        static_dir = tmp_path / "my_mod" / "static"
        prev_manifest = StepManifest(
            source_paths={static_dir},
            dest_files={build_context.dist_dir / "data.json"},  # Doesn't exist
        )

        step = StaticFileCopyStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_source_newer(
        self, build_context: BuildContext, tmp_path: Path
    ) -> None:
        """should_build returns BUILD when source is newer than output."""
        static_dir = tmp_path / "my_mod" / "static"

        # Create output first
        output_file = build_context.dist_dir / "data.json"
        output_file.write_text('{"key": "old"}')

        time.sleep(0.01)  # Ensure different mtime

        # Modify source (now newer)
        (static_dir / "data.json").write_text('{"key": "new"}')

        prev_manifest = StepManifest(
            source_paths={static_dir},
            dest_files={output_file},
        )

        step = StaticFileCopyStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_skip_when_outputs_up_to_date(
        self, build_context: BuildContext, tmp_path: Path
    ) -> None:
        """should_build returns SKIP when outputs are newer than sources."""
        static_dir = tmp_path / "my_mod" / "static"

        time.sleep(0.01)  # Ensure different mtime

        # Create output (newer than source)
        output_file = build_context.dist_dir / "data.json"
        output_file.write_text('{"key": "value"}')

        prev_manifest = StepManifest(
            source_paths={static_dir},
            dest_files={output_file},
        )

        step = StaticFileCopyStep()
        result = step.should_build(build_context, prev_manifest)

        assert result == ShouldBuild.SKIP


class TestBuildEntryPointImport:
    """Tests for Python entry point import before module collection."""

    def test_imports_entry_point_before_collect(self, tmp_path: Path) -> None:
        """build() imports python_entry_point before calling registry.collect().

        This ensures any module registrations in the entry point file are
        available when collecting modules.
        """
        # Use the global registry since that's what entry points will register to
        workspace = tmp_path / "workspace"
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        # Create a Python entry point that registers a module when imported
        # Use a unique module name to avoid conflicts with other tests
        python_entry = tmp_path / "app.py"
        python_entry.write_text(
            """
from trellis.bundler.registry import registry
registry.register("test-entry-import-module", packages={"test-unique-pkg": "1.0.0"})
"""
        )

        # Track what modules exist when collect is called
        collected_packages: list = []

        class CaptureStep(BuildStep):
            @property
            def name(self) -> str:
                return "capture"

            def run(self, ctx: BuildContext) -> None:
                collected_packages.append(list(ctx.collected.packages.keys()))

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[CaptureStep()],
            force=True,
            python_entry_point=python_entry,
        )

        # The module should have been registered (via import) before collect()
        assert "test-unique-pkg" in collected_packages[0]


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

    def test_sets_node_path_in_context_env(self, tmp_path: Path) -> None:
        """build() sets NODE_PATH to node_modules path in context env."""
        registry = ModuleRegistry()
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")
        workspace = tmp_path / "workspace"

        captured_env: list[dict[str, str]] = []

        class CaptureStep(BuildStep):
            @property
            def name(self) -> str:
                return "capture"

            def run(self, ctx: BuildContext) -> None:
                captured_env.append(ctx.env.copy())

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[CaptureStep()],
            force=True,
        )

        # NODE_PATH should be set to workspace/node_modules
        expected_node_path = str(workspace / "node_modules")
        assert captured_env[0].get("NODE_PATH") == expected_node_path

    def test_handles_relative_output_dir_in_manifest(self, tmp_path: Path) -> None:
        """build() handles relative output_dir without anchor mismatch error.

        When output_dir is relative (e.g., Path("docs/static")), dest_files
        written via ctx.dist_dir would be relative paths. save_manifest()
        needs absolute paths to compute relative_to(workspace) correctly.

        Reproduces: ValueError: 'docs/static/output.js' and '/abs/workspace'
        have different anchors
        """
        test_registry = ModuleRegistry()
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        # Use a relative path for output_dir (the bug trigger)
        relative_output_dir = Path("docs/static/trellis")

        class WriteToDistStep(BuildStep):
            @property
            def name(self) -> str:
                return "write-to-dist"

            def run(self, ctx: BuildContext) -> None:
                # Simulate what DeclarationStep does: write to ctx.dist_dir
                output_file = ctx.dist_dir / "output.js"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("// output")

                # Track the output file in manifest (this triggers the bug)
                step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
                step_manifest.dest_files.add(output_file)

        # This should not raise ValueError about different anchors
        build(
            registry=test_registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[WriteToDistStep()],
            output_dir=relative_output_dir,
        )

    def test_skips_step_when_should_build_returns_skip(self, tmp_path: Path) -> None:
        """build() skips step when should_build returns SKIP and previous manifest exists."""
        test_registry = ModuleRegistry()
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
            registry=test_registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[SkipStep()],
            force=False,
        )

        assert step_ran == [], "Step should not run when should_build returns SKIP"

    def test_runs_step_when_should_build_returns_build(self, tmp_path: Path) -> None:
        """build() runs step when should_build returns BUILD."""
        test_registry = ModuleRegistry()
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
            registry=test_registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[BuildAlwaysStep()],
            force=False,
        )

        assert step_ran == [True], "Step should run when should_build returns BUILD"

    def test_runs_step_when_should_build_returns_none(self, tmp_path: Path) -> None:
        """build() runs step when should_build returns None (always run)."""
        test_registry = ModuleRegistry()
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
            registry=test_registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[DefaultStep()],
            force=False,
        )

        assert step_ran == [True], "Step should run when should_build returns None"

    def test_preserves_manifest_for_skipped_steps(self, tmp_path: Path) -> None:
        """build() preserves previous manifest section for skipped steps."""
        test_registry = ModuleRegistry()
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
            registry=test_registry,
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
        test_registry = ModuleRegistry()
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
            registry=test_registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[SkipStep()],
            force=True,  # Force runs all
        )

        assert step_ran == [True], "Step should run when force=True"

    def test_full_rebuild_when_no_previous_manifest(self, tmp_path: Path) -> None:
        """build() runs all steps when no previous manifest exists.

        When there's no previous manifest, should_build is not called - we know
        we must build, and calling should_build would be wasteful (and it mutates
        ctx for SKIP cases).
        """
        test_registry = ModuleRegistry()
        workspace = tmp_path / "workspace"
        # Don't create workspace yet - no manifest exists
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text("// entry")

        step_ran = []
        should_build_called = []

        class TestStep(BuildStep):
            @property
            def name(self) -> str:
                return "test-step"

            def run(self, ctx: BuildContext) -> None:
                step_ran.append(True)

            def should_build(
                self, ctx: BuildContext, step_manifest: StepManifest | None
            ) -> ShouldBuild | None:
                should_build_called.append(True)
                return ShouldBuild.SKIP

        build(
            registry=test_registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=[TestStep()],
            force=False,
        )

        # should_build not called when no previous manifest (nothing to compare)
        assert should_build_called == []
        # Step runs because there's no previous manifest to skip to
        assert step_ran == [True]
