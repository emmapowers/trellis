---
sidebar_position: 2
title: Quickstart
---

# Quickstart

Get Trellis installed and running in a few minutes.

## Installation

Install Trellis from Git:

```bash
pip install git+https://github.com/emmapowers/trellis.git
```

## Run the Demo

Trellis includes a demo app. Run it to make sure everything works:

```bash
python -m trellis.examples.demo
```

Open http://127.0.0.1:8000 in your browser. You should see an interactive counter.

## Your First App

Create a file called `app.py`:

```python
from dataclasses import dataclass

from trellis import Stateful, Trellis, async_main, component
from trellis import html as h
from trellis import widgets as w


@dataclass
class Counter(Stateful):
    count: int = 0

    def increment(self) -> None:
        self.count += 1


@component
def App() -> None:
    state = Counter()

    with w.Column():
        h.H1("My First Trellis App")
        h.P(f"Count: {state.count}")
        w.Button(text="Increment", on_click=state.increment)


@async_main
async def main() -> None:
    app = Trellis(top=App)
    await app.serve()
```

Run it:

```bash
python app.py
```

Open http://127.0.0.1:8000. Click the button—the count updates.

## What Just Happened?

1. **`@dataclass` + `Stateful`** — You defined a state class. `Stateful` enables automatic reactivity.

2. **`@component`** — You defined a component function. It describes what the UI should look like.

3. **`with w.Column():`** — Components nest using Python's `with` blocks. `Column` arranges children vertically.

4. **`h.H1()`, `h.P()`** — HTML elements. The `h` module provides all standard HTML tags.

5. **`w.Button(..., on_click=...)`** — A widget with an event handler. When clicked, it calls `state.increment()`.

6. **Automatic updates** — When `state.count` changes, components that read it re-render automatically.

## Next Steps

- [Concepts](./concepts) — Understand components, state, and reactivity
- [Building UIs](./building-uis) — HTML elements, widgets, and styling
