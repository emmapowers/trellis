"""Tests for trellis.core.composition_component module."""

from trellis.core.components.composition import CompositionComponent, component
from trellis.core.rendering.element import Element


class TestCompositionComponent:
    def test_component_decorator(self) -> None:
        @component
        def MyComponent() -> None:
            pass

        assert isinstance(MyComponent, CompositionComponent)
        assert MyComponent.name == "MyComponent"

    def test_component_returns_node(self, rendered) -> None:
        @component
        def Parent() -> None:
            pass

        result = rendered(Parent)

        assert result.root_element is not None
        assert isinstance(result.root_element, Element)
        assert result.root_element.component == Parent

    def test_nested_components(self, rendered) -> None:
        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            Child()

        result = rendered(Parent)

        assert result.root_element is not None
        assert len(result.root_element.child_ids) == 1
        child = result.session.elements.get(result.root_element.child_ids[0])
        assert child is not None
        assert child.component == Child

    def test_component_with_props_via_parent(self, rendered) -> None:
        """Props are passed when component is called from parent, not from RenderSession."""
        received_text: list[str] = []

        @component
        def Child(text: str) -> None:
            received_text.append(text)

        @component
        def Parent() -> None:
            Child(text="hello")

        rendered(Parent)

        assert received_text == ["hello"]

    def test_multiple_children(self, rendered) -> None:
        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            Child()
            Child()
            Child()

        result = rendered(Parent)

        assert len(result.root_element.child_ids) == 3

    def test_implicit_child_collection(self, rendered) -> None:
        """Elements created in component body are auto-collected as children."""

        @component
        def Item(label: str) -> None:
            pass

        @component
        def List() -> None:
            Item(label="a")
            Item(label="b")
            Item(label="c")

        result = rendered(List)

        assert len(result.root_element.child_ids) == 3
        child0 = result.session.elements.get(result.root_element.child_ids[0])
        child1 = result.session.elements.get(result.root_element.child_ids[1])
        child2 = result.session.elements.get(result.root_element.child_ids[2])
        assert child0 is not None and child0.properties["label"] == "a"
        assert child1 is not None and child1.properties["label"] == "b"
        assert child2 is not None and child2.properties["label"] == "c"

    def test_conditional_children(self, rendered) -> None:
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

        result1 = rendered(ConditionalTrue)
        assert len(result1.root_element.child_ids) == 1

        result2 = rendered(ConditionalFalse)
        assert len(result2.root_element.child_ids) == 0

    def test_loop_children(self, rendered) -> None:
        """Elements created in loops are collected."""

        @component
        def Item(value: int) -> None:
            pass

        @component
        def List() -> None:
            for i in range(5):
                Item(value=i)

        result = rendered(List)

        assert len(result.root_element.child_ids) == 5
        for i, child_id in enumerate(result.root_element.child_ids):
            child = result.session.elements.get(child_id)
            assert child is not None
            assert child.properties["value"] == i

    def test_component_with_explicit_none_key(self, rendered) -> None:
        """Explicit key=None should result in None key, not 'None' string."""

        @component
        def Item() -> None:
            pass

        @component
        def App() -> None:
            Item(key=None)  # Explicit None
            Item()  # No key parameter
            Item(key="explicit")  # Explicit string key

        result = rendered(App)

        # First two should have None key
        child0 = result.session.elements.get(result.root_element.child_ids[0])
        child1 = result.session.elements.get(result.root_element.child_ids[1])
        child2 = result.session.elements.get(result.root_element.child_ids[2])
        assert child0 is not None and child0._key is None
        assert child1 is not None and child1._key is None
        # Third should have explicit key
        assert child2 is not None and child2._key == "explicit"
