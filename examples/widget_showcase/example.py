"""Example decorator for widget showcase with source code capture."""

from __future__ import annotations

import base64
import inspect
import typing as tp
from urllib.parse import quote

from trellis import component

if tp.TYPE_CHECKING:
    from trellis.core.composition_component import CompositionComponent


def example(title: str) -> tp.Callable[[tp.Callable[[], None]], CompositionComponent]:
    """Decorator that creates a component and captures its source code.

    The decorated function becomes a Trellis component with additional
    `.title` and `.source` attributes for display in ExampleCard.

    Args:
        title: Display title for the example.

    Example:
        @example("Button Variants")
        def button_variants():
            with w.Row(gap=8):
                w.Button(text="Primary", variant="primary")
                w.Button(text="Secondary", variant="secondary")
    """

    def decorator(func: tp.Callable[[], None]) -> CompositionComponent:
        # Capture source code
        try:
            full_source = inspect.getsource(func)
        except (OSError, TypeError):
            full_source = ""

        # Strip @example decorator and add @component for display
        stripped_source = _strip_decorator(full_source)
        source = _add_component_decorator(stripped_source)

        # Apply @component to make it a renderable component
        comp = component(func)

        # Attach metadata for ExampleCard to access
        comp.title = title  # type: ignore[attr-defined]
        comp.source = source  # type: ignore[attr-defined]
        comp.func_name = func.__name__  # type: ignore[attr-defined]

        return comp

    return decorator


def _strip_decorator(source: str) -> str:
    """Strip the @example(...) decorator line from source code."""
    lines = source.split("\n")
    result = []
    skip_next = False

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("@example("):
            # Check if decorator continues on next line
            if not stripped.rstrip().endswith(")"):
                skip_next = True
            continue
        if skip_next:
            if stripped.rstrip().endswith(")"):
                skip_next = False
            continue
        result.append(line)

    # Remove leading empty lines and dedent
    while result and not result[0].strip():
        result.pop(0)

    return "\n".join(result)


def _add_component_decorator(source: str) -> str:
    """Add @component decorator to the function definition."""
    lines = source.split("\n")
    result = []
    for line in lines:
        if line.lstrip().startswith("def "):
            result.append("@component")
        result.append(line)
    return "\n".join(result)


def make_playground_url(
    source: str,
    func_name: str,
    base_url: str = "/playground/",
) -> str:
    """Generate a playground URL with the example code.

    Args:
        source: The example source code (with @component, ready to display).
        func_name: The function name (should be PascalCase).
        base_url: Base URL for the playground.

    Returns:
        Full URL with #code=<base64> hash.
    """
    # Build full code with imports and App wrapper
    full_code = f"""\
from trellis import component
from trellis import widgets as w

{source}


@component
def App():
    with w.Column(padding=24):
        {func_name}()
"""

    # Encode for URL: base64(encodeURIComponent(code))
    encoded = base64.b64encode(quote(full_code).encode()).decode()

    return f"{base_url}#code={encoded}"
