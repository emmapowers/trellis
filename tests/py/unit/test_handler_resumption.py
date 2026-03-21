"""Tests for handler session resumption via SSR session store."""

from __future__ import annotations

import typing as tp

import pytest

from trellis.core.components.composition import CompositionComponent, component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.rendering.ssr import render_for_ssr
from trellis.platforms.common.handler import MessageHandler, _serialize_patches
from trellis.platforms.common.messages import (
    HelloMessage,
    Message,
    PatchMessage,
)
from trellis.platforms.server.session_store import SessionEntry, SessionStore
from trellis.widgets import Label


class MockHandler(MessageHandler):
    """Test handler with mock transport."""

    def __init__(
        self,
        root_component: tp.Any,
        app_wrapper: tp.Any,
        messages: list[Message] | None = None,
        session_store: SessionStore | None = None,
    ) -> None:
        super().__init__(root_component, app_wrapper, session_store=session_store)
        self._messages = list(messages or [])
        self._sent: list[Message] = []

    async def send_message(self, msg: Message) -> None:
        self._sent.append(msg)

    async def receive_message(self) -> Message:
        return self._messages.pop(0)


@pytest.mark.anyio
class TestHandlerResumption:
    async def test_handle_hello_without_session_id_creates_new(
        self, noop_component: CompositionComponent, app_wrapper: tp.Any
    ) -> None:
        hello = HelloMessage(client_id="c1", system_theme="light", path="/")
        handler = MockHandler(noop_component, app_wrapper, messages=[hello])

        session_id = await handler.handle_hello()

        assert session_id is not None
        assert handler.session is not None
        assert handler.session.root_element_id is None  # Not yet rendered

    async def test_handle_hello_with_session_id_resumes(
        self, noop_component: CompositionComponent, app_wrapper: tp.Any
    ) -> None:
        # First, create a session via SSR
        wrapped = app_wrapper(noop_component, "light", None)
        session = RenderSession(wrapped)
        ssr_result = render_for_ssr(session)
        wire_patches = _serialize_patches(ssr_result.patches, session)

        store = SessionStore(ttl_seconds=30)
        entry = SessionEntry(
            session=session,
            deferred_mounts=ssr_result.deferred_mounts,
            deferred_unmounts=ssr_result.deferred_unmounts,
            patches=wire_patches,
        )
        store.store("ssr-session-1", entry)

        # Client sends hello with the SSR session_id
        hello = HelloMessage(
            client_id="c1", system_theme="light", path="/", session_id="ssr-session-1"
        )
        handler = MockHandler(noop_component, app_wrapper, messages=[hello], session_store=store)

        session_id = await handler.handle_hello()

        # Session should be the same object from SSR
        assert handler.session is session
        assert session_id == "ssr-session-1"
        # Session store should no longer have the entry
        assert store.pop("ssr-session-1") is None

    async def test_handle_hello_with_expired_session_creates_new(
        self, noop_component: CompositionComponent, app_wrapper: tp.Any
    ) -> None:
        store = SessionStore(ttl_seconds=0)  # Instantly expires

        wrapped = app_wrapper(noop_component, "light", None)
        session = RenderSession(wrapped)
        ssr_result = render_for_ssr(session)
        wire_patches = _serialize_patches(ssr_result.patches, session)

        entry = SessionEntry(
            session=session,
            deferred_mounts=ssr_result.deferred_mounts,
            deferred_unmounts=ssr_result.deferred_unmounts,
            patches=wire_patches,
        )
        store.store("expired-session", entry)

        hello = HelloMessage(
            client_id="c1", system_theme="light", path="/", session_id="expired-session"
        )
        handler = MockHandler(noop_component, app_wrapper, messages=[hello], session_store=store)

        session_id = await handler.handle_hello()

        # Should create a new session since the stored one expired
        assert handler.session is not session
        assert session_id != "expired-session"

    async def test_initial_render_skips_when_already_rendered(
        self, noop_component: CompositionComponent, app_wrapper: tp.Any
    ) -> None:
        # Create a session that has already been rendered via SSR
        wrapped = app_wrapper(noop_component, "light", None)
        session = RenderSession(wrapped)
        ssr_result = render_for_ssr(session)
        wire_patches = _serialize_patches(ssr_result.patches, session)

        store = SessionStore(ttl_seconds=30)
        entry = SessionEntry(
            session=session,
            deferred_mounts=ssr_result.deferred_mounts,
            deferred_unmounts=ssr_result.deferred_unmounts,
            patches=wire_patches,
        )
        store.store("ssr-session-2", entry)

        hello = HelloMessage(
            client_id="c1", system_theme="light", path="/", session_id="ssr-session-2"
        )
        handler = MockHandler(noop_component, app_wrapper, messages=[hello], session_store=store)

        await handler.handle_hello()

        # Session was already rendered by SSR, so initial_render should return empty patches
        result = handler.initial_render()
        assert isinstance(result, PatchMessage)
        assert result.patches == []

    async def test_resumed_session_render_loop_works(self, app_wrapper: tp.Any) -> None:
        """After resuming an SSR session, dirty elements should still re-render."""

        @component
        def App() -> None:
            Label(text="hello")

        # SSR render
        wrapped = app_wrapper(App, "light", None)
        session = RenderSession(wrapped)
        ssr_result = render_for_ssr(session)
        wire_patches = _serialize_patches(ssr_result.patches, session)

        store = SessionStore(ttl_seconds=30)
        entry = SessionEntry(
            session=session,
            deferred_mounts=ssr_result.deferred_mounts,
            deferred_unmounts=ssr_result.deferred_unmounts,
            patches=wire_patches,
        )
        store.store("ssr-session-3", entry)

        hello = HelloMessage(
            client_id="c1", system_theme="light", path="/", session_id="ssr-session-3"
        )
        handler = MockHandler(App, app_wrapper, messages=[hello], session_store=store)

        await handler.handle_hello()
        handler.initial_render()

        # Mark root dirty to force re-render
        session.dirty.mark(session.root_element_id)
        patches = render(session)
        assert patches is not None
