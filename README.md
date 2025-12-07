# Trellis

[![CI](https://github.com/emmapowers/trellis/actions/workflows/ci.yml/badge.svg)](https://github.com/emmapowers/trellis/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A reactive UI framework for Python with fine-grained state tracking.

## Installation

From source (requires [pixi](https://pixi.sh)):

```bash
git clone https://github.com/emmapowers/trellis.git
cd trellis
pixi install
```

## Status

Early development. The core reactive rendering engine is functional:

- `@component` decorator for defining UI components
- Container components use context manager syntax (`with Column():`)
- `Stateful` base class for reactive state with automatic dependency tracking
- Selective re-rendering of only components affected by state changes
- Thread-safe rendering context

## Example

```python
from dataclasses import dataclass
from trellis.core import RenderContext, component, Element
from trellis.core.state import Stateful

@component
def Column(children: list[Element]) -> None:
    for child in children:
        child()

@dataclass(kw_only=True)
class AppState(Stateful):
    text: str = "Hello, World!"

state = AppState()

@component
def App() -> None:
    with Column():
        SomeText(text=state.text)

# Render
context = RenderContext(App)
context.render(from_element=None)

# Update state - only affected components re-render
state.text = "Updated!"
context.render_dirty()
```

## Not Yet Implemented

- Computed/derived state (`@composite`)
- Bi-directional state binding (`Mutable[T]`)
- Widget library (Label, TextInput, Button, etc.)
- HTML primitives
- Router/navigation
- Web server and client sync
- React component integration
