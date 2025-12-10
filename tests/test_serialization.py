"""Tests for Element tree serialization."""

from trellis.core.functional_component import component
from trellis.core.rendering import RenderContext
from trellis.core.serialization import serialize_element
from trellis.widgets.basic import Button
import trellis.html as h


class TestSerializeElement:
    """Tests for serialize_element function."""

    def test_serialize_simple_element(self) -> None:
        """Basic element serializes correctly."""

        @component
        def Simple() -> None:
            pass

        ctx = RenderContext(Simple)
        ctx.render_tree(from_element=None)

        result = serialize_element(ctx.root_element)

        assert result["type"] == "FunctionalComponent"  # React component type
        assert result["name"] == "Simple"  # Python component name
        # Elements always have a key (user-provided or server-assigned stable ID)
        assert result["key"] is not None
        assert result["key"].startswith("e")  # Server-assigned IDs start with "e"
        assert result["props"] == {}
        assert result["children"] == []

    def test_functional_component_props_not_serialized(self) -> None:
        """FunctionalComponent props are NOT serialized (layout-only)."""

        @component
        def WithProps(text: str = "", count: int = 0) -> None:
            pass

        @component
        def App() -> None:
            WithProps(text="hello", count=42)

        ctx = RenderContext(App)
        ctx.render_tree(from_element=None)

        # Get the WithProps child
        child = ctx.root_element.children[0]
        result = serialize_element(child)

        assert result["type"] == "FunctionalComponent"
        assert result["name"] == "WithProps"
        # FunctionalComponent props should NOT be serialized
        assert result["props"] == {}

    def test_serialize_element_with_key(self) -> None:
        """Element with key serializes correctly."""

        @component
        def Keyed() -> None:
            pass

        @component
        def App() -> None:
            Keyed(key="my-key")

        ctx = RenderContext(App)
        ctx.render_tree(from_element=None)

        child = ctx.root_element.children[0]
        result = serialize_element(child)

        assert result["key"] == "my-key"

    def test_serialize_nested_children(self) -> None:
        """Nested elements serialize with children inline."""

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

        ctx = RenderContext(App)
        ctx.render_tree(from_element=None)

        result = serialize_element(ctx.root_element)

        # App has Parent as child
        assert len(result["children"]) == 1
        parent_result = result["children"][0]

        # Parent has two Child elements
        assert parent_result["type"] == "FunctionalComponent"
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

        ctx = RenderContext(App)
        ctx.render_tree(from_element=None)

        child = ctx.root_element.children[0]
        result = serialize_element(child)

        # Should have callback reference
        assert "__callback__" in result["props"]["on_click"]
        cb_id = result["props"]["on_click"]["__callback__"]

        # Should be able to look up and invoke the callback
        callback = ctx.get_callback(cb_id)
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

        ctx = RenderContext(App)
        ctx.render_tree(from_element=None)

        child = ctx.root_element.children[0]
        result = serialize_element(child)
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

        ctx = RenderContext(App)
        ctx.render_tree(from_element=None)

        child = ctx.root_element.children[0]
        result = serialize_element(child)

        handlers = result["props"]["data_handlers"]
        assert len(handlers) == 2
        assert "__callback__" in handlers[0]
        assert "__callback__" in handlers[1]

        # Verify callbacks work
        ctx.get_callback(handlers[0]["__callback__"])()
        ctx.get_callback(handlers[1]["__callback__"])()
        assert handler1_calls == [1]
        assert handler2_calls == [2]

    def test_multiple_callbacks_get_unique_ids(self) -> None:
        """Each callback gets a unique ID (using HTML element)."""

        @component
        def App() -> None:
            # Use HTML element with two callback props
            with h.Div(onClick=lambda: None, onMouseEnter=lambda: None):
                pass

        ctx = RenderContext(App)
        ctx.render_tree(from_element=None)

        child = ctx.root_element.children[0]
        result = serialize_element(child)

        id_a = result["props"]["onClick"]["__callback__"]
        id_b = result["props"]["onMouseEnter"]["__callback__"]

        assert id_a != id_b
