import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import React from "react";
import { render } from "../../test-utils";
import { ThemeProvider } from "../../../../src/trellis/platforms/common/client/src/widgets/ThemeProvider";

// Mock useHostThemeMode to return undefined (no host control)
vi.mock("../../../../src/trellis/platforms/common/client/src/TrellisContext", () => ({
  useHostThemeMode: () => undefined,
}));

describe("ThemeProvider", () => {
  // Mock matchMedia
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
          const idx = listeners.indexOf(handler);
          if (idx >= 0) listeners.splice(idx, 1);
        },
      };
    });

    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: mockMatchMedia,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  function simulateSystemThemeChange(dark: boolean): void {
    currentDarkMode = dark;
    const listeners = mediaQueryListeners.get("(prefers-color-scheme: dark)") || [];
    listeners.forEach((listener) => {
      listener({ matches: dark } as MediaQueryListEvent);
    });
  }

  describe("system theme change notifications", () => {
    it("notifies callback when system theme changes while in system mode", () => {
      const onSystemThemeChange = vi.fn();

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

    it("notifies callback when system theme changes while in explicit light mode", () => {
      const onSystemThemeChange = vi.fn();

      render(
        <ThemeProvider
          theme_setting="light"
          theme="light"
          on_system_theme_change={onSystemThemeChange}
        >
          <div>content</div>
        </ThemeProvider>
      );

      simulateSystemThemeChange(true);

      // The callback should be called so Python knows the current system theme
      // for when the user switches back to system mode
      expect(onSystemThemeChange).toHaveBeenCalledWith("dark");
    });

    it("notifies callback when system theme changes while in explicit dark mode", () => {
      const onSystemThemeChange = vi.fn();

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
  });
});
