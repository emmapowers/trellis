"""Example decorator for widget showcase with source code capture."""

from __future__ import annotations

import ast
import base64
import inspect
import typing as tp
from urllib.parse import quote

from trellis import component

if tp.TYPE_CHECKING:
    from trellis.core.components.composition import CompositionComponent, RenderFunc


def example(
    title: str,
    includes: list[tp.Any] | None = None,
) -> tp.Callable[[RenderFunc], CompositionComponent]:
    """Decorator that creates a component and captures its source code.

    The decorated function becomes a Trellis component with additional
    `.title` and `.source` attributes for display in ExampleCard.

    Args:
        title: Display title for the example.
        includes: Optional list of items whose source should be included in the
            displayed code and playground. Items can be:
            - Functions or classes: source extracted via inspect.getsource()
            - Strings: treated as variable names, searched in the source file

    Example:
        @example("Button Variants")
        def ButtonVariants():
            with w.Row(gap=8):
                w.Button(text="Primary", variant="primary")

        class CounterState(Stateful):
            count: int = 0

        @example("Counter", includes=[CounterState])
        def CounterExample():
            state = CounterState()
            with state:
                w.Button(text=f"Count: {state.count}")

        STOCKS = [{"ticker": "AAPL", ...}, ...]

        def PriceCell(row: dict) -> None:
            w.Label(text=f"${row['price']}")

        @example("Stock Table", includes=["STOCKS", PriceCell])
        def StockTable():
            w.Table(columns=[...], data=STOCKS)
    """

    def decorator(func: RenderFunc) -> CompositionComponent:
        # Capture source code of the function
        try:
            full_source = inspect.getsource(func)
        except (OSError, TypeError):
            full_source = ""

        # Strip @example decorator and add @component for display
        stripped_source = _strip_decorator(full_source)
        func_source = _add_component_decorator(stripped_source)

        # Get source file for searching variable names
        # Note: Only reads project source files via inspect module.
        # This is safe for the widget showcase but shouldn't be used
        # in production code with untrusted functions.
        all_source_lines: list[str] = []
        try:
            source_file = inspect.getsourcefile(func)
            if source_file:
                with open(source_file) as f:
                    all_source_lines = f.read().split("\n")
        except OSError:
            pass

        # Capture source for each included object
        include_sources: list[str] = []
        for obj in includes or []:
            if isinstance(obj, str):
                # It's a variable name - search for it in the source file
                var_source = _find_variable_source(obj, all_source_lines)
                if var_source:
                    include_sources.append(var_source)
            else:
                # Try to get source of the object (works for functions/classes)
                try:
                    include_sources.append(inspect.getsource(obj))
                except (OSError, TypeError):
                    # Can't get source for this object
                    pass

        # Combine function source + includes for display (component first)
        if include_sources:
            source = func_source + "\n\n\n" + "\n\n".join(include_sources)
        else:
            source = func_source

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


def _find_variable_source(var_name: str, source_lines: list[str]) -> str | None:
    """Find the source for a variable assignment using AST parsing.

    Uses Python's ast module to correctly handle multi-line assignments,
    strings with brackets, comments, and other edge cases that simple
    bracket counting would fail on.

    Args:
        var_name: Name of the variable to find (must be a valid identifier).
        source_lines: Source code lines from the file.

    Returns:
        Source code of the variable assignment, or None if not found.
    """
    # Validate variable name to prevent injection
    if not var_name.isidentifier():
        return None

    source = "\n".join(source_lines)

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # If the file doesn't parse, can't extract source
        return None

    # Find Assign node targeting var_name
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    # Use get_source_segment to extract exact source
                    segment = ast.get_source_segment(source, node)
                    return segment if segment else None

    return None


def make_playground_url(
    source: str,
    func_name: str,
    base_url: str = "/trellis/playground/",
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
import typing as tp
from trellis import *
from trellis import widgets as w
from trellis import html as h
from trellis.app import theme
from trellis.widgets import IconName

{source}


@component
def App():
    with w.Card(style={{"margin": "24px"}}):
        with w.Column():
            {func_name}()
"""

    # Encode for URL: base64(encodeURIComponent(code))
    encoded = base64.b64encode(quote(full_code).encode()).decode()

    return f"{base_url}#code={encoded}"
