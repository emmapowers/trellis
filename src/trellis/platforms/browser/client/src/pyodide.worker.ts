/**
 * Pyodide Web Worker
 *
 * Runs Pyodide in a Web Worker for isolation. All Python packages are
 * pre-bundled as a zip at build time and extracted into site-packages
 * via unpackArchive. Pyodide built-in packages are loaded via loadPackage.
 *
 * This file is built separately as IIFE and imported as text by PyodideWorker.ts.
 */

import WHEEL_BUNDLE from "@trellis/wheel-bundle";
import WHEEL_MANIFEST from "@trellis/wheel-manifest";

// === Pyodide Configuration ===
// PYODIDE_VERSION and PYODIDE_PYTHON_VERSION are injected at build time via esbuild --define
declare const PYODIDE_VERSION: string;
declare const PYODIDE_PYTHON_VERSION: string;
const PYODIDE_CDN = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.js`;

// === Types ===
declare function importScripts(...urls: string[]): void;
declare function loadPyodide(options: { indexURL: string }): Promise<PyodideInterface>;

interface PyProxy {
  toJs(): unknown;
  destroy(): void;
}

interface PyodideInterface {
  loadPackage(packages: string[]): Promise<void>;
  runPythonAsync(code: string): Promise<PyProxy | undefined>;
  registerJsModule(name: string, module: unknown): void;
  unpackArchive(buffer: Uint8Array, format: string, options?: { extractDir: string }): void;
  globals: { set(key: string, value: unknown): void };
}

interface PyodideHandler {
  enqueue_message(msg: unknown): void;
}

interface WorkerMessage {
  type: "init" | "run" | "message";
  code?: string;
  payload?: unknown;
}

// === Worker State ===
let pyodide: PyodideInterface | null = null;
let pythonHandler: PyodideHandler | null = null;
let pendingMessages: unknown[] = [];

// === Helper Functions ===
function postStatus(message: string): void {
  self.postMessage({ type: "status", message });
}

function postError(message: string): void {
  console.error("[PyodideWorker] Error:", message);
  self.postMessage({ type: "error", message });
}

// === Worker Bridge ===
const workerBridge = {
  set_handler(handler: PyodideHandler): void {
    pythonHandler = handler;
    if (pendingMessages.length > 0) {
      for (const msg of pendingMessages) {
        handler.enqueue_message(msg);
      }
      pendingMessages = [];
    }
  },
  send_message(msg: unknown): void {
    self.postMessage({ type: "message", payload: msg });
  },
};

// === Pyodide Loading ===
function loadPyodideScript(): void {
  if (typeof loadPyodide !== "undefined") {
    return;
  }
  importScripts(PYODIDE_CDN);
}

async function initializePyodide(): Promise<void> {
  // Phase 1: Load Pyodide runtime
  console.log("[Pyodide] Phase 1: Loading runtime...");
  postStatus("Loading Pyodide runtime...");
  try {
    loadPyodideScript();
    const indexURL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
    pyodide = await loadPyodide({ indexURL });
  } catch (e) {
    throw new Error(
      `Loading Pyodide runtime failed: ${(e as Error).message}\n\n` +
        `This usually indicates a network issue or browser incompatibility.`
    );
  }

  // Phase 2: Load Pyodide built-in packages
  if (WHEEL_MANIFEST.pyodidePackages.length > 0) {
    console.log("[Pyodide] Phase 2: Loading built-in packages:", WHEEL_MANIFEST.pyodidePackages);
    postStatus("Loading packages...");
    await pyodide.loadPackage(WHEEL_MANIFEST.pyodidePackages);
  }

  // Phase 3: Unpack pre-bundled wheels into site-packages
  console.log("[Pyodide] Phase 3: Unpacking wheel bundle...");
  postStatus("Installing application...");
  pyodide.unpackArchive(WHEEL_BUNDLE, "zip", {
    extractDir: `/lib/python${PYODIDE_PYTHON_VERSION}/site-packages`,
  });

  // Phase 4: Register bridge
  console.log("[Pyodide] Phase 4: Registering bridge...");
  pyodide.registerJsModule("trellis_browser_bridge", workerBridge);

  console.log("[Pyodide] Initialization complete");
  postStatus("Ready");
  self.postMessage({ type: "ready" });
}

async function runApp(sourceCode?: string): Promise<void> {
  if (!pyodide) {
    throw new Error("Pyodide not initialized. Call init first.");
  }

  postStatus("Starting application...");

  // Pass config JSON into Pyodide globals for the bootstrap code
  pyodide.globals.set("CONFIG_JSON", WHEEL_MANIFEST.configJson);

  // Choose load path: user-provided source code or pre-bundled module
  let loadStep: string;
  if (sourceCode !== undefined) {
    pyodide.globals.set("SOURCE_CODE", sourceCode);
    loadStep = "apploader.load_app_from_source(SOURCE_CODE)";
  } else {
    loadStep = "apploader.load_app()";
  }

  // Bootstrap the app through AppLoader, mirroring the CLI `trellis run` flow
  const code = `
from trellis.app.config import Config
from trellis.app.apploader import AppLoader, set_apploader

config = Config.from_json(CONFIG_JSON)
apploader = AppLoader.from_config(config)
${loadStep}
set_apploader(apploader)

app = apploader.app

def app_wrapper(_component, system_theme, theme_mode):
    return app.get_wrapped_top(system_theme, theme_mode)

await apploader.platform.run(app.top, app_wrapper, batch_delay=config.batch_delay)
`;

  pyodide
    .runPythonAsync(code)
    .then((proxy) => proxy?.destroy())
    .catch((e: Error) => {
      postError(e.message);
    });
}

// === Message Handler ===
self.onmessage = async (event: MessageEvent<WorkerMessage>): Promise<void> => {
  const msg = event.data;

  try {
    switch (msg.type) {
      case "init":
        await initializePyodide();
        break;

      case "run":
        await runApp(msg.code);
        break;

      case "message":
        if (pythonHandler) {
          pythonHandler.enqueue_message(msg.payload);
        } else {
          pendingMessages.push(msg.payload);
        }
        break;
    }
  } catch (e) {
    console.error("[PyodideWorker] Error:", e);
    postError((e as Error).message);
  }
};
