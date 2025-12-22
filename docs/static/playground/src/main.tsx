/**
 * Trellis Playground
 *
 * A browser-based playground for experimenting with Trellis UI components.
 * Uses TrellisApp for Pyodide/React integration.
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import { createRoot } from "react-dom/client";
import { TrellisApp } from "../../../../src/trellis/platforms/browser/client/src/TrellisApp";

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

/**
 * Wrap user code with Trellis boilerplate.
 *
 * The playground expects an `App` component to be defined. This wrapper
 * adds the @async_main entry point that runs the app.
 */
function wrapWithBoilerplate(code: string): string {
  return `${code}

from trellis import Trellis, async_main

@async_main
async def _trellis_main():
    app = Trellis(top=App)
    await app.serve()
`;
}

const DEFAULT_CODE = `from dataclasses import dataclass
from trellis import component, Stateful, mutable, callback, Margin, Padding, Width, Height
from trellis import widgets as w
from trellis import html as h

@dataclass
class CounterState(Stateful):
    count: int = 0

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

@component
def Counter():
    state = CounterState()

    with w.Column(gap=12, style={"padding": "20px"}):
        w.Heading(text="Trellis Counter", level=2)
        w.Label(text=f"Count: {state.count}", font_size=16)
        with w.Row(gap=8):
            w.Button(text="-", on_click=state.decrement, size="sm")
            w.Button(text="+", on_click=state.increment, size="sm")

# Export the root component
App = Counter
`;

function getCodeFromUrl(): string | null {
  const hash = window.location.hash;
  if (hash.startsWith("#code=")) {
    try {
      const encoded = hash.slice(6);
      return decodeURIComponent(atob(encoded));
    } catch (e) {
      console.warn("Failed to decode code from URL:", e);
      return null;
    }
  }
  return null;
}

function Playground(): React.ReactElement {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [runId, setRunId] = useState(0);
  const [status, setStatus] = useState("Initializing...");
  const [error, setError] = useState<string | null>(null);
  const [editorReady, setEditorReady] = useState(false);
  const editorRef = useRef<MonacoEditor | null>(null);

  // Initialize Monaco editor
  useEffect(() => {
    require.config({
      paths: {
        vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs",
      },
    });

    require(["vs/editor/editor.main"], function () {
      const container = document.getElementById("editor-container")!;
      container.innerHTML = "";

      // Check for code in URL hash
      const urlCode = getCodeFromUrl();
      const initialCode = urlCode ?? DEFAULT_CODE;
      if (urlCode) {
        setCode(urlCode);
      }

      editorRef.current = monaco.editor.create(container, {
        value: initialCode,
        language: "python",
        theme: "vs-light",
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: "on",
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 4,
      });

      setEditorReady(true);
    });
  }, []);

  // Auto-run on first load after editor is ready
  useEffect(() => {
    if (editorReady && runId === 0) {
      handleRun();
    }
  }, [editorReady]);

  const handleRun = useCallback(() => {
    if (!editorRef.current) return;
    const newCode = editorRef.current.getValue();
    setCode(newCode);
    setError(null);
    setRunId((id) => id + 1);
  }, []);

  // Keyboard shortcut (Ctrl/Cmd + Enter to run)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        handleRun();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleRun]);

  // Enable run button when editor is ready
  useEffect(() => {
    const runBtn = document.getElementById("run-btn") as HTMLButtonElement;
    if (runBtn) {
      runBtn.disabled = !editorReady;
      runBtn.onclick = handleRun;
    }
  }, [editorReady, handleRun]);

  // Update status display
  useEffect(() => {
    const statusEl = document.getElementById("status");
    if (statusEl) {
      statusEl.textContent = status;
    }
  }, [status]);

  // Update error display
  useEffect(() => {
    const errorEl = document.getElementById("error");
    if (errorEl) {
      if (error) {
        errorEl.textContent = error;
        errorEl.style.display = "block";
      } else {
        errorEl.style.display = "none";
      }
    }
  }, [error]);

  if (runId === 0) {
    return <div style={{ padding: "20px", color: "#64748b" }}>Click Run to start...</div>;
  }

  // Wrap the user code with boilerplate
  const wrappedCode = wrapWithBoilerplate(code);

  return (
    <TrellisApp
      key={runId}
      source={{ type: "code", code: wrappedCode }}
      onStatusChange={setStatus}
      errorComponent={(msg) => {
        setError(msg);
        return null;
      }}
    />
  );
}

// Mount the playground
const previewDiv = document.getElementById("preview")!;
const root = createRoot(previewDiv);
root.render(<Playground />);
