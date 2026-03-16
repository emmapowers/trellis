"""Tests for SSR rendering: render_for_ssr and execute_deferred_hooks."""

from __future__ import annotations

from dataclasses import dataclass

from trellis.core.components.composition import CompositionComponent, component
from trellis.core.rendering.patches import RenderAddPatch
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession, set_render_session
from trellis.core.rendering.ssr import SSRRenderResult, execute_deferred_hooks, render_for_ssr
from trellis.core.state.stateful import Stateful
from trellis.platforms.common.serialization import serialize_element
from trellis.widgets import Label


class TestRenderForSSR:
    def test_returns_ssr_render_result(self, noop_component: CompositionComponent) -> None:
        session = RenderSession(noop_component)
        result = render_for_ssr(session)
        assert isinstance(result, SSRRenderResult)

    def test_returns_patches(self, noop_component: CompositionComponent) -> None:
        session = RenderSession(noop_component)
        result = render_for_ssr(session)
        assert len(result.patches) > 0
        assert isinstance(result.patches[0], RenderAddPatch)

    def test_sets_root_element_id(self, noop_component: CompositionComponent) -> None:
        session = RenderSession(noop_component)
        render_for_ssr(session)
        assert session.root_element_id is not None

    def test_defers_mount_hooks(self) -> None:
        mount_called = False

        @dataclass(kw_only=True)
        class TrackingState(Stateful):
            value: int = 0

            def on_mount(self) -> None:
                nonlocal mount_called
                mount_called = True

        @component
        def App() -> None:
            TrackingState()

        session = RenderSession(App)
        result = render_for_ssr(session)

        assert not mount_called, "on_mount should NOT be called during render_for_ssr"
        assert len(result.deferred_mounts) > 0, "deferred_mounts should contain element IDs"

    def test_tree_matches_regular_render(self) -> None:
        @component
        def App() -> None:
            Label(text="Hello SSR")

        # SSR render
        ssr_session = RenderSession(App)
        render_for_ssr(ssr_session)
        ssr_tree = serialize_element(ssr_session.root_element, ssr_session)

        # Regular render
        regular_session = RenderSession(App)
        set_render_session(regular_session)
        render(regular_session)
        regular_tree = serialize_element(regular_session.root_element, regular_session)

        assert ssr_tree == regular_tree


class TestExecuteDeferredHooks:
    def test_runs_mounts(self) -> None:
        mount_called = False

        @dataclass(kw_only=True)
        class TrackingState(Stateful):
            value: int = 0

            def on_mount(self) -> None:
                nonlocal mount_called
                mount_called = True

        @component
        def App() -> None:
            TrackingState()

        session = RenderSession(App)
        result = render_for_ssr(session)

        assert not mount_called
        execute_deferred_hooks(session, result.deferred_mounts, result.deferred_unmounts)
        assert mount_called, "on_mount should be called by execute_deferred_hooks"

    def test_handles_empty_unmount_list(self) -> None:
        """execute_deferred_hooks handles empty unmount lists gracefully."""

        @component
        def App() -> None:
            Label(text="hello")

        session = RenderSession(App)
        result = render_for_ssr(session)

        # Should not raise
        execute_deferred_hooks(session, result.deferred_mounts, result.deferred_unmounts)

    def test_session_functional_after_deferred_hooks(self) -> None:
        """After executing deferred hooks, the session should work normally."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 0

        @component
        def App() -> None:
            CounterState()
            Label(text="hello")

        session = RenderSession(App)
        result = render_for_ssr(session)
        execute_deferred_hooks(session, result.deferred_mounts, result.deferred_unmounts)

        # Verify the session can still do incremental renders
        # Mark root dirty to force re-render
        set_render_session(session)
        session.dirty.mark(session.root_element_id)
        patches = render(session)
        assert patches is not None
