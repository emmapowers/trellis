"""
React Component Integration in Trellis

Trellis widgets are Python functions that map to React components in the client bundle.
The `@react_component_base` decorator connects Python definitions to client-side React.

Architecture:
1. Python side: Define widget API with `@react_component_base("ComponentName")`
2. Client side: Implement React component in `client/src/widgets/ComponentName.tsx`
3. Bundle: Components are bundled together and served to the browser
"""

from __future__ import annotations

import typing as tp

from trellis.core.react_component import react_component_base
from trellis.core.rendering import Element
from trellis.core.style_props import Margin, Padding

if tp.TYPE_CHECKING:
    from collections.abc import Callable


# ---------------------------------------------------------------------------
# Example: Defining a Widget
# ---------------------------------------------------------------------------
@react_component_base("MyButton")
def MyButton(
    text: str = "",
    *,
    on_click: Callable[[], None] | None = None,
    disabled: bool = False,
    variant: tp.Literal["primary", "secondary"] = "primary",
    margin: Margin | None = None,
    padding: Padding | int | None = None,
    key: str | None = None,
) -> Element:
    """Custom button widget.

    The decorator `@react_component_base("MyButton")` means:
    - This function returns an Element with element_name="MyButton"
    - The client expects a React component named "MyButton" in the bundle
    - Props are serialized and sent to the React component

    Args:
        text: Button label text
        on_click: Callback function invoked on click (serialized as callback ref)
        disabled: Whether button is disabled
        variant: Visual style variant
        margin: Margin around the button (Margin dataclass)
        padding: Padding inside button (Padding dataclass or int for all sides)
        key: Optional key for reconciliation

    Returns:
        Element representing this widget
    """
    ...  # Implementation is in React


# The corresponding React component would be in:
# src/trellis/client/src/widgets/MyButton.tsx
#
# ```tsx
# interface MyButtonProps {
#   text?: string;
#   on_click?: () => void;
#   disabled?: boolean;
#   variant?: "primary" | "secondary";
#   style?: React.CSSProperties;
# }
#
# export function MyButton({
#   text = "",
#   on_click,
#   disabled = false,
#   variant = "primary",
#   style,
# }: MyButtonProps): React.ReactElement {
#   return (
#     <button
#       onClick={on_click}
#       disabled={disabled}
#       className={`btn btn-${variant}`}
#       style={style}
#     >
#       {text}
#     </button>
#   );
# }
# ```


# ---------------------------------------------------------------------------
# Example: Container Widget with Children
# ---------------------------------------------------------------------------
@react_component_base("Card", has_children=True)
def Card(
    *,
    title: str | None = None,
    padding: Padding | int | None = None,
    margin: Margin | None = None,
    key: str | None = None,
) -> Element:
    """Card container with optional title.

    Setting `has_children=True` means this widget can contain child elements.
    Use it with a `with` block:

        with Card(title="User Info"):
            Label(text="Name: Alice")
            Label(text="Email: alice@example.com")

    The children are passed to the React component's `children` prop.
    """
    ...


# ---------------------------------------------------------------------------
# Key Points
# ---------------------------------------------------------------------------
# 1. Python defines the API (props, types, docstrings)
# 2. React implements the rendering (TSX, CSS, interactivity)
# 3. The decorator handles:
#    - Creating Element with correct element_name
#    - Freezing props for reconciliation
#    - Converting style props (Margin, Padding) to CSS
#    - Serializing callbacks for client invocation
#
# 4. To add a new widget:
#    a. Create Python function with @react_component_base decorator
#    b. Create matching React component in client/src/widgets/
#    c. Export from client/src/widgets/index.ts
#    d. Export from src/trellis/widgets/__init__.py
