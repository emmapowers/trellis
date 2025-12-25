"""Tests for components with children parameter (container components)."""

import pytest

from trellis.core.rendering import ElementNode, RenderTree
from trellis.core.composition_component import component


class TestContainerComponent:
    def test_with_statement_collects_children(self) -> None:
        """Children created in with block are passed to component."""

        @component
        def Column(children: list[ElementNode]) -> None:
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

        ctx = RenderTree(Parent)
        ctx.render()

        assert ctx.root_node is not None
        # Parent has Column as child
        assert len(ctx.root_node.child_ids) == 1
        column_node = ctx.get_node(ctx.root_node.child_ids[0])
        assert column_node is not None
        assert column_node.component == Column
        # Column has two Child elements (mounted via child())
        assert len(column_node.child_ids) == 2

    def test_nested_containers(self) -> None:
        """Nested with blocks work correctly."""

        @component
        def Column(children: list[ElementNode]) -> None:
            for child in children:
                child()

        @component
        def Row(children: list[ElementNode]) -> None:
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

        ctx = RenderTree(Parent)
        ctx.render()

        column_node = ctx.get_node(ctx.root_node.child_ids[0])
        assert column_node is not None
        assert column_node.component.name == "Column"
        row_node = ctx.get_node(column_node.child_ids[0])
        assert row_node is not None
        assert row_node.component.name == "Row"
        assert len(row_node.child_ids) == 1

    def test_container_receives_children_list(self) -> None:
        """Container component receives children as a list of descriptors."""
        received_children: list = []

        @component
        def Column(children: list[ElementNode]) -> None:
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

        ctx = RenderTree(Parent)
        ctx.render()

        assert len(received_children) == 2
        for child in received_children:
            assert isinstance(child, ElementNode)

    def test_component_without_children_param_raises_on_with(self) -> None:
        """Using with on a component without children param raises TypeError."""

        @component
        def NoChildren() -> None:
            pass

        @component
        def Parent() -> None:
            with NoChildren():  # Should raise
                pass

        ctx = RenderTree(Parent)
        with pytest.raises(TypeError, match="does not accept children"):
            ctx.render()

    def test_cannot_provide_children_prop_and_use_with(self) -> None:
        """Can't pass children as prop AND use with block."""

        @component
        def Column(children: list[ElementNode]) -> None:
            for child in children:
                child()

        @component
        def Parent() -> None:
            with Column(children=[]):  # Should raise
                pass

        ctx = RenderTree(Parent)
        with pytest.raises(RuntimeError, match="Cannot provide 'children'.*and use 'with' block"):
            ctx.render()

    def test_empty_with_block(self) -> None:
        """Empty with block results in empty children list."""
        received_children: list | None = None

        @component
        def Column(children: list[ElementNode]) -> None:
            nonlocal received_children
            received_children = children
            for child in children:
                child()

        @component
        def Parent() -> None:
            with Column():
                pass

        ctx = RenderTree(Parent)
        ctx.render()

        assert received_children == []

    def test_child_call_mounts_element(self) -> None:
        """Calling child() mounts the node in the container."""

        @component
        def Wrapper(children: list[ElementNode]) -> None:
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

        ctx = RenderTree(Parent)
        ctx.render()

        wrapper = ctx.get_node(ctx.root_node.child_ids[0])
        assert wrapper is not None
        # Only one child mounted, even though 3 were collected
        assert len(wrapper.child_ids) == 1

    def test_container_can_reorder_children(self) -> None:
        """Container can mount children in different order."""

        @component
        def Reverse(children: list[ElementNode]) -> None:
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

        ctx = RenderTree(Parent)
        ctx.render()

        reverse_node = ctx.get_node(ctx.root_node.child_ids[0])
        assert reverse_node is not None
        # Children should be in reverse order
        child0 = ctx.get_node(reverse_node.child_ids[0])
        child1 = ctx.get_node(reverse_node.child_ids[1])
        child2 = ctx.get_node(reverse_node.child_ids[2])
        assert child0 is not None and child0.properties["value"] == 3
        assert child1 is not None and child1.properties["value"] == 2
        assert child2 is not None and child2.properties["value"] == 1
