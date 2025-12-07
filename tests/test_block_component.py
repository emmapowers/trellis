"""Tests for components with children parameter (container components)."""

import pytest

from trellis.core.rendering import Element, ElementDescriptor, RenderContext
from trellis.core.functional_component import component


class TestContainerComponent:
    def test_with_statement_collects_children(self) -> None:
        """Children created in with block are passed to component."""

        @component
        def Column(children: list[ElementDescriptor]) -> None:
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

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert ctx.root_element is not None
        # Parent has Column as child
        assert len(ctx.root_element.children) == 1
        column_elem = ctx.root_element.children[0]
        assert column_elem.component == Column
        # Column has two Child elements (mounted via child())
        assert len(column_elem.children) == 2

    def test_nested_containers(self) -> None:
        """Nested with blocks work correctly."""

        @component
        def Column(children: list[ElementDescriptor]) -> None:
            for child in children:
                child()

        @component
        def Row(children: list[ElementDescriptor]) -> None:
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

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        column_elem = ctx.root_element.children[0]
        assert column_elem.component.name == "Column"
        row_elem = column_elem.children[0]
        assert row_elem.component.name == "Row"
        assert len(row_elem.children) == 1

    def test_container_receives_children_list(self) -> None:
        """Container component receives children as a list of descriptors."""
        received_children: list = []

        @component
        def Column(children: list[ElementDescriptor]) -> None:
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

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert len(received_children) == 2
        for child in received_children:
            assert isinstance(child, ElementDescriptor)

    def test_component_without_children_param_raises_on_with(self) -> None:
        """Using with on a component without children param raises TypeError."""

        @component
        def NoChildren() -> None:
            pass

        @component
        def Parent() -> None:
            with NoChildren():  # Should raise
                pass

        ctx = RenderContext(Parent)
        with pytest.raises(TypeError, match="does not have a 'children' parameter"):
            ctx.render(from_element=None)

    def test_cannot_provide_children_prop_and_use_with(self) -> None:
        """Can't pass children as prop AND use with block."""

        @component
        def Column(children: list[ElementDescriptor]) -> None:
            for child in children:
                child()

        @component
        def Parent() -> None:
            with Column(children=[]):  # Should raise
                pass

        ctx = RenderContext(Parent)
        with pytest.raises(RuntimeError, match="Cannot provide 'children'.*and use 'with' block"):
            ctx.render(from_element=None)

    def test_empty_with_block(self) -> None:
        """Empty with block results in empty children list."""
        received_children: list | None = None

        @component
        def Column(children: list[ElementDescriptor]) -> None:
            nonlocal received_children
            received_children = children
            for child in children:
                child()

        @component
        def Parent() -> None:
            with Column():
                pass

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert received_children == []

    def test_child_call_mounts_element(self) -> None:
        """Calling child() mounts the element in the container."""

        @component
        def Wrapper(children: list[ElementDescriptor]) -> None:
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

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        wrapper = ctx.root_element.children[0]
        # Only one child mounted, even though 3 were collected
        assert len(wrapper.children) == 1

    def test_container_can_reorder_children(self) -> None:
        """Container can mount children in different order."""

        @component
        def Reverse(children: list[ElementDescriptor]) -> None:
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

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        reverse_elem = ctx.root_element.children[0]
        # Children should be in reverse order
        assert reverse_elem.children[0].properties["value"] == 3
        assert reverse_elem.children[1].properties["value"] == 2
        assert reverse_elem.children[2].properties["value"] == 1
