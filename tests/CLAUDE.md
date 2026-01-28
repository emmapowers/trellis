# Tests

## Structure

```
tests/
├── py/
│   ├── unit/          # Isolated Python unit tests
│   └── integration/   # Python modules working together
├── js/
│   ├── unit/          # Isolated JS unit tests
│   └── integration/   # JS modules working together
├── platform/          # Cross-language protocol tests (Node + Python over socket)
└── e2e/               # Full browser tests with Playwright
```

## Test Categories

**Unit tests** (`py/unit/`, `js/unit/`): Test a single function, class, or module in isolation. Dependencies are faked or stubbed. Fast and deterministic.

**Integration tests** (`py/integration/`, `js/integration/`): Test multiple modules working together within one language. May use real dependencies but stay within the language boundary.

**Platform tests** (`platform/`): Test the Python ↔ JS bridge. These start a headless Node client and a Trellis Python backend communicating over a socket. Validates message serialization, the client-server protocol, and core rendering logic without needing a browser.

**End-to-end tests** (`e2e/`): Full browser tests using Playwright. Test the complete application in a real browser environment. Use for behavior that requires a real DOM: event handling, focus, layout, browser-specific quirks.

## Frameworks

- **Python**: pytest
- **JavaScript**: vitest
- **E2E**: Playwright

## Best Practices

### Isolation
- Unit tests exercise one unit with dependencies faked or stubbed
- If a test needs real collaborators from other modules, it belongs in integration or higher
- Short setup; long setup suggests too many dependencies or the test is doing too much

### Clarity
- Test name describes behavior, not implementation (`rejects_empty_input` not `test_validate`)
- One logical assertion per test - a failure should pinpoint what broke
- Tests should be readable without referring to the implementation

### Independence
- No dependence on run order or shared mutable state
- Each test sets up what it needs and cleans up after
- No "this test only passes after that test"

### Maintenance
- Test public API and behavior, not internal details
- Refactoring should not break tests if behavior is unchanged
- Delete tests when the behavior they cover is intentionally removed
- Treat test code with the same care as production code

### Organization
- Test file structure mirrors source structure
- File and test names make it easy to find tests from code and code from tests
- Keep test utilities and fixtures in a shared location within each test category

### Internal Details
- Test via public API, not `_private` attributes
- If testing internals is necessary, document WHY in a comment
- Private attribute tests should be tagged with `# INTERNAL TEST: <reason>` comment

### DRY Test Setup
- Use fixtures from conftest.py for common patterns
- If you write the same setup in 3+ tests, extract a fixture
- Prefer parametrize over copy-paste test variations

## Markers

Use markers to categorize tests that need special handling:

```python
@pytest.mark.slow      # Tests taking >1s or requiring subprocess
@pytest.mark.network   # Tests requiring network access
@pytest.mark.platform  # Cross-platform protocol tests
```

Run excluding slow tests: `pytest -m "not slow"`

## Optional Dependencies

Some platforms have runtime dependencies not available in CI (pytauri for desktop).

```python
from tests.helpers import requires_pytauri

@requires_pytauri
class TestDesktopFeature:
    def test_something(self) -> None:
        # Import inside test - class marker skips before import runs
        from trellis.platforms.desktop import DesktopPlatform
        ...
```

The import must be inside the test/class body so the skip runs before Python attempts the import.

## Python Fixtures

Shared fixtures are defined in `conftest.py`. **All integration tests have been migrated to use these fixtures.** Use them instead of writing custom setup.

### Component Creation

```python
def test_with_component(make_component):
    """make_component creates a simple CompositionComponent."""
    comp = make_component("MyComp")
    assert comp.name == "MyComp"

def test_with_noop(noop_component):
    """noop_component is a pre-made component that does nothing."""
    session = RenderSession(noop_component)
```

### Rendering

```python
def test_render_result(rendered):
    """rendered() returns RenderResult with session, patches, and tree."""
    @component
    def MyComp():
        Label(text="Hello")

    result = rendered(MyComp)
    assert result.tree["component"] == "MyComp"
    assert len(result.patches) > 0
    assert result.root_element is not None
```

### Incremental Updates

```python
def test_incremental(capture_patches):
    """capture_patches tracks patches across multiple renders."""
    capture = capture_patches(MyComp)
    capture.render()  # Initial render

    state.value = "new"
    patches = capture.render_dirty()  # Captures update patches
    assert capture.patch_count == 2
```

### Unit Test Mocks

```python
def test_with_mock_state(mock_element_state):
    """mock_element_state creates mock ElementState without render context."""
    state = mock_element_state(id="test-1", local_state={"count": 0})
    # Use in unit tests that don't need full rendering
```

## JavaScript Utilities

Shared utilities are in `js/trellis-test-utils.ts`. Import what you need:

```typescript
import { makeElement, makePatch, makeHelloResponse } from "../trellis-test-utils";

// Create elements
const button = makeElement("btn-1", "Button", { text: "Click" });

// Create patches
const addPatch = makeAddPatch(button, "parent-id");
const updatePatch = makeUpdatePatch("btn-1", { text: "New" });

// Create messages
const helloResp = makeHelloResponse("session-123", "1.0.0");
```
