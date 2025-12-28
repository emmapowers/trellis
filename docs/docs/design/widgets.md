---
sidebar_position: 8
title: Widgets
---

# Widgets

> **Prototype toolkit** — The widget library exists to build applications complex enough to test the core framework. The API will change significantly.

## Overview

Trellis includes a widget library that provides common UI components. These widgets wrap React components on the client side and are exposed as Python functions on the server side.

Widgets are accessed via `trellis.widgets` (conventionally imported as `w`):

```python
from trellis import widgets as w

with w.Column():
    w.Label(text="Hello")
    w.Button(text="Click me", on_click=handle_click)
```

## Available Widgets

| Category | Widgets |
|----------|---------|
| **Layout** | `Column`, `Row`, `Card` |
| **Forms** | `Button`, `TextInput`, `NumberInput`, `Checkbox`, `Slider`, `Select` |
| **Text** | `Label`, `Heading`, `Divider` |
| **Data** | `Table`, `Stat`, `Tag`, `Badge` |
| **Charts** | `TimeSeriesChart`, `LineChart`, `BarChart`, `AreaChart`, `PieChart`, `Sparkline` |
| **Feedback** | `ProgressBar`, `StatusIndicator`, `Tooltip`, `Callout`, `Collapsible` |
| **Navigation** | `Tabs`/`Tab`, `Breadcrumb`, `Tree`, `Menu`/`MenuItem`, `Toolbar` |
| **Icons** | `Icon` (800+ Lucide icons) |

## Implementation

### Client-side

Widgets are implemented as React components in TypeScript. Each widget:

- Receives props serialized from Python
- Handles user interactions and calls back to Python via message passing
- Uses React Aria hooks for accessibility (keyboard navigation, focus management, ARIA attributes)

The widget implementations live in `src/trellis/platforms/common/client/src/widgets/`.

### Python-side

Each widget is a function decorated with `@react_component_base` that returns an `Element`. The decorator handles:

- Registering the component type
- Serializing props for the client
- Managing callback references for event handlers

```python
from collections.abc import Callable
from typing import Literal

from trellis.core.react_component import react_component_base
from trellis.core.rendering import Element

@react_component_base("Button")
def Button(
    text: str = "",
    *,
    on_click: Callable[[], None] | None = None,
    variant: Literal["primary", "secondary", "outline", "ghost", "danger"] = "primary",
    # ...
) -> Element:
    ...
```

### Accessibility

All interactive widgets use [React Aria](https://react-spectrum.adobe.com/react-aria/) hooks for accessibility:

- **Keyboard navigation** — Arrow keys, Tab, Enter, Escape work as expected
- **Focus management** — Visible focus indicators, focus trapping in modals
- **ARIA attributes** — Proper roles, states, and properties for screen readers
- **Screen reader announcements** — Live regions for dynamic content

## Charts

Chart widgets use [Recharts](https://recharts.org/) for general-purpose charts and [uPlot](https://github.com/leeoniya/uPlot) for high-performance time-series data.

- `TimeSeriesChart` — Real-time streaming data (uPlot)
- `LineChart`, `BarChart`, `AreaChart`, `PieChart` — Standard charts (Recharts)
- `Sparkline` — Inline mini charts (Recharts)

## Lower-level Control

When widgets don't meet your needs, use HTML primitives directly:

```python
from trellis import html as h

with h.Div(className="custom-container"):
    h.Span(text="Custom content")
```

HTML elements provide full control over structure and styling while still participating in Trellis's reactive rendering system.
