# Trellis

[![CI](https://github.com/emmapowers/trellis/actions/workflows/ci.yml/badge.svg)](https://github.com/emmapowers/trellis/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A reactive UI framework for Python with fine-grained state tracking.

<p align="center">
  <img src="docs/demo-preview.gif" alt="Demo" width="387">
</p>

## Example

```python
@dataclass(kw_only=True)
class Counter(Stateful):
    count: int = 0

    def increment(self) -> None:
        self.count += 1


@component
def App() -> None:
    state = Counter()

    with Column():
        with Row():
            html.Span("Count: ", style={"fontWeight": "bold"})
            html.Text(state.count)
        Button(text="Increment", on_click=state.increment)


@async_main
async def main() -> None:
    app = Trellis(top=App)
    await app.serve()
```

## Installation

From source (requires [pixi](https://pixi.sh)):

```bash
git clone https://github.com/emmapowers/trellis.git
cd trellis
pixi install
```

To run the demo

```bash
pixi run demo
```

## Not Yet Implemented

- Bi-directional state binding (`Mutable[T]`)
- Router/navigation
- Widget library - placeholders for simple things like layout and buttons are implemented.
- Partial updates - the entire tree is sent to the client on every render
- Lots more...
