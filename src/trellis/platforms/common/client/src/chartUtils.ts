/**
 * Chart utilities for color palette management and color manipulation.
 */

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
