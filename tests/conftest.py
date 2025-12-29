"""Pytest configuration and shared fixtures for Trellis tests."""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass, field
from unittest.mock import Mock

import pytest

from trellis.core.components.composition import CompositionComponent
from trellis.core.rendering.element import Element
from trellis.core.rendering.patches import RenderPatch
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful
from trellis.platforms.common.serialization import serialize_node

# =============================================================================
# Marker Configuration
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks test as slow (>1s or subprocess)")
    config.addinivalue_line("markers", "network: requires network access")
    config.addinivalue_line("markers", "platform: cross-platform protocol tests")


# =============================================================================
# Component Fixtures
# =============================================================================


@pytest.fixture
def make_component() -> tp.Callable[[str], CompositionComponent]:
    """Factory to create simple test components.

    Usage:
        def test_something(make_component):
            comp = make_component("MyComp")
            # comp.name == "MyComp"
    """

    def _make(name: str) -> CompositionComponent:
        return CompositionComponent(name=name, render_func=lambda: None)

    return _make


@pytest.fixture
def noop_component() -> CompositionComponent:
    """A pre-made component that does nothing, for tests that need a simple root."""
    return CompositionComponent(name="NoopRoot", render_func=lambda: None)


# =============================================================================
# Session Fixtures
# =============================================================================


@pytest.fixture
def render_session(noop_component: CompositionComponent) -> RenderSession:
    """Fresh RenderSession with a noop root for each test.

    Usage:
        def test_session_behavior(render_session):
            # render_session is ready to use
            render(render_session)
    """
    return RenderSession(noop_component)


@dataclass
class RenderResult:
    """Result of rendering a component, with convenient accessors."""

    session: RenderSession
    patches: list[RenderPatch]
    tree: dict[str, tp.Any]

    @property
    def root_element(self) -> Element:
        """The root element after rendering."""
        return self.session.root_element


@pytest.fixture
def rendered() -> tp.Callable[[CompositionComponent], RenderResult]:
    """Render a component and return (session, patches, tree).

    Usage:
        def test_component_renders(rendered):
            @component
            def MyComp():
                Label(text="Hello")

            result = rendered(MyComp)
            assert result.tree["component"] == "MyComp"
            assert len(result.root_element.child_ids) == 1
    """

    def _render(root: CompositionComponent) -> RenderResult:
        session = RenderSession(root)
        patches = render(session)
        tree = serialize_node(session.root_element, session)
        return RenderResult(session=session, patches=patches, tree=tree)

    return _render


# =============================================================================
# Patch Capture Fixture
# =============================================================================


@dataclass
class PatchCapture:
    """Captures patches from multiple render calls."""

    session: RenderSession
    all_patches: list[list[RenderPatch]] = field(default_factory=list)

    def render(self) -> list[RenderPatch]:
        """Render and capture patches."""
        patches = render(self.session)
        self.all_patches.append(patches)
        return patches

    def render_dirty(self) -> list[RenderPatch]:
        """Re-render dirty nodes and capture patches."""
        from trellis.core.rendering.render import render_dirty

        patches = render_dirty(self.session)
        self.all_patches.append(patches)
        return patches

    @property
    def last_patches(self) -> list[RenderPatch]:
        """Get patches from the most recent render."""
        return self.all_patches[-1] if self.all_patches else []

    @property
    def patch_count(self) -> int:
        """Total number of render calls captured."""
        return len(self.all_patches)


@pytest.fixture
def capture_patches() -> tp.Callable[[CompositionComponent], PatchCapture]:
    """Create a patch capture helper for testing incremental renders.

    Usage:
        def test_incremental_updates(capture_patches):
            @component
            def Counter():
                Label(text=str(state.count))

            capture = capture_patches(Counter)
            capture.render()  # Initial render

            state.count += 1
            patches = capture.render_dirty()  # Incremental update
            assert len(patches) > 0
    """

    def _capture(root: CompositionComponent) -> PatchCapture:
        session = RenderSession(root)
        return PatchCapture(session=session)

    return _capture


# =============================================================================
# Mock Fixtures for Unit Tests
# =============================================================================


@pytest.fixture
def mock_element_state() -> tp.Callable[..., Mock]:
    """Factory for mock ElementState objects without render context.

    Useful for unit testing functions that accept ElementState
    without needing to set up a full render session.

    Usage:
        def test_state_handling(mock_element_state):
            state = mock_element_state(id="test-1", local_state={"count": 0})
            # Use state in unit tests
    """

    def _make(
        id: str = "test-1",
        local_state: dict[str, tp.Any] | None = None,
        context: dict[str, tp.Any] | None = None,
    ) -> Mock:
        mock = Mock()
        mock.id = id
        mock.local_state = local_state or {}
        mock.context = context or {}
        return mock

    return _make


@pytest.fixture
def mock_stateful() -> tp.Callable[..., Stateful]:
    """Factory for creating Stateful test instances.

    Usage:
        def test_stateful_behavior(mock_stateful):
            @dataclass(kw_only=True)
            class CounterState(Stateful):
                count: int = 0

            state = mock_stateful(CounterState, count=5)
            assert state.count == 5
    """

    def _make[T: Stateful](cls: type[T], **kwargs: tp.Any) -> T:
        return cls(**kwargs)

    return _make


# =============================================================================
# Helper Functions
# =============================================================================


def render_to_tree(session: RenderSession) -> dict[str, tp.Any]:
    """Render and return the serialized tree dict.

    This is a test helper that extracts the tree from the initial render's
    RenderAddPatch. For incremental renders, use render(session) directly to get patches.

    Args:
        session: The RenderSession to render

    Returns:
        Serialized tree dict (same format as the old render() method)

    Raises:
        ValueError: If render() doesn't return a RenderAddPatch with the tree
    """
    from trellis.core.rendering.patches import RenderAddPatch

    patches = render(session)
    if not patches:
        raise ValueError("render() returned no patches")

    first_patch = patches[0]
    if not isinstance(first_patch, RenderAddPatch):
        raise ValueError(f"Expected RenderAddPatch, got {type(first_patch).__name__}")

    # Serialize the node to wire format for test assertions
    return serialize_node(first_patch.node, session)
