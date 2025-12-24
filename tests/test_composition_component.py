"""Tests for trellis.core.composition_component module."""

from trellis.core.rendering import ElementNode, RenderTree
from trellis.core.composition_component import CompositionComponent, component


class TestCompositionComponent:
    def test_component_decorator(self) -> None:
        @component
        def MyComponent() -> None:
            pass

        assert isinstance(MyComponent, CompositionComponent)
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
        assert len(ctx.root_node.child_ids) == 1
        child = ctx.get_node(ctx.root_node.child_ids[0])
        assert child is not None
        assert child.component == Child

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

        assert len(ctx.root_node.child_ids) == 3

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

        assert len(ctx.root_node.child_ids) == 3
        child0 = ctx.get_node(ctx.root_node.child_ids[0])
        child1 = ctx.get_node(ctx.root_node.child_ids[1])
        child2 = ctx.get_node(ctx.root_node.child_ids[2])
        assert child0 is not None and child0.properties["label"] == "a"
        assert child1 is not None and child1.properties["label"] == "b"
        assert child2 is not None and child2.properties["label"] == "c"

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
        assert len(ctx.root_node.child_ids) == 1

        ctx2 = RenderTree(ConditionalFalse)
        ctx2.render()
        assert len(ctx2.root_node.child_ids) == 0

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

        assert len(ctx.root_node.child_ids) == 5
        for i, child_id in enumerate(ctx.root_node.child_ids):
            child = ctx.get_node(child_id)
            assert child is not None
            assert child.properties["value"] == i

    def test_component_with_explicit_none_key(self) -> None:
        """Explicit key=None should result in None key, not 'None' string."""

        @component
        def Item() -> None:
            pass

        @component
        def App() -> None:
            Item(key=None)  # Explicit None
            Item()  # No key parameter
            Item(key="explicit")  # Explicit string key

        ctx = RenderTree(App)
        ctx.render()

        # First two should have None key
        child0 = ctx.get_node(ctx.root_node.child_ids[0])
        child1 = ctx.get_node(ctx.root_node.child_ids[1])
        child2 = ctx.get_node(ctx.root_node.child_ids[2])
        assert child0 is not None and child0.key is None
        assert child1 is not None and child1.key is None
        # Third should have explicit key
        assert child2 is not None and child2.key == "explicit"
