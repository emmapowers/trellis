"""Desktop platform implementation for development using PyTauri."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.console import Console

from trellis.app.apploader import get_dist_dir
from trellis.platforms.desktop.standalone_platform import DesktopStandalonePlatform

if TYPE_CHECKING:
    from trellis.app.config import Config
    from trellis.bundler import BuildConfig
    from trellis.core.rendering.element import Element
    from trellis.platforms.common.handler import AppWrapper

_console = Console()


def _print_startup_banner(title: str) -> None:
    """Print a colorful startup banner."""
    _console.print()
    _console.print("  [bold green]🌿 Trellis[/bold green] [dim]desktop app[/dim]")
    _console.print()
    _console.print(f"  [bold]➜[/bold]  [cyan]Window:[/cyan]   {title}")
    _console.print()
    _console.print("  [dim]Press Ctrl+C or close window to exit[/dim]")
    _console.print()


def _build_tauri_config_override(
    *, dist_path: str, window_title: str, window_width: int, window_height: int
) -> dict[str, Any]:
    """Build runtime Tauri config overrides for desktop window and frontend assets."""
    return {
        "build": {"frontendDist": dist_path},
        "app": {
            "windows": [
                {
                    "title": window_title,
                    "width": window_width,
                    "height": window_height,
                    "visible": False,
                }
            ]
        },
    }


class DesktopPlatform(DesktopStandalonePlatform):
    """Desktop platform for development.

    Extends DesktopStandalonePlatform with build configuration, hot reload,
    and a startup banner. Used when running `trellis run --desktop`.
    """

    def get_build_config(self, config: Config) -> BuildConfig:
        """Get build configuration for this platform.

        Args:
            config: Application configuration

        Returns:
            BuildConfig with entry point and build steps
        """
        # Bundler imports are local to this method so importing DesktopPlatform
        # does not pull in the entire bundler module tree.
        from trellis.bundler import (  # noqa: PLC0415
            BuildConfig,
            BundleBuildStep,
            IconAssetStep,
            IndexHtmlRenderStep,
            PackageInstallStep,
            RegistryGenerationStep,
            StaticFileCopyStep,
        )

        entry_point = Path(__file__).parent / "client" / "src" / "main.tsx"
        template_path = Path(__file__).parent / "client" / "src" / "index.html.j2"
        return BuildConfig(
            entry_point=entry_point,
            steps=[
                PackageInstallStep(),
                RegistryGenerationStep(),
                BundleBuildStep(output_name="bundle"),
                StaticFileCopyStep(),
                IconAssetStep(icon_path=config.icon, include_icns=True),
                IndexHtmlRenderStep(template_path, {"title": config.title}),
            ],
        )

    def _get_config_override(self, **kwargs: Any) -> dict[str, Any] | None:
        """Return Tauri config overrides for dev mode (frontendDist + window metadata)."""
        dist_path = str(get_dist_dir())
        return _build_tauri_config_override(
            dist_path=dist_path,
            window_title=kwargs.get("window_title", "Trellis App"),
            window_width=kwargs.get("window_width", 1024),
            window_height=kwargs.get("window_height", 768),
        )

    async def run(
        self,
        root_component: Callable[[], Element],
        app_wrapper: AppWrapper,
        *,
        window_title: str = "Trellis App",
        window_width: int = 1024,
        window_height: int = 768,
        batch_delay: float = 1.0 / 30,
        hot_reload: bool = True,
        **_kwargs: Any,
    ) -> None:
        """Start PyTauri desktop application in dev mode.

        Prints a startup banner, then delegates to the standalone runtime.
        Hot reload defaults to True in dev mode.
        """
        _print_startup_banner(window_title)
        await super().run(
            root_component,
            app_wrapper,
            window_title=window_title,
            window_width=window_width,
            window_height=window_height,
            batch_delay=batch_delay,
            hot_reload=hot_reload,
            **_kwargs,
        )


__all__ = ["DesktopPlatform"]
