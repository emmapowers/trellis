"""Component definition system for the Trellis UI framework.

This package provides:
- `Component`: Abstract base class for all components
- `CompositionComponent`: Component implementation using render functions
- `component`: Decorator to create components from functions
- `ReactComponentBase`: Base class for React-based widget components
"""

from trellis.core.components.base import Component
from trellis.core.components.composition import CompositionComponent, component
from trellis.core.components.react import ReactComponentBase, react_component_base
from trellis.core.components.style_props import Height, Margin, Padding, Width

__all__ = [
    "Component",
    "CompositionComponent",
    "Height",
    "Margin",
    "Padding",
    "ReactComponentBase",
    "Width",
    "component",
    "react_component_base",
]
