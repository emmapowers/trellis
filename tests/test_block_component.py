"""Tests for trellis.core.block_component module."""

import pytest

from trellis.core.rendering import Element, Elements, RenderContext
from trellis.core.functional_component import component
from trellis.core.block_component import BlockComponent, BlockElement, blockComponent


class TestBlockComponent:
    def test_block_component_decorator(self) -> None:
        @blockComponent
        def Column(children: list[Element]) -> Elements:
            return children

        assert isinstance(Column, BlockComponent)
        assert Column.name == "Column"

    def test_block_component_context_manager(self) -> None:
        @blockComponent
        def Column(children: list[Element]) -> Elements:
            return children

        @component
        def Child() -> Elements:
            return None

        @component
        def Parent() -> Elements:
            with Column() as col:
                Child()
                Child()
            return col

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert ctx.root_element is not None
        # Parent has Column as child
        assert len(ctx.root_element.children) == 1
        column_elem = ctx.root_element.children[0]
        assert column_elem.component == Column
        # Column has two Child elements
        assert len(column_elem.children) == 2

    def test_block_element_is_block_element_type(self) -> None:
        @blockComponent
        def Column(children: list[Element]) -> Elements:
            return children

        @component
        def Parent() -> Elements:
            with Column() as col:
                pass
            return col

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        column_elem = ctx.root_element.children[0]
        assert isinstance(column_elem, BlockElement)

    def test_nested_block_components(self) -> None:
        @blockComponent
        def Column(children: list[Element]) -> Elements:
            return children

        @blockComponent
        def Row(children: list[Element]) -> Elements:
            return children

        @component
        def Child() -> Elements:
            return None

        @component
        def Parent() -> Elements:
            with Column() as col:
                with Row() as row:
                    Child()
            return col

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        column_elem = ctx.root_element.children[0]
        assert column_elem.component.name == "Column"
        row_elem = column_elem.children[0]
        assert row_elem.component.name == "Row"
        assert len(row_elem.children) == 1

    def test_block_component_cannot_be_reused(self) -> None:
        @blockComponent
        def Column(children: list[Element]) -> Elements:
            return children

        @component
        def Parent() -> Elements:
            col = Column()
            with col:
                pass
            with col:  # Should raise
                pass
            return col

        ctx = RenderContext(Parent)
        with pytest.raises(RuntimeError, match="only use.*once"):
            ctx.render(from_element=None)

    def test_block_component_children_passed_to_render_func(self) -> None:
        received_children: list = []

        @blockComponent
        def Column(children: list[Element]) -> Elements:
            received_children.extend(children)
            return children

        @component
        def Child() -> Elements:
            return None

        @component
        def Parent() -> Elements:
            with Column() as col:
                Child()
                Child()
            return col

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert len(received_children) == 2
