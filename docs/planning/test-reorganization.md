# Test Reorganization Plan

This document summarizes the findings from the test inventory and outlines a phased plan for reorganizing the test suite.

## Current State

**Scale**: 31 test files, ~27,000 lines of test code
- Python: 27 test files
- JavaScript: 4 test files
- Largest: `test_tracked.py` (2061 lines), `test_widgets.py` (1692 lines), `test_mutable.py` (937 lines)

**Classification Breakdown** (from inventory):

| Classification | Files | Notes |
|---------------|-------|-------|
| Pure Unit | 6 | test_reconciler, test_messages, test_ports, test_serve_platform, test_routes, test_base |
| Pure Integration | 10 | Most rendering/state tests |
| Mixed | 11 | Need splitting |

---

## Key Problems

### 1. Classification Mismatch

Most tests labeled "unit" are actually integration tests—they instantiate `RenderSession`, call `render()`, and exercise the full component system. Only ~6 files are truly isolated.

**Examples of misclassified:**
- `test_state.py` - uses RenderSession for 19 of 21 tests
- `test_widgets.py` - every test renders full component trees
- `test_composition_component.py` - needs render pipeline

### 2. Large Files Needing Splits

| File | Lines | Split Into |
|------|-------|-----------|
| `test_tracked.py` | 2061 | unit (mutations) + integration (reactivity) |
| `test_widgets.py` | 1692 | by widget category (layout, inputs, charts) |
| `test_mutable.py` | 937 | unit (class/snapshot) + integration (serialization/rerender) |
| `test_rendering.py` | 877 | unit (Element) + integration (concurrency, lifecycle) |
| `test_message_handler.py` | 801 | unit (message conversion) + integration (render loop) |
| `test_fine_grained_classes.py` | 728 | one file per class (ElementStore, StateStore, etc.) |

### 3. Tests Accessing Internals

62 accesses to private attributes across 6 files:
- `test_state.py`: `_state_props`, `_session_ref`, `watchers`
- `test_tracked.py`: `_deps`, `_owner`, `_attr`
- `test_message_handler.py`: internal state
- `test_trellis.py`: `app._args`

These create fragile tests that break on refactoring even when behavior is unchanged.

### 4. Missing Infrastructure

- **No `conftest.py`** - no shared fixtures
- **Minimal `helpers.py`** - only `render_to_tree()`
- **No test markers** - no way to skip slow/network tests
- **Repeated patterns** - same render-and-check pattern copied everywhere

### 5. Missing Tests

| Area | Gap |
|------|-----|
| `Trellis.serve()` | No tests (needs platform mocking) |
| Widget error cases | No tests for invalid props, missing required props |
| Reconciler edge cases | Duplicate key handling in real renders |
| Context error messages | Error message quality not verified |

---

## Fixture Recommendations

Create `tests/py/conftest.py` with:

```python
# Session fixtures
@pytest.fixture
def render_session():
    """Fresh RenderSession for each test."""
    return RenderSession(root=lambda: None)

@pytest.fixture
def rendered(render_session):
    """Render a component and return (session, root_element, tree_dict)."""
    def _render(component):
        render_session.root = component
        patches = render(render_session)
        tree = serialize_node(patches[0].node, render_session)
        return render_session, render_session.root_element, tree
    return _render

# Isolation helpers
@pytest.fixture
def mock_element_state():
    """Factory for mock ElementState objects without render context."""
    def _make(id="test-1", dirty=False, local_state=None):
        # Return mock that satisfies ElementState protocol
        ...
    return _make

# Markers
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks test as slow")
    config.addinivalue_line("markers", "network: requires network access")
```

**Key fixtures to add:**
1. `render_session` - clean session per test
2. `rendered` - helper that renders and returns useful objects
3. `mock_element_state` - for unit testing without render context
4. `mock_stateful` - for testing Stateful subclasses in isolation
5. `capture_patches` - helper to capture and inspect render patches

---

## Quality Criteria Additions

Add to `tests/CLAUDE.md`:

### Avoid Internal Access

```markdown
### Internal Details
- Test via public API, not `_private` attributes
- If testing internals is necessary, document WHY in a comment
- Private attribute tests should be tagged with `# INTERNAL TEST` comment
```

### Test Markers

```markdown
### Markers
- `@pytest.mark.slow` - Tests taking >1s or requiring subprocess
- `@pytest.mark.network` - Tests requiring network access
- `@pytest.mark.platform` - Cross-platform protocol tests
```

### Fixture-First Pattern

```markdown
### DRY Test Setup
- Use fixtures from conftest.py for common patterns
- If you write the same setup in 3+ tests, extract a fixture
- Prefer parametrize over copy-paste test variations
```

---

## CLAUDE.md Organization

### Keep in Root `CLAUDE.md`:
- Project architecture overview
- Tech stack and dependencies
- Commands (`pixi run test`, etc.)
- Import conventions
- General coding style

### Keep in `tests/CLAUDE.md`:
- Test directory structure
- Test categories (unit/integration/platform/e2e)
- Quality standards (isolation, clarity, independence, maintenance)
- Fixture descriptions and usage
- Test-specific patterns and conventions

### Add New `tests/py/conftest.py`:
- All shared Python fixtures
- Marker definitions
- Common test utilities

---

## Phased Reorganization Plan

### Phase 1: Infrastructure Setup

**Goal**: Establish foundation without moving tests

1. Create `tests/py/conftest.py` with core fixtures
2. Create `tests/js/test-utils.ts` for JS test utilities
3. Add pytest markers for slow/network tests
4. Update `tests/CLAUDE.md` with fixture documentation

**Deliverables:**
- `conftest.py` with `render_session`, `rendered`, `mock_element_state`
- Updated `tests/CLAUDE.md`
- Working marker configuration

### Phase 2: Create Directory Structure

**Goal**: Set up target hierarchy

```
tests/
├── py/
│   ├── conftest.py     # shared fixtures
│   ├── unit/
│   │   └── .gitkeep
│   └── integration/
│       └── .gitkeep
├── js/
│   ├── unit/
│   │   └── .gitkeep
│   └── integration/
│       └── .gitkeep
├── platform/
│   └── .gitkeep
└── e2e/
    └── .gitkeep
```

### Phase 3: Split Large Files

**Goal**: Break mixed files into classifiable units (do not move yet)

Priority order:
1. `test_fine_grained_classes.py` → 4 files (one per class)
2. `test_tracked.py` → `test_tracked_unit.py` + `test_tracked_integration.py`
3. `test_mutable.py` → `test_mutable_unit.py` + `test_mutable_integration.py`
4. `test_rendering.py` → `test_element_unit.py` + `test_rendering_integration.py`
5. `test_message_handler.py` → `test_message_conversion_unit.py` + `test_render_loop_integration.py`
6. `test_widgets.py` → by category (layout, inputs, charts, etc.)

**Rule**: Each resulting file should be <400 lines.

### Phase 4: Migrate to New Structure

**Goal**: Move files to proper locations

Batch migrations:
1. Move all pure unit tests to `py/unit/`
2. Move all pure integration tests to `py/integration/`
3. Move JS tests to corresponding directories
4. Update imports and verify tests pass after each batch

### Phase 5: Refactor Internal Access

**Goal**: Remove private attribute access where possible

Files to refactor:
1. `test_state.py` - expose needed state via public API or accept testing internals
2. `test_tracked.py` - reduce `_deps`, `_owner` access
3. `test_message_handler.py` - mock at boundaries

**Rule**: If internal access is truly necessary, add `# INTERNAL TEST: <reason>` comment.

### Phase 6: Fill Test Gaps

**Goal**: Add missing test coverage

Priority additions:
1. `Trellis.serve()` with platform mocking
2. Widget error cases (invalid props, type errors)
3. Context error message quality
4. Reconciler duplicate key handling in integration context

---

## Summary: What Goes Where

| Content | Location |
|---------|----------|
| Test directory structure | `tests/CLAUDE.md` |
| Test quality principles | `tests/CLAUDE.md` |
| Fixture reference | `tests/CLAUDE.md` |
| pytest/vitest commands | Root `CLAUDE.md` (existing) |
| TDD workflow | Root `CLAUDE.md` (existing) |
| New marker documentation | `tests/CLAUDE.md` |

The root `CLAUDE.md` focuses on "how to work with this project" while `tests/CLAUDE.md` focuses on "how to write good tests for this project."

---

## Recommended First Steps

1. **Create the infrastructure** (Phase 1) - this enables all other work
2. **Split `test_fine_grained_classes.py`** - cleanest split, good practice
3. **Split `test_tracked.py`** - largest file, clear unit/integration boundary
