---
sidebar_position: 4
title: Platforms
---

# Platforms

Trellis applications can run on multiple platforms using the same component code. Each platform provides a transport layer that connects the Python backend to a frontend renderer, adapting to platform-specific capabilities and constraints.

## Table of Contents

1. [Platform Architecture](#platform-architecture)
2. [Message Protocol](#message-protocol)
3. [Key Classes](#key-classes)
4. [Server Platform](#server-platform)
5. [Desktop Platform](#desktop-platform)
6. [Browser Platform](#browser-platform)
7. [Platform Selection](#platform-selection)

---

## Platform Architecture

All platforms share the same fundamental architecture: Python manages application state and produces a UI tree, which is serialized and sent to a React renderer. User interactions flow back as messages that trigger callbacks, modify state, and produce updated UI.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Trellis Application                         │
│  ┌────────────────────────┐         ┌────────────────────────────┐  │
│  │     Python Backend     │         │      Frontend Renderer     │  │
│  │                        │         │                            │  │
│  │  ┌──────────────────┐  │         │  ┌──────────────────────┐  │  │
│  │  │   Components +   │  │         │  │   React + Widgets    │  │  │
│  │  │      State       │  │         │  │                      │  │  │
│  │  └────────┬─────────┘  │         │  └──────────┬───────────┘  │  │
│  │           │            │         │             │              │  │
│  │  ┌────────▼─────────┐  │         │  ┌──────────▼───────────┐  │  │
│  │  │   RenderTree +   │  │ Message │  │   TreeRenderer +     │  │  │
│  │  │ MessageHandler   │◄─┼─Protocol┼─►│   TrellisClient      │  │  │
│  │  └──────────────────┘  │         │  └──────────────────────┘  │  │
│  └────────────────────────┘         └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

What varies between platforms:

| Aspect | Server | Desktop | Browser |
|--------|--------|---------|---------|
| **Transport** | WebSocket | PyTauri IPC Channel | postMessage (Worker) |
| **Python location** | Remote server | Local process | Browser (Web Worker) |
| **Frontend location** | Browser | System webview | Same browser |
| **Multiple clients** | Yes (multi-session) | No (single window) | No (single app) |
| **Event loop** | asyncio on main thread | asyncio in background thread | asyncio in Pyodide |

What stays the same:

- Component model and rendering
- State management and reactivity
- Message protocol and serialization
- React-based frontend rendering

---

## Message Protocol

All platforms use the same message types, serialized with msgpack:

| Message | Direction | Purpose |
|---------|-----------|---------|
| `HelloMessage` | Client → Server | Initialize session with client ID |
| `HelloResponseMessage` | Server → Client | Return session ID and server version |
| `RenderMessage` | Server → Client | Serialized component tree |
| `EventMessage` | Client → Server | User interaction (callback ID + args) |
| `ErrorMessage` | Server → Client | Render or callback error details |

### Message Flow

```
┌──────────┐                              ┌──────────┐
│  Client  │                              │  Server  │
└────┬─────┘                              └────┬─────┘
     │                                         │
     │  HelloMessage { client_id }             │
     │────────────────────────────────────────►│
     │                                         │
     │  HelloResponseMessage { session_id }    │
     │◄────────────────────────────────────────│
     │                                         │
     │  RenderMessage { tree }                 │
     │◄────────────────────────────────────────│
     │                                         │
     │  EventMessage { callback_id, args }     │
     │────────────────────────────────────────►│
     │                                         │
     │  RenderMessage { tree }                 │
     │◄────────────────────────────────────────│
     │                                         │
```

The initial handshake establishes a session, then the server sends the initial render. Subsequent interactions follow the event → re-render cycle.

---

## Key Classes

### Platform (base class)

```python
class Platform(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def run(self, root_component, **kwargs) -> None: ...
```

Each platform implements `run()` to start the application with platform-specific setup.

### MessageHandler

The `MessageHandler` base class provides the core render/event/re-render loop:

```python
class MessageHandler:
    tree: RenderTree
    session_id: str | None

    def __init__(self, root_component): ...

    # Transport methods - subclasses implement these
    async def send_message(self, msg: Message) -> None: ...
    async def receive_message(self) -> Message: ...

    # Core protocol
    async def handle_hello(self) -> str: ...
    def initial_render(self) -> Message: ...
    async def handle_message(self, msg: Message) -> Message | None: ...

    # Main loop
    async def run(self) -> None:
        await self.handle_hello()
        await self.send_message(self.initial_render())
        while True:
            msg = await self.receive_message()
            response = await self.handle_message(msg)
            if response:
                await self.send_message(response)
```

Platform-specific handlers extend this, implementing `send_message()` and `receive_message()` for their transport.

### Client-Side Classes

On the frontend, each platform has a client class that:
- Manages the transport connection
- Serializes/deserializes messages
- Provides `send()` and receives messages via callbacks

The `TreeRenderer` component consumes messages and renders the UI tree using React.

---

## Server Platform

The server platform runs Python on a remote server, with the UI rendered in a web browser connected via WebSocket.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Server Platform                              │
│  ┌────────────────────────┐         ┌────────────────────────────┐  │
│  │   Python (Server)      │         │   Browser                  │  │
│  │                        │         │                            │  │
│  │  FastAPI + Uvicorn     │         │  React + TrellisClient     │  │
│  │  WebSocketHandler      │◄───────►│  WebSocket connection      │  │
│  │                        │   WS    │                            │  │
│  └────────────────────────┘         └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Components

**ServerPlatform** (`platforms/server/platform.py`)
- Creates FastAPI application with routes
- Configures uvicorn server
- Serves static bundle at `/static/bundle.js`
- Returns HTML page at `/`

**WebSocketMessageHandler** (`platforms/server/handler.py`)
- Extends `MessageHandler` with WebSocket transport
- `send_message()`: sends msgpack bytes via WebSocket
- `receive_message()`: receives msgpack bytes via WebSocket
- Uses the standard `run()` loop

**TrellisClient** (`platforms/server/client/`)
- TypeScript WebSocket client
- Connects to `/ws` endpoint
- Sends/receives msgpack-encoded messages

### Event Loop

The server platform uses asyncio on the main thread:

```python
async def run(self, root_component, **kwargs):
    # FastAPI app with WebSocket endpoint
    app = create_app(root_component)

    # Uvicorn runs the asyncio event loop
    server = uvicorn.Server(config)
    await server.serve()
```

Each WebSocket connection gets its own `WebSocketMessageHandler` instance running `handler.run()` as a coroutine.

### Multi-Session Support

The server platform supports multiple concurrent clients:
- Each WebSocket connection creates a new handler
- Each handler has its own `RenderTree` and session
- State is isolated per session by default
- Shared state requires explicit coordination

### Usage

```python
from trellis import Trellis, async_main

@async_main
async def main():
    app = Trellis(top=MyApp)
    await app.serve()  # Defaults to server platform

# Or explicitly:
app = Trellis(top=MyApp, platform="server", host="0.0.0.0", port=8080)
```

---

## Desktop Platform

The desktop platform runs Python locally with UI rendered in a system webview, using [PyTauri](https://github.com/pydantic/pytauri) for the native shell.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Desktop Platform                             │
│  ┌────────────────────────┐         ┌────────────────────────────┐  │
│  │   Python (Local)       │         │   System WebView           │  │
│  │                        │         │                            │  │
│  │  PyTauri Commands      │         │  React + DesktopClient     │  │
│  │  PyTauriMessageHandler │◄───────►│  Channel-based IPC         │  │
│  │                        │  IPC    │                            │  │
│  └────────────────────────┘         └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Components

**DesktopPlatform** (`platforms/desktop/platform.py`)
- Creates PyTauri application
- Registers IPC commands
- Manages platform state (root component, handler)
- Bridges async handlers to PyTauri's event loop

**PyTauriMessageHandler** (`platforms/desktop/handler.py`)
- Extends `MessageHandler` with queue-based transport
- `send_message()`: sends via PyTauri channel
- `receive_message()`: pulls from async queue
- Uses the standard `run()` loop

**DesktopClient** (`platforms/desktop/client/`)
- TypeScript PyTauri client
- Uses `@tauri-apps/api` for IPC
- Calls `trellis_connect` to establish channel
- Calls `trellis_send` to send messages
- Receives messages via channel callback

### Event Loop

PyTauri controls the main thread with its own event loop for window management. Trellis uses a **blocking portal** to run asyncio in a background thread:

```python
async def run(self, root_component, **kwargs):
    self._root_component = root_component
    commands = self._create_commands()

    # PyTauri runs on main thread, asyncio runs in background thread
    with start_blocking_portal("asyncio") as portal:
        app = builder_factory().build(
            context=context_factory(config_dir),
            invoke_handler=commands.generate_handler(portal),
        )
        app.run_return()  # Blocks until window closes
```

The portal bridges PyTauri commands (called from main thread) to async handlers (running in background thread).

### IPC Commands

The desktop platform registers three PyTauri commands:

| Command | Purpose |
|---------|---------|
| `trellis_connect` | Establish IPC channel, create handler, spawn `run()` task |
| `trellis_send` | Enqueue message data for handler to process |
| `trellis_log` | Forward JavaScript console output to Python stdout |

### Message Queue Pattern

Unlike WebSocket's bidirectional stream, PyTauri IPC uses separate channels for each direction:
- **Client → Server**: via `trellis_send` command → async queue → `receive_message()`
- **Server → Client**: via `channel.send()` from `send_message()`

This allows the standard `MessageHandler.run()` loop to work:

```python
class PyTauriMessageHandler(MessageHandler):
    _queue: asyncio.Queue[bytes]

    async def receive_message(self) -> Message:
        data = await self._queue.get()  # Waits for trellis_send
        return self._decoder.decode(data)

    def enqueue(self, data: bytes) -> None:
        self._queue.put_nowait(data)  # Called by trellis_send command
```

### Dependencies

Desktop requires additional packages (automatically included):
- `pytauri` - Python/Tauri bridge
- `pytauri-wheel` - Pre-built Tauri runtime
- `@tauri-apps/api` (JS) - Tauri JavaScript API
- `tauri-plugin-pytauri-api` (JS) - PyTauri JavaScript bindings

### Usage

```bash
# Run with --desktop flag
pixi run demo --desktop

# Or programmatically
from trellis import Trellis, async_main

@async_main
async def main():
    app = Trellis(top=MyApp, platform="desktop")
    await app.serve()
```

---

## Browser Platform

The browser platform runs Python directly in the browser using [Pyodide](https://pyodide.org/) (Python compiled to WebAssembly). No server-side Python is required—the entire application runs client-side.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Browser Platform                              │
│  ┌────────────────────────┐         ┌────────────────────────────┐  │
│  │   Web Worker           │         │   Main Thread              │  │
│  │                        │         │                            │  │
│  │  Pyodide Runtime       │         │  React + BrowserClient     │  │
│  │  BrowserMessageHandler │◄───────►│  TrellisApp + TreeRenderer │  │
│  │                        │ postMsg │                            │  │
│  └────────────────────────┘         └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Components

**BrowserPlatform** (`platforms/browser/platform.py`)
- Runs inside Pyodide in the browser
- Connects to JavaScript via a registered bridge module
- `bundle()`: No-op (bundling done before loading)
- `run()`: Sets up bridge, runs message loop

**BrowserMessageHandler** (`platforms/browser/handler.py`)
- Extends `MessageHandler` with queue-based transport
- `send_message()`: calls bridge callback → `postMessage` to main thread
- `receive_message()`: awaits on async queue populated by JavaScript
- `enqueue_message()`: called by JS bridge to queue incoming messages

**BrowserServePlatform** (`platforms/browser/serve_platform.py`)
- CLI mode for development: `python app.py --browser`
- Packages source code and serves via HTTP
- Generates HTML with embedded source config

**TrellisApp** (`platforms/browser/client/src/TrellisApp.tsx`)
- React component orchestrating the browser platform
- Creates and manages PyodideWorker
- Wires up bidirectional messaging
- Renders loading states, errors, and the UI tree

**PyodideWorker** (`platforms/browser/client/src/PyodideWorker.ts`)
- Manages the Web Worker lifecycle
- Worker code is built separately and loaded via blob URL
- Handles init/run/message protocol with worker

**pyodide.worker.ts** (`platforms/browser/client/src/pyodide.worker.ts`)
- Runs in isolated Web Worker context
- Loads Pyodide runtime from CDN
- Installs packages (micropip, msgspec, rich, trellis)
- Registers `trellis_browser_bridge` JS module for Python
- Executes Python source code

### Worker Isolation Model

The browser platform uses Web Worker isolation:

1. **Clean Restarts**: Worker termination kills all Python state instantly
2. **Non-blocking UI**: Pyodide runs off the main thread
3. **Message Queue Safety**: Async queue prevents race conditions
4. **Sandboxing**: Python can't access DOM directly (must use bridge)

The worker acts as a process boundary—terminating it is equivalent to killing a subprocess.

### Source Loading Modes

The browser platform supports three ways to load Python code:

**Code Mode** — Raw Python string (simplest, used by docs demos):
```javascript
source = { type: "code", code: "print('hello')" }
```

**Module Mode** — Package files (used by `--browser` CLI):
```javascript
source = {
  type: "module",
  files: {
    "myapp/__init__.py": "...",
    "myapp/app.py": "...",
  },
  moduleName: "myapp.app",
}
```
Files are written to Pyodide's virtual filesystem, then executed via `runpy.run_module()`.

**Wheel Mode** — Install from URL (production deployment):
```javascript
source = {
  type: "wheel",
  wheelUrl: "https://example.com/app-0.1.0-py3-none-any.whl",
}
```

### Message Flow

The browser platform uses a bridge pattern for communication:

```
TrellisApp creates PyodideWorker
    ↓ (postMessage: "init")
Worker loads Pyodide, installs packages
Worker registers trellis_browser_bridge module
    ↓ (postMessage: "ready")
TrellisApp calls worker.run(source)
    ↓ (postMessage: "run")
Worker executes Python source
Python imports bridge, creates handler
Python calls bridge.set_handler(handler)
Python calls handler.run() (waits for messages)
    ↓
TrellisApp calls client.sendHello()
    ↓ (postMessage: "message" with HELLO)
Worker calls handler.enqueue_message(HELLO)
Python receives HELLO, sends HELLO_RESPONSE
    ↓ (bridge.send_message → postMessage)
TrellisApp receives HELLO_RESPONSE
TrellisApp renders <TreeRenderer />
```

### Event Loop

Python's asyncio runs inside Pyodide's event loop, which integrates with the browser's event loop. The message handler's `run()` loop works the same as other platforms:

```python
async def run(self):
    await self.handle_hello()
    await self.send_message(self.initial_render())
    while True:
        msg = await self.receive_message()  # Awaits on queue
        response = await self.handle_message(msg)
        if response:
            await self.send_message(response)
```

### Bridge Module

JavaScript registers a module that Python imports:

```python
# Python side (in BrowserPlatform.run)
import trellis_browser_bridge as bridge
bridge.set_handler(handler_proxy)  # Register Python handler
bridge.send_message(msg)           # Send to JS
```

```typescript
// JavaScript side (in worker)
const workerBridge = {
  set_handler(handler) {
    pythonHandler = handler;
    // Flush any queued messages
  },
  send_message(msg) {
    self.postMessage({ type: "message", payload: msg });
  },
};
pyodide.registerJsModule("trellis_browser_bridge", workerBridge);
```

### Usage

**Development (CLI serve mode):**
```bash
python myapp.py --browser
# Serves at http://localhost:PORT with auto-selected port
```

**Documentation/Playground:**
The docs use `TrellisApp` directly to run interactive examples.

**Production:**
Build and deploy the HTML with embedded wheel URL.

---

## Platform Selection

### Automatic Detection

By default, Trellis auto-detects the platform:
1. If running in Pyodide → Browser platform
2. Otherwise → Server platform

### Explicit Selection

```python
# Via constructor
app = Trellis(top=MyApp, platform="desktop")

# Via CLI
python myapp.py --platform=desktop
python myapp.py --desktop  # Shortcut
python myapp.py --browser  # Serve for browser via Pyodide
```

### Platform-Specific Arguments

Some arguments only apply to specific platforms:

| Argument | Platform | Purpose |
|----------|----------|---------|
| `host` | Server | Bind address |
| `port` | Server | Bind port |
| `static_dir` | Server | Custom static files |
| `window_title` | Desktop | Window title |
| `window_width` | Desktop | Initial width |
| `window_height` | Desktop | Initial height |

Using an argument with the wrong platform raises `PlatformArgumentError`.

---

## Implementation Files

| File | Purpose |
|------|---------|
| `core/platform.py` | `Platform` base class, `PlatformType` enum |
| `core/message_handler.py` | `MessageHandler` base class |
| `core/messages.py` | Message types (`HelloMessage`, etc.) |
| `core/trellis.py` | `Trellis` class, platform selection |
| `platforms/server/platform.py` | `ServerPlatform` |
| `platforms/server/handler.py` | `WebSocketMessageHandler` |
| `platforms/server/routes.py` | FastAPI routes |
| `platforms/server/client/` | TypeScript WebSocket client |
| `platforms/desktop/platform.py` | `DesktopPlatform` |
| `platforms/desktop/handler.py` | `PyTauriMessageHandler` |
| `platforms/desktop/client/` | TypeScript PyTauri client |
| `platforms/browser/platform.py` | `BrowserPlatform` (runs in Pyodide) |
| `platforms/browser/handler.py` | `BrowserMessageHandler` (queue-based) |
| `platforms/browser/serve_platform.py` | `BrowserServePlatform` (CLI serve mode) |
| `platforms/browser/client/src/TrellisApp.tsx` | React component for browser apps |
| `platforms/browser/client/src/PyodideWorker.ts` | Worker lifecycle manager |
| `platforms/browser/client/src/pyodide.worker.ts` | Worker runtime (Pyodide init, bridge) |
| `platforms/browser/client/src/BrowserClient.ts` | Message client for browser |
| `platforms/common/client/` | Shared TypeScript (types, TreeRenderer, widgets) |
