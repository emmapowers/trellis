"""Tests for SSR orchestrator."""

from __future__ import annotations

import typing as tp

import pytest

from trellis.core.components.composition import CompositionComponent, component
from trellis.platforms.server.session_store import SessionStore
from trellis.platforms.server.ssr import SSROrchestrator
from trellis.widgets import Label


@pytest.fixture
def ssr_orchestrator(noop_component: CompositionComponent, app_wrapper: tp.Any) -> SSROrchestrator:
    store = SessionStore(ttl_seconds=30)
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

    store = SessionStore(ttl_seconds=30)
    return SSROrchestrator(
        root_component=App,
        app_wrapper=app_wrapper,
        session_store=store,
        ssr_renderer=None,
    )


class TestSSROrchestrator:
    def test_render_to_response_returns_html(self, label_orchestrator: SSROrchestrator) -> None:
        html_template = (
            '<!DOCTYPE html><html><body><div id="root"><!--ssr-outlet--></div></body></html>'
        )
        result = label_orchestrator.render_to_response(
            path="/", system_theme="light", theme_mode=None, html_template=html_template
        )
        assert "<!DOCTYPE html>" in result

    def test_render_to_response_has_dehydration_script(
        self, label_orchestrator: SSROrchestrator
    ) -> None:
        html_template = (
            '<!DOCTYPE html><html><body><div id="root"><!--ssr-outlet--></div></body></html>'
        )
        result = label_orchestrator.render_to_response(
            path="/", system_theme="light", theme_mode=None, html_template=html_template
        )
        assert "window.__TRELLIS_SSR__" in result

    def test_render_to_response_stores_session(self, label_orchestrator: SSROrchestrator) -> None:
        html_template = (
            '<!DOCTYPE html><html><body><div id="root"><!--ssr-outlet--></div></body></html>'
        )
        result = label_orchestrator.render_to_response(
            path="/", system_theme="light", theme_mode=None, html_template=html_template
        )
        # The session store should have an entry - extract session_id from the HTML
        assert "sessionId" in result

    def test_render_to_response_falls_back_without_renderer(
        self, label_orchestrator: SSROrchestrator
    ) -> None:
        """Without an SSR renderer, dehydration data is still embedded but no rendered HTML."""
        html_template = (
            '<!DOCTYPE html><html><body><div id="root"><!--ssr-outlet--></div></body></html>'
        )
        result = label_orchestrator.render_to_response(
            path="/", system_theme="light", theme_mode=None, html_template=html_template
        )
        # Should still have dehydration script
        assert "window.__TRELLIS_SSR__" in result
        # The SSR outlet should be replaced (empty since no renderer)
        assert "<!--ssr-outlet-->" not in result

    def test_dehydration_data_contains_session_id(
        self, label_orchestrator: SSROrchestrator
    ) -> None:
        html_template = (
            '<!DOCTYPE html><html><body><div id="root"><!--ssr-outlet--></div></body></html>'
        )
        result = label_orchestrator.render_to_response(
            path="/", system_theme="light", theme_mode=None, html_template=html_template
        )
        # Session ID should be in dehydration data
        assert '"sessionId"' in result or "'sessionId'" in result

    def test_dehydration_data_contains_patches(self, label_orchestrator: SSROrchestrator) -> None:
        html_template = (
            '<!DOCTYPE html><html><body><div id="root"><!--ssr-outlet--></div></body></html>'
        )
        result = label_orchestrator.render_to_response(
            path="/", system_theme="light", theme_mode=None, html_template=html_template
        )
        assert '"patches"' in result or "'patches'" in result
