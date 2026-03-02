/**
 * Chart utilities for color palette management and color manipulation.
 */

import { useState, useCallback, useEffect, useMemo } from "react";

const PALETTE_SIZE = 10;

/**
 * Returns `count` CSS variable references cycling through the chart palette.
 */
export function getChartColors(count: number): string[] {
  const result: string[] = [];
  for (let i = 0; i < count; i++) {
    result.push(`var(--trellis-chart-${(i % PALETTE_SIZE) + 1})`);
  }
  return result;
}

/**
 * Apply opacity to a color string.
 *
 * Handles hex (3 and 6 digit), rgb(), rgba(), and CSS variables.
 * CSS variables use color-mix() since they can't be decomposed.
 * Unsupported formats are returned unchanged.
 */
export function withOpacity(color: string, opacity: number): string {
  // 6-digit hex
  if (color.match(/^#[0-9a-fA-F]{6}$/)) {
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  }

  // 3-digit hex
  if (color.match(/^#[0-9a-fA-F]{3}$/)) {
    const r = parseInt(color[1] + color[1], 16);
    const g = parseInt(color[2] + color[2], 16);
    const b = parseInt(color[3] + color[3], 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  }

  // rgb()
  const rgbMatch = color.match(/^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/);
  if (rgbMatch) {
    return `rgba(${rgbMatch[1]}, ${rgbMatch[2]}, ${rgbMatch[3]}, ${opacity})`;
  }

  // rgba() — replace existing alpha
  const rgbaMatch = color.match(/^rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*[\d.]+\s*\)$/);
  if (rgbaMatch) {
    return `rgba(${rgbaMatch[1]}, ${rgbaMatch[2]}, ${rgbaMatch[3]}, ${opacity})`;
  }

  // CSS variable — use color-mix
  if (color.startsWith("var(")) {
    const percent = Math.round(opacity * 100);
    return `color-mix(in srgb, ${color} ${percent}%, transparent)`;
  }

  // Unsupported format — return unchanged
  return color;
}

export interface ResolvedTheme {
  ref: React.RefCallback<HTMLElement>;
  chartColors: string[];
  resolveColor: (cssVar: string) => string;
  themeVersion: number;
}

/**
 * Hook that resolves CSS variable chart colors to computed values.
 *
 * Canvas APIs (like uPlot) can't use CSS variables directly, so this hook
 * resolves them via getComputedStyle. It watches for theme changes on the
 * .trellis-root element and re-resolves when the theme switches.
 */
export function useResolvedTheme(seriesCount: number): ResolvedTheme {
  const [themeVersion, setThemeVersion] = useState(0);
  const [rootEl, setRootEl] = useState<Element | null>(null);

  const ref = useCallback((node: HTMLElement | null) => {
    if (node) {
      setRootEl(node.closest(".trellis-root") || node);
    }
  }, []);

  // Watch for data-theme attribute changes on .trellis-root
  useEffect(() => {
    if (!rootEl) return;

    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === "attributes" && mutation.attributeName === "data-theme") {
          setThemeVersion((v) => v + 1);
        }
      }
    });

    observer.observe(rootEl, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, [rootEl]);

  const resolveColor = useCallback(
    (cssVar: string): string => {
      if (!rootEl) return cssVar;
      // Extract variable name from var(--name) syntax
      const match = cssVar.match(/^var\((--[\w-]+)\)$/);
      if (!match) return cssVar;
      return getComputedStyle(rootEl).getPropertyValue(match[1]).trim() || cssVar;
    },
    [rootEl, themeVersion],
  );

  const chartColors = useMemo(() => {
    const vars = getChartColors(seriesCount);
    return vars.map((v) => resolveColor(v));
  }, [seriesCount, resolveColor]);

  return { ref, chartColors, resolveColor, themeVersion };
}
