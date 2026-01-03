"""Tests for conditional container children rendering.

This module tests that conditional containers preserve their children
when the container doesn't render them on a subsequent pass.

With the ChildRef fix:
- `child_ids` reflects RENDERED children (what's shown to frontend)
- `props["children"]` contains ChildRefs (stable references to collected children)

When a container hides children:
- child_ids becomes empty (nothing rendered)
- props["children"] still has ChildRefs (can render them later)
- Soft unmount is called (lifecycle hooks, but Element stays in session.elements)

When a container shows children again:
- Container calls ChildRef() to render them
- child_ids reflects rendered children again
- Mount hooks are called
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from trellis.core.components.composition import component
from trellis.core.state.stateful import Stateful

if TYPE_CHECKING:
    from tests.conftest import PatchCapture


class TestConditionalChildrenFix:
    """Tests verifying that conditional containers preserve children via ChildRef.

    These tests verify that when a container has its OWN state that triggers
    a re-render, children collected during the parent's render are preserved
    and can be rendered again.
    """

    def test_conditional_container_preserves_children_when_only_container_rerenders(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """Children are preserved when container re-renders without parent re-rendering.

        When only the container re-renders (not its parent), children collected
        during the parent's render are preserved via ChildRef and can be rendered again.
        """
        render_counts: dict[str, int] = {}

        @dataclass
        class VisibilityState(Stateful):
            visible: bool = True

        # Store state reference at module level so we can access it
        container_state: list[VisibilityState] = []

        @component
        def Child() -> None:
            render_counts["child"] = render_counts.get("child", 0) + 1

        @component
        def ConditionalContainer(*, children: list | None = None) -> None:
            """Container with its own visibility state.

            When this component's state changes, ONLY this component re-renders,
            not the parent that collected the children.
            """
            state = VisibilityState()
            container_state.append(state)
            if state.visible and children:
                for child in children:
                    child()

        @component
        def App() -> None:
            render_counts["app"] = render_counts.get("app", 0) + 1
            with ConditionalContainer():
                Child()

        capture = capture_patches(App)
        capture.render()

        # Render 1: visible=True, child should render
        assert render_counts.get("child", 0) == 1, "Child should render when visible"
        assert render_counts.get("app", 0) == 1, "App rendered once"

        # Get the container element
        container_id = capture.session.root_element.child_ids[0]
        container = capture.session.elements.get(container_id)
        assert container is not None
        assert len(container.child_ids) == 1, "Container should have 1 child"

        # Change state on the CONTAINER (not App)
        # This should only re-render ConditionalContainer, not App
        container_state[-1].visible = False
        capture.render()

        # App should NOT have re-rendered - only the container
        assert render_counts.get("app", 0) == 1, "App should not re-render"

        container = capture.session.elements.get(container_id)
        assert container is not None
        # child_ids reflects RENDERED children (none when hidden)
        # but props["children"] still has ChildRefs for later rendering
        assert len(container.child_ids) == 0, "No children rendered when hidden"

        # Now show again - only container re-renders
        container_state[-1].visible = True
        capture.render()

        # App still should not have re-rendered
        assert render_counts.get("app", 0) == 1, "App should still not re-render"

        container = capture.session.elements.get(container_id)
        assert container is not None
        # Children are preserved via ChildRef and rendered again
        assert len(container.child_ids) == 1, "Children rendered again after showing"

        # Child should have rendered twice (once initially, once after showing again)
        assert render_counts.get("child", 0) == 2, "Child re-renders when shown again"

    def test_tab_container_preserves_unrendered_children(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """Tab container preserves all children even when only rendering one.

        This test shows that a container with three children can render any
        of them based on state. child_ids reflects the currently rendered child,
        but props["children"] contains ChildRefs for all collected children.
        """
        render_counts: dict[str, int] = {}

        @dataclass
        class SelectionState(Stateful):
            selected: int = 0  # 0, 1, or 2

        container_state: list[SelectionState] = []

        @component
        def ChildA() -> None:
            render_counts["a"] = render_counts.get("a", 0) + 1

        @component
        def ChildB() -> None:
            render_counts["b"] = render_counts.get("b", 0) + 1

        @component
        def ChildC() -> None:
            render_counts["c"] = render_counts.get("c", 0) + 1

        @component
        def TabContainer(*, children: list | None = None) -> None:
            """Only renders the child at the selected index."""
            state = SelectionState()
            container_state.append(state)
            if children and 0 <= state.selected < len(children):
                children[state.selected]()

        @component
        def App() -> None:
            render_counts["app"] = render_counts.get("app", 0) + 1
            with TabContainer():
                ChildA()
                ChildB()
                ChildC()

        capture = capture_patches(App)
        capture.render()

        # Render 1: selected=0, only ChildA renders
        assert render_counts == {"app": 1, "a": 1}, "Only ChildA should render initially"

        container_id = capture.session.root_element.child_ids[0]
        container = capture.session.elements.get(container_id)
        assert container is not None

        # child_ids reflects RENDERED children (only ChildA)
        # props["children"] has ChildRefs for all 3 collected children
        assert len(container.child_ids) == 1, "Only selected child rendered"
        assert len(container.props.get("children", [])) == 3, "All children collected"

        # Change to selected=1 (only container re-renders)
        container_state[-1].selected = 1
        capture.render()

        # App should not re-render
        assert render_counts.get("app", 0) == 1, "App should not re-render"

        container = capture.session.elements.get(container_id)
        assert container is not None

        # ChildB should now render because props["children"] has all ChildRefs
        assert render_counts.get("b", 0) == 1, "ChildB renders when selected"
        assert len(container.child_ids) == 1, "Only selected child rendered"

    def test_nested_conditional_containers_with_internal_state(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """Nested conditional containers with internal state work correctly."""
        render_counts: dict[str, int] = {}

        @dataclass
        class VisibilityState(Stateful):
            visible: bool = True

        outer_state: list[VisibilityState] = []

        @component
        def DeepChild() -> None:
            render_counts["deep"] = render_counts.get("deep", 0) + 1

        @component
        def InnerContainer(*, children: list | None = None) -> None:
            """Inner container with no state - just passes through."""
            render_counts["inner"] = render_counts.get("inner", 0) + 1
            if children:
                for child in children:
                    child()

        @component
        def OuterContainer(*, children: list | None = None) -> None:
            """Outer container with visibility state."""
            state = VisibilityState()
            outer_state.append(state)
            render_counts["outer"] = render_counts.get("outer", 0) + 1
            if state.visible and children:
                for child in children:
                    child()

        @component
        def App() -> None:
            render_counts["app"] = render_counts.get("app", 0) + 1
            with OuterContainer():
                with InnerContainer():
                    DeepChild()

        capture = capture_patches(App)
        capture.render()

        assert render_counts == {"app": 1, "outer": 1, "inner": 1, "deep": 1}

        # Hide outer (only outer re-renders)
        outer_state[-1].visible = False
        capture.render()

        assert render_counts.get("app", 0) == 1, "App should not re-render"
        assert render_counts.get("outer", 0) == 2, "Outer re-rendered"

        # Show outer again
        outer_state[-1].visible = True
        capture.render()

        assert render_counts.get("app", 0) == 1, "App still should not re-render"

        # Children preserved via ChildRef - inner and deep child re-render
        assert render_counts.get("inner", 0) == 2, "Inner re-renders when outer shows again"
        assert render_counts.get("deep", 0) == 2, "Deep child re-renders when outer shows again"
