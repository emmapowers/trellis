/**
 * Trellis Playground
 *
 * A browser-based playground for experimenting with Trellis UI components.
 * Uses Pyodide to run Python in the browser and React to render the UI.
 */

import React from "react";
import { createRoot, Root } from "react-dom/client";
import { SerializedElement, renderNode } from "../../src/trellis/client/src/core";
import { getWidget } from "../../src/trellis/client/src/widgets";

// Pyodide types (loaded from CDN)
declare const loadPyodide: () => Promise<PyodideInterface>;
declare const require: {
  config: (config: { paths: Record<string, string> }) => void;
  (deps: string[], callback: () => void): void;
};
declare const monaco: MonacoNamespace;

interface PyodideInterface {
  loadPackage(packages: string | string[]): Promise<void>;
  pyimport(name: string): PyProxy;
  runPythonAsync(code: string): Promise<unknown>;
}

interface PyProxy {
  install(pkg: string): Promise<void>;
  toJs(options?: { dict_converter: typeof Object.fromEntries }): unknown;
  render(): PyProxy;
  handle_event(callbackId: string): PyProxy;
}

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

const DEFAULT_CODE = `from trellis.core import component
from trellis.core.state import Stateful
from trellis.html import *
from trellis.widgets import *

class CounterState(Stateful):
    count: int = 0

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

@component
def Counter():
    state = CounterState()

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
// Pyodide Setup
// ============================================================================

async function initPyodide(): Promise<PyodideInterface> {
  updateStatus("Loading Pyodide...");

  pyodide = await loadPyodide();

  updateStatus("Installing packages...");

  // Load packages built into Pyodide
  await pyodide.loadPackage(["micropip", "msgspec", "pygments"]);

  updateStatus("Installing Trellis...");

  // Install rich from PyPI (pure Python, works in Pyodide)
  // pygments is already loaded above, so rich's dependency is satisfied
  const micropip = pyodide.pyimport("micropip");
  await micropip.install("rich");

  // Install trellis wheel - try multiple sources
  // deps=false because server dependencies (uvicorn, fastapi, httpx) don't work in Pyodide
  const wheelSources = [
    "/dist/trellis-0.1.0-py3-none-any.whl", // Local development (served from project root)
    "./trellis-0.1.0-py3-none-any.whl", // Same directory (for standalone deployment)
    "https://emmapowers.github.io/trellis/trellis-0.1.0-py3-none-any.whl", // GitHub Pages
  ];

  let installed = false;
  for (const wheelUrl of wheelSources) {
    try {
      console.log(`Trying to install from ${wheelUrl}...`);
      // Call micropip.install via Python to use deps=False correctly
      await pyodide.runPythonAsync(`
import micropip
await micropip.install("${wheelUrl}", deps=False)
`);
      console.log(`Successfully installed from ${wheelUrl}`);
      installed = true;
      break;
    } catch (e) {
      console.log(`Failed to install from ${wheelUrl}: ${(e as Error).message}`);
    }
  }

  if (!installed) {
    throw new Error(
      "Could not install trellis wheel. For local development, run: pixi run build-wheel"
    );
  }

  updateStatus("Ready");
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

async function handleEvent(callbackId: string): Promise<void> {
  if (!runtime) return;

  try {
    // Call the Python callback and get updated tree
    const updatedTree = runtime
      .handle_event(callbackId)
      .toJs({ dict_converter: Object.fromEntries }) as SerializedElement;
    renderTree(updatedTree);
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

    // Get the App component and create runtime
    runtime = (await pyodide!.runPythonAsync(`
from trellis_playground import BrowserRuntime
BrowserRuntime(App)
`)) as PyProxy;

    // Initial render
    const tree = runtime.render().toJs({ dict_converter: Object.fromEntries }) as SerializedElement;
    renderTree(tree);

    updateStatus("Running");
  } catch (e) {
    showError((e as Error).message);
    updateStatus("Error");
  }
}

// ============================================================================
// Initialization
// ============================================================================

async function init(): Promise<void> {
  try {
    // Initialize in parallel
    await Promise.all([initPyodide(), initMonaco()]);

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
