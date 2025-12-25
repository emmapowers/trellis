# Test Refactor Plan

This document outlines test changes needed after the rendering refactor (Phases 1-5).

## Background

The rendering refactor introduced a pure `reconcile_children()` function in Phase 3. The existing tests in `test_reconcile.py` and `test_reconcile_edge_cases.py` were written when reconciliation was impure. They use `Stateful.on_mount/on_unmount` hooks to observe reconciliation effects, but:

1. Lifecycle hooks are already well-tested in `test_state.py` and `test_state_edge_cases.py`
2. The pure reconciler function itself has no direct unit tests
3. The tests conflate two concerns: reconciliation algorithm correctness and integration behavior

## Changes Needed

### 1. Add Pure `reconcile_children()` Unit Tests

Create `tests/test_reconcile_pure.py` with direct tests for the pure function:

```python
from trellis.core.reconcile import reconcile_children, ReconcileResult

class TestReconcileChildren:
    """Unit tests for the pure reconcile_children function."""

    def test_empty_to_empty(self):
        """Empty lists produce empty result."""
        result = reconcile_children([], [])
        assert result == ReconcileResult(added=[], removed=[], matched=[], child_order=[])

    def test_empty_to_many(self):
        """All new IDs are added."""
        result = reconcile_children([], ["a", "b", "c"])
        assert result.added == ["a", "b", "c"]
        assert result.removed == []
        assert result.matched == []
        assert result.child_order == ["a", "b", "c"]

    def test_many_to_empty(self):
        """All old IDs are removed."""
        result = reconcile_children(["a", "b", "c"], [])
        assert result.added == []
        assert result.removed == ["a", "b", "c"]
        assert result.matched == []
        assert result.child_order == []

    def test_all_match(self):
        """Identical lists produce all matched."""
        result = reconcile_children(["a", "b", "c"], ["a", "b", "c"])
        assert result.added == []
        assert result.removed == []
        assert result.matched == ["a", "b", "c"]
        assert result.child_order == ["a", "b", "c"]

    def test_head_match_append(self):
        """Head matching with append at end."""
        result = reconcile_children(["a", "b"], ["a", "b", "c", "d"])
        assert result.added == ["c", "d"]
        assert result.removed == []
        assert set(result.matched) == {"a", "b"}

    def test_tail_match_prepend(self):
        """Tail matching with prepend at start."""
        result = reconcile_children(["c", "d"], ["a", "b", "c", "d"])
        assert result.added == ["a", "b"]
        assert result.removed == []
        assert set(result.matched) == {"c", "d"}

    def test_middle_removal(self):
        """Remove from middle (exercises head + tail scan)."""
        result = reconcile_children(["a", "b", "c", "d", "e"], ["a", "b", "d", "e"])
        assert result.added == []
        assert result.removed == ["c"]
        assert set(result.matched) == {"a", "b", "d", "e"}

    def test_middle_insertion(self):
        """Insert in middle."""
        result = reconcile_children(["a", "d"], ["a", "b", "c", "d"])
        assert set(result.added) == {"b", "c"}
        assert result.removed == []
        assert set(result.matched) == {"a", "d"}

    def test_reorder_same_elements(self):
        """Reordering preserves all as matched."""
        result = reconcile_children(["a", "b", "c"], ["c", "a", "b"])
        assert result.added == []
        assert result.removed == []
        assert set(result.matched) == {"a", "b", "c"}
        assert result.child_order == ["c", "a", "b"]

    def test_complete_replacement(self):
        """All old removed, all new added."""
        result = reconcile_children(["a", "b", "c"], ["x", "y", "z"])
        assert set(result.added) == {"x", "y", "z"}
        assert set(result.removed) == {"a", "b", "c"}
        assert result.matched == []

    def test_partial_overlap(self):
        """Some matched, some added, some removed."""
        result = reconcile_children(["a", "b", "c"], ["b", "c", "d"])
        assert result.added == ["d"]
        assert result.removed == ["a"]
        assert set(result.matched) == {"b", "c"}
```

### 2. Add `_escape_key()` Unit Tests

Add to `tests/test_rendering.py` or create new file:

```python
from trellis.core.rendering import _escape_key

class TestEscapeKey:
    """Tests for URL-encoding special characters in keys."""

    def test_no_special_chars(self):
        """Keys without special chars pass through."""
        assert _escape_key("simple") == "simple"
        assert _escape_key("with-dash") == "with-dash"
        assert _escape_key("with_underscore") == "with_underscore"

    def test_escape_colon(self):
        assert _escape_key("my:key") == "my%3Akey"

    def test_escape_at(self):
        assert _escape_key("item@home") == "item%40home"

    def test_escape_slash(self):
        assert _escape_key("row/5") == "row%2F5"

    def test_escape_percent(self):
        """Percent must be escaped first to avoid double-encoding."""
        assert _escape_key("100%") == "100%25"

    def test_multiple_special_chars(self):
        assert _escape_key("a:b@c/d%e") == "a%3Ab%40c%2Fd%25e"
```

### 3. Add Position ID Generation Tests

Add to `tests/test_rendering.py`:

```python
class TestPositionIdGeneration:
    """Tests for next_position_id() and position-based IDs."""

    def test_root_id_format(self):
        """Root node ID includes component identity."""
        @component
        def App():
            pass

        ctx = RenderTree(App)
        ctx.render()

        # Format: /@{id(component)}
        assert ctx.root_node.id.startswith("/@")
        assert str(id(App)) in ctx.root_node.id

    def test_child_id_includes_position(self):
        """Child IDs include position index."""
        @component
        def Child():
            pass

        @component
        def Parent():
            Child()
            Child()
            Child()

        ctx = RenderTree(Parent)
        ctx.render()

        # Children should have /0@, /1@, /2@ in their IDs
        child_ids = ctx.root_node.child_ids
        assert "/0@" in child_ids[0]
        assert "/1@" in child_ids[1]
        assert "/2@" in child_ids[2]

    def test_keyed_child_id_format(self):
        """Keyed children use :key@ format."""
        @component
        def Child():
            pass

        @component
        def Parent():
            Child(key="submit")

        ctx = RenderTree(Parent)
        ctx.render()

        child_id = ctx.root_node.child_ids[0]
        assert ":submit@" in child_id

    def test_different_component_types_different_ids(self):
        """Same position, different component = different ID."""
        @component
        def TypeA():
            pass

        @component
        def TypeB():
            pass

        show_a = [True]

        @component
        def Parent():
            if show_a[0]:
                TypeA()
            else:
                TypeB()

        ctx = RenderTree(Parent)
        ctx.render()
        id_a = ctx.root_node.child_ids[0]

        show_a[0] = False
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()
        id_b = ctx.root_node.child_ids[0]

        # Different components at same position get different IDs
        assert id_a != id_b
```

### 4. Refactor Existing Reconcile Tests

**Keep as integration tests** (move to `test_reconcile_integration.py` or leave in place):
- `test_key_based_matching_preserves_node_id` - verifies ID preservation through full render
- `test_position_type_matching_without_keys` - verifies position-based matching
- Tests in `TestBuiltinWidgetsReconciliation` - verify ReactComponent/HtmlElement work

**Remove or simplify** (functionality covered elsewhere):
- `TestElementLifecycle` - covered by `test_state.py`
- `TestStatefulLifecycle` - covered by `test_state.py` and `test_state_edge_cases.py`
- `TestLifecycleOrder` - covered by `test_state_edge_cases.py`

**Move to appropriate location**:
- `TestPropsComparison` - This tests the reuse optimization in `_place()`, not reconciliation. Consider moving to `test_rendering.py` or a new `test_reuse_optimization.py`.

### 5. Add Patch Generation Tests

The inline patch generation (Phase 4) has limited direct testing. Add to `test_message_handler.py` or new file:

```python
class TestPatchGeneration:
    """Tests for inline patch generation during reconciliation."""

    def test_add_patch_contains_subtree(self):
        """AddPatch includes full nested subtree."""
        # Verify that when a subtree is added, the AddPatch
        # contains the serialized children recursively
        ...

    def test_remove_patch_for_subtree(self):
        """RemovePatch generated for removed subtree root only."""
        # Children of removed node don't get individual RemovePatches
        ...

    def test_update_patch_only_changed_props(self):
        """UpdatePatch only includes props that changed."""
        ...

    def test_patch_order_remove_add_update(self):
        """Patches are ordered: remove, then add, then update."""
        ...
```

## Summary

| File | Action |
|------|--------|
| `tests/test_reconcile_pure.py` | **New** - Pure function tests for `reconcile_children()` |
| `tests/test_rendering.py` | **Add** - `_escape_key()` and position ID tests |
| `tests/test_reconcile.py` | **Refactor** - Remove lifecycle tests (covered elsewhere), keep ID preservation tests |
| `tests/test_reconcile_edge_cases.py` | **Keep** - Most tests are about list operations/ID preservation, not hooks |
| `tests/test_message_handler.py` | **Add** - More patch generation tests |

## Priority

1. **High**: Pure `reconcile_children()` tests - validates the core algorithm
2. **Medium**: `_escape_key()` tests - edge case coverage for ID generation
3. **Medium**: Position ID generation tests - documents expected ID format
4. **Low**: Refactoring existing tests - they work, just redundant
