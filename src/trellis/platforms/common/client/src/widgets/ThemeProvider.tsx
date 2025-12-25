import React, { useEffect, useRef } from "react";
import { useHostThemeMode } from "../TrellisContext";

interface ThemeProviderProps {
  mode: string; // "system" | "light" | "dark" - user's preference
  resolved_theme: string; // "light" | "dark" - actual theme to apply
  root_id?: string;
  on_system_theme_change?: (theme: string) => void;
  on_theme_mode_change?: (mode: string) => void;
  children?: React.ReactNode;
}

/**
 * ThemeProvider manages the theme for a Trellis app.
 *
 * It updates the data-theme attribute on the trellis-root element based on
 * resolved_theme, and listens for OS theme changes when mode is "system".
 *
 * The trellis-root element should already exist in the DOM (created by the HTML
 * template or host page) with the .trellis-root class applied.
 */
export function ThemeProvider({
  mode,
  resolved_theme,
  root_id,
  on_system_theme_change,
  on_theme_mode_change,
  children,
}: ThemeProviderProps): React.ReactElement {
  const systemThemeCallbackRef = useRef(on_system_theme_change);
  systemThemeCallbackRef.current = on_system_theme_change;

  const themeModeCallbackRef = useRef(on_theme_mode_change);
  themeModeCallbackRef.current = on_theme_mode_change;

  // Get host-controlled theme mode from context (for browser extension use)
  const hostThemeMode = useHostThemeMode();

  // Ref to find our position in the DOM (needed for shadow DOM support)
  const containerRef = useRef<HTMLDivElement>(null);

  // Apply theme to the trellis-root element
  // When host explicitly controls theme (light/dark), use that directly to avoid
  // timing issues where Python's resolved_theme hasn't caught up yet.
  // For "system" mode or when host doesn't control, use resolved_theme from Python.
  useEffect(() => {
    if (!containerRef.current) return;

    // Use getRootNode() to support both regular DOM and shadow DOM
    // In regular DOM, this returns document. In shadow DOM, returns the shadow root.
    const rootNode = containerRef.current.getRootNode();
    const queryRoot = rootNode instanceof ShadowRoot ? rootNode : document;

    const rootEl = root_id
      ? queryRoot.getElementById(root_id)
      : queryRoot.querySelector(".trellis-root");

    if (rootEl && rootEl instanceof HTMLElement) {
      // If host explicitly sets light/dark, use that directly
      // This handles race conditions where HELLO hasn't been processed yet
      const themeToApply =
        hostThemeMode === "light" || hostThemeMode === "dark"
          ? hostThemeMode
          : resolved_theme;
      rootEl.dataset.theme = themeToApply;
    }
  }, [resolved_theme, root_id, hostThemeMode]);

  // Listen for OS theme changes when mode is "system"
  useEffect(() => {
    // Only listen when mode is "system" and callback is provided
    if (mode !== "system" || !systemThemeCallbackRef.current) return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleMediaChange = (e: MediaQueryListEvent) => {
      systemThemeCallbackRef.current?.(e.matches ? "dark" : "light");
    };
    mediaQuery.addEventListener("change", handleMediaChange);

    return () => {
      mediaQuery.removeEventListener("change", handleMediaChange);
    };
  }, [mode]);

  // Notify Python when host theme mode changes (for browser extension use)
  // Skip initial render (undefined -> value) and only fire on actual changes
  const prevHostThemeModeRef = useRef(hostThemeMode);
  useEffect(() => {
    // Only invoke callback if:
    // 1. The value actually changed (not just initial render)
    // 2. The new value is defined (host is controlling theme)
    // 3. The callback exists
    if (
      prevHostThemeModeRef.current !== hostThemeMode &&
      hostThemeMode !== undefined &&
      themeModeCallbackRef.current
    ) {
      themeModeCallbackRef.current(hostThemeMode);
    }
    prevHostThemeModeRef.current = hostThemeMode;
  }, [hostThemeMode]);

  // ThemeProvider renders a wrapper div to get a DOM reference for shadow DOM support
  return <div ref={containerRef}>{children}</div>;
}
