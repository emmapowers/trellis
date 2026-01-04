# Router Implementation Plan

## Development Approach

**This implementation follows Test-Driven Development (TDD).** Use the `test-driven-development` skill for all features:

1. Write failing tests first
2. Implement minimum code to pass
3. Refactor while keeping tests green
4. Commit at logical checkpoints

## Overview

Add client-side routing to Trellis with `RouterState`, `Route`, and `Link` components. Routing state is reactive (extends `Stateful`) and works across all platforms.

## Design Decisions

- **Manual provision**: `with RouterState():` at root (like other state)
- **Exact matching**: React Router v6 style (no prefix matching)
- **Param syntax**: Colon style `/users/:id`
- **Embedded mode**: `Trellis(embedded=True)` for desktop and iframe scenarios
- **Initial URL**: Sent in HelloMessage (not separate message)
- **Private fields**: `_path`, `_params`, etc. with read-only properties

## API

```python
from trellis import RouterState, Route, Link, router

@component
def App():
    with RouterState():
        Route("/", HomePage)
        Route("/users", UsersPage)
        Route("/users/:id", UserDetailPage)
        Route("*", NotFoundPage)

@component
def UserDetailPage():
    user_id = router().params["id"]
    Link("/users", children=[w.Label(text="Back")])
    w.Button(on_click=lambda: router().navigate("/"))
```

## Implementation Phases

### Phase 0: Setup

Copy this plan to `docs/planning/router-implementation.md` for reference.

### Phase 1: Path Matching (TDD)

**Tests**: `tests/py/unit/test_router_path_matching.py`
- Exact match, param extraction, no-match cases, root path, trailing slash normalization

**Implementation**: `src/trellis/routing/path_matching.py`
```python
def match_path(pattern: str, path: str) -> tuple[bool, dict[str, str]]:
    """Match path against pattern, extract params."""
```

### Phase 2: RouterState (TDD)

**Tests**: `tests/py/unit/test_router_state.py`
- Init with path, navigate updates path/history, go_back/go_forward, can_go_back/forward, reactivity

**Implementation**: `src/trellis/routing/state.py`
```python
@dataclass(kw_only=True)
class RouterState(Stateful):
    _path: str = "/"
    _params: dict[str, str] = field(default_factory=dict)
    _query: dict[str, str] = field(default_factory=dict)
    _history: list[str] = field(default_factory=list)
    _history_index: int = 0

    @property
    def path(self) -> str: ...
    @property
    def params(self) -> dict[str, str]: ...
    @property
    def query(self) -> dict[str, str]: ...
    @property
    def history(self) -> list[str]: ...
    @property
    def can_go_back(self) -> bool: ...
    @property
    def can_go_forward(self) -> bool: ...

    def navigate(self, path: str) -> None: ...
    def go_back(self) -> None: ...
    def go_forward(self) -> None: ...

def router() -> RouterState:
    return RouterState.from_context()
```

### Phase 3: Messages (TDD)

**Tests**: `tests/py/unit/test_router_messages.py`
- Roundtrip serialization for all new message types

**Modify**: `src/trellis/platforms/common/messages.py`
```python
class HelloMessage(msgspec.Struct, tag="hello", tag_field="type"):
    client_id: str
    path: str = "/"  # ADD

class HistoryPush(msgspec.Struct, tag="history_push", tag_field="type"):
    path: str

class HistoryBack(msgspec.Struct, tag="history_back", tag_field="type"):
    pass

class HistoryForward(msgspec.Struct, tag="history_forward", tag_field="type"):
    pass

class UrlChanged(msgspec.Struct, tag="url_changed", tag_field="type"):
    path: str

# Update union
Message = ... | HistoryPush | HistoryBack | HistoryForward | UrlChanged
```

**Modify**: `src/trellis/platforms/common/client/src/types.ts`
- Mirror all new message types in TypeScript

### Phase 4: Route Component (TDD)

**Tests**: `tests/py/integration/test_router_route.py`
- Renders when match, doesn't render when no match, extracts params, re-renders on path change

**Implementation**: `src/trellis/routing/components.py`
```python
@component
def Route(*, pattern: str, children: list | None = None) -> None:
    state = router()
    matched, params = match_path(pattern, state.path)
    if matched:
        # Store params, render children
```

### Phase 5: Link Component (TDD)

**Tests**: `tests/py/integration/test_router_link.py`
- Renders anchor, has href, click navigates

**Implementation**: `src/trellis/routing/components.py`
```python
@component
def Link(*, to: str, children: list | None = None) -> None:
    def handle_click(e):
        e.preventDefault()
        router().navigate(to)
    with h.A(href=to, onClick=handle_click):
        # render children
```

### Phase 6: Handler Integration

**Modify**: `src/trellis/platforms/common/handler.py`
- Read initial path from HelloMessage
- Handle UrlChanged message (update RouterState from popstate)
- RouterState calls handler to send HistoryPush/Back/Forward

### Phase 7: Client Router Manager (TDD)

**Tests**: `tests/js/unit/RouterManager.test.ts`
- Standalone: pushState, back, forward, popstate sends UrlChanged
- Embedded: internal history only, no window.history calls

**Implementation**: `src/trellis/platforms/common/client/src/RouterManager.ts`
- Manages history based on embedded mode
- Handles HistoryPush/Back/Forward messages
- Sends UrlChanged on popstate (standalone only)

**Modify**: `src/trellis/platforms/common/client/src/ClientMessageHandler.ts`
- Dispatch history messages to RouterManager

**Modify**: Each client to include path in HelloMessage:
- `src/trellis/platforms/server/client/src/TrellisClient.ts`
- `src/trellis/platforms/desktop/client/src/DesktopClient.ts`
- `src/trellis/platforms/browser/client/src/BrowserClient.ts`

### Phase 8: Embedded Mode

**Tests**: `tests/py/unit/test_trellis_embedded.py`
- embedded param, desktop always embedded, browser respects param

**Modify**: `src/trellis/app/entry.py`
- Add `embedded: bool = False` parameter
- Desktop platform forces embedded=True

### Phase 9: Exports

**Create**: `src/trellis/routing/__init__.py`
```python
from trellis.routing.components import Link, Route
from trellis.routing.state import RouterState, router
__all__ = ["Link", "Route", "RouterState", "router"]
```

**Modify**: `src/trellis/__init__.py`
- Export Link, Route, RouterState, router

## Files to Create

| File | Purpose |
|------|---------|
| `src/trellis/routing/__init__.py` | Package exports |
| `src/trellis/routing/path_matching.py` | Pattern matching logic |
| `src/trellis/routing/state.py` | RouterState class |
| `src/trellis/routing/components.py` | Route, Link components |
| `src/trellis/platforms/common/client/src/RouterManager.ts` | Client history management |
| `tests/py/unit/test_router_path_matching.py` | Path matching tests |
| `tests/py/unit/test_router_state.py` | RouterState tests |
| `tests/py/unit/test_router_messages.py` | Message serialization tests |
| `tests/py/integration/test_router_route.py` | Route component tests |
| `tests/py/integration/test_router_link.py` | Link component tests |
| `tests/js/unit/RouterManager.test.ts` | Client router tests |

## Files to Modify

| File | Changes |
|------|---------|
| `src/trellis/platforms/common/messages.py` | Add path to HelloMessage, add history messages |
| `src/trellis/platforms/common/client/src/types.ts` | TypeScript message mirrors |
| `src/trellis/platforms/common/handler.py` | Handle UrlChanged, send history messages |
| `src/trellis/platforms/common/client/src/ClientMessageHandler.ts` | Dispatch history messages |
| `src/trellis/platforms/server/client/src/TrellisClient.ts` | Path in hello, RouterManager |
| `src/trellis/platforms/desktop/client/src/DesktopClient.ts` | Path in hello, embedded mode |
| `src/trellis/platforms/browser/client/src/BrowserClient.ts` | Path in hello, embedded option |
| `src/trellis/app/entry.py` | Add embedded param |
| `src/trellis/__init__.py` | Export routing API |

## Platform Behavior Summary

| Platform | URL Bar | History API | Embedded Default |
|----------|---------|-------------|------------------|
| Server | Real | Real pushState | False |
| Desktop | None | Emulated | Always True |
| Browser standalone | Real | Real pushState | False |
| Browser embedded | None | Emulated | True (explicit) |

## Test Commands

```bash
pixi run pytest tests/py/unit/test_router*.py -v
pixi run pytest tests/py/integration/test_router*.py -v
pixi run vitest tests/js/unit/RouterManager.test.ts
```
