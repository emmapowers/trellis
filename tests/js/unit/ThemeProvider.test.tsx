import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import React from "react";
import { cleanup, render } from "../test-utils";
import { ThemeProvider } from "../../../src/trellis/app/client/ThemeProvider";

vi.mock("@trellis/trellis-core/TrellisContext", () => ({
  useHostThemeMode: () => undefined,
}));

describe("ThemeProvider", () => {
  let mockMatchMedia: ReturnType<typeof vi.fn>;
  let mediaQueryListeners: Map<string, ((e: MediaQueryListEvent) => void)[]>;
  let currentDarkMode: boolean;

  beforeEach(() => {
    mediaQueryListeners = new Map();
    currentDarkMode = false;

    mockMatchMedia = vi.fn((query: string) => {
      const listeners: ((e: MediaQueryListEvent) => void)[] = [];
      mediaQueryListeners.set(query, listeners);

      return {
        matches: query === "(prefers-color-scheme: dark)" ? currentDarkMode : false,
        media: query,
        addEventListener: (_event: string, handler: (e: MediaQueryListEvent) => void) => {
          listeners.push(handler);
        },
        removeEventListener: (_event: string, handler: (e: MediaQueryListEvent) => void) => {
          const index = listeners.indexOf(handler);
          if (index >= 0) {
            listeners.splice(index, 1);
          }
        },
      };
    });

    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: mockMatchMedia,
    });
  });

  afterEach(() => {
    cleanup();
    document.body.innerHTML = "";
    vi.clearAllMocks();
  });

  function simulateSystemThemeChange(dark: boolean): void {
    currentDarkMode = dark;
    const listeners = mediaQueryListeners.get("(prefers-color-scheme: dark)") || [];
    listeners.forEach((listener) => {
      listener({ matches: dark } as MediaQueryListEvent);
    });
  }

  it("notifies callback when the system theme changes", () => {
    const onSystemThemeChange = vi.fn();
    const root = document.createElement("div");
    root.className = "trellis-root";
    document.body.appendChild(root);

    render(
      <ThemeProvider
        theme_setting="system"
        theme="light"
        on_system_theme_change={onSystemThemeChange}
      >
        <div>content</div>
      </ThemeProvider>
    );

    simulateSystemThemeChange(true);

    expect(onSystemThemeChange).toHaveBeenCalledWith("dark");
  });

  it("applies the dark class to the trellis root for dark mode", () => {
    const root = document.createElement("div");
    root.className = "trellis-root";
    document.body.appendChild(root);

    render(
      <ThemeProvider theme_setting="dark" theme="dark">
        <div>content</div>
      </ThemeProvider>
    );

    expect(root.classList.contains("dark")).toBe(true);
  });

  it("keeps notifying system theme changes in explicit mode", () => {
    const onSystemThemeChange = vi.fn();
    const root = document.createElement("div");
    root.className = "trellis-root dark";
    document.body.appendChild(root);

    render(
      <ThemeProvider
        theme_setting="dark"
        theme="dark"
        on_system_theme_change={onSystemThemeChange}
      >
        <div>content</div>
      </ThemeProvider>
    );

    simulateSystemThemeChange(false);

    expect(onSystemThemeChange).toHaveBeenCalledWith("light");
  });

  it("removes the dark class from the trellis root for light mode", () => {
    const root = document.createElement("div");
    root.className = "trellis-root dark";
    document.body.appendChild(root);

    render(
      <ThemeProvider theme_setting="light" theme="light">
        <div>content</div>
      </ThemeProvider>
    );

    expect(root.classList.contains("dark")).toBe(false);
  });
});
