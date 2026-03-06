"""Integration tests for the first shadcn-backed smoke widget."""

from trellis import widgets as w
from trellis.core.components.composition import component


def test_button_renders_as_react_component(rendered) -> None:
    """The public Button widget should render through the React widget pipeline."""

    @component
    def App() -> None:
        w.Button(text="Smoke")

    result = rendered(App)
    button_node = result.session.elements.get(result.root_element.child_ids[0])

    assert button_node is not None
    assert button_node.component.element_name == "Button"
    assert dict(button_node.props)["text"] == "Smoke"
