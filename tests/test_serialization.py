"""Tests for Element tree serialization."""

from trellis.core.functional_component import component
from trellis.core.rendering import RenderContext
from trellis.core.serialization import (
    clear_callbacks,
    get_callback,
    serialize_element,
)


class TestSerializeElement:
    """Tests for serialize_element function."""

    def setup_method(self) -> None:
        """Clear callback registry between tests."""
        clear_callbacks()

    def teardown_method(self) -> None:
        """Clean up callbacks after tests."""
        clear_callbacks()

    def test_serialize_simple_element(self) -> None:
        """Basic element serializes correctly."""

        @component
        def Simple() -> None:
            pass

        ctx = RenderContext(Simple)
        ctx.render(from_element=None)

        result = serialize_element(ctx.root_element)

        assert result["type"] == "FunctionalComponent"  # React component type
        assert result["name"] == "Simple"  # Python component name
        assert result["key"] is None
        assert result["props"] == {}
        assert result["children"] == []

    def test_serialize_element_with_props(self) -> None:
        """Element with props serializes correctly."""

        @component
        def WithProps(text: str = "", count: int = 0) -> None:
            pass

        @component
        def App() -> None:
            WithProps(text="hello", count=42)

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        # Get the WithProps child
        child = ctx.root_element.children[0]
        result = serialize_element(child)

        assert result["type"] == "FunctionalComponent"
        assert result["name"] == "WithProps"
        assert result["props"]["text"] == "hello"
        assert result["props"]["count"] == 42

    def test_serialize_element_with_key(self) -> None:
        """Element with key serializes correctly."""

        @component
        def Keyed() -> None:
            pass

        @component
        def App() -> None:
            Keyed(key="my-key")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

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
        ctx.render(from_element=None)

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
        """Callbacks are replaced with ID references."""
        called = []

        def on_click() -> None:
            called.append(True)

        @component
        def WithCallback(on_click=None) -> None:
            pass

        @component
        def App() -> None:
            WithCallback(on_click=on_click)

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        child = ctx.root_element.children[0]
        result = serialize_element(child)

        # Should have callback reference
        assert "__callback__" in result["props"]["on_click"]
        cb_id = result["props"]["on_click"]["__callback__"]

        # Should be able to look up and invoke the callback
        callback = get_callback(cb_id)
        assert callback is not None
        callback()
        assert called == [True]

    def test_serialize_various_prop_types(self) -> None:
        """Various prop types serialize correctly."""

        @component
        def ManyProps(
            string_val: str = "",
            int_val: int = 0,
            float_val: float = 0.0,
            bool_val: bool = False,
            none_val: None = None,
            list_val: list | None = None,
            dict_val: dict | None = None,
        ) -> None:
            pass

        @component
        def App() -> None:
            ManyProps(
                string_val="hello",
                int_val=42,
                float_val=3.14,
                bool_val=True,
                none_val=None,
                list_val=[1, 2, 3],
                dict_val={"a": 1, "b": 2},
            )

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        child = ctx.root_element.children[0]
        result = serialize_element(child)
        props = result["props"]

        assert props["string_val"] == "hello"
        assert props["int_val"] == 42
        assert props["float_val"] == 3.14
        assert props["bool_val"] is True
        assert props["none_val"] is None
        assert props["list_val"] == [1, 2, 3]
        assert props["dict_val"] == {"a": 1, "b": 2}

    def test_serialize_nested_callbacks(self) -> None:
        """Callbacks nested in lists/dicts are handled."""
        handler1_calls = []
        handler2_calls = []

        def handler1() -> None:
            handler1_calls.append(1)

        def handler2() -> None:
            handler2_calls.append(2)

        @component
        def WithHandlers(handlers: list | None = None) -> None:
            pass

        @component
        def App() -> None:
            WithHandlers(handlers=[handler1, handler2])

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        child = ctx.root_element.children[0]
        result = serialize_element(child)

        handlers = result["props"]["handlers"]
        assert len(handlers) == 2
        assert "__callback__" in handlers[0]
        assert "__callback__" in handlers[1]

        # Verify callbacks work
        get_callback(handlers[0]["__callback__"])()
        get_callback(handlers[1]["__callback__"])()
        assert handler1_calls == [1]
        assert handler2_calls == [2]

    def test_multiple_callbacks_get_unique_ids(self) -> None:
        """Each callback gets a unique ID."""

        @component
        def TwoCallbacks(on_a=None, on_b=None) -> None:
            pass

        @component
        def App() -> None:
            TwoCallbacks(on_a=lambda: None, on_b=lambda: None)

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        child = ctx.root_element.children[0]
        result = serialize_element(child)

        id_a = result["props"]["on_a"]["__callback__"]
        id_b = result["props"]["on_b"]["__callback__"]

        assert id_a != id_b
