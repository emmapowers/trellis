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
    """Register project-specific pytest markers.
    
    Adds the following markers to pytest so they can be used in tests:
    - slow: marks tests that are slow (roughly >1s or run in a subprocess)
    - network: marks tests that require network access
    - platform: marks cross-platform protocol tests
    """
    config.addinivalue_line("markers", "slow: marks test as slow (>1s or subprocess)")
    config.addinivalue_line("markers", "network: requires network access")
    config.addinivalue_line("markers", "platform: cross-platform protocol tests")


# =============================================================================
# Component Fixtures
# =============================================================================


@pytest.fixture
def make_component() -> tp.Callable[[str], CompositionComponent]:
    """
    Create a factory that constructs CompositionComponent instances for tests.
    
    Returns:
        A callable that accepts a component name (str) and returns a CompositionComponent with that name whose `render_func` is a no-op.
    """

    def _make(name: str) -> CompositionComponent:
        """
        Create a CompositionComponent with the given name whose render function is a no-op.
        
        Parameters:
            name (str): The name to assign to the created component.
        
        Returns:
            component (CompositionComponent): A CompositionComponent instance with `render_func` that does nothing.
        """
        return CompositionComponent(name=name, render_func=lambda: None)

    return _make


@pytest.fixture
def noop_component() -> CompositionComponent:
    """
    Provides a pre-made no-op root CompositionComponent for tests.
    
    Returns:
        CompositionComponent: A component named "NoopRoot" whose render function performs no work.
    """
    return CompositionComponent(name="NoopRoot", render_func=lambda: None)


# =============================================================================
# Session Fixtures
# =============================================================================


@pytest.fixture
def render_session(noop_component: CompositionComponent) -> RenderSession:
    """
    Provide a fresh RenderSession initialized with a noop component for each test.
    
    Returns:
        RenderSession: A new RenderSession configured with the noop root component.
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
        """
        Access the root Element of the associated render session.
        
        Returns:
            Element: The root Element belonging to this instance's RenderSession.
        """
        return self.session.root_element


@pytest.fixture
def rendered() -> tp.Callable[[CompositionComponent], RenderResult]:
    """
    Create a helper that renders a component and returns a RenderResult.
    
    The returned callable accepts a CompositionComponent, runs a render for that component, and returns a RenderResult containing the RenderSession, the list of produced render patches, and the serialized root tree.
    
    Returns:
        Callable[[CompositionComponent], RenderResult]: Function that renders the given component and returns its RenderResult.
    """

    def _render(root: CompositionComponent) -> RenderResult:
        """
        Render the given CompositionComponent and return the resulting render artifacts.
        
        Parameters:
            root (CompositionComponent): The component to use as the root of the render session.
        
        Returns:
            RenderResult: Object containing the created RenderSession, the list of RenderPatch objects produced by the render, and the serialized tree of the session's root element.
        """
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
        """
        Render the associated RenderSession and record the produced patches.
        
        Appends the list of patches from rendering to the capture's `all_patches` and returns that list.
        
        Returns:
            list[RenderPatch]: The patches produced by rendering the session.
        """
        patches = render(self.session)
        self.all_patches.append(patches)
        return patches

    def render_dirty(self) -> list[RenderPatch]:
        """
        Re-render nodes marked dirty and record the resulting patches.
        
        Appends the produced patches to self.all_patches.
        
        Returns:
            patches (list[RenderPatch]): Patches produced by the dirty re-render.
        """
        from trellis.core.rendering.render import render_dirty

        patches = render_dirty(self.session)
        self.all_patches.append(patches)
        return patches

    @property
    def last_patches(self) -> list[RenderPatch]:
        """
        Retrieve the patches from the most recent render.
        
        Returns:
            list[RenderPatch]: The list of patches produced by the most recent render, or an empty list if no renders have been captured.
        """
        return self.all_patches[-1] if self.all_patches else []

    @property
    def patch_count(self) -> int:
        """
        Number of render calls captured.
        
        Returns:
            The total count of captured render calls as an integer.
        """
        return len(self.all_patches)


@pytest.fixture
def capture_patches() -> tp.Callable[[CompositionComponent], PatchCapture]:
    """
    Return a factory that creates a PatchCapture for a given component root.
    
    Returns:
        factory (Callable[[CompositionComponent], PatchCapture]): A callable that, when given a CompositionComponent, creates a RenderSession for that component and returns a PatchCapture which collects patches produced by subsequent renders (initial and incremental).
    """

    def _capture(root: CompositionComponent) -> PatchCapture:
        """
        Create a PatchCapture for a new RenderSession initialized with the given root component.
        
        Parameters:
            root (CompositionComponent): The root component to use when creating the RenderSession.
        
        Returns:
            PatchCapture: A capture object tied to the created RenderSession that aggregates patches across renders.
        """
        session = RenderSession(root)
        return PatchCapture(session=session)

    return _capture


# =============================================================================
# Mock Fixtures for Unit Tests
# =============================================================================


@pytest.fixture
def mock_element_state() -> tp.Callable[..., Mock]:
    """
    Create a factory that produces Mock objects shaped like an ElementState for unit tests.
    
    The returned callable accepts optional arguments `id`, `local_state`, and `context` and returns a unittest.mock.Mock with those attributes set (defaults: id="test-1", local_state={}, context={}). This avoids needing a full render session when testing functions that operate on ElementState-like objects.
    
    Returns:
        factory (callable): A function `factory(id=..., local_state=None, context=None) -> Mock`.
    """

    def _make(
        id: str = "test-1",
        local_state: dict[str, tp.Any] | None = None,
        context: dict[str, tp.Any] | None = None,
    ) -> Mock:
        """
        Create a unittest.mock.Mock that simulates an element's saved state.
        
        Parameters:
            id (str): Identifier assigned to the mock's `id` attribute. Defaults to "test-1".
            local_state (dict[str, Any] | None): Initial local state placed on the mock's `local_state` attribute; uses an empty dict if None.
            context (dict[str, Any] | None): Initial context placed on the mock's `context` attribute; uses an empty dict if None.
        
        Returns:
            mock (Mock): A Mock instance with `id`, `local_state`, and `context` attributes set.
        """
        mock = Mock()
        mock.id = id
        mock.local_state = local_state or {}
        mock.context = context or {}
        return mock

    return _make


@pytest.fixture
def mock_stateful() -> tp.Callable[..., Stateful]:
    """
    Provide a factory that constructs instances of a Stateful subclass for tests.
    
    The returned callable instantiates the given Stateful subclass using the provided keyword arguments.
    
    Returns:
        factory (Callable[[type[Stateful], **Any], Stateful]): A function that accepts a Stateful subclass and keyword arguments and returns an instance of that subclass.
    """

    def _make[T: Stateful](cls: type[T], **kwargs: tp.Any) -> T:
        """
        Instantiate the given Stateful subclass with the provided constructor arguments.
        
        Parameters:
            cls (type[T]): The Stateful subclass to instantiate.
            **kwargs: Keyword arguments forwarded to the class constructor.
        
        Returns:
            T: An instance of the provided Stateful subclass.
        """
        return cls(**kwargs)

    return _make