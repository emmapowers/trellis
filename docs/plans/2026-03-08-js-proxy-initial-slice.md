# JS Proxy Initial Slice Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first end-to-end JS proxy slice: a bundled TypeScript object registered through `trellis.registry`, callable from Python through a typed async proxy, with full request/response round trips over the existing message transport.

**Architecture:** Start with static named proxy targets instead of DOM refs or globals. Add a new registry export kind for bundled JS objects, generate startup wiring into `_registry.ts`, add request/response message types to the shared protocol, then connect a small Python `JsProxy` surface to a client-side proxy target registry. Keep v1 intentionally narrow: primitive/list/dict payloads only, no proxy arguments, no callback args, no returned proxy objects, no ref lifecycle, no release semantics.

**Tech Stack:** Python 3.13, `msgspec`, asyncio, existing Trellis `MessageHandler`, TypeScript client runtime, Vitest, pytest, Pixi, FastAPI/WebSocket server platform.

---

## Phase 1: Registry and Wire Protocol

### Task 1: Add bundled object registration to the module registry

**Files:**
- Modify: `src/trellis/registry/__init__.py`
- Modify: `src/trellis/bundler/workspace.py`
- Test: `tests/py/unit/test_registry.py`
- Test: `tests/py/unit/test_workspace.py`

**Step 1: Write the failing tests**

Add coverage that proves object exports are first-class registry entries and generate runtime wiring instead of plain re-exports.

```python
def test_collect_errors_on_duplicate_object_name() -> None:
    registry = ModuleRegistry()
    registry.register(
        "module-a",
        exports=[("demo_api", ExportKind.OBJECT, "demo.ts")],
    )
    registry.register(
        "module-b",
        exports=[("demo_api", ExportKind.OBJECT, "other.ts")],
    )

    with pytest.raises(ValueError, match=r"Export name collision.*demo_api"):
        registry.collect()


def test_generates_object_registration_code() -> None:
    collected = CollectedModules(
        modules=[
            Module(
                name="demo",
                exports=[ModuleExport("demo_api", ExportKind.OBJECT, "demo.ts")],
            )
        ],
        packages={},
    )

    code = generate_registry_ts(collected)

    assert 'import { registerProxyTarget } from "@trellis/trellis-core/proxyTargets";' in code
    assert 'import { demo_api } from "@trellis/demo/demo";' in code
    assert 'registerProxyTarget("demo_api", demo_api);' in code
```

**Step 2: Run tests to verify they fail**

Run:

```bash
pixi run pytest tests/py/unit/test_registry.py tests/py/unit/test_workspace.py -v
```

Expected: failure because `ExportKind.OBJECT` and generated object registration do not exist yet.

**Step 3: Write the minimal implementation**

Add `OBJECT` to `ExportKind`, treat it as a named export with collision checking, and update `_registry.ts` generation to import object exports and register them during `initRegistry()`.

```python
class ExportKind(StrEnum):
    COMPONENT = auto()
    FUNCTION = auto()
    OBJECT = auto()
    INITIALIZER = auto()
    STYLESHEET = auto()
```

```ts
import { registerProxyTarget } from "@trellis/trellis-core/proxyTargets";
import { demo_api } from "@trellis/demo/demo";

export function initRegistry(): void {
  registerProxyTarget("demo_api", demo_api);
}
```

**Step 4: Run tests to verify they pass**

Run:

```bash
pixi run pytest tests/py/unit/test_registry.py tests/py/unit/test_workspace.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/trellis/registry/__init__.py src/trellis/bundler/workspace.py tests/py/unit/test_registry.py tests/py/unit/test_workspace.py
git commit -m "feat: register bundled js proxy objects"
```

### Task 2: Add proxy call message types to the shared protocol

**Files:**
- Modify: `src/trellis/platforms/common/messages.py`
- Modify: `src/trellis/platforms/common/__init__.py`
- Modify: `src/trellis/platforms/common/client/src/types.ts`
- Test: `tests/py/unit/test_messages.py`

**Step 1: Write the failing tests**

Add message round-trip coverage for the new request/response types at the Python protocol boundary.

```python
def test_proxy_call_msgpack_roundtrip() -> None:
    encoder = msgspec.msgpack.Encoder()
    decoder = msgspec.msgpack.Decoder(Message)

    original = ProxyCall(request_id="req-1", proxy_id="demo_api", method="greet", args=["Emma"])
    decoded = decoder.decode(encoder.encode(original))

    assert isinstance(decoded, ProxyCall)
    assert decoded.method == "greet"
    assert decoded.args == ["Emma"]


def test_proxy_call_response_msgpack_roundtrip() -> None:
    encoder = msgspec.msgpack.Encoder()
    decoder = msgspec.msgpack.Decoder(Message)

    original = ProxyCallResponse(request_id="req-1", result={"message": "hello"})
    decoded = decoder.decode(encoder.encode(original))

    assert isinstance(decoded, ProxyCallResponse)
    assert decoded.result == {"message": "hello"}
```

**Step 2: Run tests to verify they fail**

Run:

```bash
pixi run pytest tests/py/unit/test_messages.py -v
```

Expected: failure because the proxy message types are not part of the Python message union yet.

**Step 3: Write the minimal implementation**

Add `ProxyCall` and `ProxyCallResponse` to the shared Python message union, export them from `trellis.platforms.common`, and mirror the types in the TypeScript message definitions.

```python
class ProxyCall(msgspec.Struct, tag="proxy_call", tag_field="type"):
    request_id: str
    proxy_id: str
    method: str
    args: list[tp.Any] = []


class ProxyCallResponse(msgspec.Struct, tag="proxy_call_response", tag_field="type"):
    request_id: str
    result: tp.Any = None
    error: str | None = None
```

```ts
export interface ProxyCallMessage {
  type: "proxy_call";
  request_id: string;
  proxy_id: string;
  method: string;
  args: unknown[];
}

export interface ProxyCallResponseMessage {
  type: "proxy_call_response";
  request_id: string;
  result?: unknown;
  error?: string | null;
}
```

**Step 4: Run tests to verify they pass**

Run:

```bash
pixi run pytest tests/py/unit/test_messages.py -v
```

Expected: PASS.

**Step 5: Run a real app build smoke test**

Use an existing app to make sure registry generation and startup still work after the protocol addition.

Run:

```bash
pixi run trellis run --server --app-root examples/hello_world
```

Expected: app serves successfully, initial page loads, no startup tracebacks, no client console error about unknown message shapes.

**Step 6: Commit**

```bash
git add src/trellis/platforms/common/messages.py src/trellis/platforms/common/__init__.py src/trellis/platforms/common/client/src/types.ts tests/py/unit/test_messages.py
git commit -m "feat: add js proxy protocol messages"
```

## Phase 2: Client Runtime and Python Proxy API

### Task 3: Add a client-side proxy target registry and dispatch path

**Files:**
- Create: `src/trellis/platforms/common/client/src/proxyTargets.ts`
- Modify: `src/trellis/platforms/common/client/src/ClientMessageHandler.ts`
- Modify: `src/trellis/platforms/common/client/src/TrellisClient.ts`
- Modify: `src/trellis/platforms/server/client/src/TrellisClient.ts`
- Modify: `src/trellis/platforms/browser/client/src/BrowserClient.ts`
- Modify: `src/trellis/platforms/desktop/client/src/DesktopClient.ts`
- Test: `tests/js/unit/ClientMessageHandler.test.ts`
- Test: `tests/js/unit/BrowserClient.test.ts`

**Step 1: Write the failing tests**

Add JS tests that prove the client can receive a proxy call, invoke a registered object method, and send a structured response for both success and failure.

```ts
it("dispatches proxy calls to registered targets", async () => {
  registerProxyTarget("demo_api", {
    greet(name: string) {
      return `hello ${name}`;
    },
  });

  const sendProxyResponse = vi.fn();
  const handler = new ClientMessageHandler({ sendProxyResponse });

  await handler.handleMessage({
    type: MessageType.PROXY_CALL,
    request_id: "req-1",
    proxy_id: "demo_api",
    method: "greet",
    args: ["Emma"],
  });

  expect(sendProxyResponse).toHaveBeenCalledWith({
    type: MessageType.PROXY_CALL_RESPONSE,
    request_id: "req-1",
    result: "hello Emma",
    error: null,
  });
});


it("returns proxy call errors without throwing transport loop state away", async () => {
  registerProxyTarget("demo_api", {
    explode() {
      throw new TypeError("bad input");
    },
  });
```

**Step 2: Run tests to verify they fail**

Run:

```bash
cd tests/js && npm test -- ClientMessageHandler.test.ts BrowserClient.test.ts
```

Expected: failure because there is no proxy target registry or reply path.

**Step 3: Write the minimal implementation**

Create a small proxy target registry module, let `ClientMessageHandler` accept an async send callback for proxy responses, and have platform clients wire that callback to their existing transports.

```ts
const proxyTargets: Record<string, Record<string, unknown>> = {};

export function registerProxyTarget(name: string, target: Record<string, unknown>): void {
  proxyTargets[name] = target;
}

export function getProxyTarget(name: string): Record<string, unknown> | undefined {
  return proxyTargets[name];
}
```

```ts
case MessageType.PROXY_CALL:
  await this.handleProxyCall(msg);
  break;
```

Keep v1 strict:
- `proxy_id` must resolve to a registered object
- `method` must exist and be callable
- `args` stay as `unknown[]`
- return raw msgpack-safe values only
- serialize errors into `error` strings without introducing retry logic

**Step 4: Run tests to verify they pass**

Run:

```bash
cd tests/js && npm test -- ClientMessageHandler.test.ts BrowserClient.test.ts
```

Expected: PASS.

**Step 5: Run a real app smoke test**

Run:

```bash
pixi run trellis run --server --app-root examples/hello_world
```

Expected: existing app still connects, renders, and handles normal events after the client message handler becomes async-aware for proxy calls.

**Step 6: Commit**

```bash
git add src/trellis/platforms/common/client/src/proxyTargets.ts src/trellis/platforms/common/client/src/ClientMessageHandler.ts src/trellis/platforms/common/client/src/TrellisClient.ts src/trellis/platforms/server/client/src/TrellisClient.ts src/trellis/platforms/browser/client/src/BrowserClient.ts src/trellis/platforms/desktop/client/src/DesktopClient.ts tests/js/unit/ClientMessageHandler.test.ts tests/js/unit/BrowserClient.test.ts
git commit -m "feat: dispatch js proxy calls on the client"
```

### Task 4: Add the Python `JsProxy` surface and server-side request tracking

**Files:**
- Create: `src/trellis/core/proxy.py`
- Modify: `src/trellis/core/__init__.py`
- Modify: `src/trellis/__init__.py`
- Modify: `src/trellis/platforms/common/handler.py`
- Test: `tests/py/unit/test_proxy.py`
- Test: `tests/py/integration/test_message_handler_integration.py`

**Step 1: Write the failing tests**

Add value-heavy Python tests around the real behavior this feature needs:
- method name translation from snake_case to camelCase
- request tracking and response resolution
- error propagation from client response back to awaiting Python code
- handler integration that routes `proxy_call_response` into the pending future table

```python
@pytest.mark.asyncio
async def test_js_proxy_method_sends_proxy_call() -> None:
    transport = RecordingProxyTransport()
    proxy = js_object(DemoApi, "demo_api", transport=transport)

    task = asyncio.create_task(proxy.get_message("Emma"))

    await asyncio.sleep(0)

    assert transport.sent_messages == [
        ProxyCall(
            request_id=transport.sent_messages[0].request_id,
            proxy_id="demo_api",
            method="getMessage",
            args=["Emma"],
        )
    ]

    transport.resolve_last("hello Emma")
    assert await task == "hello Emma"


@pytest.mark.asyncio
async def test_proxy_response_error_raises_runtime_error() -> None:
    ...
```

```python
def test_handle_message_with_proxy_call_response_resolves_pending_future(
    app_wrapper: AppWrapper,
) -> None:
    ...
```

**Step 2: Run tests to verify they fail**

Run:

```bash
pixi run pytest tests/py/unit/test_proxy.py tests/py/integration/test_message_handler_integration.py -v
```

Expected: failure because there is no `JsProxy`, `js_object()`, or server-side pending-response handling yet.

**Step 3: Write the minimal implementation**

Create a small, clean proxy layer instead of coupling proxy concerns directly into `Ref` or `Stateful`.

```python
class ProxyTransport(Protocol):
    async def call_proxy(self, proxy_id: str, method: str, args: list[tp.Any]) -> tp.Any: ...


class JsProxy:
    _proxy_id: str
    _transport: ProxyTransport

    def __init_subclass__(cls) -> None:
        ...


def js_object(proxy_type: type[T], proxy_id: str, *, transport: ProxyTransport | None = None) -> T:
    ...
```

In `MessageHandler`:
- keep a `dict[str, asyncio.Future[tp.Any]]` for in-flight proxy calls
- add a `call_proxy()` helper used by `JsProxy`
- handle `ProxyCallResponse` in `handle_message()`
- reject duplicate or unknown `request_id` values cleanly

Keep the implementation narrow:
- only serialize msgpack-native values
- no bytes, callbacks, proxy arguments, or nested proxy returns
- no compatibility shim with `Ref`

**Step 4: Run tests to verify they pass**

Run:

```bash
pixi run pytest tests/py/unit/test_proxy.py tests/py/integration/test_message_handler_integration.py -v
```

Expected: PASS.

**Step 5: Run a real app smoke test**

Run:

```bash
pixi run trellis run --server --app-root examples/hello_world
```

Expected: app still boots and normal callbacks still work after the handler gains in-flight proxy bookkeeping.

**Step 6: Commit**

```bash
git add src/trellis/core/proxy.py src/trellis/core/__init__.py src/trellis/__init__.py src/trellis/platforms/common/handler.py tests/py/unit/test_proxy.py tests/py/integration/test_message_handler_integration.py
git commit -m "feat: add python js proxy transport"
```

## Phase 3: End-to-End Demo, Hardening, and Cleanup

### Task 5: Build a dedicated demo app that proves the initial slice in the real runtime

**Files:**
- Create: `examples/js_proxy_demo/trellis_config.py`
- Create: `examples/js_proxy_demo/js_proxy_demo/__init__.py`
- Create: `examples/js_proxy_demo/js_proxy_demo/app.py`
- Create: `examples/js_proxy_demo/js_proxy_demo/client/demo_api.ts`
- Create: `examples/js_proxy_demo/js_proxy_demo/client/__init__.py`
- Modify: `tests/py/integration/test_bundler.py`

**Step 1: Write the failing integration test**

Add one bundler-level test that verifies a module exporting an object ends up in generated registry wiring. Do not add brittle snapshot tests for entire generated files.

```python
def test_bundle_registry_registers_proxy_object(tmp_path: Path) -> None:
    registry = ModuleRegistry()
    registry.register(
        "demo-module",
        base_path=tmp_path,
        exports=[("demo_api", ExportKind.OBJECT, "demo.ts")],
    )

    collected = registry.collect()
    code = generate_registry_ts(collected)

    assert 'registerProxyTarget("demo_api", demo_api);' in code
```

**Step 2: Run test to verify it fails if wiring is incomplete**

Run:

```bash
pixi run pytest tests/py/integration/test_bundler.py -k proxy -v
```

Expected: if the earlier phases are complete this should already pass; if the real app exposed a missing bundler edge, this test should catch it before the demo is added.

**Step 3: Write the demo app**

Create a tiny app that exercises one successful call and one error path through the real server/browser flow.

```python
class DemoApi(JsProxy):
    async def greet(self, name: str) -> str: ...


demo_api = js_object(DemoApi, "demo_api")


@component
def App() -> None:
    state = DemoState()

    async def call_greet() -> None:
        state.message = await demo_api.greet("Emma")

    w.Button(text="Call JS", on_click=call_greet)
    w.Label(text=state.message)
```

```ts
export const demo_api = {
  greet(name: string) {
    return `hello ${name}`;
  },
};
```

Register the object from Python with `registry.register(...)` in the demo package import path, using a dedicated module name and explicit `base_path`.

**Step 4: Run the real app and perform an end-to-end test**

Run:

```bash
pixi run trellis run --server --app-root examples/js_proxy_demo
```

Manual end-to-end verification:
- load the page in a browser
- click the button that triggers `await demo_api.greet("Emma")`
- confirm the label updates with the returned JS value
- trigger the error case and confirm the UI shows the surfaced Python-side error rather than hanging forever
- inspect browser console and server logs for unexpected exceptions

If the real app breaks in a way the tests did not catch:
- fix the implementation first
- add or adjust the narrowest valuable regression test that captures the real failure mode
- rerun the app before moving on

**Step 5: Commit**

```bash
git add examples/js_proxy_demo tests/py/integration/test_bundler.py
git commit -m "feat: add js proxy demo app"
```

### Task 6: Final cleanup, focused regression coverage, and full verification

**Files:**
- Modify: any touched files with dead code or abandoned helper branches
- Test: targeted files added above only if a real failure exposed missing coverage

**Step 1: Remove dead code**

Delete any helper paths that were introduced during implementation but are no longer needed, especially:
- unused temporary serialization helpers
- duplicated transport wrappers
- registry branches that became redundant once `OBJECT` settled

Do not leave commented-out code or compatibility aliases behind.

**Step 2: Run targeted regression tests**

Run:

```bash
pixi run pytest tests/py/unit/test_registry.py tests/py/unit/test_workspace.py tests/py/unit/test_messages.py tests/py/unit/test_proxy.py tests/py/integration/test_message_handler_integration.py tests/py/integration/test_bundler.py -v
cd tests/js && npm test -- ClientMessageHandler.test.ts BrowserClient.test.ts
```

Expected: PASS.

**Step 3: Run formatting, type checks, and full automated verification**

Run:

```bash
pixi run cleanup
pixi run mypy
pixi run test
pixi run test-js
```

Expected: PASS.

**Step 4: Run the real app again and repeat the end-to-end test**

Run:

```bash
pixi run trellis run --server --app-root examples/js_proxy_demo
```

Manual end-to-end verification:
- confirm success path still updates the UI
- confirm error path still resolves promptly and visibly
- refresh the page and repeat to catch startup-order regressions
- verify no stale request hangs remain after repeated clicks

**Step 5: Final commit**

```bash
git add src tests examples
git commit -m "feat: complete initial js proxy slice"
```
