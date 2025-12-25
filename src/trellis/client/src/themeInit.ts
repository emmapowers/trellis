/**
 * Theme initialization helper for Trellis.
 *
 * This script should run as early as possible (ideally inline in <head>)
 * to prevent flash of wrong theme. It detects the theme preference and
 * sets the data-theme attribute before any content renders.
 *
 * Usage:
 *   - Standalone: trellisInitTheme() - finds #trellis-root or uses body
 *   - Embedded: trellisInitTheme(element) - initializes specific element
 */

/**
 * Detect the current theme preference.
 *
 * Priority:
 * 1. Host page theme (Docusaurus, etc.) via data-theme on <html>
 * 2. OS preference via prefers-color-scheme media query
 * 3. Default to "light"
 */
export function detectTheme(): "light" | "dark" {
  // Check for host page theme first (Docusaurus, etc.)
  const hostTheme = document.documentElement.dataset.theme;
  if (hostTheme === "dark" || hostTheme === "light") {
    return hostTheme;
  }

  // Fall back to OS preference
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }

  return "light";
}

/**
 * Initialize theme on an element.
 *
 * Sets the data-theme attribute and adds the trellis-root class.
 * If no element is provided, finds #trellis-root or falls back to body.
 *
 * @param el - Optional element to initialize. If not provided, finds
 *             #trellis-root or uses document.body.
 * @returns The initialized element
 */
export function trellisInitTheme(el?: HTMLElement | null): HTMLElement {
  const root =
    el || document.getElementById("trellis-root") || document.body;

  root.dataset.theme = detectTheme();
  root.classList.add("trellis-root");

  return root;
}

/**
 * Generate a unique ID for a Trellis root element.
 *
 * Used in multi-instance scenarios (e.g., multiple Trellis apps on
 * the same Docusaurus page) where each instance needs a unique ID.
 */
export function generateTrellisRootId(): string {
  return `trellis-root-${crypto.randomUUID().slice(0, 8)}`;
}

// For inline script usage - attach to window
declare global {
  interface Window {
    trellisInitTheme: typeof trellisInitTheme;
    detectTheme: typeof detectTheme;
    generateTrellisRootId: typeof generateTrellisRootId;
  }
}

if (typeof window !== "undefined") {
  window.trellisInitTheme = trellisInitTheme;
  window.detectTheme = detectTheme;
  window.generateTrellisRootId = generateTrellisRootId;
}
