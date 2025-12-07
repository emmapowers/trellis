"""Tests for trellis.core.functional_component module."""

from trellis.core.rendering import Element, RenderContext
from trellis.core.functional_component import FunctionalComponent, component


class TestFunctionalComponent:
    def test_component_decorator(self) -> None:
        @component
        def MyComponent() -> None:
            pass

        assert isinstance(MyComponent, FunctionalComponent)
        assert MyComponent.name == "MyComponent"

    def test_component_returns_element(self) -> None:
        @component
        def Parent() -> None:
            pass

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert ctx.root_element is not None
        assert isinstance(ctx.root_element, Element)
        assert ctx.root_element.component == Parent

    def test_nested_components(self) -> None:
        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            Child()

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert ctx.root_element is not None
        assert len(ctx.root_element.children) == 1
        assert ctx.root_element.children[0].component == Child

    def test_component_depth_tracking(self) -> None:
        @component
        def GrandChild() -> None:
            pass

        @component
        def Child() -> None:
            GrandChild()

        @component
        def Parent() -> None:
            Child()

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert ctx.root_element.depth == 0
        assert ctx.root_element.children[0].depth == 1
        assert ctx.root_element.children[0].children[0].depth == 2

    def test_component_with_props_via_parent(self) -> None:
        """Props are passed when component is called from parent, not from RenderContext."""
        received_text: list[str] = []

        @component
        def Child(text: str) -> None:
            received_text.append(text)

        @component
        def Parent() -> None:
            Child(text="hello")

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert received_text == ["hello"]

    def test_multiple_children(self) -> None:
        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            Child()
            Child()
            Child()

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert len(ctx.root_element.children) == 3

    def test_implicit_child_collection(self) -> None:
        """Elements created in component body are auto-collected as children."""

        @component
        def Item(label: str) -> None:
            pass

        @component
        def List() -> None:
            Item(label="a")
            Item(label="b")
            Item(label="c")

        ctx = RenderContext(List)
        ctx.render(from_element=None)

        assert len(ctx.root_element.children) == 3
        assert ctx.root_element.children[0].properties["label"] == "a"
        assert ctx.root_element.children[1].properties["label"] == "b"
        assert ctx.root_element.children[2].properties["label"] == "c"

    def test_conditional_children(self) -> None:
        """Only created elements are collected."""

        @component
        def Item() -> None:
            pass

        @component
        def ConditionalTrue() -> None:
            Item()

        @component
        def ConditionalFalse() -> None:
            pass  # No Item created

        ctx = RenderContext(ConditionalTrue)
        ctx.render(from_element=None)
        assert len(ctx.root_element.children) == 1

        ctx2 = RenderContext(ConditionalFalse)
        ctx2.render(from_element=None)
        assert len(ctx2.root_element.children) == 0

    def test_loop_children(self) -> None:
        """Elements created in loops are collected."""

        @component
        def Item(value: int) -> None:
            pass

        @component
        def List() -> None:
            for i in range(5):
                Item(value=i)

        ctx = RenderContext(List)
        ctx.render(from_element=None)

        assert len(ctx.root_element.children) == 5
        for i, child in enumerate(ctx.root_element.children):
            assert child.properties["value"] == i
