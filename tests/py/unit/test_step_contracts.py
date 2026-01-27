"""Unit tests for build step contracts.

These tests verify what each step provides when run() is called,
and the should_build() logic for determining when steps need to run.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from trellis.bundler.manifest import BuildManifest, StepManifest
from trellis.bundler.registry import ModuleRegistry
from trellis.bundler.steps import (
    BuildContext,
    IndexHtmlRenderStep,
    PackageInstallStep,
    RegistryGenerationStep,
    ShouldBuild,
    TsconfigStep,
)


@pytest.fixture
def make_context(tmp_path: Path):
    """Factory to create BuildContext instances for testing."""

    def _make(
        *,
        packages: dict[str, str] | None = None,
        module_names: list[str] | None = None,
    ) -> BuildContext:
        registry = ModuleRegistry()

        # Register modules with specified packages
        if module_names:
            for name in module_names:
                registry.register(name)
        if packages:
            # Register a module with the packages
            registry.register("test-module", packages=packages)

        collected = registry.collect()
        workspace = tmp_path / "workspace"
        workspace.mkdir(exist_ok=True)
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir(exist_ok=True)

        return BuildContext(
            registry=registry,
            entry_point=tmp_path / "main.tsx",
            workspace=workspace,
            collected=collected,
            dist_dir=dist_dir,
            manifest=BuildManifest(),
        )

    return _make


class TestPackageInstallStepContract:
    """Tests for PackageInstallStep's contract.

    Contract:
    - run() stores packages in manifest metadata for change detection
    - run() calls ensure_packages with collected packages
    """

    @patch("trellis.bundler.steps.ensure_packages")
    def test_run_stores_packages_in_manifest_metadata(
        self, mock_ensure: MagicMock, make_context
    ) -> None:
        """run() stores packages in step manifest for next build's comparison."""
        ctx = make_context(packages={"react": "18.2.0", "lodash": "4.17.21"})
        step = PackageInstallStep()

        step.run(ctx)

        step_manifest = ctx.manifest.steps["package-install"]
        assert step_manifest.metadata["packages"] == {
            "react": "18.2.0",
            "lodash": "4.17.21",
        }

    @patch("trellis.bundler.steps.ensure_packages")
    def test_run_calls_ensure_packages_with_collected_packages(
        self, mock_ensure: MagicMock, make_context
    ) -> None:
        """run() calls ensure_packages with packages from collected modules."""
        ctx = make_context(packages={"react": "18.2.0"})
        step = PackageInstallStep()

        step.run(ctx)

        mock_ensure.assert_called_once_with({"react": "18.2.0"}, ctx.workspace)


class TestPackageInstallStepShouldBuild:
    """Tests for PackageInstallStep's should_build() logic."""

    def test_returns_build_when_no_previous_manifest(self, make_context) -> None:
        """should_build() returns BUILD when no previous manifest exists."""
        ctx = make_context(packages={"react": "18.2.0"})
        step = PackageInstallStep()

        result = step.should_build(ctx, None)

        assert result == ShouldBuild.BUILD

    def test_returns_skip_when_packages_unchanged(self, make_context) -> None:
        """should_build() returns SKIP when packages match previous build."""
        ctx = make_context(packages={"react": "18.2.0"})
        step = PackageInstallStep()
        prev_manifest = StepManifest(metadata={"packages": {"react": "18.2.0"}})

        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.SKIP

    def test_returns_build_when_packages_changed(self, make_context) -> None:
        """should_build() returns BUILD when packages differ from previous build."""
        ctx = make_context(packages={"react": "18.3.0"})  # Version changed
        step = PackageInstallStep()
        prev_manifest = StepManifest(metadata={"packages": {"react": "18.2.0"}})

        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_package_added(self, make_context) -> None:
        """should_build() returns BUILD when a new package is added."""
        ctx = make_context(packages={"react": "18.2.0", "lodash": "4.17.21"})
        step = PackageInstallStep()
        prev_manifest = StepManifest(metadata={"packages": {"react": "18.2.0"}})

        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.BUILD


class TestRegistryGenerationStepContract:
    """Tests for RegistryGenerationStep's contract.

    Contract:
    - run() sets ctx.generated_files["_registry"] to the registry path
    - run() appends --alias:@trellis/_registry=... to ctx.esbuild_args
    - run() stores collected_hash in manifest metadata
    """

    @patch("trellis.bundler.steps.write_registry_ts")
    def test_run_sets_generated_files_registry(
        self, mock_write: MagicMock, make_context, tmp_path: Path
    ) -> None:
        """run() sets ctx.generated_files["_registry"] to the registry path."""
        registry_path = tmp_path / "workspace" / "_registry.ts"
        mock_write.return_value = registry_path
        ctx = make_context()
        step = RegistryGenerationStep()

        step.run(ctx)

        assert ctx.generated_files["_registry"] == registry_path

    @patch("trellis.bundler.steps.write_registry_ts")
    def test_run_appends_alias_to_esbuild_args(
        self, mock_write: MagicMock, make_context, tmp_path: Path
    ) -> None:
        """run() appends --alias:@trellis/_registry=... to ctx.esbuild_args."""
        registry_path = tmp_path / "workspace" / "_registry.ts"
        mock_write.return_value = registry_path
        ctx = make_context()
        step = RegistryGenerationStep()

        step.run(ctx)

        assert f"--alias:@trellis/_registry={registry_path}" in ctx.esbuild_args

    @patch("trellis.bundler.steps.write_registry_ts")
    def test_run_stores_collected_hash_in_manifest(
        self, mock_write: MagicMock, make_context, tmp_path: Path
    ) -> None:
        """run() stores collected_hash in step manifest metadata."""
        registry_path = tmp_path / "workspace" / "_registry.ts"
        mock_write.return_value = registry_path
        ctx = make_context()
        step = RegistryGenerationStep()

        step.run(ctx)

        step_manifest = ctx.manifest.steps["registry-generation"]
        assert "collected_hash" in step_manifest.metadata
        assert isinstance(step_manifest.metadata["collected_hash"], str)


class TestRegistryGenerationStepShouldBuild:
    """Tests for RegistryGenerationStep's should_build() logic."""

    def test_returns_build_when_no_previous_manifest(self, make_context) -> None:
        """should_build() returns BUILD when no previous manifest exists."""
        ctx = make_context()
        step = RegistryGenerationStep()

        result = step.should_build(ctx, None)

        assert result == ShouldBuild.BUILD

    @patch("trellis.bundler.steps.write_registry_ts")
    def test_returns_skip_when_collected_hash_unchanged(
        self, mock_write: MagicMock, make_context, tmp_path: Path
    ) -> None:
        """should_build() returns SKIP when collected hash matches previous."""
        ctx = make_context()
        step = RegistryGenerationStep()

        # Create the registry file that should_build checks for
        registry_path = ctx.workspace / "_registry.ts"
        registry_path.write_text("// registry")

        # Compute the expected hash
        current_hash = step._compute_collected_hash(ctx)
        prev_manifest = StepManifest(metadata={"collected_hash": current_hash})

        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.SKIP

    def test_returns_build_when_collected_hash_changed(self, make_context) -> None:
        """should_build() returns BUILD when collected hash differs."""
        ctx = make_context()
        step = RegistryGenerationStep()
        prev_manifest = StepManifest(metadata={"collected_hash": "different-hash"})

        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.BUILD


class TestTsconfigStepContract:
    """Tests for TsconfigStep's contract.

    Contract:
    - run() sets ctx.generated_files["tsconfig"] to the tsconfig.json path
    - run() writes valid tsconfig.json to workspace
    - run() stores inputs_hash in manifest metadata
    """

    def test_run_sets_generated_files_tsconfig(self, make_context) -> None:
        """run() sets ctx.generated_files["tsconfig"] to the tsconfig path."""
        ctx = make_context()
        step = TsconfigStep()

        step.run(ctx)

        assert ctx.generated_files["tsconfig"] == ctx.workspace / "tsconfig.json"

    def test_run_writes_tsconfig_file(self, make_context) -> None:
        """run() writes tsconfig.json to workspace."""
        ctx = make_context()
        step = TsconfigStep()

        step.run(ctx)

        tsconfig_path = ctx.workspace / "tsconfig.json"
        assert tsconfig_path.exists()

    def test_run_stores_inputs_hash_in_manifest(self, make_context) -> None:
        """run() stores inputs_hash in step manifest metadata."""
        ctx = make_context()
        step = TsconfigStep()

        step.run(ctx)

        step_manifest = ctx.manifest.steps["tsconfig"]
        assert "inputs_hash" in step_manifest.metadata
        assert isinstance(step_manifest.metadata["inputs_hash"], str)

    def test_run_includes_registry_alias_when_present(self, make_context) -> None:
        """run() includes _registry alias in tsconfig when in generated_files."""
        ctx = make_context()
        registry_path = ctx.workspace / "_registry.ts"
        ctx.generated_files["_registry"] = registry_path
        step = TsconfigStep()

        step.run(ctx)

        tsconfig = json.loads((ctx.workspace / "tsconfig.json").read_text())
        assert "@trellis/_registry" in tsconfig["compilerOptions"]["paths"]


class TestTsconfigStepShouldBuild:
    """Tests for TsconfigStep's should_build() logic."""

    def test_returns_build_when_no_previous_manifest(self, make_context) -> None:
        """should_build() returns BUILD when no previous manifest exists."""
        ctx = make_context()
        step = TsconfigStep()

        result = step.should_build(ctx, None)

        assert result == ShouldBuild.BUILD

    def test_returns_skip_when_inputs_hash_unchanged(self, make_context) -> None:
        """should_build() returns SKIP when inputs hash matches previous."""
        ctx = make_context()
        step = TsconfigStep()

        # Create the tsconfig file that should_build checks for
        tsconfig_path = ctx.workspace / "tsconfig.json"
        tsconfig_path.write_text("{}")

        current_hash = step._compute_inputs_hash(ctx)
        prev_manifest = StepManifest(metadata={"inputs_hash": current_hash})

        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.SKIP

    def test_returns_build_when_inputs_hash_changed(self, make_context) -> None:
        """should_build() returns BUILD when inputs hash differs."""
        ctx = make_context()
        step = TsconfigStep()
        prev_manifest = StepManifest(metadata={"inputs_hash": "different-hash"})

        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.BUILD


class TestIndexHtmlRenderStepContract:
    """Tests for IndexHtmlRenderStep's contract.

    Contract:
    - run() reads ctx.template_context and merges with constructor context
    - run() writes rendered index.html to dist_dir
    - run() stores context_hash in manifest metadata
    - Constructor context takes precedence over ctx.template_context
    """

    def test_run_renders_template_to_dist(self, make_context, tmp_path: Path) -> None:
        """run() renders template to ctx.dist_dir/index.html."""
        template_path = tmp_path / "template.html.j2"
        template_path.write_text("<html><body>Hello</body></html>")
        ctx = make_context()
        step = IndexHtmlRenderStep(template_path)

        step.run(ctx)

        output_path = ctx.dist_dir / "index.html"
        assert output_path.exists()
        assert "Hello" in output_path.read_text()

    def test_run_uses_template_context(self, make_context, tmp_path: Path) -> None:
        """run() uses variables from ctx.template_context."""
        template_path = tmp_path / "template.html.j2"
        template_path.write_text("<html><body>{{ message }}</body></html>")
        ctx = make_context()
        ctx.template_context["message"] = "Hello from context"
        step = IndexHtmlRenderStep(template_path)

        step.run(ctx)

        output = (ctx.dist_dir / "index.html").read_text()
        assert "Hello from context" in output

    def test_run_constructor_context_overrides_template_context(
        self, make_context, tmp_path: Path
    ) -> None:
        """run() uses constructor context over ctx.template_context for same key."""
        template_path = tmp_path / "template.html.j2"
        template_path.write_text("<html><body>{{ message }}</body></html>")
        ctx = make_context()
        ctx.template_context["message"] = "From template_context"
        step = IndexHtmlRenderStep(template_path, context={"message": "From constructor"})

        step.run(ctx)

        output = (ctx.dist_dir / "index.html").read_text()
        assert "From constructor" in output

    def test_run_stores_context_hash_in_manifest(self, make_context, tmp_path: Path) -> None:
        """run() stores context_hash in step manifest metadata."""
        template_path = tmp_path / "template.html.j2"
        template_path.write_text("<html><body>Hello</body></html>")
        ctx = make_context()
        step = IndexHtmlRenderStep(template_path)

        step.run(ctx)

        step_manifest = ctx.manifest.steps["index-html-render"]
        assert "context_hash" in step_manifest.metadata


class TestIndexHtmlRenderStepShouldBuild:
    """Tests for IndexHtmlRenderStep's should_build() logic."""

    def test_returns_build_when_no_previous_manifest(self, make_context, tmp_path: Path) -> None:
        """should_build() returns BUILD when no previous manifest exists."""
        template_path = tmp_path / "template.html.j2"
        template_path.write_text("<html></html>")
        ctx = make_context()
        step = IndexHtmlRenderStep(template_path)

        result = step.should_build(ctx, None)

        assert result == ShouldBuild.BUILD

    def test_returns_build_when_context_hash_changed(self, make_context, tmp_path: Path) -> None:
        """should_build() returns BUILD when context hash differs."""
        template_path = tmp_path / "template.html.j2"
        template_path.write_text("<html></html>")
        output_path = tmp_path / "dist" / "index.html"
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text("<html></html>")

        ctx = make_context()
        step = IndexHtmlRenderStep(template_path)
        prev_manifest = StepManifest(
            source_paths={template_path},
            dest_files={output_path},
            metadata={"context_hash": "different-hash"},
        )

        result = step.should_build(ctx, prev_manifest)

        assert result == ShouldBuild.BUILD
