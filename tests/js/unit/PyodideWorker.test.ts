/**
 * Tests for PyodideWorker error handling.
 *
 * These tests verify that the PyodideWorker properly handles and surfaces
 * errors through callbacks.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock Worker before importing PyodideWorker
class MockWorker {
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: ErrorEvent) => void) | null = null;
  private messageHandler: ((msg: unknown) => void) | null = null;

  postMessage(msg: unknown): void {
    this.messageHandler?.(msg);
  }

  // Test helper to simulate messages from the worker
  simulateMessage(data: unknown): void {
    this.onmessage?.({ data } as MessageEvent);
  }

  // Test helper to set up message handler
  onPostMessage(handler: (msg: unknown) => void): void {
    this.messageHandler = handler;
  }

  terminate(): void {}
}

// Mock URL.createObjectURL and URL.revokeObjectURL
const mockCreateObjectURL = vi.fn(() => "blob:mock-url");
const mockRevokeObjectURL = vi.fn();
vi.stubGlobal("URL", {
  createObjectURL: mockCreateObjectURL,
  revokeObjectURL: mockRevokeObjectURL,
});

// Mock Blob
vi.stubGlobal("Blob", class MockBlob {
  constructor(_parts: unknown[], _options: unknown) {}
});

// Store reference to mock worker for test control
let mockWorkerInstance: MockWorker | null = null;

vi.stubGlobal("Worker", class {
  constructor(_url: string) {
    mockWorkerInstance = new MockWorker();
    return mockWorkerInstance;
  }
});

// Mock globalThis.location
vi.stubGlobal("location", { origin: "http://localhost:3000" });

// Now import PyodideWorker after mocks are set up
import { PyodideWorker } from "@browser/PyodideWorker";

describe("PyodideWorker error handling", () => {
  beforeEach(() => {
    mockWorkerInstance = null;
    vi.clearAllMocks();
  });

  it("calls onError callback for errors after ready", async () => {
    const errors: string[] = [];
    const worker = new PyodideWorker();

    // Start creation but don't await yet
    const createPromise = worker.create({
      onError: (e) => errors.push(e),
    });

    // Simulate ready message
    mockWorkerInstance?.simulateMessage({ type: "ready" });

    await createPromise;

    // Now simulate an error after ready
    mockWorkerInstance?.simulateMessage({
      type: "error",
      message: "Runtime error in Python",
    });

    expect(errors).toContain("Runtime error in Python");
  });

  it("rejects create promise for errors during initialization", async () => {
    const worker = new PyodideWorker();

    // Start creation
    const createPromise = worker.create({});

    // Simulate error during init (before ready)
    mockWorkerInstance?.simulateMessage({
      type: "error",
      message: "Failed to load Pyodide",
    });

    await expect(createPromise).rejects.toThrow("Failed to load Pyodide");
  });

  it("calls status callback during loading", async () => {
    const statuses: string[] = [];
    const worker = new PyodideWorker();

    const createPromise = worker.create({
      onStatus: (status) => statuses.push(status),
    });

    // Simulate status updates
    mockWorkerInstance?.simulateMessage({
      type: "status",
      message: "Loading Pyodide...",
    });
    mockWorkerInstance?.simulateMessage({
      type: "status",
      message: "Installing packages...",
    });
    mockWorkerInstance?.simulateMessage({ type: "ready" });

    await createPromise;

    expect(statuses).toContain("Loading Pyodide...");
    expect(statuses).toContain("Installing packages...");
  });

  it("does not call onError during initialization (rejects promise instead)", async () => {
    const errors: string[] = [];
    const worker = new PyodideWorker();

    const createPromise = worker.create({
      onError: (e) => errors.push(e),
    });

    // Error during init should reject, not call onError
    mockWorkerInstance?.simulateMessage({
      type: "error",
      message: "Init error",
    });

    await expect(createPromise).rejects.toThrow("Init error");
    expect(errors).toHaveLength(0);
  });
});
