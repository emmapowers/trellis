/**
 * Pyodide Web Worker
 *
 * Runs Pyodide in a Web Worker for isolation. When re-running code,
 * the worker can be terminated and recreated for a clean restart.
 *
 * This file is built separately as IIFE and imported as text by PyodideWorker.ts.
 */

// === Pyodide Configuration ===
const PYODIDE_VERSION = "0.29.0";
const PYODIDE_CDN = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.js`;

// Wheel paths - will be combined with pageOrigin to make absolute URLs
const WHEEL_PATHS = [
  "/trellis/trellis-0.1.0-py3-none-any.whl",
  "/trellis-0.1.0-py3-none-any.whl",
];

// === Types ===
declare function importScripts(...urls: string[]): void;
declare function loadPyodide(options: { indexURL: string }): Promise<PyodideInterface>;

interface PyodideInterface {
  loadPackage(packages: string[]): Promise<void>;
  runPythonAsync(code: string): Promise<unknown>;
  registerJsModule(name: string, module: unknown): void;
  pyimport(name: string): { install(pkg: string): Promise<void> };
  globals: {
    set(name: string, value: unknown): void;
    delete(name: string): void;
  };
  FS: {
    mkdir(path: string): void;
    writeFile(path: string, content: string): void;
  };
}

interface PyodideHandler {
  enqueue_message(msg: unknown): void;
}

interface PythonSource {
  type: "code" | "module" | "wheel";
  code?: string;
  files?: Record<string, string>;
  moduleName?: string;
  wheelUrl?: string;
}

interface WorkerMessage {
  type: "init" | "run" | "message";
  trellisWheelUrl?: string;
  pageOrigin?: string;
  source?: PythonSource;
  main?: string;
  payload?: unknown;
}

// === Worker State ===
let pyodide: PyodideInterface | null = null;
let pythonHandler: PyodideHandler | null = null;
let pendingMessages: unknown[] = []; // Queue messages until handler is set

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
    // Flush any messages that arrived before handler was set
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

async function installTrellisWheel(
  pyodide: PyodideInterface,
  customUrl: string | undefined,
  pageOrigin: string
): Promise<void> {
  // Build absolute URLs from paths + origin
  const absoluteUrls = WHEEL_PATHS.map((path) => pageOrigin + path);
  const sources = customUrl ? [customUrl, ...absoluteUrls] : absoluteUrls;

  for (const wheelUrl of sources) {
    try {
      // Use globals to avoid string interpolation injection
      pyodide.globals.set("_wheel_url", wheelUrl);
      await pyodide.runPythonAsync(
        `import micropip\nawait micropip.install(_wheel_url, deps=False)`
      );
      pyodide.globals.delete("_wheel_url");
      return;
    } catch {
      // Try next source
    }
  }

  throw new Error(
    "Could not install trellis wheel. " +
      "For local development, run: pixi run build-wheel && pixi run copy-wheel-to-docs"
  );
}

async function initializePyodide(
  trellisWheelUrl: string | undefined,
  pageOrigin: string
): Promise<void> {
  postStatus("Loading Pyodide runtime...");
  loadPyodideScript();

  const indexURL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
  pyodide = await loadPyodide({ indexURL });

  postStatus("Loading packages...");
  await pyodide.loadPackage(["micropip", "msgspec", "pygments"]);

  const micropip = pyodide.pyimport("micropip");
  await micropip.install("rich");
  await micropip.install("httpx");
  await micropip.install("wcmatch");

  postStatus("Installing Trellis...");
  await installTrellisWheel(pyodide, trellisWheelUrl, pageOrigin);

  pyodide.registerJsModule("trellis_browser_bridge", workerBridge);

  postStatus("Ready");
  self.postMessage({ type: "ready" });
}

// === Source Loading ===
/** Validate that a string is a valid Python identifier */
function isValidPythonIdentifier(name: string): boolean {
  return /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name);
}

function prepareSource(source: PythonSource, main: string | undefined): string {
  if (source.type === "code") {
    return source.code!;
  }

  if (source.type === "module") {
    for (const [path, content] of Object.entries(source.files!)) {
      const parts = path.split("/");
      if (parts.length > 1) {
        let dir = "";
        for (let i = 0; i < parts.length - 1; i++) {
          dir = dir ? dir + "/" + parts[i] : parts[i];
          try {
            pyodide!.FS.mkdir(dir);
          } catch {
            // Directory may already exist
          }
        }
      }
      pyodide!.FS.writeFile(path, content);
    }

    // Validate module name to prevent code injection
    const moduleParts = source.moduleName!.split(".");
    if (!moduleParts.every(isValidPythonIdentifier)) {
      throw new Error(
        `Invalid module name: "${source.moduleName}". Must be a valid Python module path.`
      );
    }
    return `import runpy\nrunpy.run_module("${source.moduleName}", run_name="__main__", alter_sys=True)`;
  }

  if (source.type === "wheel") {
    if (main) {
      // Validate module name to prevent code injection
      // Module names can have dots but each part must be a valid identifier
      const parts = main.split(".");
      if (!parts.every(isValidPythonIdentifier)) {
        throw new Error(
          `Invalid module name: "${main}". Must be a valid Python module path.`
        );
      }
      return `import runpy\nrunpy.run_module("${main}", run_name="__main__", alter_sys=True)`;
    }
    throw new Error("'main' is required when using wheel source mode");
  }

  throw new Error(`Unknown source type: ${(source as PythonSource).type}`);
}

async function runCode(
  source: PythonSource,
  main: string | undefined
): Promise<void> {
  if (!pyodide) {
    throw new Error("Pyodide not initialized. Call init first.");
  }

  if (source.type === "wheel") {
    postStatus("Installing application...");
    // Use globals to avoid string interpolation injection
    pyodide.globals.set("_app_wheel_url", source.wheelUrl);
    await pyodide.runPythonAsync(
      `import micropip\nawait micropip.install(_app_wheel_url)`
    );
    pyodide.globals.delete("_app_wheel_url");
  }

  postStatus("Starting application...");
  const code = prepareSource(source, main);

  pyodide.runPythonAsync(code).catch((e: Error) => {
    postError(e.message);
  });
}

// === Message Handler ===
self.onmessage = async (event: MessageEvent<WorkerMessage>): Promise<void> => {
  const msg = event.data;

  try {
    switch (msg.type) {
      case "init":
        await initializePyodide(msg.trellisWheelUrl, msg.pageOrigin!);
        break;

      case "run":
        await runCode(msg.source!, msg.main);
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
