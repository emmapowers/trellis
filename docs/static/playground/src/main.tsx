/**
 * Trellis Playground
 *
 * A browser-based playground for experimenting with Trellis UI components.
 * Uses Pyodide to run Python in the browser and React to render the UI.
 */

import React from "react";
import { createRoot, Root } from "react-dom/client";
import { SerializedElement, renderNode } from "../../../../src/trellis/client/src/core";
import { getWidget } from "../../../../src/trellis/client/src/widgets";
import { initPyodide, PyodideInterface, PyProxy } from "../../../src/lib/pyodide-init";

// Monaco types (loaded from CDN)
declare const require: {
  config: (config: { paths: Record<string, string> }) => void;
  (deps: string[], callback: () => void): void;
};
declare const monaco: MonacoNamespace;

interface MonacoNamespace {
  editor: {
    create(container: HTMLElement, options: MonacoEditorOptions): MonacoEditor;
  };
}

interface MonacoEditorOptions {
  value: string;
  language: string;
  theme: string;
  minimap: { enabled: boolean };
  fontSize: number;
  lineNumbers: string;
  scrollBeyondLastLine: boolean;
  automaticLayout: boolean;
  tabSize: number;
}

interface MonacoEditor {
  getValue(): string;
  setValue(value: string): void;
}

// ============================================================================
// Global State
// ============================================================================

let pyodide: PyodideInterface | null = null;
let runtime: PyProxy | null = null;
let editor: MonacoEditor | null = null;
let reactRoot: Root | null = null;

// ============================================================================
// Default Example Code
// ============================================================================

const DEFAULT_CODE = `from dataclasses import dataclass
from trellis.core import component
from trellis.core.state import Stateful
from trellis.html import *
from trellis.widgets import *

@dataclass
class CounterState(Stateful):
    count: int

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

@component
def Counter():
    state = CounterState(count=0)

    with Div(style={"padding": "20px", "fontFamily": "system-ui"}):
        with Column():
            H1("Trellis Counter")
            P(f"Count: {state.count}")
            with Row():
                Button(text="-", on_click=state.decrement)
                Button(text="+", on_click=state.increment)

# Export the root component
App = Counter
`;

// ============================================================================
// Pyodide Setup (uses shared module)
// ============================================================================

async function setupPyodide(): Promise<PyodideInterface> {
  pyodide = await initPyodide(updateStatus);
  return pyodide;
}

// ============================================================================
// Monaco Editor Setup
// ============================================================================

async function initMonaco(): Promise<MonacoEditor> {
  return new Promise((resolve) => {
    require.config({
      paths: {
        vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs",
      },
    });

    require(["vs/editor/editor.main"], function () {
      const container = document.getElementById("editor-container")!;
      container.innerHTML = ""; // Remove loading spinner

      editor = monaco.editor.create(container, {
        value: DEFAULT_CODE,
        language: "python",
        theme: "vs-light",
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: "on",
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 4,
      });

      resolve(editor);
    });
  });
}

// ============================================================================
// App Logic
// ============================================================================

function updateStatus(text: string): void {
  document.getElementById("status")!.textContent = text;
}

function showError(error: string): void {
  const errorDiv = document.getElementById("error")!;
  errorDiv.textContent = error;
  errorDiv.style.display = "block";
}

function hideError(): void {
  document.getElementById("error")!.style.display = "none";
}

function renderTree(tree: SerializedElement): void {
  const previewDiv = document.getElementById("preview")!;

  if (!reactRoot) {
    reactRoot = createRoot(previewDiv);
  }

  const element = renderNode(tree, { onEvent: handleEvent, getWidget }, "root");
  reactRoot.render(element);
}

function handleEvent(callbackId: string, args?: unknown[]): void {
  if (!runtime) return;

  try {
    // Post event to Python - render callback will be called with updated tree
    runtime.post_event(callbackId, args ?? []);
  } catch (e) {
    showError(`Event error: ${(e as Error).message}`);
  }
}

async function runCode(): Promise<void> {
  hideError();
  updateStatus("Running...");

  const code = editor!.getValue();

  try {
    // Execute user code
    await pyodide!.runPythonAsync(code);

    // Register JS render callback in Python globals via pyodide.registerJsModule
    // The callback receives tree dicts from Python and renders them
    const jsCallbacks = {
      render: (treeProxy: PyProxy) => {
        const tree = treeProxy.toJs({ dict_converter: Object.fromEntries }) as SerializedElement;
        renderTree(tree);
      }
    };
    pyodide!.registerJsModule("js_callbacks", jsCallbacks);

    // Create runtime and start message loop in background
    runtime = (await pyodide!.runPythonAsync(`
import asyncio
import js_callbacks
from trellis_playground import PlaygroundMessageHandler

handler = PlaygroundMessageHandler(App)
handler.set_render_callback(js_callbacks.render)

# Start the message loop in the background
asyncio.ensure_future(handler.run())

handler
`)) as PyProxy;

    updateStatus("Running");
  } catch (e) {
    showError((e as Error).message);
    updateStatus("Error");
  }
}

// ============================================================================
// URL Code Loading
// ============================================================================

function getCodeFromUrl(): string | null {
  const hash = window.location.hash;
  if (hash.startsWith('#code=')) {
    try {
      const encoded = hash.slice(6); // Remove '#code='
      return decodeURIComponent(atob(encoded));
    } catch (e) {
      console.warn('Failed to decode code from URL:', e);
      return null;
    }
  }
  return null;
}

// ============================================================================
// Initialization
// ============================================================================

async function init(): Promise<void> {
  try {
    // Initialize in parallel
    await Promise.all([setupPyodide(), initMonaco()]);

    // Check for code in URL hash
    const urlCode = getCodeFromUrl();
    if (urlCode && editor) {
      editor.setValue(urlCode);
    }

    // Enable run button
    const runBtn = document.getElementById("run-btn") as HTMLButtonElement;
    runBtn.disabled = false;
    runBtn.addEventListener("click", runCode);

    // Run the default code on startup
    await runCode();

    // Add keyboard shortcut (Ctrl/Cmd + Enter to run)
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        runCode();
      }
    });
  } catch (e) {
    showError(`Initialization failed: ${(e as Error).message}`);
    updateStatus("Failed");
  }
}

// Start initialization when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
