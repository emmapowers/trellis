"""Tests for SSRPreRenderStep build step."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from trellis.bundler.steps import SSRPreRenderStep


@pytest.fixture
def step() -> SSRPreRenderStep:
    return SSRPreRenderStep()


@pytest.fixture
def build_ctx(tmp_path: Path) -> MagicMock:
    ctx = MagicMock()
    ctx.dist_dir = tmp_path
    ctx.template_context = {}
    return ctx


def _mock_ssr_run(
    build_ctx: MagicMock,
    step: SSRPreRenderStep,
    *,
    render_return: str | None = "<div>rendered</div>",
    render_side_effect: Exception | None = None,
    app: MagicMock | None = None,
    app_initially_none: bool = False,
) -> tuple[MagicMock, MagicMock, MagicMock]:
    """Run step with standard mocking, returning (mock_app, mock_renderer, mock_apploader)."""
    mock_app = app or MagicMock()
    mock_renderer = MagicMock()
    if render_side_effect:
        mock_renderer.render.side_effect = render_side_effect
    else:
        mock_renderer.render.return_value = render_return

    mock_apploader = MagicMock()
    if app_initially_none:
        mock_apploader.app = None

        def set_app() -> None:
            mock_apploader.app = mock_app

        mock_apploader.load_app.side_effect = set_app
    else:
        mock_apploader.app = mock_app

    mock_session = MagicMock()
    mock_session.root_element = MagicMock()

    mock_ssr_result = MagicMock(patches=[])

    with (
        patch("trellis.app.apploader.get_apploader", return_value=mock_apploader),
        patch("trellis.core.rendering.session.RenderSession", return_value=mock_session),
        patch("trellis.core.rendering.ssr.render_for_ssr", return_value=mock_ssr_result),
        patch("trellis.platforms.common.handler._serialize_patches", return_value=[]),
        patch("trellis.platforms.common.serialization.serialize_element", return_value={}),
        patch(
            "trellis.platforms.common.ssr_utils.build_dehydration_data",
            return_value='{"serverVersion":"0.0.0","patches":[]}',
        ),
        patch("trellis.platforms.server.ssr_renderer.SSRRenderer", return_value=mock_renderer),
    ):
        step.run(build_ctx)

    return mock_app, mock_renderer, mock_apploader


class TestSSRPreRenderStep:
    """Tests for the SSRPreRenderStep build step."""

    def test_step_name(self, step: SSRPreRenderStep) -> None:
        assert step.name == "ssr-pre-render"

    def test_skips_when_no_ssr_bundle(self, step: SSRPreRenderStep, build_ctx: MagicMock) -> None:
        """When ssr.js doesn't exist in dist_dir, logs warning and returns."""
        step.run(build_ctx)
        assert "ssr_enabled" not in build_ctx.template_context

    def test_renders_once(self, step: SSRPreRenderStep, build_ctx: MagicMock) -> None:
        """Renders the app once (CSS variables handle both themes)."""
        (build_ctx.dist_dir / "ssr.js").touch()

        mock_app, mock_renderer, _ = _mock_ssr_run(build_ctx, step)

        mock_app.get_wrapped_top.assert_called_once()
        mock_renderer.render.assert_called_once()

    def test_populates_template_context(self, step: SSRPreRenderStep, build_ctx: MagicMock) -> None:
        """Sets ssr_enabled, ssr_html, and ssr_data in template context."""
        (build_ctx.dist_dir / "ssr.js").touch()

        _mock_ssr_run(build_ctx, step)

        ctx = build_ctx.template_context
        assert ctx["ssr_enabled"] is True
        assert "ssr_html" in ctx
        assert "ssr_data" in ctx

    def test_stops_renderer_on_exception(
        self, step: SSRPreRenderStep, build_ctx: MagicMock
    ) -> None:
        """renderer.stop() is called even when rendering raises."""
        (build_ctx.dist_dir / "ssr.js").touch()

        mock_renderer = MagicMock()
        mock_renderer.render.side_effect = RuntimeError("render failed")
        mock_session = MagicMock()
        mock_session.root_element = MagicMock()

        with (
            patch(
                "trellis.app.apploader.get_apploader",
                return_value=MagicMock(app=MagicMock()),
            ),
            patch(
                "trellis.core.rendering.session.RenderSession",
                return_value=mock_session,
            ),
            patch(
                "trellis.core.rendering.ssr.render_for_ssr",
                return_value=MagicMock(patches=[]),
            ),
            patch("trellis.platforms.common.handler._serialize_patches", return_value=[]),
            patch("trellis.platforms.common.serialization.serialize_element", return_value={}),
            patch(
                "trellis.platforms.common.ssr_utils.build_dehydration_data",
                return_value="{}",
            ),
            patch(
                "trellis.platforms.server.ssr_renderer.SSRRenderer",
                return_value=mock_renderer,
            ),
            pytest.raises(RuntimeError, match="render failed"),
        ):
            step.run(build_ctx)

        mock_renderer.stop.assert_called_once()

    def test_loads_app_if_not_loaded(self, step: SSRPreRenderStep, build_ctx: MagicMock) -> None:
        """Calls apploader.load_app() when app is None."""
        (build_ctx.dist_dir / "ssr.js").touch()

        _, _, mock_apploader = _mock_ssr_run(build_ctx, step, app_initially_none=True)

        mock_apploader.load_app.assert_called_once()
