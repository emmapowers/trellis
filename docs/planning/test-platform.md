# Test Platform Implementation Plan

Create a new "test" platform for Trellis that enables full integration testing without a browser. Like server/desktop/browser platforms, it has a Python handler + JavaScript client with bidirectional communication.

## Architecture

```
┌───────────────────────┐       msgpack       ┌───────────────────────┐
│   Python (pytest)     │ ←── stdin/stdout ──→ │   Node.js (jsdom)     │
│                       │                      │                       │
│ • TestPlatform        │     bidirectional    │ • TestClient          │
│ • TestMessageHandler  │ ←─────────────────→  │ • ClientMessageHandler│
│ • RenderTree          │                      │ • TrellisStore        │
│ • Component rendering │                      │ • TreeRenderer        │
│                       │                      │ • React + jsdom DOM   │
└───────────────────────┘                      └───────────────────────┘
```

**This is a real platform** like server/desktop/browser:
- Uses the same `MessageHandler.run()` loop pattern
- Same HelloMessage → HelloResponseMessage → RenderMessage flow
- Bidirectional: Python sends renders, client sends events
- Full React rendering with jsdom for DOM testing

**Test scenarios enabled:**
- Connection handshake workflow
- Full render cycle with hooks
- Callbacks: click → EventMessage → Python callback → PatchMessage
- Mutable state (text input changes → events)

## Python Side: TestPlatform

**New file**: `src/trellis/platforms/test/platform.py`

```python
class TestPlatform(Platform):
    """Test platform using subprocess + stdio for integration testing."""

    @property
    def name(self) -> str:
        return "test"

    async def run(self, root_component: Callable[[], None], **kwargs) -> None:
        # Spawn Node.js client subprocess
        client_script = Path(__file__).parent / "client" / "dist" / "test-client.js"
        self.process = await asyncio.create_subprocess_exec(
            "node", str(client_script),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )

        handler = StdioMessageHandler(root_component, self.process)
        await handler.run()
```

**New file**: `src/trellis/platforms/test/handler.py`

```python
class StdioMessageHandler(MessageHandler):
    """Message handler using subprocess stdin/stdout for transport."""

    def __init__(self, root_component, process: asyncio.subprocess.Process):
        super().__init__(root_component)
        self.process = process

    async def send_message(self, msg: Message) -> None:
        data = msgspec.msgpack.encode(msg)
        # Length-prefixed binary format
        self.process.stdin.write(len(data).to_bytes(4, "big") + data)
        await self.process.stdin.drain()

    async def receive_message(self) -> Message:
        # Read length prefix
        length_bytes = await self.process.stdout.readexactly(4)
        length = int.from_bytes(length_bytes, "big")
        # Read message
        data = await self.process.stdout.readexactly(length)
        return msgspec.msgpack.decode(data, type=Message)
```

## JavaScript Side: TestClient

**New file**: `src/trellis/platforms/test/client/src/TestClient.ts`

```typescript
import { encode, decode } from "@msgpack/msgpack";
import { TrellisClient } from "@common/TrellisClient";
import { ClientMessageHandler, ConnectionState } from "@common/ClientMessageHandler";
import { Message, MessageType, HelloMessage, EventMessage } from "@common/types";

/**
 * Test client using stdin/stdout for communication with Python.
 * Runs in Node.js with jsdom for React rendering.
 */
export class TestClient implements TrellisClient {
  private handler: ClientMessageHandler;
  private clientId: string;

  constructor(callbacks: ClientMessageHandlerCallbacks = {}) {
    this.clientId = crypto.randomUUID();
    this.handler = new ClientMessageHandler(callbacks);
  }

  async connect(): Promise<void> {
    this.handler.setConnectionState("connecting");

    // Start reading from stdin
    this.startReading();

    // Send HelloMessage
    const hello: HelloMessage = { type: MessageType.HELLO, client_id: this.clientId };
    this.send(hello);
  }

  private startReading(): void {
    let buffer = Buffer.alloc(0);

    process.stdin.on("data", (chunk: Buffer) => {
      buffer = Buffer.concat([buffer, chunk]);

      // Parse length-prefixed messages
      while (buffer.length >= 4) {
        const length = buffer.readUInt32BE(0);
        if (buffer.length < 4 + length) break;

        const msgBytes = buffer.slice(4, 4 + length);
        buffer = buffer.slice(4 + length);

        const msg = decode(msgBytes) as Message;
        this.handler.handleMessage(msg);
      }
    });
  }

  private send(msg: Message): void {
    const data = encode(msg);
    const lengthPrefix = Buffer.alloc(4);
    lengthPrefix.writeUInt32BE(data.length);
    process.stdout.write(Buffer.concat([lengthPrefix, Buffer.from(data)]));
  }

  sendEvent(callbackId: string, args: unknown[] = []): void {
    const msg: EventMessage = { type: MessageType.EVENT, callback_id: callbackId, args };
    this.send(msg);
  }

  getConnectionState(): ConnectionState { return this.handler.getConnectionState(); }
  getSessionId(): string | null { return this.handler.getSessionId(); }
  getServerVersion(): string | null { return this.handler.getServerVersion(); }
}
```

**New file**: `src/trellis/platforms/test/client/src/main.tsx`

```typescript
import { JSDOM } from "jsdom";
import React from "react";
import { createRoot } from "react-dom/client";
import { act } from "react";
import { TestClient } from "./TestClient";
import { TrellisRoot } from "@common/TrellisRoot";

// Set up jsdom globals for React
const dom = new JSDOM("<!DOCTYPE html><div id='root'></div>");
(global as any).document = dom.window.document;
(global as any).window = dom.window;

async function main() {
  const client = new TestClient({
    onConnected: () => console.error("[TestClient] Connected"),
    onError: (err) => console.error("[TestClient] Error:", err),
  });

  // Create React root and render
  const container = document.getElementById("root")!;
  let root: ReturnType<typeof createRoot>;

  act(() => {
    root = createRoot(container);
    root.render(<TrellisRoot client={client} />);
  });

  // Connect to Python (starts message loop)
  await client.connect();
}

main().catch(console.error);
```

**Build step**: Bundle with esbuild including jsdom, React, @msgpack/msgpack.

## Test Utilities

**New file**: `src/trellis/platforms/test/testing.py`

Test utilities for pytest integration:

```python
import asyncio
from contextlib import asynccontextmanager
from trellis import component, Stateful
from .platform import TestPlatform
from .handler import StdioMessageHandler

class TestApp:
    """Test harness for running Trellis apps in integration tests."""

    def __init__(self, root_component):
        self.root_component = root_component
        self.platform = TestPlatform()
        self.handler = None
        self._task = None

    async def start(self):
        """Start the test platform (spawns Node.js client)."""
        await self.platform.run(self.root_component)
        self.handler = self.platform.handler

    async def wait_for_render(self):
        """Wait for next render cycle to complete."""
        # Allow render loop to process
        await asyncio.sleep(0.05)

    async def simulate_click(self, callback_id: str, args: list = None):
        """Simulate a user clicking an element with given callback."""
        # Send a control message to trigger callback in JS
        # JS client will send EventMessage back
        pass

    async def get_dom_html(self) -> str:
        """Get the current jsdom HTML output."""
        # Query the JS client for DOM state
        pass

    async def stop(self):
        """Stop the test platform."""
        if self.handler:
            await self.handler.stop()

@asynccontextmanager
async def test_app(root_component):
    """Context manager for running test apps."""
    app = TestApp(root_component)
    try:
        await app.start()
        yield app
    finally:
        await app.stop()
```

## Integration Test Cases

**New file**: `tests/integration/test_platform.py`

```python
import pytest
from trellis import component, Stateful
from trellis import widgets as w
from trellis.platforms.test import test_app

@pytest.mark.asyncio
class TestConnection:
    """Test the connection handshake workflow."""

    async def test_handshake_completes(self):
        """HelloMessage → HelloResponseMessage flow works."""
        @component
        def App():
            return w.Label(text="Hello")

        async with test_app(App) as app:
            assert app.handler.session_id is not None
            assert app.handler.server_version is not None

    async def test_initial_render_received(self):
        """Initial RenderMessage populates JS store."""
        @component
        def App():
            return w.Label(text="Hello")

        async with test_app(App) as app:
            await app.wait_for_render()
            dom = await app.get_dom_html()
            assert "Hello" in dom


@pytest.mark.asyncio
class TestCallbacks:
    """Test callback round-trip: JS click → Python callback → JS patch."""

    async def test_button_click_triggers_callback(self):
        """Clicking a button invokes the Python callback."""
        clicks = []

        @component
        def App():
            def on_click():
                clicks.append(1)
            return w.Button(text="Click me", on_click=on_click)

        async with test_app(App) as app:
            await app.wait_for_render()
            # Simulate user clicking the button
            await app.simulate_click_by_text("Click me")
            await app.wait_for_render()
            assert len(clicks) == 1

    async def test_callback_updates_state(self):
        """State changes from callback trigger re-render with patches."""
        @component
        def Counter():
            count = use_state(0)
            return w.Button(text=str(count.value), on_click=lambda: count.set(count.value + 1))

        async with test_app(Counter) as app:
            await app.wait_for_render()
            dom = await app.get_dom_html()
            assert "0" in dom

            await app.simulate_click_by_text("0")
            await app.wait_for_render()
            dom = await app.get_dom_html()
            assert "1" in dom


@pytest.mark.asyncio
class TestMutableState:
    """Test mutable state (text input, etc.)."""

    async def test_text_input_changes(self):
        """Typing in an input field sends events and updates state."""
        @component
        def App():
            text = use_state("")
            return w.InputGroup(value=text.value, on_change=text.set)

        async with test_app(App) as app:
            await app.wait_for_render()
            await app.type_in_input("Hello World")
            await app.wait_for_render()
            # Verify state updated
            ...
```

## Files to Add

| File | Purpose |
|------|---------|
| `src/trellis/platforms/test/__init__.py` | Package exports |
| `src/trellis/platforms/test/platform.py` | TestPlatform class |
| `src/trellis/platforms/test/handler.py` | StdioMessageHandler class |
| `src/trellis/platforms/test/testing.py` | TestApp and test_app context manager |
| `src/trellis/platforms/test/client/src/TestClient.ts` | JS client with stdio transport |
| `src/trellis/platforms/test/client/src/main.tsx` | JS entry point with jsdom setup |
| `src/trellis/platforms/test/client/build.ts` | esbuild script |
| `tests/integration/test_platform.py` | Integration test cases |

**Dependencies**:
- `jsdom` (npm) - DOM environment for React in Node.js

## Build Integration

Add to `pixi.toml`:
```toml
build-test-platform = { cmd = "npm run build", cwd = "src/trellis/platforms/test/client" }
test-integration = { cmd = "pytest tests/integration -vv", depends-on = ["build-test-platform"] }
```

## Implementation Order

1. **Create platform directory structure**
   - `src/trellis/platforms/test/` with Python files
   - `src/trellis/platforms/test/client/` with TypeScript files

2. **Implement Python handler** (`handler.py`)
   - `StdioMessageHandler` with length-prefixed msgpack over stdin/stdout
   - Inherits from `MessageHandler` base class

3. **Implement Python platform** (`platform.py`)
   - `TestPlatform` spawns Node.js subprocess
   - Manages process lifecycle

4. **Implement JavaScript client** (`TestClient.ts`)
   - Bidirectional stdin/stdout with length-prefixed msgpack
   - Uses `ClientMessageHandler` for message processing

5. **Implement JavaScript entry point** (`main.tsx`)
   - jsdom setup
   - React rendering with `TrellisRoot`
   - Connect to Python via `TestClient`

6. **Implement test utilities** (`testing.py`)
   - `TestApp` class for test harness
   - `test_app` context manager
   - `simulate_click_by_text`, `get_dom_html`, etc.

7. **Add integration tests**
   - Connection handshake tests
   - Callback round-trip tests
   - State update tests
   - Input/mutable state tests
