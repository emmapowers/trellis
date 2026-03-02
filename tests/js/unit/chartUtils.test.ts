import { describe, it, expect } from "vitest";
import { getChartColors, withOpacity } from "@trellis/trellis-core/chartUtils";

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
