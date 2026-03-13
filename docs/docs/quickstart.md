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

For desktop app support, install with the desktop extra:

```bash
pip install "trellis[desktop] @ git+https://github.com/emmapowers/trellis.git"
```

## Run the Demo

Trellis includes a demo app. Run it to make sure everything works:

```bash
python -m trellis.examples.demo
```

Open http://127.0.0.1:8000 in your browser. You should see an interactive counter.

To run as a desktop app (requires desktop extra):

```bash
python -m trellis.examples.demo --desktop
```

## Your First App

Create two files:

**trellis_config.py:**
```python
from trellis.app.config import Config

config = Config(name="My App", module="app")
```

**app.py:**
```python
from trellis import App, component, state_var
from trellis import widgets as w


@component
def MyApp() -> None:
    count = state_var(0)

    with w.Column():
        w.Heading(text="My First Trellis App")
        w.Label(text=f"Count: {count.value}")
        w.Button(text="Increment", on_click=lambda: count.set(count.value + 1))


app = App(MyApp)
```

Run it:

```bash
trellis run
```

Open http://127.0.0.1:8000. Click the button—the count updates.

Or run as a desktop app:

```bash
trellis run --desktop
```

## What Just Happened?

1. **`state_var()`** — You created a small slot-local piece of reactive state. When its value changes, readers re-render automatically.

2. **`@component`** — You defined a component function. It describes what the UI should look like.

3. **`with w.Column():`** — Components nest using Python's `with` blocks. `Column` arranges children vertically.

4. **`w.Heading()`, `w.Label()`** — Widgets for displaying text. `Heading` renders semantic HTML headings.

5. **`w.Button(..., on_click=...)`** — A widget with an event handler. When clicked, it updates `count`.

6. **Automatic updates** — When `count.value` changes, components that read it re-render automatically.

## Next Steps

- [Concepts](./concepts) — Understand components, state, and reactivity
- [Building UIs](./building-uis) — HTML elements, widgets, and styling
