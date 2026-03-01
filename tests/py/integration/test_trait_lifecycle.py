"""Integration tests for trait lifecycle dispatch in the renderer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from trellis.core.components.composition import component
from trellis.core.rendering.element import Element
from trellis.core.rendering.element_state import ElementState

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.conftest import PatchCapture
    from trellis.core.components.composition import CompositionComponent

    CapturePatches = Callable[[CompositionComponent], PatchCapture]


# =============================================================================
# Recording trait for tests
# =============================================================================


@dataclass
class RecordingTraitState:
    """State for RecordingTrait — tracks lifecycle calls."""

    calls: list[str] = field(default_factory=list)


class RecordingTrait:
    """A test trait that records lifecycle hook invocations."""

    def _before_execute(self, element: Element, state: ElementState, session: object) -> None:
        ts = state.trait(RecordingTraitState)
        ts.calls.append("before_execute")

    def _after_execute(self, element: Element, state: ElementState, session: object) -> None:
        ts = state.trait(RecordingTraitState)
        ts.calls.append("after_execute")

    def _on_trait_mount(self, element: Element, state: ElementState, session: object) -> None:
        ts = state.trait(RecordingTraitState)
        ts.calls.append("on_trait_mount")

    def _on_trait_unmount(self, element: Element, state: ElementState, session: object) -> None:
        ts = state.trait(RecordingTraitState)
        ts.calls.append("on_trait_unmount")


class RecordingElement(RecordingTrait, Element):
    """Element subclass with recording trait for testing lifecycle dispatch."""

    pass


# =============================================================================
# Tests
# =============================================================================


class TestTraitBeforeAfterExecute:
    def test_before_execute_called_before_component(self, capture_patches: CapturePatches) -> None:
        """_before_execute fires before the component's execute() runs."""
        execution_order: list[str] = []

        @component(element_class=RecordingElement)
        def MyComp() -> None:
            execution_order.append("execute")

        capture = capture_patches(MyComp)
        capture.render()

        # The recording trait adds "before_execute" and "after_execute"
        # but those are in trait state. Check execution_order only has "execute".
        assert execution_order == ["execute"]

        # Verify trait hooks were called by checking trait state
        root_id = capture.session.root_element.id
        state = capture.session.states.get(root_id)
        ts = state.trait(RecordingTraitState)
        assert "before_execute" in ts.calls
        assert ts.calls.index("before_execute") < ts.calls.index("after_execute")

    def test_after_execute_called_after_component(self, capture_patches: CapturePatches) -> None:
        """_after_execute fires after the component's execute() runs."""

        @component(element_class=RecordingElement)
        def MyComp() -> None:
            pass

        capture = capture_patches(MyComp)
        capture.render()

        root_id = capture.session.root_element.id
        state = capture.session.states.get(root_id)
        ts = state.trait(RecordingTraitState)
        assert ts.calls[:2] == ["before_execute", "after_execute"]


class TestTraitMountUnmount:
    def test_on_trait_mount_called_after_initial_render(
        self, capture_patches: CapturePatches
    ) -> None:
        """_on_trait_mount fires after the initial render completes."""

        @component(element_class=RecordingElement)
        def MyComp() -> None:
            pass

        capture = capture_patches(MyComp)
        capture.render()

        root_id = capture.session.root_element.id
        state = capture.session.states.get(root_id)
        ts = state.trait(RecordingTraitState)
        assert "on_trait_mount" in ts.calls

    def test_on_trait_mount_not_called_on_rerender(self, capture_patches: CapturePatches) -> None:
        """_on_trait_mount does NOT fire on subsequent re-renders."""

        @component(element_class=RecordingElement)
        def MyComp() -> None:
            pass

        capture = capture_patches(MyComp)
        capture.render()

        root_id = capture.session.root_element.id
        state = capture.session.states.get(root_id)
        ts = state.trait(RecordingTraitState)
        mount_count_before = ts.calls.count("on_trait_mount")

        capture.session.dirty.mark(root_id)
        capture.render()

        assert ts.calls.count("on_trait_mount") == mount_count_before

    def test_on_trait_unmount_called_on_removal(self, capture_patches: CapturePatches) -> None:
        """_on_trait_unmount fires when an element is removed from the tree."""
        show_child = [True]

        @component(element_class=RecordingElement)
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            if show_child[0]:
                Child()

        capture = capture_patches(Parent)
        capture.render()

        # Get child's state to track unmount
        child_id = capture.session.root_element.child_ids[0]
        child_state = capture.session.states.get(child_id)
        ts = child_state.trait(RecordingTraitState)
        assert "on_trait_mount" in ts.calls
        assert "on_trait_unmount" not in ts.calls

        # Remove child
        show_child[0] = False
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert "on_trait_unmount" in ts.calls


class TestTraitHookOrdering:
    def test_full_lifecycle_order(self, capture_patches: CapturePatches) -> None:
        """Verify the complete ordering: before_execute, after_execute, on_trait_mount."""

        @component(element_class=RecordingElement)
        def MyComp() -> None:
            pass

        capture = capture_patches(MyComp)
        capture.render()

        root_id = capture.session.root_element.id
        state = capture.session.states.get(root_id)
        ts = state.trait(RecordingTraitState)

        assert ts.calls == ["before_execute", "after_execute", "on_trait_mount"]
