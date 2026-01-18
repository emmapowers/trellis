/**
 * Main thread worker manager for Pyodide.
 *
 * Creates and manages a Web Worker running Pyodide. The worker code is built
 * separately and imported as text, then loaded via blob URL. When re-running
 * code, call terminate() to kill the worker (and all Python execution), then
 * create() a new one.
 */

// Import worker code as text (built by bundler with --loader:.worker-bundle=text)
// Uses @trellis alias so esbuild can resolve the pre-built worker bundle
import WORKER_CODE from "@trellis/browser/pyodide.worker-bundle";
import type { HelloMessage, EventMessage, UrlChangedMessage } from "@trellis/trellis-core/client/src/types";

// === Types ===

/** Python source to load and execute */
export type PythonSource =
  | { type: "code"; code: string }
  | { type: "module"; files: Record<string, string>; moduleName: string }
  | { type: "wheel"; wheelUrl: string };

/** Messages from main thread to worker */
type WorkerInMessage =
  | { type: "init"; trellisWheelUrl?: string; pageOrigin: string }
  | { type: "run"; source: PythonSource; main?: string }
  | { type: "message"; payload: HelloMessage | EventMessage | UrlChangedMessage };

/** Messages from worker to main thread */
type WorkerOutMessage =
  | { type: "status"; message: string }
  | { type: "ready" }
  | { type: "message"; payload: Record<string, unknown> }
  | { type: "error"; message: string };

export interface PyodideWorkerOptions {
  /** Callback for status updates during loading */
  onStatus?: (status: string) => void;
  /** Custom trellis wheel URL */
  trellisWheelUrl?: string;
}

type MessageCallback = (msg: Record<string, unknown>) => void;

// === Worker Manager ===

/**
 * Manages a Pyodide Web Worker.
 *
 * Usage:
 * ```ts
 * const worker = new PyodideWorker();
 * await worker.create({ onStatus: console.log });
 * worker.onMessage((msg) => handleMessage(msg));
 * worker.run(source, main);
 * // Later, to re-run:
 * worker.terminate();
 * await worker.create({ onStatus: console.log });
 * ```
 */
export class PyodideWorker {
  private worker: Worker | null = null;
  private messageCallback: MessageCallback | null = null;
  private statusCallback: ((status: string) => void) | null = null;
  private readyPromise: Promise<void> | null = null;
  private readyResolve: (() => void) | null = null;
  private readyReject: ((error: Error) => void) | null = null;
  private blobUrl: string | null = null;

  /**
   * Create and initialize a new worker with Pyodide.
   *
   * This loads Pyodide, installs packages, and registers the bridge.
   * Resolves when Pyodide is ready to run code.
   */
  async create(options: PyodideWorkerOptions = {}): Promise<void> {
    if (this.worker) {
      throw new Error("Worker already exists. Call terminate() first.");
    }

    this.statusCallback = options.onStatus ?? null;

    // Create promise to track initialization
    this.readyPromise = new Promise((resolve, reject) => {
      this.readyResolve = resolve;
      this.readyReject = reject;
    });

    // Create worker from built code via blob URL
    const blob = new Blob([WORKER_CODE], { type: "application/javascript" });
    this.blobUrl = URL.createObjectURL(blob);
    this.worker = new Worker(this.blobUrl);

    // Handle messages from worker
    this.worker.onmessage = (event: MessageEvent<WorkerOutMessage>) => {
      this.handleWorkerMessage(event.data);
    };

    this.worker.onerror = (error) => {
      console.error("Worker error:", error);
      this.readyReject?.(new Error(`Worker error: ${error.message}`));
    };

    // Send init message with page origin for absolute URL construction
    const initMsg: WorkerInMessage = {
      type: "init",
      trellisWheelUrl: options.trellisWheelUrl,
      pageOrigin: globalThis.location?.origin ?? "",
    };
    this.worker.postMessage(initMsg);

    // Wait for ready signal
    return this.readyPromise;
  }

  /**
   * Handle messages from the worker.
   */
  private handleWorkerMessage(msg: WorkerOutMessage): void {
    switch (msg.type) {
      case "status":
        this.statusCallback?.(msg.message);
        break;

      case "ready":
        this.readyResolve?.();
        // Clear callbacks to prevent later error calls from rejecting resolved promise
        this.readyResolve = null;
        this.readyReject = null;
        break;

      case "message":
        this.messageCallback?.(msg.payload);
        break;

      case "error":
        console.error("Worker reported error:", msg.message);
        // If we're still initializing, reject the promise
        if (this.readyReject) {
          this.readyReject(new Error(msg.message));
          this.readyResolve = null;
          this.readyReject = null;
        }
        break;
    }
  }

  /**
   * Register callback for messages from Python (HELLO_RESPONSE, RENDER, ERROR).
   */
  onMessage(callback: MessageCallback): void {
    this.messageCallback = callback;
  }

  /**
   * Send a message to Python (HELLO, EVENT, URL_CHANGED).
   */
  sendMessage(msg: HelloMessage | EventMessage | UrlChangedMessage): void {
    if (!this.worker) {
      console.warn("PyodideWorker: No worker, cannot send message");
      return;
    }

    const workerMsg: WorkerInMessage = {
      type: "message",
      payload: msg,
    };
    this.worker.postMessage(workerMsg);
  }

  /**
   * Run Python code in the worker.
   */
  run(source: PythonSource, main?: string): void {
    if (!this.worker) {
      throw new Error("Worker not created. Call create() first.");
    }

    const runMsg: WorkerInMessage = {
      type: "run",
      source,
      main,
    };
    this.worker.postMessage(runMsg);
  }

  /**
   * Terminate the worker, killing all Python execution.
   *
   * After calling this, you can create() a new worker for a fresh start.
   */
  terminate(): void {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
    }
    if (this.blobUrl) {
      URL.revokeObjectURL(this.blobUrl);
      this.blobUrl = null;
    }
    this.messageCallback = null;
    this.statusCallback = null;
    this.readyPromise = null;
    this.readyResolve = null;
    this.readyReject = null;
  }

  /**
   * Check if the worker exists.
   */
  isAlive(): boolean {
    return this.worker !== null;
  }
}
