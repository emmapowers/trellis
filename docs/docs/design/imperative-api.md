---
sidebar_position: 2
title: Imperative DOM API
---

# Imperative DOM Operations in Trellis

## Philosophy

Trellis is a declarative UI framework - you describe **what the UI should look like** based on state, not **how to update it**. However, some DOM operations are inherently imperative:

- Browser-driven side effects (focus, scroll)
- Reading current DOM state (measurements, positions)
- One-time actions that don't map to state updates
- Integration with third-party libraries

This document describes Trellis's API for these imperative operations.

## Two Approaches

### 1. Events - For Triggering Actions

Use events when you need to trigger a one-time imperative action (focus, scroll, play/pause).

```python
from dataclasses import dataclass, field
from trellis.core import component, Elements
from trellis.core.state import Stateful
from trellis.core.events import FocusEvent

@dataclass(kw_only=True)
class SearchState(Stateful):
    query: str = ""
    focus_input: FocusEvent = field(default_factory=FocusEvent)

@component
def SearchForm(state: SearchState) -> Elements:
    def reset():
        state.query = ""
        state.focus_input.fire()  # Triggers focus imperatively
    
    return Column(
        Input(
            value=state.query,
            focus=state.focus_input,  # Subscribe to event
            on_input=lambda e: setattr(state, 'query', e.target.value)
        ),
        Button("Reset", on_click=reset)
    )
```

**Key characteristics:**
- One-way: firing the event triggers the imperative operation
- No state to sync back
- Clean and declarative from the caller's perspective

### 2. Refs - For Reading State

Use refs when you need to read DOM state or make multiple imperative calls to the same element.

```python
from trellis.core import component, Elements, InputRef
from trellis.core.state import Stateful

@dataclass(kw_only=True)
class FormState(Stateful):
    query: str = ""

@component
def SearchForm(state: FormState) -> Elements:
    input_ref = InputRef()  # Create separately
    
    def handle_submit(e):
        # Read current selection
        start = input_ref.selection_start
        end = input_ref.selection_end
        
        # Imperative calls
        input_ref.blur()
        
        # ... process form
    
    def handle_key(e):
        if e.key == "Escape":
            input_ref.blur()
    
    return Column(
        Input(
            ref=input_ref,  # Pass in via ref=
            value=state.query,
            on_input=lambda e: setattr(state, 'query', e.target.value),
            on_keydown=handle_key
        ),
        Button("Search", on_click=handle_submit)
    )
```

**Key characteristics:**
- Two-way: can read properties and call methods
- Direct access to the underlying DOM node
- Type-safe methods and properties per element type

## Element-Specific Ref Classes

Each DOM element type has its own ref class with appropriate methods:

### InputRef
```python
input_ref = InputRef()

# Methods
input_ref.focus()
input_ref.blur()
input_ref.select()

# Properties (read-only)
input_ref.value
input_ref.selection_start
input_ref.selection_end
```

### VideoRef
```python
video_ref = VideoRef()

# Methods
video_ref.play()
video_ref.pause()

# Properties
video_ref.current_time  # Read/write
video_ref.paused  # Read-only
video_ref.duration  # Read-only
```

### CanvasRef
```python
canvas_ref = CanvasRef()

# Methods
ctx = canvas_ref.get_context('2d')

# Properties
canvas_ref.width
canvas_ref.height
```

### DivRef (for measurements and scroll)
```python
div_ref = DivRef()

# Methods
rect = div_ref.get_bounding_client_rect()
div_ref.scroll_into_view()

# Properties
div_ref.scroll_top  # Read/write
div_ref.scroll_left  # Read/write
div_ref.offset_width  # Read-only
div_ref.client_height  # Read-only
```

## Event Types

### FocusEvent
```python
focus_event = FocusEvent()
focus_event.fire()  # Triggers element.focus()
```

### ScrollEvent
```python
@dataclass(kw_only=True)
class ListState(Stateful):
    scroll_to_top: ScrollEvent = field(default_factory=ScrollEvent)

@component
def List(state: ListState, items: list) -> Elements:
    return Div(
        scroll=state.scroll_to_top,
        children=[Item(i) for i in items]
    )
```

### PlayEvent / PauseEvent (for media)
```python
@dataclass(kw_only=True)
class VideoState(Stateful):
    play: PlayEvent = field(default_factory=PlayEvent)
    pause: PauseEvent = field(default_factory=PauseEvent)
```

## Combining Events and Refs

Sometimes you need both:

```python
@dataclass(kw_only=True)
class VideoPlayerState(Stateful):
    is_playing: bool = False
    seek_to: SeekEvent = field(default_factory=SeekEvent)

@component
def VideoPlayer(state: VideoPlayerState, src: str) -> Elements:
    video_ref = VideoRef()
    
    def toggle_play():
        if state.is_playing:
            video_ref.pause()
            state.is_playing = False
        else:
            video_ref.play()
            state.is_playing = True
    
    def handle_time_update(e):
        # Read current position from ref
        current = video_ref.current_time
        # ... update progress bar
    
    return Column(
        Video(
            ref=video_ref,
            seek=state.seek_to,
            src=src,
            on_time_update=handle_time_update
        ),
        Button(
            "Play" if not state.is_playing else "Pause",
            on_click=toggle_play
        )
    )
```

## Design Principles

1. **Prefer events for one-time actions** - They're declarative and don't require managing ref lifecycle

2. **Use refs for reading state** - Measurements, positions, computed styles, form values

3. **Events are one-way** - Fire and forget. No bidirectional syncing needed.

4. **Refs are escape hatches** - Use them when you need fine-grained control or must read from the DOM

5. **Type safety** - Each element type has its own ref class with appropriate methods

## When NOT to Use Imperative Operations

Don't use imperative operations for things that should be declarative:

```python
# ❌ BAD - Don't use refs to set values
def update_input():
    input_ref.value = "new value"  # Don't do this!

# ✅ GOOD - Update state and let Trellis update the DOM
def update_input():
    state.query = "new value"
```

```python
# ❌ BAD - Don't manually show/hide elements
def toggle_visibility():
    div_ref.style.display = "none"  # Don't do this!

# ✅ GOOD - Use conditional rendering
@component
def MyComponent(state: State) -> Elements:
    return Div(
        style={"display": "block" if state.visible else "none"}
    )
```

## Integration with Third-Party Libraries

Refs are essential when integrating with libraries that expect DOM nodes:

```python
from trellis.core import component, DivRef
import plotly.graph_objects as go

@component
def PlotlyChart(data: list) -> Elements:
    container_ref = DivRef()
    
    def on_mount():
        # Pass the DOM node to Plotly
        fig = go.Figure(data=data)
        fig.show(container_ref.element)
    
    return Div(
        ref=container_ref,
        on_mount=on_mount
    )
```

## Summary

| Use Case | Approach | Example |
|----------|----------|---------|
| Trigger focus | Event | `FocusEvent().fire()` |
| Trigger scroll | Event | `ScrollEvent().fire()` |
| Play/pause video | Event | `PlayEvent().fire()` |
| Read input selection | Ref | `input_ref.selection_start` |
| Measure element | Ref | `div_ref.get_bounding_client_rect()` |
| Check scroll position | Ref | `div_ref.scroll_top` |
| Third-party library | Ref | `plotly.show(div_ref.element)` |

The general rule: **events for actions, refs for reading**.
