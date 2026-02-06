"""Pytest configuration and shared fixtures for Trellis tests."""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import Mock

import pytest

from trellis.core.components.base import Component
from trellis.core.components.composition import CompositionComponent
from trellis.core.rendering.element import Element
from trellis.core.rendering.patches import RenderAddPatch, RenderPatch
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful
from trellis.platforms.common.serialization import serialize_element

# =============================================================================
# Marker Configuration
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks test as slow (>1s or subprocess)")
    config.addinivalue_line("markers", "network: requires network access")
    config.addinivalue_line("markers", "platform: cross-platform protocol tests")


# =============================================================================
# AppLoader Fixtures
# =============================================================================


@pytest.fixture
def reset_apploader() -> tp.Generator[None]:
    """Reset global _apploader before and after test."""
    import trellis.app.apploader as apploader_module  # noqa: PLC0415

    apploader_module._apploader = None
    yield
    apploader_module._apploader = None


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
        tree = serialize_element(session.root_element, session)
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
        patches = render(self.session)
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
# App Setup Fixtures
# =============================================================================

WriteTrellisConfig = tp.Callable[..., Path]
WriteAppModule = tp.Callable[..., Path]
WriteApp = tp.Callable[..., Path]


@pytest.fixture
def write_trellis_config(tmp_path: Path) -> WriteTrellisConfig:
    """Factory to write trellis_config.py with sensible defaults.

    Usage:
        def test_config(write_trellis_config):
            app_root = write_trellis_config(name="my-app", module="main")
            # app_root / "trellis_config.py" exists with valid Config

        def test_bad_config(write_trellis_config):
            app_root = write_trellis_config(content="def broken(")
            # app_root / "trellis_config.py" has raw content
    """

    def _write(
        name: str = "test-app",
        module: str = "main",
        platform: str | None = None,
        *,
        content: str | None = None,
    ) -> Path:
        if content is not None:
            (tmp_path / "trellis_config.py").write_text(content)
        else:
            lines = [
                "from trellis.app.config import Config",
            ]
            kwargs = [f'name="{name}"', f'module="{module}"']
            if platform is not None:
                lines.append("from trellis.platforms.common.base import PlatformType")
                kwargs.append(f"platform=PlatformType.{platform}")
            lines.append(f"config = Config({', '.join(kwargs)})")
            (tmp_path / "trellis_config.py").write_text("\n".join(lines) + "\n")
        return tmp_path

    return _write


@pytest.fixture
def write_app_module(tmp_path: Path) -> WriteAppModule:
    """Factory to write app module files with sensible defaults.

    Usage:
        def test_module(write_app_module):
            path = write_app_module(module_name="main", component_name="Root")
            # tmp_path / "main.py" exists with @component + App

        def test_broken_module(write_app_module):
            path = write_app_module(content="import nonexistent")
    """

    def _write(
        module_name: str = "main",
        component_name: str = "Root",
        *,
        content: str | None = None,
    ) -> Path:
        file_path = tmp_path / f"{module_name}.py"
        if content is not None:
            file_path.write_text(content)
        else:
            file_path.write_text(
                "from trellis import component\n"
                "from trellis.app import App\n"
                "\n"
                "@component\n"
                f"def {component_name}():\n"
                "    pass\n"
                "\n"
                f"app = App({component_name})\n"
            )
        return file_path

    return _write


@pytest.fixture
def write_app(
    write_trellis_config: WriteTrellisConfig,
    write_app_module: WriteAppModule,
) -> WriteApp:
    """Convenience fixture that writes both config and module.

    Usage:
        def test_full_app(write_app):
            app_root = write_app(name="my-app", module="main")
            # app_root has trellis_config.py + main.py
    """

    def _write(
        name: str = "test-app",
        module: str = "main",
        component_name: str = "Root",
        platform: str | None = None,
    ) -> Path:
        app_root = write_trellis_config(name=name, module=module, platform=platform)
        write_app_module(module_name=module, component_name=component_name)
        return app_root

    return _write


# =============================================================================
# Helper Functions
# =============================================================================


def find_element_by_type(node: dict[str, tp.Any], elem_type: str) -> dict[str, tp.Any] | None:
    """Recursively find an element by type (HTML tag) in a serialized tree.

    Args:
        node: Serialized element tree (from serialize_node)
        elem_type: HTML tag to find (e.g., "a", "div", "button")

    Returns:
        The matching element dict, or None if not found
    """
    if node.get("type") == elem_type:
        return node
    for child in node.get("children", []):
        result = find_element_by_type(child, elem_type)
        if result:
            return result
    return None


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
    patches = render(session)
    if not patches:
        raise ValueError("render() returned no patches")

    first_patch = patches[0]
    if not isinstance(first_patch, RenderAddPatch):
        raise ValueError(f"Expected RenderAddPatch, got {type(first_patch).__name__}")

    # Serialize the element to wire format for test assertions
    return serialize_element(first_patch.element, session)


def get_button_element(tree_node: dict[str, tp.Any]) -> dict[str, tp.Any]:
    """Get the actual _Button react element from a Button composition wrapper.

    Button is a composition component that wraps _Button. This helper
    navigates to the inner _Button element which has the actual props.

    Args:
        tree_node: Serialized Button element from render tree

    Returns:
        The inner _Button element dict with actual props
    """
    if tree_node.get("name") == "Button" and tree_node.get("type") == "CompositionComponent":
        children = tree_node.get("children", [])
        if children:
            return children[0]
    return tree_node


# =============================================================================
# Handler Fixtures
# =============================================================================


@pytest.fixture
def app_wrapper() -> tp.Callable[[tp.Any, str, str | None], CompositionComponent]:
    """Simple app wrapper for tests that don't need full TrellisApp theming.

    This provides a minimal wrapper that satisfies the AppWrapper signature
    without pulling in the full TrellisApp infrastructure.

    Usage:
        def test_handler_behavior(app_wrapper):
            handler = SomeHandler(component, app_wrapper)
            # handler can be used without TrellisApp
    """

    def wrapper(
        component: Component,
        system_theme: str,
        theme_mode: str | None,
    ) -> CompositionComponent:
        # Minimal wrapper - just wraps component without TrellisApp
        def render_func() -> None:
            component()

        return CompositionComponent(name="TestRoot", render_func=render_func)

    return wrapper
