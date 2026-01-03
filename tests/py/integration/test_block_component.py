"""Tests for components with children parameter (container components)."""

import pytest

from trellis.core.components.composition import component
from trellis.core.rendering.child_ref import ChildRef
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession


class TestContainerComponent:
    def test_with_statement_collects_children(self, rendered) -> None:
        """Children created in with block are passed to component."""

        @component
        def Column(children: list[ChildRef]) -> None:
            for child in children:
                child()

        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            with Column():
                Child()
                Child()

        result = rendered(Parent)

        root_node = result.session.elements.get(result.session.root_node_id)
        assert root_node is not None
        # Parent has Column as child
        assert len(root_node.child_ids) == 1
        column_node = result.session.elements.get(root_node.child_ids[0])
        assert column_node is not None
        assert column_node.component == Column
        # Column has two Child elements (mounted via child())
        assert len(column_node.child_ids) == 2

    def test_nested_containers(self, rendered) -> None:
        """Nested with blocks work correctly."""

        @component
        def Column(children: list[ChildRef]) -> None:
            for child in children:
                child()

        @component
        def Row(children: list[ChildRef]) -> None:
            for child in children:
                child()

        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            with Column():
                with Row():
                    Child()

        result = rendered(Parent)

        root_node = result.session.elements.get(result.session.root_node_id)
        assert root_node is not None
        column_node = result.session.elements.get(root_node.child_ids[0])
        assert column_node is not None
        assert column_node.component.name == "Column"
        row_node = result.session.elements.get(column_node.child_ids[0])
        assert row_node is not None
        assert row_node.component.name == "Row"
        assert len(row_node.child_ids) == 1

    def test_container_receives_children_list(self, rendered) -> None:
        """Container component receives children as a list of ChildRefs."""
        received_children: list = []

        @component
        def Column(children: list[ChildRef]) -> None:
            received_children.extend(children)
            for child in children:
                child()

        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            with Column():
                Child()
                Child()

        rendered(Parent)

        assert len(received_children) == 2
        for child in received_children:
            assert isinstance(child, ChildRef)

    def test_component_without_children_param_raises_on_with(self) -> None:
        """Using with on a component without children param raises TypeError."""

        @component
        def NoChildren() -> None:
            pass

        @component
        def Parent() -> None:
            with NoChildren():  # Should raise
                pass

        ctx = RenderSession(Parent)
        with pytest.raises(TypeError, match="does not accept children"):
            render(ctx)

    def test_cannot_provide_children_prop_and_use_with(self) -> None:
        """Can't pass children as prop AND use with block."""

        @component
        def Column(children: list[ChildRef]) -> None:
            for child in children:
                child()

        @component
        def Parent() -> None:
            with Column(children=[]):  # Should raise
                pass

        ctx = RenderSession(Parent)
        with pytest.raises(RuntimeError, match=r"Cannot provide 'children'.*and use 'with' block"):
            render(ctx)

    def test_empty_with_block(self, rendered) -> None:
        """Empty with block results in empty children list."""
        received_children: list[ChildRef] | None = None

        @component
        def Column(children: list[ChildRef]) -> None:
            nonlocal received_children
            received_children = children
            for child in children:
                child()

        @component
        def Parent() -> None:
            with Column():
                pass

        rendered(Parent)

        assert received_children == []

    def test_child_call_mounts_element(self, rendered) -> None:
        """Calling child() mounts the node in the container."""

        @component
        def Wrapper(children: list[ChildRef]) -> None:
            # Only mount first child
            if children:
                children[0]()

        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            with Wrapper():
                Child()
                Child()
                Child()

        result = rendered(Parent)

        root_node = result.session.elements.get(result.session.root_node_id)
        assert root_node is not None
        wrapper = result.session.elements.get(root_node.child_ids[0])
        assert wrapper is not None
        # Only one child mounted, even though 3 were collected
        assert len(wrapper.child_ids) == 1

    def test_container_can_reorder_children(self, rendered) -> None:
        """Container can mount children in different order."""

        @component
        def Reverse(children: list[ChildRef]) -> None:
            for child in reversed(children):
                child()

        @component
        def Item(value: int) -> None:
            pass

        @component
        def Parent() -> None:
            with Reverse():
                Item(value=1)
                Item(value=2)
                Item(value=3)

        result = rendered(Parent)

        root_node = result.session.elements.get(result.session.root_node_id)
        assert root_node is not None
        reverse_node = result.session.elements.get(root_node.child_ids[0])
        assert reverse_node is not None
        # Children should be in reverse order
        child0 = result.session.elements.get(reverse_node.child_ids[0])
        child1 = result.session.elements.get(reverse_node.child_ids[1])
        child2 = result.session.elements.get(reverse_node.child_ids[2])
        assert child0 is not None and child0.properties["value"] == 3
        assert child1 is not None and child1.properties["value"] == 2
        assert child2 is not None and child2.properties["value"] == 1
