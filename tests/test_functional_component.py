"""Tests for trellis.core.functional_component module."""

from trellis.core.rendering import Element, Elements, RenderContext
from trellis.core.functional_component import FunctionalComponent, component


class TestFunctionalComponent:
    def test_component_decorator(self) -> None:
        @component
        def MyComponent() -> Elements:
            return None

        assert isinstance(MyComponent, FunctionalComponent)
        assert MyComponent.name == "MyComponent"

    def test_component_returns_element(self) -> None:
        @component
        def Parent() -> Elements:
            return None

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert ctx.root_element is not None
        assert isinstance(ctx.root_element, Element)
        assert ctx.root_element.component == Parent

    def test_nested_components(self) -> None:
        @component
        def Child() -> Elements:
            return None

        @component
        def Parent() -> Elements:
            return Child()

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert ctx.root_element is not None
        assert len(ctx.root_element.children) == 1
        assert ctx.root_element.children[0].component == Child

    def test_component_depth_tracking(self) -> None:
        @component
        def GrandChild() -> Elements:
            return None

        @component
        def Child() -> Elements:
            return GrandChild()

        @component
        def Parent() -> Elements:
            return Child()

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert ctx.root_element.depth == 0
        assert ctx.root_element.children[0].depth == 1
        assert ctx.root_element.children[0].children[0].depth == 2

    def test_component_with_props_via_parent(self) -> None:
        """Props are passed when component is called from parent, not from RenderContext."""
        received_text: list[str] = []

        @component
        def Child(text: str) -> Elements:
            received_text.append(text)
            return None

        @component
        def Parent() -> Elements:
            return Child(text="hello")

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert received_text == ["hello"]

    def test_multiple_children(self) -> None:
        @component
        def Child() -> Elements:
            return None

        @component
        def Parent() -> Elements:
            return [Child(), Child(), Child()]

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert len(ctx.root_element.children) == 3
