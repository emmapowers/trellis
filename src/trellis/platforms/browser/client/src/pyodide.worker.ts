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

interface PyProxy {
  toJs(): unknown;
  destroy(): void;
}

interface PyodideInterface {
  loadPackage(packages: string[]): Promise<void>;
  // Returns undefined when Python returns None, otherwise a PyProxy
  runPythonAsync(code: string): Promise<PyProxy | undefined>;
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

/** Result from Python wheel install helper */
interface WheelInstallResult {
  success: boolean;
  retry: boolean;
  error: string;
}

/**
 * Python helper for wheel installation with structured error handling.
 *
 * Returns a dict with:
 * - success: whether installation succeeded
 * - retry: whether to try the next URL (only true for fetch errors)
 * - error: error message if failed
 */
const WHEEL_INSTALL_HELPER = `
async def _try_install_wheel(url: str) -> dict:
    """Try to install a wheel, returning structured error info."""
    import micropip
    try:
        await micropip.install(url, verbose=True)
        return {"success": True, "retry": False, "error": ""}
    except Exception as e:
        msg = str(e).lower()
        # Fetch errors - worth trying next URL
        is_fetch_error = (
            "404" in msg or
            "not found" in msg or
            "failed to fetch" in msg or
            "networkerror" in msg or
            "network error" in msg or
            "cors" in msg or
            "cross-origin" in msg or
            "not a zip file" in msg  # Server returned HTML error page
        )
        return {
            "success": False,
            "retry": is_fetch_error,
            "error": str(e)
        }
`;

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

/**
 * Categorize an error into a user-friendly message.
 *
 * Identifies common error types (network, CORS, 404, package) and returns
 * helpful messages with context about what might have caused the error.
 */
function categorizeError(error: Error): string {
  const msg = error.message.toLowerCase();

  // Network connectivity issues
  if (msg.includes("networkerror") || msg.includes("failed to fetch")) {
    return "Network error - check your internet connection or if the server is running";
  }

  // CORS policy violations
  if (msg.includes("cors") || msg.includes("cross-origin")) {
    return "CORS error - the server needs to allow cross-origin requests";
  }

  // File not found (404)
  if (msg.includes("404") || msg.includes("not found")) {
    return "File not found (404)";
  }

  // Package installation failures (micropip-specific)
  if (msg.includes("no matching distribution") || msg.includes("can't find")) {
    return "Package not available for Pyodide (may need a pure Python wheel)";
  }

  // Return original message for unknown errors
  return error.message;
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
  const errors: Array<{ url: string; error: string }> = [];

  for (const wheelUrl of sources) {
    console.log(`[Pyodide] Trying wheel: ${wheelUrl}`);
    // Use globals to avoid string interpolation injection
    pyodide.globals.set("_wheel_url", wheelUrl);
    const resultProxy = await pyodide.runPythonAsync(
      `await _try_install_wheel(_wheel_url)`
    );
    pyodide.globals.delete("_wheel_url");

    // _try_install_wheel always returns a dict, never None
    if (!resultProxy) {
      throw new Error("Unexpected: _try_install_wheel returned None");
    }

    let result: WheelInstallResult;
    try {
      result = resultProxy.toJs() as WheelInstallResult;
    } finally {
      resultProxy.destroy();
    }

    if (result.success) {
      console.log(`[Pyodide] Successfully installed wheel from: ${wheelUrl}`);
      // Log installed packages for debugging (print returns None, no proxy)
      await pyodide.runPythonAsync(`
import micropip
print("[Pyodide] Installed packages:", list(micropip.list().keys()))
`);
      return;
    }

    // Installation failed
    const errorMsg = categorizeError(new Error(result.error));
    console.warn(`[Pyodide] Failed to install from ${wheelUrl}: ${errorMsg}`);
    errors.push({ url: wheelUrl, error: errorMsg });

    if (!result.retry) {
      // Not a fetch error - don't try other URLs, they'll have the same problem
      console.warn(`[Pyodide] Installation error (not a fetch error), stopping`);
      break;
    }
  }

  // Determine error message based on whether we stopped early
  const lastError = errors[errors.length - 1];
  const stoppedEarly = errors.length < sources.length;

  if (stoppedEarly && lastError) {
    // We stopped because of an installation error, not because we ran out of URLs
    throw new Error(
      `Failed to install Trellis wheel.\n\n` +
        `The wheel was found but installation failed:\n` +
        `  ${lastError.error}\n\n` +
        `This is usually caused by a missing or incompatible dependency.`
    );
  }

  // All URLs failed with fetch errors
  const details = errors
    .map(({ url, error }) => `  • ${url}\n    → ${error}`)
    .join("\n");

  throw new Error(
    `Could not download Trellis wheel.\n\n` +
      `Tried:\n${details}\n\n` +
      `For local development, run:\n` +
      `  pixi run build-wheel && pixi run copy-wheel-to-docs`
  );
}

async function initializePyodide(
  trellisWheelUrl: string | undefined,
  pageOrigin: string
): Promise<void> {
  // Phase 1: Load Pyodide runtime
  console.log("[Pyodide] Phase 1: Loading runtime...");
  postStatus("Loading Pyodide runtime...");
  try {
    loadPyodideScript();
    const indexURL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
    pyodide = await loadPyodide({ indexURL });
  } catch (e) {
    throw new Error(
      `Loading Pyodide runtime failed: ${categorizeError(e as Error)}\n\n` +
        `This usually indicates a network issue or browser incompatibility.`
    );
  }

  // Phase 2: Load micropip and define install helper
  console.log("[Pyodide] Phase 2: Loading micropip...");
  postStatus("Installing Trellis...");
  try {
    await pyodide.loadPackage(["micropip"]);
    // Defining a function returns None, so no proxy to destroy
    await pyodide.runPythonAsync(WHEEL_INSTALL_HELPER);
  } catch (e) {
    throw new Error(
      `Loading package manager failed: ${categorizeError(e as Error)}`
    );
  }

  // Phase 3: Install Trellis wheel
  console.log("[Pyodide] Phase 3: Installing Trellis wheel...");
  await installTrellisWheel(pyodide, trellisWheelUrl, pageOrigin);

  // Phase 4: Register bridge
  console.log("[Pyodide] Phase 4: Registering bridge...");
  pyodide.registerJsModule("trellis_browser_bridge", workerBridge);

  console.log("[Pyodide] Initialization complete");
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
    // micropip.install returns None, no proxy to destroy
    await pyodide.runPythonAsync(
      `import micropip\nawait micropip.install(_app_wheel_url)`
    );
    pyodide.globals.delete("_app_wheel_url");
  }

  postStatus("Starting application...");
  const code = prepareSource(source, main);

  // App code may or may not return a value; destroy proxy if present
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
