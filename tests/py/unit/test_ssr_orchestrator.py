"""Tests for SSR orchestrator."""

from __future__ import annotations

import re
import typing as tp

import pytest

from trellis.core.components.composition import CompositionComponent, component
from trellis.platforms.server.session_store import SessionStore
from trellis.platforms.server.ssr import SSROrchestrator
from trellis.widgets import Label


@pytest.fixture
def ssr_orchestrator(noop_component: CompositionComponent, app_wrapper: tp.Any) -> SSROrchestrator:
    store = SessionStore(ttl_seconds=300)
    return SSROrchestrator(
        root_component=noop_component,
        app_wrapper=app_wrapper,
        session_store=store,
        ssr_renderer=None,
    )


@pytest.fixture
def label_orchestrator(app_wrapper: tp.Any) -> SSROrchestrator:
    @component
    def App() -> None:
        Label(text="Hello SSR")

    store = SessionStore(ttl_seconds=300)
    return SSROrchestrator(
        root_component=App,
        app_wrapper=app_wrapper,
        session_store=store,
        ssr_renderer=None,
    )


_HTML_TEMPLATE = '<!DOCTYPE html><html><body><div id="root"><!--ssr-outlet--></div></body></html>'


class TestSSROrchestrator:
    def test_render_to_response_returns_html(self, label_orchestrator: SSROrchestrator) -> None:
        result = label_orchestrator.render_to_response(
            path="/", system_theme="light", theme_mode=None, html_template=_HTML_TEMPLATE
        )
        assert "<!DOCTYPE html>" in result

    def test_render_to_response_has_dehydration_script(
        self, label_orchestrator: SSROrchestrator
    ) -> None:
        result = label_orchestrator.render_to_response(
            path="/", system_theme="light", theme_mode=None, html_template=_HTML_TEMPLATE
        )
        assert "window.__TRELLIS_SSR__" in result

    def test_render_to_response_stores_session(self, label_orchestrator: SSROrchestrator) -> None:
        result = label_orchestrator.render_to_response(
            path="/", system_theme="light", theme_mode=None, html_template=_HTML_TEMPLATE
        )
        assert "sessionId" in result

    def test_render_to_response_falls_back_without_renderer(
        self, label_orchestrator: SSROrchestrator
    ) -> None:
        """Without an SSR renderer, dehydration data is still embedded but no rendered HTML."""
        result = label_orchestrator.render_to_response(
            path="/", system_theme="light", theme_mode=None, html_template=_HTML_TEMPLATE
        )
        assert "window.__TRELLIS_SSR__" in result
        assert "<!--ssr-outlet-->" not in result

    def test_dehydration_data_contains_session_id(
        self, label_orchestrator: SSROrchestrator
    ) -> None:
        result = label_orchestrator.render_to_response(
            path="/", system_theme="light", theme_mode=None, html_template=_HTML_TEMPLATE
        )
        assert '"sessionId"' in result

    def test_dehydration_data_contains_patches(self, label_orchestrator: SSROrchestrator) -> None:
        result = label_orchestrator.render_to_response(
            path="/", system_theme="light", theme_mode=None, html_template=_HTML_TEMPLATE
        )
        assert '"patches"' in result

    def test_second_request_same_route_reuses_cache(
        self, label_orchestrator: SSROrchestrator
    ) -> None:
        """Two requests for the same route+theme should produce different session IDs
        (fresh dehydration data) even though the rendered HTML is cached."""
        results = []
        for _ in range(2):
            html = label_orchestrator.render_to_response(
                path="/", system_theme="light", theme_mode=None, html_template=_HTML_TEMPLATE
            )
            results.append(html)

        # Both should have dehydration scripts
        for html in results:
            assert "window.__TRELLIS_SSR__" in html

        # Extract session IDs — they should differ
        session_ids = []
        for html in results:
            match = re.search(r'"sessionId"\s*:\s*"([^"]+)"', html)
            assert match is not None
            session_ids.append(match.group(1))

        assert session_ids[0] != session_ids[1]
