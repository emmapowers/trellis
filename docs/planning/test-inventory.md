# Test Inventory Plan

This document outlines the plan to inventory existing tests before refactoring them to meet the quality standards in `tests/CLAUDE.md`.

## Target Structure

From `tests/CLAUDE.md`:

```
tests/
├── py/
│   ├── unit/          # Isolated Python unit tests
│   └── integration/   # Python modules working together
├── js/
│   ├── unit/          # Isolated JS unit tests
│   └── integration/   # JS modules working together
├── platform/          # Cross-language protocol tests
└── e2e/               # Full browser tests with Playwright
```

## Quality Standards

| Principle | Requirement |
|-----------|-------------|
| **Isolation** | Unit tests exercise one unit with dependencies faked or stubbed |
| **Clarity** | Test name describes behavior; one logical assertion per test |
| **Independence** | No dependence on run order or shared mutable state |
| **Maintenance** | Test public API and behavior, not internal details |

## Inventory Schema

Each test file will be analyzed and documented with:

| Field | Description |
|-------|-------------|
| **File** | Current path (e.g., `tests/test_state.py`) |
| **Module Under Test** | Primary module being tested (e.g., `trellis.core.state.stateful`) |
| **Test Classes** | List of test classes with brief descriptions |
| **Test Count** | Number of test methods |
| **Dependencies** | External modules used in tests (real vs mocked) |
| **Fixtures Used** | Shared fixtures or helpers from `helpers.py` |
| **Classification** | Unit / Integration / Platform / E2E |
| **Issues** | Quality problems identified (isolation, clarity, etc.) |
| **Target Location** | Recommended location in new structure |

### Per-Test Analysis Fields

For each test method, capture:

| Field | Description |
|-------|-------------|
| **Purpose** | What behavior is this test verifying and why does it matter? |
| **Invariants** | Properties that must hold; the contract being verified |
| **Assertion Coverage** | Do the actual assertions verify the stated invariants? (Yes / Partial / No + explanation) |

The **Invariants** field is the key to safe refactoring: when moving or restructuring tests, the invariant is what must be preserved. A test can change its implementation details but must still verify the same invariant.

## Execution Model

### How to Start a Session

When starting with fresh context, tell the assistant:

> Read `docs/planning/test-inventory.md` and continue the test inventory where we left off.

The assistant will:
1. Read this plan to understand the task and schema
2. Read `docs/planning/test-inventory-results.md` to find the next file
3. Read relevant source code, then the test file
4. Analyze and append results

### Batch and Checkpoint

Inventory is done **one test file per session** to allow careful analysis within context limits. Each session is independent and can start with fresh context.

**Session workflow:**
1. Read this plan (`docs/planning/test-inventory.md`)
2. Read the results file (`docs/planning/test-inventory-results.md`) to find where to continue
3. Pick the next un-inventoried file from the "Test Files to Inventory" list
4. Read the source code being tested (the module under test) to understand what behavior the tests should verify
5. Read the test file completely
6. Analyze each test method using the per-test schema
7. Append results to the results file
8. Mark the file as complete in the progress tracker

**Critical**: Each session must read the relevant source code before analyzing tests. You cannot assess whether a test verifies the right invariant without understanding what the code is supposed to do.

### Progress Tracking

The results file maintains a progress section at the top:

```markdown
## Progress

| File | Status |
|------|--------|
| test_state.py | Complete |
| test_app.py | Complete |
| test_base.py | In Progress |
| test_block_component.py | Not Started |
...
```

### Phase 1: File-by-File Analysis

For each test file:

1. **Gather context**: Read the module(s) under test to understand expected behavior
2. **Read test file**: Read the entire test file
3. **Analyze per-test**: For each test method, document Purpose, Invariants, Assertion Coverage
4. **Assess quality**: Note issues with isolation, clarity, independence, maintenance
5. **Classify**: Determine if unit, integration, platform, or e2e
6. **Write results**: Append to results file using the output format below

### Phase 2: Summary Analysis

After all files are inventoried:

1. Count tests by classification
2. Identify common patterns and anti-patterns
3. Map dependencies between test files
4. Prioritize files for refactoring based on issue severity

## Questions to Answer Per Test

When analyzing each test method, answer these questions to populate the per-test schema fields:

**Purpose & Invariants:**
1. **What is being tested?** (function, class, behavior)
2. **Why does this test exist?** What would break if this test didn't exist?
3. **What invariant does this verify?** State the property that must hold, not the implementation.
4. **Do the assertions actually verify that invariant?** Check for gaps or over-assertion.

**Quality Assessment:**
5. **Is it isolated?** (uses real dependencies vs stubs)
6. **Is it clear?** (name describes behavior, single concern)
7. **Is it independent?** (no shared mutable state, no order dependency)
8. **Does it test API or internals?** (public interface vs implementation details)

## Test Files to Inventory

Current test files in `tests/`:

```
test_app.py
test_base.py
test_block_component.py
test_composition_component.py
test_context.py
test_deep_trees.py
test_efficient_updates.py
test_event_handling.py
test_html.py
test_mutable.py
test_reconciler.py
test_rendering.py
test_serialization.py
test_state.py
test_state_edge_cases.py
test_tracked.py
test_widgets.py
integration/test_session.py
```

Supporting files:
- `helpers.py` - shared test utilities

## Inventory Output

Results are written to `docs/planning/test-inventory-results.md`.

### Output Format

```markdown
# Test Inventory Results

## Progress

| File | Status |
|------|--------|
| test_state.py | Complete |
| test_app.py | Not Started |
| ... | ... |

---

## test_state.py

**Module Under Test**: `trellis.core.state.stateful`
**Classification**: Unit
**Test Count**: 12
**Target Location**: `tests/py/unit/core/test_state.py`

### Dependencies
- Real: `trellis.core.rendering` (RenderSession)
- Mocked: None

### Fixtures Used
- `helpers.make_session()`

### Tests

#### `test_property_change_marks_node_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify that modifying a Stateful property marks dependent nodes for re-render |
| **Invariants** | When a tracked property changes, all nodes that read it during their last render must be marked dirty |
| **Assertion Coverage** | Yes - asserts node appears in session.dirty_nodes after property write |

#### `test_reading_property_registers_dependency`

| Field | Value |
|-------|-------|
| ... | ... |

### Quality Issues

- **Line 45**: Test uses real RenderSession instead of stub; should be integration test or mock the session
- **Line 78**: Test name `test_state_3` doesn't describe behavior

---

## test_app.py

(next file...)
```

### Final Sections (Phase 2)

After all files complete, add:

1. **Summary Statistics**: Counts by classification, issue types
2. **Common Patterns**: Good patterns to preserve
3. **Anti-Patterns**: Issues that appear across multiple files
4. **Refactoring Priority**: Ordered list based on issue severity and dependency

## Next Steps

After inventory completion:

1. Create migration plan based on priority
2. Refactor tests file-by-file
3. Move to new directory structure
4. Verify test coverage maintained
