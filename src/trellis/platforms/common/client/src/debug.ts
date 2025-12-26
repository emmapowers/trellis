/**
 * Debug logging utilities for Trellis client.
 *
 * Debug categories are synchronized from the server via the HelloResponseMessage.
 * When enabled, debug logs appear in the browser console with category prefixes.
 */

/** Set of enabled debug categories (set by server via HelloResponse). */
let debugCategories: Set<string> = new Set();

/**
 * Set the enabled debug categories.
 * Called when HelloResponseMessage is received with debug config.
 *
 * @param categories - Array of category names to enable
 */
export function setDebugCategories(categories: string[]): void {
  debugCategories = new Set(categories);
  if (categories.length > 0) {
    console.debug("[trellis:debug] Enabled categories:", categories.join(", "));
  }
}

/**
 * Check if a debug category is enabled.
 *
 * @param category - Category name to check
 * @returns true if the category or "all" is enabled
 */
export function isDebugEnabled(category: string): boolean {
  return debugCategories.has(category) || debugCategories.has("all");
}

/**
 * Log a debug message if the category is enabled.
 *
 * @param category - Debug category (e.g., "store", "messages", "client")
 * @param args - Arguments to log
 */
export function debugLog(category: string, ...args: unknown[]): void {
  if (isDebugEnabled(category)) {
    console.debug(`[trellis:${category}]`, ...args);
  }
}

/**
 * Get the currently enabled categories.
 *
 * @returns Array of enabled category names
 */
export function getEnabledCategories(): string[] {
  return Array.from(debugCategories);
}
