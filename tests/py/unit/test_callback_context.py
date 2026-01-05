"""Unit tests for callback context module."""

import threading
from dataclasses import dataclass

import pytest

from trellis.core.callback_context import (
    callback_context,
    get_callback_element_state,
    get_callback_session,
)
from trellis.core.components.composition import component
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful


class TestCallbackContext:
    """Tests for callback context management."""

    def test_get_element_state_without_context_raises(self) -> None:
        """Getting element state without active callback context raises RuntimeError."""
        with pytest.raises(RuntimeError, match="outside of callback context"):
            get_callback_element_state()

    def test_get_session_without_context_raises(self) -> None:
        """Getting session without active callback context raises RuntimeError."""
        with pytest.raises(RuntimeError, match="outside of callback context"):
            get_callback_session()

    def test_callback_context_provides_element_state(self) -> None:
        """callback_context provides access to element state."""

        @component
        def App() -> None:
            pass

        session = RenderSession(App)
        node_id = "test-node-1"

        # Create element state for this node
        element_state = session.states.get_or_create(node_id)
        element_state.context[str] = "test-context-value"

        with callback_context(session, node_id):
            state = get_callback_element_state()
            assert state is element_state
            assert state.context[str] == "test-context-value"

    def test_callback_context_provides_session(self) -> None:
        """callback_context provides access to session."""

        @component
        def App() -> None:
            pass

        session = RenderSession(App)
        node_id = "test-node-1"
        session.states.get_or_create(node_id)

        with callback_context(session, node_id):
            retrieved_session = get_callback_session()
            assert retrieved_session is session

    def test_context_cleared_after_exit(self) -> None:
        """Callback context is cleared after exiting the context manager."""

        @component
        def App() -> None:
            pass

        session = RenderSession(App)
        node_id = "test-node-1"
        session.states.get_or_create(node_id)

        with callback_context(session, node_id):
            # Inside context - should work
            get_callback_element_state()

        # Outside context - should raise
        with pytest.raises(RuntimeError, match="outside of callback context"):
            get_callback_element_state()


class TestCallbackContextLocking:
    """Tests for callback context session locking."""

    def test_callback_context_holds_session_lock(self) -> None:
        """callback_context acquires the session lock.

        Note: RLock allows the same thread to re-acquire, so we test
        from a separate thread to verify the lock is held.
        """

        @component
        def App() -> None:
            pass

        session = RenderSession(App)
        node_id = "test-node-1"
        session.states.get_or_create(node_id)

        # Track if other thread could acquire lock
        other_thread_acquired: list[bool] = []

        def try_acquire() -> None:
            acquired = session.lock.acquire(blocking=False)
            other_thread_acquired.append(acquired)
            if acquired:
                session.lock.release()

        with callback_context(session, node_id):
            # Try to acquire from another thread - should fail
            thread = threading.Thread(target=try_acquire)
            thread.start()
            thread.join()

            assert other_thread_acquired == [False], "Other thread should not acquire lock"

        # After context, other thread should be able to acquire
        other_thread_acquired.clear()
        thread = threading.Thread(target=try_acquire)
        thread.start()
        thread.join()

        assert other_thread_acquired == [True], "Other thread should acquire lock after context"

    def test_lock_released_on_exception(self) -> None:
        """Session lock is released even if exception occurs in callback."""

        @component
        def App() -> None:
            pass

        session = RenderSession(App)
        node_id = "test-node-1"
        session.states.get_or_create(node_id)

        with pytest.raises(ValueError, match="test error"):
            with callback_context(session, node_id):
                raise ValueError("test error")

        # Lock should be released after exception
        assert session.lock.acquire(blocking=False)
        session.lock.release()


class TestFromContextInCallback:
    """Tests for Stateful.from_context() working in callback context."""

    def test_from_context_works_in_callback_context(self) -> None:
        """from_context() returns state when in callback context."""

        @dataclass(kw_only=True)
        class TestState(Stateful):
            value: str = "test"

        @component
        def App() -> None:
            pass

        session = RenderSession(App)
        node_id = "test-node-1"

        # Set up context on the node (simulating what __enter__ does during render)
        element_state = session.states.get_or_create(node_id)
        test_state = TestState(value="hello")
        element_state.context[TestState] = test_state

        # Without callback_context, from_context should fail
        with pytest.raises(RuntimeError, match="outside of render context"):
            TestState.from_context()

        # With callback_context, from_context should work
        with callback_context(session, node_id):
            result = TestState.from_context()
            assert result is test_state
            assert result.value == "hello"

    def test_from_context_walks_parent_chain_in_callback(self) -> None:
        """from_context() walks up parent chain in callback context."""

        @dataclass(kw_only=True)
        class ParentState(Stateful):
            name: str = ""

        @component
        def App() -> None:
            pass

        session = RenderSession(App)

        # Set up parent-child relationship
        parent_id = "parent-node"
        child_id = "child-node"

        parent_state = session.states.get_or_create(parent_id)
        child_state = session.states.get_or_create(child_id)
        child_state.parent_id = parent_id

        # Put context on parent
        state_instance = ParentState(name="from-parent")
        parent_state.context[ParentState] = state_instance

        # Callback from child should find parent's context
        with callback_context(session, child_id):
            result = ParentState.from_context()
            assert result is state_instance
            assert result.name == "from-parent"

    def test_from_context_returns_default_in_callback(self) -> None:
        """from_context() returns default when state not found in callback."""

        @dataclass(kw_only=True)
        class MissingState(Stateful):
            pass

        @component
        def App() -> None:
            pass

        session = RenderSession(App)
        node_id = "test-node"
        session.states.get_or_create(node_id)

        with callback_context(session, node_id):
            # With default=None, should return None
            result = MissingState.from_context(default=None)
            assert result is None

            # Without default, should raise LookupError
            with pytest.raises(LookupError, match="No MissingState found"):
                MissingState.from_context()
