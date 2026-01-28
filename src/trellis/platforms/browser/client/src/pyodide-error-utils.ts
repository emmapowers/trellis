/**
 * Error categorization utilities for Pyodide worker.
 *
 * These functions translate low-level error messages into user-friendly,
 * actionable messages that help users understand what went wrong.
 */

/** Timeout for Pyodide initialization in milliseconds. */
export const INIT_TIMEOUT_MS = 60_000;

/**
 * Categorize an error into a user-friendly message.
 *
 * Identifies common error types (network, CORS, 404, package) and returns
 * helpful messages with context about what might have caused the error.
 */
export function categorizeError(error: Error): string {
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

/**
 * Entry representing a failed wheel installation attempt.
 */
export interface WheelInstallError {
  url: string;
  error: string;
}

/**
 * Format a comprehensive error message for wheel installation failures.
 *
 * Lists all URLs that were tried, the specific error for each, and
 * instructions for local development.
 */
export function formatWheelInstallError(errors: WheelInstallError[]): string {
  const details = errors
    .map(({ url, error }) => `  • ${url}\n    → ${error}`)
    .join("\n");

  return (
    `Could not install Trellis wheel.\n\n` +
    `Tried:\n${details}\n\n` +
    `For local development, run:\n` +
    `  pixi run build-wheel && pixi run copy-wheel-to-docs`
  );
}

/**
 * Initialization phase identifiers.
 */
export type InitPhase = "pyodide_load" | "micropip_load" | "wheel_install";

/**
 * Format an error message with phase-specific context.
 *
 * Each initialization phase has different failure modes, so we provide
 * tailored context to help users understand what went wrong.
 */
export function formatPhaseError(phase: string, errorMessage: string): string {
  switch (phase) {
    case "pyodide_load":
      return (
        `Loading Pyodide runtime failed: ${errorMessage}\n\n` +
        `This usually indicates a network issue or browser incompatibility.`
      );

    case "micropip_load":
      return `Loading package manager failed: ${errorMessage}`;

    case "wheel_install":
      return `Installing Trellis failed: ${errorMessage}`;

    default:
      return errorMessage;
  }
}

/**
 * Format an error message for initialization timeout.
 *
 * Provides context about what might have caused the timeout and
 * suggests debugging steps.
 */
export function formatTimeoutError(): string {
  return (
    `Initialization timed out.\n\n` +
    `This can happen if:\n` +
    `• Network is slow or blocked\n` +
    `• Python code has an infinite loop during startup\n\n` +
    `Check the browser console for details.`
  );
}
