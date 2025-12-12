"""Tests for trellis.core.functional_component module."""

from trellis.core.rendering import ElementNode, RenderTree
from trellis.core.functional_component import FunctionalComponent, component


class TestFunctionalComponent:
    def test_component_decorator(self) -> None:
        @component
        def MyComponent() -> None:
            pass

        assert isinstance(MyComponent, FunctionalComponent)
        assert MyComponent.name == "MyComponent"

    def test_component_returns_node(self) -> None:
        @component
        def Parent() -> None:
            pass

        ctx = RenderTree(Parent)
        ctx.render()

        assert ctx.root_node is not None
        assert isinstance(ctx.root_node, ElementNode)
        assert ctx.root_node.component == Parent

    def test_nested_components(self) -> None:
        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            Child()

        ctx = RenderTree(Parent)
        ctx.render()

        assert ctx.root_node is not None
        assert len(ctx.root_node.children) == 1
        assert ctx.root_node.children[0].component == Child

    def test_component_with_props_via_parent(self) -> None:
        """Props are passed when component is called from parent, not from RenderTree."""
        received_text: list[str] = []

        @component
        def Child(text: str) -> None:
            received_text.append(text)

        @component
        def Parent() -> None:
            Child(text="hello")

        ctx = RenderTree(Parent)
        ctx.render()

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

        ctx = RenderTree(Parent)
        ctx.render()

        assert len(ctx.root_node.children) == 3

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

        ctx = RenderTree(List)
        ctx.render()

        assert len(ctx.root_node.children) == 3
        assert ctx.root_node.children[0].properties["label"] == "a"
        assert ctx.root_node.children[1].properties["label"] == "b"
        assert ctx.root_node.children[2].properties["label"] == "c"

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

        ctx = RenderTree(ConditionalTrue)
        ctx.render()
        assert len(ctx.root_node.children) == 1

        ctx2 = RenderTree(ConditionalFalse)
        ctx2.render()
        assert len(ctx2.root_node.children) == 0

    def test_loop_children(self) -> None:
        """Elements created in loops are collected."""

        @component
        def Item(value: int) -> None:
            pass

        @component
        def List() -> None:
            for i in range(5):
                Item(value=i)

        ctx = RenderTree(List)
        ctx.render()

        assert len(ctx.root_node.children) == 5
        for i, child in enumerate(ctx.root_node.children):
            assert child.properties["value"] == i
