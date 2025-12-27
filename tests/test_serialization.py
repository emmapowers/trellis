"""Tests for ElementNode tree serialization."""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.platforms.common.serialization import parse_callback_id, serialize_node
from trellis.widgets.basic import Button
import trellis.html as h


class TestSerializeNode:
    """Tests for serialize_node function."""

    def test_serialize_simple_node(self) -> None:
        """Basic node serializes correctly."""

        @component
        def Simple() -> None:
            pass

        ctx = RenderSession(Simple)
        render(ctx)

        result = serialize_node(ctx.root_element, ctx)

        assert result["type"] == "CompositionComponent"  # React component type
        assert result["name"] == "Simple"  # Python component name
        # Nodes have position-based IDs with component identity: /@{id}
        assert result["key"] is not None
        assert result["key"].startswith("/@")  # Position-based IDs start with "/@"
        assert result["props"] == {}
        assert result["children"] == []

    def test_composition_component_props_not_serialized(self) -> None:
        """CompositionComponent props are NOT serialized (layout-only)."""

        @component
        def WithProps(text: str = "", count: int = 0) -> None:
            pass

        @component
        def App() -> None:
            WithProps(text="hello", count=42)

        ctx = RenderSession(App)
        render(ctx)

        # Get the WithProps child
        child = ctx.elements.get(ctx.root_element.child_ids[0])
        result = serialize_node(child, ctx)

        assert result["type"] == "CompositionComponent"
        assert result["name"] == "WithProps"
        # CompositionComponent props should NOT be serialized
        assert result["props"] == {}

    def test_serialize_node_with_key(self) -> None:
        """Node with key serializes correctly."""

        @component
        def Keyed() -> None:
            pass

        @component
        def App() -> None:
            Keyed(key="my-key")

        ctx = RenderSession(App)
        render(ctx)

        child = ctx.elements.get(ctx.root_element.child_ids[0])
        result = serialize_node(child, ctx)

        # Position-based IDs include user key with :key@ prefix
        # Format: /{parent_path}/:my-key@{component_id}
        assert ":my-key@" in result["key"]

    def test_serialize_nested_children(self) -> None:
        """Nested nodes serialize with children inline."""

        @component
        def Child() -> None:
            pass

        @component
        def Parent(children: list) -> None:
            for c in children:
                c()

        @component
        def App() -> None:
            with Parent():
                Child()
                Child()

        ctx = RenderSession(App)
        render(ctx)

        result = serialize_node(ctx.root_element, ctx)

        # App has Parent as child
        assert len(result["children"]) == 1
        parent_result = result["children"][0]

        # Parent has two Child nodes
        assert parent_result["type"] == "CompositionComponent"
        assert parent_result["name"] == "Parent"
        assert len(parent_result["children"]) == 2
        assert parent_result["children"][0]["name"] == "Child"
        assert parent_result["children"][1]["name"] == "Child"

    def test_serialize_callback_creates_reference(self) -> None:
        """Callbacks are replaced with ID references (using ReactComponent)."""
        called = []

        def on_click() -> None:
            called.append(True)

        @component
        def App() -> None:
            # Use Button (a ReactComponent) to test callback serialization
            Button(text="Click me", on_click=on_click)

        ctx = RenderSession(App)
        render(ctx)

        child = ctx.elements.get(ctx.root_element.child_ids[0])
        result = serialize_node(child, ctx)

        # Should have callback reference
        assert "__callback__" in result["props"]["on_click"]
        cb_id = result["props"]["on_click"]["__callback__"]

        # Should be able to look up and invoke the callback
        # parse_callback_id returns (node_id, prop_name)
        node_id, prop_name = parse_callback_id(cb_id)
        callback = ctx.get_callback(node_id, prop_name)
        assert callback is not None
        callback()
        assert called == [True]

    def test_serialize_various_prop_types(self) -> None:
        """Various prop types serialize correctly (using HTML element)."""

        @component
        def App() -> None:
            # Use HTML element (a ReactComponent) to test prop serialization
            with h.Div(
                id="test",
                data_string="hello",
                data_int=42,
                data_float=3.14,
                data_bool=True,
                data_none=None,
                data_list=[1, 2, 3],
                data_dict={"a": 1, "b": 2},
            ):
                pass

        ctx = RenderSession(App)
        render(ctx)

        child = ctx.elements.get(ctx.root_element.child_ids[0])
        result = serialize_node(child, ctx)
        props = result["props"]

        assert props["id"] == "test"
        assert props["data_string"] == "hello"
        assert props["data_int"] == 42
        assert props["data_float"] == 3.14
        assert props["data_bool"] is True
        assert props["data_none"] is None
        assert props["data_list"] == [1, 2, 3]
        assert props["data_dict"] == {"a": 1, "b": 2}

    def test_serialize_nested_callbacks(self) -> None:
        """Callbacks nested in lists/dicts are handled (using HTML element)."""
        handler1_calls = []
        handler2_calls = []

        def handler1() -> None:
            handler1_calls.append(1)

        def handler2() -> None:
            handler2_calls.append(2)

        @component
        def App() -> None:
            # Use HTML element with data prop containing list of callbacks
            with h.Div(data_handlers=[handler1, handler2]):
                pass

        ctx = RenderSession(App)
        render(ctx)

        child = ctx.elements.get(ctx.root_element.child_ids[0])
        result = serialize_node(child, ctx)

        handlers = result["props"]["data_handlers"]
        assert len(handlers) == 2
        assert "__callback__" in handlers[0]
        assert "__callback__" in handlers[1]

        # Verify callbacks work
        node_id_0, prop_name_0 = parse_callback_id(handlers[0]["__callback__"])
        ctx.get_callback(node_id_0, prop_name_0)()
        node_id_1, prop_name_1 = parse_callback_id(handlers[1]["__callback__"])
        ctx.get_callback(node_id_1, prop_name_1)()
        assert handler1_calls == [1]
        assert handler2_calls == [2]

    def test_multiple_callbacks_get_unique_ids(self) -> None:
        """Each callback gets a unique ID (using HTML element)."""

        @component
        def App() -> None:
            # Use HTML element with two callback props
            with h.Div(onClick=lambda: None, onMouseEnter=lambda: None):
                pass

        ctx = RenderSession(App)
        render(ctx)

        child = ctx.elements.get(ctx.root_element.child_ids[0])
        result = serialize_node(child, ctx)

        id_a = result["props"]["onClick"]["__callback__"]
        id_b = result["props"]["onMouseEnter"]["__callback__"]

        assert id_a != id_b
