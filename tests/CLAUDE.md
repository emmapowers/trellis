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
