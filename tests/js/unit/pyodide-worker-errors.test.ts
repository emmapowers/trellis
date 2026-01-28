/**
 * Tests for Pyodide worker error handling utilities.
 *
 * These tests verify that errors are categorized into user-friendly messages
 * and that the worker provides actionable error information.
 */
import { describe, it, expect } from "vitest";

import {
  categorizeError,
  formatWheelInstallError,
  formatPhaseError,
  formatTimeoutError,
  INIT_TIMEOUT_MS,
} from "@browser/pyodide-error-utils";

describe("categorizeError", () => {
  it("identifies network errors", () => {
    const error = new Error("NetworkError when attempting to fetch resource");
    expect(categorizeError(error)).toContain("Network error");
  });

  it("identifies failed to fetch errors", () => {
    const error = new Error("Failed to fetch");
    expect(categorizeError(error)).toContain("Network error");
  });

  it("identifies CORS errors from blocked message", () => {
    const error = new Error("Cross-Origin Request Blocked");
    expect(categorizeError(error)).toContain("CORS");
  });

  it("identifies CORS errors from cors keyword", () => {
    const error = new Error("cors policy: No 'Access-Control-Allow-Origin'");
    expect(categorizeError(error)).toContain("CORS");
  });

  it("identifies 404 errors", () => {
    const error = new Error("404 Not Found");
    expect(categorizeError(error)).toContain("not found");
  });

  it("identifies 404 errors with different casing", () => {
    const error = new Error("HTTP Error: 404 not found");
    expect(categorizeError(error)).toContain("not found");
  });

  it("identifies missing package errors from micropip", () => {
    const error = new Error("Can't find a pure Python 3 wheel for 'numpy'");
    expect(categorizeError(error)).toContain("not available for Pyodide");
  });

  it("identifies missing distribution errors", () => {
    const error = new Error("No matching distribution found for somepackage");
    expect(categorizeError(error)).toContain("not available for Pyodide");
  });

  it("passes through unknown errors unchanged", () => {
    const error = new Error("Something completely unexpected happened");
    expect(categorizeError(error)).toBe("Something completely unexpected happened");
  });

  it("handles errors with empty message", () => {
    const error = new Error("");
    expect(categorizeError(error)).toBe("");
  });
});

describe("formatWheelInstallError", () => {
  it("lists all URLs tried when all fail", () => {
    const errors = [
      { url: "/path/a.whl", error: "404 Not Found" },
      { url: "/path/b.whl", error: "Network error" },
    ];
    const message = formatWheelInstallError(errors);

    expect(message).toContain("/path/a.whl");
    expect(message).toContain("/path/b.whl");
  });

  it("includes the specific error for each URL", () => {
    const errors = [
      { url: "/a.whl", error: "File not found (404)" },
      { url: "/b.whl", error: "CORS error" },
    ];
    const message = formatWheelInstallError(errors);

    expect(message).toContain("File not found (404)");
    expect(message).toContain("CORS error");
  });

  it("includes dev instructions", () => {
    const errors = [{ url: "/a.whl", error: "404" }];
    const message = formatWheelInstallError(errors);

    expect(message).toContain("pixi run build-wheel");
  });

  it("formats errors with URL and error on separate lines", () => {
    const errors = [{ url: "/test.whl", error: "some error" }];
    const message = formatWheelInstallError(errors);

    // Should have structured output with bullet points
    expect(message).toContain("•");
    expect(message).toContain("/test.whl");
    expect(message).toContain("some error");
  });

  it("has a clear header explaining the problem", () => {
    const errors = [{ url: "/a.whl", error: "error" }];
    const message = formatWheelInstallError(errors);

    expect(message).toContain("Could not install Trellis wheel");
  });
});

describe("formatPhaseError", () => {
  it("formats pyodide_load phase with helpful context", () => {
    const message = formatPhaseError("pyodide_load", "NetworkError");

    expect(message).toContain("Loading Pyodide runtime failed");
    expect(message).toContain("NetworkError");
    expect(message).toContain("network");
  });

  it("formats micropip_load phase with helpful context", () => {
    const message = formatPhaseError("micropip_load", "Some error");

    expect(message).toContain("package manager");
    expect(message).toContain("Some error");
  });

  it("formats wheel_install phase with helpful context", () => {
    const message = formatPhaseError("wheel_install", "Wheel error");

    expect(message).toContain("Trellis");
    expect(message).toContain("Wheel error");
  });

  it("formats unknown phases with generic message", () => {
    const message = formatPhaseError("unknown_phase", "Error details");

    expect(message).toContain("Error details");
  });
});

describe("formatTimeoutError", () => {
  it("includes timeout message", () => {
    const message = formatTimeoutError();

    expect(message).toContain("timed out");
  });

  it("includes common causes", () => {
    const message = formatTimeoutError();

    expect(message).toContain("Network");
    expect(message).toContain("infinite loop");
  });

  it("suggests checking console", () => {
    const message = formatTimeoutError();

    expect(message).toContain("console");
  });
});

describe("INIT_TIMEOUT_MS", () => {
  it("is 60 seconds", () => {
    expect(INIT_TIMEOUT_MS).toBe(60_000);
  });
});
