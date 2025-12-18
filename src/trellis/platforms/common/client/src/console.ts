/**
 * Shared console configuration for all platforms.
 *
 * Provides warning filtering and allows platforms to add custom handlers
 * (e.g., desktop forwards to Python stdout).
 */

type LogHandler = (level: string, args: unknown[]) => void;
const handlers: LogHandler[] = [];

/** Register a handler to receive console messages (for platform-specific forwarding). */
export function addConsoleHandler(handler: LogHandler): void {
  handlers.push(handler);
}

function shouldSuppressWarning(message: unknown): boolean {
  return (
    typeof message === "string" &&
    message.startsWith("If you do not provide a visible label")
  );
}

// Override console methods once, with filtering and handler dispatch
const originalLog = console.log;
const originalWarn = console.warn;
const originalError = console.error;

console.log = (...args: unknown[]) => {
  originalLog.apply(console, args);
  handlers.forEach((h) => h("log", args));
};

console.warn = (...args: unknown[]) => {
  if (shouldSuppressWarning(args[0])) return;
  originalWarn.apply(console, args);
  handlers.forEach((h) => h("warn", args));
};

console.error = (...args: unknown[]) => {
  originalError.apply(console, args);
  handlers.forEach((h) => h("error", args));
};
