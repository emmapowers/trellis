---
sidebar_position: 3
title: CSS Design
---

# Trellis CSS Design Document

## 1. Purpose

Trellis applications need a way to style components that is:

- **Type-safe** — catch typos and invalid values at type-check time, not in the browser
- **Pythonic** — feels natural alongside Trellis components, not a string-based escape hatch
- **Performant** — minimal runtime overhead, especially for static styles
- **Composable** — build complex styles from simple pieces, support variants and states
- **Scoped by default** — avoid class name collisions across modules without manual namespacing

String-based CSS (inline or external) provides none of these. Existing Python CSS libraries are either too verbose (dataclasses with every property) or lack type safety (dict-based). Trellis CSS provides a builder API that is concise, fully typed, and optimized for the framework's reactive model.

---

## 2. Table of Contents

1. [Purpose](#1-purpose)
2. [Table of Contents](#2-table-of-contents)
3. [Features](#3-features)
4. [Examples](#4-examples)
5. [Detailed Design](#5-detailed-design)
   - [5.1 Builder Pattern](#51-builder-pattern)
   - [5.2 Pipe Operator for Composition](#52-pipe-operator-for-composition)
   - [5.3 Pseudo-States](#53-pseudo-states)
   - [5.4 Responsive Breakpoints](#54-responsive-breakpoints)
   - [5.5 Units](#55-units)
   - [5.6 Colors](#56-colors)
   - [5.7 CSS Functions](#57-css-functions)
   - [5.8 Transforms](#58-transforms)
   - [5.9 Animations and Keyframes](#59-animations-and-keyframes)
   - [5.10 Named Classes vs Inline Styles](#510-named-classes-vs-inline-styles)
   - [5.11 Class Inheritance with extend()](#511-class-inheritance-with-extend)
   - [5.12 Scoping](#512-scoping)
   - [5.13 Tailwind-Style Utilities](#513-tailwind-style-utilities)
   - [5.14 Caching and Performance](#514-caching-and-performance)
   - [5.15 The css= Prop](#515-the-css-prop)

---

## 3. Features

### Core API

- **Builder pattern, not dataclasses** — More ergonomic, chainable, and enables caching via ops tuples. Dataclasses are too static for conditional composition.

- **Pipe operator (`|`) for composition** — Combines styles, pseudo-states, and breakpoints. Reads left-to-right, later wins for precedence. `| None` is a no-op for conditional composition.

- **Pseudo-states and breakpoints return builders** — `hover().bg(blue)` instead of `.hover(lambda s: s.bg(blue))`. Same pattern for `focus()`, `active()`, `disabled()`, `sm()`, `md()`, `lg()`, `xl()`.

- **Unified `css=` prop** — Framework decides whether to emit a class or inline style. Anonymous styles with pseudo-states auto-promote to generated classes.

- **Classes before inline styles** — `css() | style()` is valid (inline overrides class). `style() | css()` is an error. This ensures clear precedence without generating CSS.

### Type Safety

- **Units as types** — `px()`, `rem()`, `pct()`, `em()`, `vh()`, `vw()` return frozen objects that stringify to valid CSS. Type checker catches invalid combinations.

- **CSS functions as composable objects** — `rgb()`, `rgba()`, `hsl()`, `var()`, `calc()`, `linear_gradient()`. Chainable transforms: `translate(x).scale(y).rotate(z)`.

### Performance

- **Module-scope classes register at import** — Pre-compiled during startup, zero render-time cost. Framework warns if `css()` is declared inside a render function.

- **Ops tuple for cheap hashing** — Builder appends to an immutable tuple. Hash without building enables fast cache lookups.

- **LRU cache with bounded size** — Same style object → cache hit. Cache can persist to disk for warm starts.

- **Dev mode hot style warnings** — Tracks creation sites, warns when one line produces many unique style hashes.

### Scoping

- **File-scoped class names by default** — `css("btn")` in `button.py` generates `.button_btn_a7f3`. Prevents collisions across modules.

- **Explicit global opt-in** — `css("reset", Scope.Global)` for intentionally shared classes.

### Inheritance

- **`extend()` for build-time inheritance** — Copies all styles from a base class into a new class with overrides. Generates a single flattened class.

- **`|` for runtime composition** — Combines class names at render time. No flattening, relies on CSS cascade.

---

## 4. Examples

### 4.1 Inline text styling

```python
from trellis.css import style, rgb

@component
def Price(amount: float, sale: bool = False):
    # style() creates an anonymous inline style, conditionally applied
    html.span(
        css=style().color(rgb(220, 38, 38)).font_weight(700) if sale else None,
        children=[f"${amount:.2f}"],
    )
```

### 4.2 Declared class in a component

```python
from trellis.css import css, hover, px, rgb

# css() declares a named class, registered at module load
# hover() returns a builder for :hover pseudo-state
tag = (
    css("tag")
    .padding(px(4), px(10))
    .bg(rgb(243, 244, 246))
    .rounded(px(9999))
    | hover().bg(rgb(229, 231, 235))
)


@component
def Tag(label: str):
    html.span(css=tag, children=[label])
```

### 4.3 Extending a base class

```python
from trellis.css import css, hover, px, rem, rgb

# Base row style with hover state
row = (
    css("list-row")
    .display("flex")
    .align_items("center")
    .gap(rem(1))
    .padding(rem(0.75), rem(1))
    .cursor("pointer")
    .border_bottom(px(1), rgb(243, 244, 246))
    | hover().bg(rgb(249, 250, 251))
)

# extend() copies base styles into a new class with overrides
row_selected = row.extend("list-row-selected").bg(rgb(239, 246, 255)) | hover().bg(rgb(219, 234, 254))


@component
def ListRow(children, selected: bool = False, on_click: Callable[[], None] | None = None):
    # Pick class based on state - just a reference, no runtime cost
    html.div(css=row_selected if selected else row, on_click=on_click, children=children)
```

---

## 5. Detailed Design

### 5.1 Builder Pattern

The core API uses a builder pattern where each method returns a new builder instance. Internally, builders accumulate operations as an immutable tuple, enabling cheap hashing and caching.

```python
class StyleBuilder:
    __slots__ = ("_ops",)
    
    def __init__(self, ops: tuple = ()):
        self._ops = ops
    
    def bg(self, color: Color) -> "StyleBuilder":
        return StyleBuilder((*self._ops, ("bg", color)))
    
    def padding(self, *args: Length) -> "StyleBuilder":
        return StyleBuilder((*self._ops, ("padding", args)))
    
    def __hash__(self) -> int:
        return hash(self._ops)
```

**Entry points:**

- `style()` — returns an anonymous `StyleBuilder` for inline styles
- `css(name)` — returns a `ClassBuilder` that registers a named class

**Usage:**

```python
# Anonymous inline
style().bg(rgb(255, 0, 0)).padding(px(8))

# Named class
css("btn").bg(rgb(0, 123, 255)).padding(px(8), px(16))
```

Methods should cover all common CSS properties with Pythonic names (snake_case). Properties that take complex values accept the appropriate unit/function types.

---

### 5.2 Pipe Operator for Composition

The `|` operator combines styles. For named classes, it concatenates class names. For inline styles, it merges properties (later wins).

```python
def __or__(self, other: "StyleBuilder | None") -> "StyleBuilder":
    if other is None:
        return self
    return StyleBuilder((*self._ops, ("merge", other._ops)))
```

**Precedence:** Left-to-right, later values override earlier for the same property.

**Conditional composition:** `| None` is a no-op, enabling:

```python
styles = base | (variant if condition else None) | (override if other_condition else None)
```

**Ordering restriction:** Classes must come before inline styles. `css() | style()` is valid (inline overrides class via natural CSS specificity). `style() | css()` is an error (class cannot override inline without generating CSS).

```python
# Valid - class first, inline override
css("btn") | style().bg(red)
# → class="btn" style="background-color: red"

# Valid - multiple classes, then inline
btn | btn_primary | style().opacity(0.5)
# → class="btn btn-primary" style="opacity: 0.5"

# Error - class after inline
style().bg(red) | css("btn")
# → RuntimeError: class cannot follow inline style

# Error - class between inline styles  
style().bg(red) | css("btn") | style().padding(px(8))
# → RuntimeError: class cannot follow inline style
```

**Type-level enforcement:** Use separate base types (`ClassStyle` and `InlineStyle`) with overloaded `__or__` operators. `ClassStyle | InlineStyle` returns a `MixedStyle` that only accepts further `InlineStyle`. `InlineStyle | ClassStyle` raises `TypeError` at type-check time (or runtime if not caught).

---

### 5.3 Pseudo-States

Pseudo-state functions return a builder scoped to that state. They compose with `|`.

```python
def hover() -> PseudoBuilder:
    return PseudoBuilder("hover")

def focus() -> PseudoBuilder:
    return PseudoBuilder("focus")

def active() -> PseudoBuilder:
    return PseudoBuilder("active")

def disabled() -> PseudoBuilder:
    return PseudoBuilder("disabled")
```

**Usage:**

```python
btn = (
    css("btn")
    .bg(blue)
    .color(white)
    | hover().bg(dark_blue)
    | focus().ring(px(2), blue_300)
    | active().bg(darker_blue)
    | disabled().opacity(0.5).cursor("not-allowed")
)
```

**Multiple properties:** Pseudo builders are chainable, so `hover().bg(x).color(y)` applies both on hover.

**Anonymous styles with pseudo-states:** When `style()` is combined with pseudo-states, the framework auto-generates a class name (content-hashed) since inline styles cannot express `:hover`.

---

### 5.4 Responsive Breakpoints

Breakpoint functions work like pseudo-states, returning a builder scoped to a media query.

```python
def sm() -> BreakpointBuilder:  # min-width: 640px
    return BreakpointBuilder("sm")

def md() -> BreakpointBuilder:  # min-width: 768px
    return BreakpointBuilder("md")

def lg() -> BreakpointBuilder:  # min-width: 1024px
    return BreakpointBuilder("lg")

def xl() -> BreakpointBuilder:  # min-width: 1280px
    return BreakpointBuilder("xl")
```

**Usage:**

```python
layout = (
    css("layout")
    .padding(px(16))
    .columns(1)
    | sm().columns(2)
    | md().columns(3).padding(px(24))
    | lg().columns(4).padding(px(32))
)
```

**Combining with pseudo-states:**

```python
card = (
    css("card")
    .shadow("sm")
    | hover().shadow("md")
    | md(hover()).shadow("lg")  # larger shadow on hover, only on md+
)
```

---

### 5.5 Units

Units are frozen dataclasses that stringify to valid CSS. Type aliases group related units for property signatures.

```python
@dataclass(frozen=True, slots=True)
class Px:
    value: float
    def __str__(self) -> str:
        return f"{self.value}px"

@dataclass(frozen=True, slots=True)
class Rem:
    value: float
    def __str__(self) -> str:
        return f"{self.value}rem"

@dataclass(frozen=True, slots=True)
class Pct:
    value: float
    def __str__(self) -> str:
        return f"{self.value}%"

# Shorthand constructors
def px(v: float) -> Px: return Px(v)
def rem(v: float) -> Rem: return Rem(v)
def pct(v: float) -> Pct: return Pct(v)
def em(v: float) -> Em: return Em(v)
def vh(v: float) -> Vh: return Vh(v)
def vw(v: float) -> Vw: return Vw(v)

# Type aliases for property signatures
Length = Px | Rem | Em | Pct | Vh | Vw
LengthOrAuto = Length | Literal["auto"]
```

**Angle units** for transforms/gradients:

```python
def deg(v: float) -> Deg: return Deg(v)
def rad(v: float) -> Rad: return Rad(v)

Angle = Deg | Rad
```

**Time units** for animations/transitions:

```python
def ms(v: float) -> Ms: return Ms(v)
def s(v: float) -> S: return S(v)

Time = Ms | S
```

---

### 5.6 Colors

Color functions return frozen objects. Support RGB, RGBA, HSL, and CSS variable references.

```python
@dataclass(frozen=True, slots=True)
class Rgb:
    r: int
    g: int
    b: int
    def __str__(self) -> str:
        return f"rgb({self.r}, {self.g}, {self.b})"

@dataclass(frozen=True, slots=True)
class Rgba:
    r: int
    g: int
    b: int
    a: float
    def __str__(self) -> str:
        return f"rgba({self.r}, {self.g}, {self.b}, {self.a})"

def rgb(r: int, g: int, b: int, a: float | None = None) -> Rgb | Rgba:
    if a is not None:
        return Rgba(r, g, b, a)
    return Rgb(r, g, b)

def hsl(h: int, s: float, l: float) -> Hsl:
    return Hsl(h, s, l)

Color = Rgb | Rgba | Hsl | Var | Literal["transparent", "currentColor", "inherit"] | str
```

**Color scales** (generated, Tailwind-style):

```python
class colors:
    blue_50 = rgb(239, 246, 255)
    blue_100 = rgb(219, 234, 254)
    blue_500 = rgb(59, 130, 246)
    blue_600 = rgb(37, 99, 235)
    # ... etc for all colors and shades
```

---

### 5.7 CSS Functions

CSS functions like `calc()`, `var()`, and gradients are typed objects.

**calc():**

```python
@dataclass(frozen=True, slots=True)
class Calc:
    expr: str
    def __str__(self) -> str:
        return f"calc({self.expr})"

# With operator overloading on units
width = calc(pct(100) - px(240))  # calc(100% - 240px)
```

**var():**

```python
@dataclass(frozen=True, slots=True)
class Var:
    name: str
    fallback: str | None = None
    def __str__(self) -> str:
        if self.fallback:
            return f"var(--{self.name}, {self.fallback})"
        return f"var(--{self.name})"

# Usage
style().color(var("text-primary")).bg(var("bg-surface", "#ffffff"))
```

**Gradients:**

```python
def linear_gradient(direction: Angle, *stops: Color) -> LinearGradient:
    return LinearGradient(direction, stops)

def radial_gradient(*stops: Color, shape: str = "ellipse") -> RadialGradient:
    return RadialGradient(stops, shape)

# Usage
style().bg(linear_gradient(deg(135), colors.blue_500, colors.purple_600))
```

**url():**

```python
def url(path: str) -> Url:
    return Url(path)

style().bg(url("/images/pattern.svg"))
```

---

### 5.8 Transforms

Transforms are chainable. Each transform function returns a `Transform` object with a `.then()` method (or use method chaining directly).

```python
@dataclass(frozen=True, slots=True)
class Transform:
    ops: tuple
    
    def translate(self, x: Length, y: Length | None = None) -> "Transform":
        return Transform((*self.ops, ("translate", x, y)))
    
    def scale(self, x: float, y: float | None = None) -> "Transform":
        return Transform((*self.ops, ("scale", x, y)))
    
    def rotate(self, angle: Angle) -> "Transform":
        return Transform((*self.ops, ("rotate", angle)))
    
    def skew(self, x: Angle, y: Angle | None = None) -> "Transform":
        return Transform((*self.ops, ("skew", x, y)))

# Entry point
def translate(x: Length, y: Length | None = None) -> Transform:
    return Transform(()).translate(x, y)

def scale(x: float, y: float | None = None) -> Transform:
    return Transform(()).scale(x, y)

def rotate(angle: Angle) -> Transform:
    return Transform(()).rotate(angle)
```

**Usage:**

```python
card = (
    css("card")
    .transform(translate(px(0), px(0)))
    .transition("transform", ms(150))
    | hover().transform(translate(px(0), px(-4)).scale(1.02))
)
```

---

### 5.9 Animations and Keyframes

Keyframes are declared with a builder. Animations reference keyframes by name or inline.

```python
class KeyframesBuilder:
    def __init__(self, name: str):
        self.name = name
        self.frames: list[tuple[int, StyleBuilder]] = []
    
    def frame(self, offset: int, **props) -> "KeyframesBuilder":
        # offset is 0-100 (percent)
        self.frames.append((offset, style_from_props(props)))
        return self

def keyframes(name: str) -> KeyframesBuilder:
    return KeyframesBuilder(name)
```

**Usage:**

```python
fade_in = (
    keyframes("fade-in")
    .frame(0, opacity=0)
    .frame(100, opacity=1)
)

slide_up = (
    keyframes("slide-up")
    .frame(0, opacity=0, transform=translate(px(0), px(20)))
    .frame(100, opacity=1, transform=translate(px(0), px(0)))
)

animated_box = (
    css("animated-box")
    .animation(fade_in, duration=ms(300), timing="ease-out", fill="forwards")
)
```

**Animation properties:**

```python
.animation(
    keyframes,           # KeyframesBuilder or name string
    duration: Time,
    timing: Literal["linear", "ease", "ease-in", "ease-out", "ease-in-out"] | CubicBezier = "ease",
    delay: Time | None = None,
    iteration_count: int | Literal["infinite"] = 1,
    direction: Literal["normal", "reverse", "alternate", "alternate-reverse"] = "normal",
    fill: Literal["none", "forwards", "backwards", "both"] = "none",
)
```

---

### 5.10 Named Classes vs Inline Styles

**`css(name)`** declares a named class:

- Registered with the framework at module load time
- Compiled once, referenced by class name at render time
- Supports pseudo-states and breakpoints natively
- File-scoped by default

**`style()`** creates an anonymous inline style:

- Evaluated at render time (but cached by ops hash)
- Emits `style="..."` attribute when possible
- Auto-promotes to generated class if pseudo-states or breakpoints are used

**Choosing between them:**

| Use case | Approach |
|----------|----------|
| Reusable component styles | `css()` at module scope |
| One-off dynamic styling | `style()` inline |
| Styles based on props | `style()` or pre-declared variants with `css()` |

---

### 5.11 Class Inheritance with extend()

`extend()` creates a new named class based on an existing one. All properties are copied at build time, producing a single flattened class.

```python
class ClassBuilder:
    def extend(self, new_name: str) -> "ClassBuilder":
        # Returns a new ClassBuilder with all ops from self,
        # registered under new_name
        return ClassBuilder(new_name, base_ops=self._ops)
```

**Usage:**

```python
btn = css("btn").padding(px(8), px(16)).rounded(px(4))

btn_primary = btn.extend("btn-primary").bg(blue).color(white)
btn_danger = btn.extend("btn-danger").bg(red).color(white)
```

**Contrast with `|`:**

- `extend()` — build-time, flattens into one class, parent changes don't propagate
- `|` — runtime, concatenates class names, relies on CSS cascade

---

### 5.12 Scoping

By default, class names are scoped to the Python file where they are declared. This prevents collisions without requiring manual namespacing.

```python
# components/button.py
btn = css("btn").bg(blue)
# → generates: .button_btn_a7f3 { ... }

# components/card.py  
btn = css("btn").bg(green)  # different file, no collision
# → generates: .card_btn_b2e1 { ... }
```

**Explicit global scope:**

```python
from trellis.css import css, Scope

reset = css("reset", Scope.Global).margin(px(0)).padding(px(0))
# → generates: .reset { ... }
```

**Implementation:** The framework inspects the call site (via `inspect` or a frame hack) to determine the source file. The scope suffix is a hash of the file path.

---

### 5.13 Tailwind-Style Utilities

For rapid prototyping or utility-first workflows, pre-defined atomic classes are available under the `tw` namespace.

```python
@dataclass(frozen=True, slots=True)
class Utility:
    name: str
    prop: str
    value: str
    
    def __str__(self) -> str:
        return self.name
    
    def __or__(self, other: "Utility | UtilitySet | None") -> "UtilitySet":
        if other is None:
            return UtilitySet((self,))
        if isinstance(other, UtilitySet):
            return UtilitySet((self, *other.utilities))
        return UtilitySet((self, other))

class tw:
    flex = Utility("flex", "display", "flex")
    block = Utility("block", "display", "block")
    hidden = Utility("hidden", "display", "none")
    
    p_1 = Utility("p-1", "padding", "0.25rem")
    p_2 = Utility("p-2", "padding", "0.5rem")
    p_4 = Utility("p-4", "padding", "1rem")
    # ... etc
    
    bg_blue_500 = Utility("bg-blue-500", "background-color", "#3b82f6")
    text_white = Utility("text-white", "color", "#ffffff")
    # ... etc
```

**Usage:**

```python
html.div(
    css=tw.flex | tw.p_4 | tw.bg_blue_500 | hover(tw.bg_blue_600),
    children=[...],
)
```

**With pseudo-states and breakpoints:**

```python
btn_classes = (
    tw.flex | tw.justify_center | tw.py_2 | tw.px_4
    | hover(tw.bg_blue_600)
    | focus(tw.ring_2)
    | sm(tw.px_6)
)
```

Utilities are generated from scales (spacing, colors, typography) and can be extended by the application.

---

### 5.14 Caching and Performance

**Ops tuple hashing:**

Every builder method appends to an immutable tuple. The tuple is hashable, so we can cache compiled styles by hash without running `build()`.

```python
_style_cache: dict[int, CompiledStyle] = {}

def resolve_style(builder: StyleBuilder) -> CompiledStyle:
    h = hash(builder)
    if h not in _style_cache:
        _style_cache[h] = builder.build()
    return _style_cache[h]
```

**Bounded cache:**

Use `cachetools.LRUCache` to prevent unbounded growth:

```python
from cachetools import LRUCache

_style_cache = LRUCache(maxsize=10_000)
```

**Persistent cache:**

For faster startup, serialize the cache to disk:

```python
def save_cache(path: Path):
    with open(path, "wb") as f:
        pickle.dump(dict(_style_cache), f)

def load_cache(path: Path):
    if path.exists():
        with open(path, "rb") as f:
            _style_cache.update(pickle.load(f))
```

**Dev mode warnings:**

Track where styles are created. Warn if a single source location produces many unique hashes:

```python
_creation_sites: dict[tuple[str, int], set[int]] = {}  # (file, line) -> hashes

def track_creation(builder: StyleBuilder, frame: FrameInfo):
    key = (frame.filename, frame.lineno)
    _creation_sites.setdefault(key, set()).add(hash(builder))
    
    if len(_creation_sites[key]) > 50:
        warnings.warn(
            f"Hot style at {key[0]}:{key[1]} - {len(_creation_sites[key])} unique styles. "
            "Consider hoisting to module scope.",
            StylePerformanceWarning,
        )
```

---

### 5.15 The css= Prop

Trellis elements accept a `css=` prop that handles both classes and inline styles. The framework inspects the value and emits the appropriate attributes.

**Rules:**

1. Named class (`ClassBuilder`) → emits `class="..."`
2. Anonymous style (`StyleBuilder`) without pseudo-states → emits `style="..."`
3. Anonymous style with pseudo-states → auto-generates a class, emits `class="..."`
4. Combined with `|` → concatenates classes or merges inline properties
5. `None` → no styling

**Example outputs:**

```python
html.button(css=btn)
# → <button class="button_btn_a7f3">

html.button(css=style().bg(blue))
# → <button style="background-color: rgb(0, 0, 255)">

html.button(css=style().bg(blue) | hover().bg(dark_blue))
# → <button class="_ts_7f3a">
# Framework emits: ._ts_7f3a { background-color: blue; }
#                  ._ts_7f3a:hover { background-color: darkblue; }

html.button(css=btn | tw.px_8 | hover(tw.scale_105))
# → <button class="button_btn_a7f3 px-8 hover:scale-105">

html.button(css=btn | style().opacity(0.5))
# → <button class="button_btn_a7f3" style="opacity: 0.5">
```

**Restriction:** Classes must come before inline styles. The framework enforces this ordering to ensure predictable specificity without generating CSS. Use separate types (`ClassStyle`, `InlineStyle`, `MixedStyle`) with overloaded `__or__` to catch violations at type-check time when possible.

```python
# Error at type-check (or runtime)
style().bg(red) | css("btn")  # TypeError: ClassStyle cannot follow InlineStyle
```
