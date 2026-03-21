/**
 * Common initialization for all Trellis platform entry points.
 *
 * Must be imported first — before any React rendering or other imports.
 * Sets up Symbol.dispose polyfill, widget registry, theme CSS, and
 * console filtering.
 */

// Polyfill for Symbol.dispose (Explicit Resource Management)
// Not yet supported in Safari/older WebKit versions.
// Required by @tauri-apps/api on desktop.
(Symbol as any).dispose ??= Symbol("Symbol.dispose");
(Symbol as any).asyncDispose ??= Symbol("Symbol.asyncDispose");

// Initialize widget registry before any rendering
import { initRegistry } from "@trellis/_registry";
initRegistry();

// Load theme CSS variables and console filtering
import "@trellis/trellis-core/theme.css";
import "@trellis/trellis-core/console";
