"""Tests for BuildConfig dataclass and platform get_build_config() methods."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import requires_pytauri
from trellis.app.apploader import AppLoader, set_apploader
from trellis.app.config import Config
from trellis.app.configvars import cli_context
from trellis.bundler.build_config import BuildConfig
from trellis.bundler.steps import (
    BundleBuildStep,
    DeclarationStep,
    IconAssetStep,
    IndexHtmlRenderStep,
    PackageInstallStep,
    RegistryGenerationStep,
    StaticFileCopyStep,
    TsconfigStep,
)
from trellis.platforms.browser.build_steps import (
    DependencyResolveStep,
    PyodideWorkerBuildStep,
    WheelBuildStep,
    WheelBundleStep,
)
from trellis.platforms.browser.serve_platform import BrowserServePlatform
from trellis.platforms.server.platform import ServerPlatform


class TestBuildConfig:
    """Tests for BuildConfig dataclass."""

    def test_creation(self) -> None:
        """BuildConfig can be created with entry_point and steps."""
        config = BuildConfig(
            entry_point=Path("/some/main.tsx"),
            steps=[PackageInstallStep()],
        )
        assert config.entry_point == Path("/some/main.tsx")
        assert len(config.steps) == 1

    def test_frozen(self) -> None:
        """BuildConfig is immutable (frozen)."""
        config = BuildConfig(
            entry_point=Path("/some/main.tsx"),
            steps=[],
        )
        with pytest.raises(AttributeError):
            config.entry_point = Path("/other.tsx")  # type: ignore[misc]


class TestServerGetBuildConfig:
    """Tests for ServerPlatform.get_build_config()."""

    def test_entry_point(self) -> None:
        """Entry point is server/client/src/main.tsx."""
        platform = ServerPlatform()
        config = Config(name="myapp", module="main")

        build_config = platform.get_build_config(config)

        assert build_config.entry_point.name == "main.tsx"
        assert "server" in str(build_config.entry_point)

    def test_step_types_and_order(self) -> None:
        """Steps are correct types in correct order."""
        platform = ServerPlatform()
        config = Config(name="myapp", module="main")

        build_config = platform.get_build_config(config)

        step_types = [type(s) for s in build_config.steps]
        assert step_types == [
            PackageInstallStep,
            RegistryGenerationStep,
            BundleBuildStep,
            StaticFileCopyStep,
            IconAssetStep,
            IndexHtmlRenderStep,
        ]

    def test_template_vars_include_static_path_and_title(self) -> None:
        """IndexHtmlRenderStep has static_path and title from config."""
        platform = ServerPlatform()
        config = Config(name="myapp", module="main")

        build_config = platform.get_build_config(config)

        html_step = build_config.steps[-1]
        assert isinstance(html_step, IndexHtmlRenderStep)
        assert html_step._context["static_path"] == "/static"
        assert html_step._context["title"] == "myapp"

    def test_title_from_config(self) -> None:
        """Title in template context comes from config.title."""
        platform = ServerPlatform()
        config = Config(name="myapp", module="main", title="Custom Title")

        build_config = platform.get_build_config(config)

        html_step = build_config.steps[-1]
        assert isinstance(html_step, IndexHtmlRenderStep)
        assert html_step._context["title"] == "Custom Title"


@requires_pytauri
class TestDesktopGetBuildConfig:
    """Tests for DesktopPlatform.get_build_config()."""

    def test_entry_point(self) -> None:
        """Entry point is desktop/client/src/main.tsx."""
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        platform = DesktopPlatform()
        config = Config(name="myapp", module="main")

        build_config = platform.get_build_config(config)

        assert build_config.entry_point.name == "main.tsx"
        assert "desktop" in str(build_config.entry_point)

    def test_step_types_and_order(self) -> None:
        """Steps are correct types in correct order."""
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        platform = DesktopPlatform()
        config = Config(name="myapp", module="main")

        build_config = platform.get_build_config(config)

        step_types = [type(s) for s in build_config.steps]
        assert step_types == [
            PackageInstallStep,
            RegistryGenerationStep,
            BundleBuildStep,
            StaticFileCopyStep,
            IconAssetStep,
            IndexHtmlRenderStep,
        ]

    def test_template_vars_include_title(self) -> None:
        """IndexHtmlRenderStep has title from config."""
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        platform = DesktopPlatform()
        config = Config(name="myapp", module="main", title="Desktop App")

        build_config = platform.get_build_config(config)

        html_step = build_config.steps[-1]
        assert isinstance(html_step, IndexHtmlRenderStep)
        assert html_step._context["title"] == "Desktop App"


class TestBrowserServeGetBuildConfig:
    """Tests for BrowserServePlatform.get_build_config()."""

    @pytest.fixture(autouse=True)
    def _setup_apploader(self, tmp_path: Path, reset_apploader: None) -> None:
        """Set up a global apploader so get_app_root() works."""
        set_apploader(AppLoader(tmp_path))

    def test_app_mode_entry_point(self) -> None:
        """App mode entry point is browser/client/src/main.tsx."""
        platform = BrowserServePlatform()
        config = Config(name="myapp", module="main")

        build_config = platform.get_build_config(config)

        assert build_config.entry_point.name == "main.tsx"
        assert "browser" in str(build_config.entry_point)

    def test_app_mode_step_types_and_order(self) -> None:
        """App mode has correct steps including browser-specific ones."""
        platform = BrowserServePlatform()
        config = Config(name="myapp", module="main")

        build_config = platform.get_build_config(config)

        step_types = [type(s) for s in build_config.steps]
        assert step_types == [
            PackageInstallStep,
            RegistryGenerationStep,
            WheelBuildStep,
            DependencyResolveStep,
            WheelBundleStep,
            PyodideWorkerBuildStep,
            BundleBuildStep,
            StaticFileCopyStep,
            IconAssetStep,
            IndexHtmlRenderStep,
        ]

    def test_app_mode_template_vars(self) -> None:
        """App mode IndexHtmlRenderStep has title and routing_mode from config."""
        platform = BrowserServePlatform()
        config = Config(name="myapp", module="main", title="Browser App")

        build_config = platform.get_build_config(config)

        html_step = build_config.steps[-1]
        assert isinstance(html_step, IndexHtmlRenderStep)
        assert html_step._context["title"] == "Browser App"
        assert html_step._context["routing_mode"] == "hash"

    def test_library_mode_entry_point(self) -> None:
        """Library mode entry point is browser/client/src/index.ts."""
        platform = BrowserServePlatform()
        with cli_context({"library": True}):
            config = Config(name="myapp", module="main")

        build_config = platform.get_build_config(config)

        assert build_config.entry_point.name == "index.ts"
        assert "browser" in str(build_config.entry_point)

    def test_library_mode_step_types_and_order(self) -> None:
        """Library mode has correct steps including TsconfigStep, DeclarationStep."""
        platform = BrowserServePlatform()
        with cli_context({"library": True}):
            config = Config(name="myapp", module="main")

        build_config = platform.get_build_config(config)

        step_types = [type(s) for s in build_config.steps]
        assert step_types == [
            PackageInstallStep,
            RegistryGenerationStep,
            TsconfigStep,
            WheelBuildStep,
            DependencyResolveStep,
            WheelBundleStep,
            PyodideWorkerBuildStep,
            BundleBuildStep,
            DeclarationStep,
            StaticFileCopyStep,
        ]

    def test_library_mode_no_index_html(self) -> None:
        """Library mode does not include IndexHtmlRenderStep."""
        platform = BrowserServePlatform()
        with cli_context({"library": True}):
            config = Config(name="myapp", module="main")

        build_config = platform.get_build_config(config)

        assert not any(isinstance(s, IndexHtmlRenderStep) for s in build_config.steps)
        assert not any(isinstance(s, IconAssetStep) for s in build_config.steps)
