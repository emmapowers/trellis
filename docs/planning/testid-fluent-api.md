# Plan: Global `testid` via Fluent `.testid()` Method

## Goal
Add a global `.testid()` method on ElementNode that can be called on any component and renders as `data-testid` in the browser DOM. This enables stable Playwright selectors without modifying individual component implementations.

## Design Approach

**Fluent API:** Instead of adding `testid=` parameter to every component, provide a `.testid()` method on ElementNode:

```python
Button(text="Save", on_click=save).testid("save-btn")
Counter().testid("counter")
```

**Key insight:** When `.testid()` is called on an auto-collected node, it finds and replaces that node in the current frame with a new node that has the testid set.

**Client-side:**
- HTML elements: Apply `data-testid` directly
- React widgets: Wrap in a span with `data-testid` (like CompositionComponent) - no widget changes needed

## Implementation

### 1. Add `testid` field to ElementNode
**File:** `src/trellis/core/rendering.py`

```python
@dataclass(frozen=True)
class ElementNode:
    component: IComponent
    props: FrozenProps = ()
    key: str | None = None
    testid: str | None = None  # NEW
    children: tuple[ElementNode, ...] = ()
    id: str = ""
    _auto_collected: bool = False
```

### 2. Add `.testid()` method to ElementNode
**File:** `src/trellis/core/rendering.py`

```python
def testid(self, id: str) -> ElementNode:
    """Set testid for this element, updating in frame if auto-collected.

    Returns a new ElementNode with testid set. If this node was auto-collected
    into a parent's frame, the frame is updated with the new node.

    Example:
        Button(text="Save").testid("save-btn")
    """
    from dataclasses import replace as dataclass_replace

    new_node = dataclass_replace(self, testid=id)

    # If this node was auto-collected, replace it in the frame
    ctx = get_active_render_tree()
    if ctx and self._auto_collected:
        frame = ctx.current_frame()
        if frame:
            for i, child in enumerate(frame.children):
                if child is self:  # Identity check
                    frame.children[i] = new_node
                    # Transfer auto_collected flag
                    object.__setattr__(new_node, "_auto_collected", True)
                    break

    return new_node
```

### 3. Serialize `testid` field
**File:** `src/trellis/core/serialization.py`

```python
return {
    "kind": node.component.element_kind.value,
    "type": node.component.element_name,
    "name": node.component.name,
    "key": node.key or node.id,
    "testid": node.testid,  # NEW - may be None
    "props": props,
    "children": [...],
}
```

### 4. Update SerializedElement type
**File:** `src/trellis/client/src/core/types.ts`

```typescript
interface SerializedElement {
  kind: string;
  type: string;
  name: string;
  key: string;
  testid?: string | null;  // NEW
  props: Record<string, unknown>;
  children: SerializedElement[];
}
```

### 5. Apply `data-testid` in renderNode()
**File:** `src/trellis/client/src/core/renderTree.tsx`

**For HTML elements:**
```typescript
if (HTML_TAGS.has(node.type)) {
  const { _text, ...htmlProps } = processedProps;
  const testIdAttr = node.testid ? { "data-testid": node.testid } : {};
  const allChildren = _text != null ? [_text, ...children] : children;
  return React.createElement(
    node.type,
    { ...htmlProps, ...testIdAttr, key },
    ...allChildren
  );
}
```

**For custom React components - wrap in span when testid present:**
```typescript
const element = (
  <Component key={key} {...processedProps} name={node.name}>
    {children}
  </Component>
);

// Wrap with testid span if needed (avoids modifying widget implementations)
if (node.testid) {
  return (
    <span data-testid={node.testid} style={{ display: "contents" }}>
      {element}
    </span>
  );
}
return element;
```

### 6. Update CompositionComponent wrapper
**File:** `src/trellis/client/src/widgets/CompositionComponent.tsx`

```typescript
interface CompositionComponentProps {
  name?: string;
  testid?: string | null;  // NEW
  children?: React.ReactNode;
}

export function CompositionComponent({
  name,
  testid,
  children,
}: CompositionComponentProps): React.ReactElement {
  return (
    <span
      data-trellis-component={name}
      data-testid={testid ?? undefined}  // NEW
      style={{ display: "contents" }}
    >
      {children}
    </span>
  );
}
```

## Files to Modify

| File | Change |
|------|--------|
| `src/trellis/core/rendering.py` | Add `testid` field and `.testid()` method to ElementNode |
| `src/trellis/core/serialization.py` | Serialize `testid` field |
| `src/trellis/client/src/core/types.ts` | Add `testid` to SerializedElement |
| `src/trellis/client/src/core/renderTree.tsx` | Apply `data-testid` to HTML elements, wrap widgets |
| `src/trellis/client/src/widgets/CompositionComponent.tsx` | Accept `testid` prop |

## Usage Examples

```python
@component
def MyApp():
    with h.Div().testid("main-container"):
        Button(text="Save", on_click=save).testid("save-btn")
        Counter().testid("counter")  # Works on CompositionComponents

        # Also works in loops
        for item in items:
            Card(key=item.id).testid(f"card-{item.id}")
```

Browser DOM:
```html
<div data-testid="main-container">
  <span data-testid="save-btn" style="display: contents">
    <button>Save</button>
  </span>
  <span data-trellis-component="Counter" data-testid="counter" style="display: contents">
    ...
  </span>
</div>
```

## Testing

1. Add `.testid()` calls to demo.py components
2. Run demo, use Playwright to verify `data-testid` attributes appear
3. Verify `page.getByTestId("save-btn")` works

## Benefits

- **Zero per-component changes** - no widget implementations touched
- **Fluent API** - clean, chainable syntax
- **Optional** - only adds DOM wrapper when testid is used
- **Works everywhere** - HTML elements, widgets, CompositionComponents
