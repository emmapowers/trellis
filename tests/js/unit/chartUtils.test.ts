import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, act, cleanup } from "@testing-library/react";
import { getChartColors, withOpacity, useResolvedTheme } from "@trellis/trellis-core/chartUtils";

describe("getChartColors", () => {
  it("returns empty array for 0", () => {
    expect(getChartColors(0)).toEqual([]);
  });

  it("returns requested number of CSS variable refs", () => {
    const result = getChartColors(3);
    expect(result).toHaveLength(3);
    expect(result[0]).toBe("var(--trellis-chart-1)");
    expect(result[1]).toBe("var(--trellis-chart-2)");
    expect(result[2]).toBe("var(--trellis-chart-3)");
  });

  it("returns all 10 palette colors", () => {
    const result = getChartColors(10);
    expect(result).toHaveLength(10);
    for (let i = 0; i < 10; i++) {
      expect(result[i]).toBe(`var(--trellis-chart-${i + 1})`);
    }
  });

  it("wraps around when requesting more than 10", () => {
    const result = getChartColors(12);
    expect(result).toHaveLength(12);
    expect(result[10]).toBe("var(--trellis-chart-1)");
    expect(result[11]).toBe("var(--trellis-chart-2)");
  });
});

describe("withOpacity", () => {
  it("handles 6-digit hex", () => {
    expect(withOpacity("#ff0000", 0.5)).toBe("rgba(255, 0, 0, 0.5)");
  });

  it("handles 3-digit hex", () => {
    expect(withOpacity("#f00", 0.5)).toBe("rgba(255, 0, 0, 0.5)");
  });

  it("handles rgb()", () => {
    expect(withOpacity("rgb(255, 0, 0)", 0.5)).toBe("rgba(255, 0, 0, 0.5)");
  });

  it("handles rgba() by replacing alpha", () => {
    expect(withOpacity("rgba(255, 0, 0, 1)", 0.5)).toBe("rgba(255, 0, 0, 0.5)");
  });

  it("handles CSS variables via color-mix", () => {
    expect(withOpacity("var(--trellis-chart-1)", 0.3)).toBe(
      "color-mix(in srgb, var(--trellis-chart-1) 30%, transparent)"
    );
  });

  it("returns unsupported formats unchanged", () => {
    expect(withOpacity("hsl(0, 100%, 50%)", 0.5)).toBe("hsl(0, 100%, 50%)");
  });
});

describe("useResolvedTheme", () => {
  afterEach(() => {
    cleanup();
    // Clean up DOM nodes added during tests
    while (document.body.firstChild) {
      document.body.removeChild(document.body.firstChild);
    }
  });

  function renderWithTrellisRoot(seriesCount: number) {
    // Create a .trellis-root ancestor so the hook can find it
    const root = document.createElement("div");
    root.className = "trellis-root";
    root.setAttribute("data-theme", "light");
    // Set CSS custom properties so getComputedStyle can resolve them
    for (let i = 1; i <= 10; i++) {
      root.style.setProperty(`--trellis-chart-${i}`, `#color${i}`);
    }
    root.style.setProperty("--trellis-text-secondary", "#64748b");
    document.body.appendChild(root);

    const container = document.createElement("div");
    root.appendChild(container);

    const result = renderHook(() => useResolvedTheme(seriesCount), {
      container,
    });

    // Attach the ref callback to the container so the hook can find the root
    act(() => {
      result.result.current.ref(container);
    });

    return { result, root };
  }

  it("returns correct structure", () => {
    const { result } = renderWithTrellisRoot(3);
    const theme = result.result.current;
    expect(theme).toHaveProperty("ref");
    expect(theme).toHaveProperty("chartColors");
    expect(theme).toHaveProperty("resolveColor");
    expect(theme).toHaveProperty("themeVersion");
    expect(typeof theme.ref).toBe("function");
    expect(typeof theme.resolveColor).toBe("function");
    expect(typeof theme.themeVersion).toBe("number");
  });

  it("chartColors has correct length", () => {
    const { result } = renderWithTrellisRoot(5);
    expect(result.result.current.chartColors).toHaveLength(5);
  });

  it("themeVersion increments on data-theme attribute change", async () => {
    const { result, root } = renderWithTrellisRoot(2);
    const initialVersion = result.result.current.themeVersion;

    await act(async () => {
      root.setAttribute("data-theme", "dark");
      // MutationObserver fires asynchronously, give it a tick
      await new Promise((r) => setTimeout(r, 0));
    });

    expect(result.result.current.themeVersion).toBeGreaterThan(initialVersion);
  });
});
