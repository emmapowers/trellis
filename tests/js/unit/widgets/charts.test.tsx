import React from "react";
import { describe, it, expect } from "vitest";
import { render } from "../../test-utils";
import { LineChart } from "../../../../src/trellis/widgets/client/LineChart";
import { BarChart } from "../../../../src/trellis/widgets/client/BarChart";
import { AreaChart } from "../../../../src/trellis/widgets/client/AreaChart";
import { PieChart } from "../../../../src/trellis/widgets/client/PieChart";

const sampleData = [
  { name: "Jan", a: 100, b: 80 },
  { name: "Feb", a: 120, b: 90 },
  { name: "Mar", a: 90, b: 110 },
];

const pieData = [
  { name: "A", value: 60 },
  { name: "B", value: 30 },
  { name: "C", value: 10 },
];

// Recharts needs a container with dimensions for ResponsiveContainer.
// In jsdom it gets 0x0 so we use fixed width to bypass ResponsiveContainer.
const CHART_WIDTH = 400;
const CHART_HEIGHT = 200;

describe("LineChart", () => {
  it("renders SVG", () => {
    const { container } = render(
      <LineChart data={sampleData} data_keys={["a", "b"]} width={CHART_WIDTH} height={CHART_HEIGHT} />
    );
    expect(container.querySelector("svg")).toBeTruthy();
  });

  it("uses theme palette colors by default", () => {
    const { container } = render(
      <LineChart data={sampleData} data_keys={["a", "b"]} width={CHART_WIDTH} height={CHART_HEIGHT} />
    );
    const paths = container.querySelectorAll(".recharts-line-curve");
    expect(paths.length).toBeGreaterThan(0);
    for (const path of paths) {
      const stroke = path.getAttribute("stroke") || "";
      expect(stroke).toMatch(/^var\(--trellis-chart-/);
    }
  });

  it("custom colors prop overrides defaults", () => {
    const { container } = render(
      <LineChart
        data={sampleData}
        data_keys={["a"]}
        colors={["#abc123"]}
        width={CHART_WIDTH}
        height={CHART_HEIGHT}
      />
    );
    const path = container.querySelector(".recharts-line-curve");
    expect(path).toBeTruthy();
    expect(path?.getAttribute("stroke")).toBe("#abc123");
  });

  it("renders tooltip wrapper", () => {
    const { container } = render(
      <LineChart data={sampleData} data_keys={["a"]} width={CHART_WIDTH} height={CHART_HEIGHT} />
    );
    const tooltip = container.querySelector(".recharts-tooltip-wrapper");
    expect(tooltip).toBeTruthy();
  });
});

describe("BarChart", () => {
  it("renders SVG", () => {
    const { container } = render(
      <BarChart data={sampleData} data_keys={["a", "b"]} width={CHART_WIDTH} height={CHART_HEIGHT} />
    );
    expect(container.querySelector("svg")).toBeTruthy();
  });

  it("uses theme palette colors by default", () => {
    const { container } = render(
      <BarChart data={sampleData} data_keys={["a", "b"]} width={CHART_WIDTH} height={CHART_HEIGHT} />
    );
    // Bar rectangles don't render in jsdom, so check legend icons which carry the fill color
    const icons = container.querySelectorAll(".recharts-legend-icon");
    expect(icons.length).toBeGreaterThan(0);
    expect(icons[0].getAttribute("fill")).toMatch(/^var\(--trellis-chart-/);
  });

  it("custom colors prop overrides defaults", () => {
    const { container } = render(
      <BarChart
        data={sampleData}
        data_keys={["a"]}
        colors={["#abc123"]}
        width={CHART_WIDTH}
        height={CHART_HEIGHT}
      />
    );
    const icons = container.querySelectorAll(".recharts-legend-icon");
    expect(icons.length).toBeGreaterThan(0);
    expect(icons[0].getAttribute("fill")).toBe("#abc123");
  });
});

describe("AreaChart", () => {
  it("renders SVG", () => {
    const { container } = render(
      <AreaChart data={sampleData} data_keys={["a", "b"]} width={CHART_WIDTH} height={CHART_HEIGHT} />
    );
    expect(container.querySelector("svg")).toBeTruthy();
  });

  it("uses theme palette colors by default", () => {
    const { container } = render(
      <AreaChart data={sampleData} data_keys={["a", "b"]} width={CHART_WIDTH} height={CHART_HEIGHT} />
    );
    const areas = container.querySelectorAll(".recharts-area-curve");
    expect(areas.length).toBeGreaterThan(0);
    for (const area of areas) {
      const stroke = area.getAttribute("stroke") || "";
      expect(stroke).toMatch(/^var\(--trellis-chart-/);
    }
  });

  it("custom colors prop overrides defaults", () => {
    const { container } = render(
      <AreaChart
        data={sampleData}
        data_keys={["a"]}
        colors={["#abc123"]}
        width={CHART_WIDTH}
        height={CHART_HEIGHT}
      />
    );
    const area = container.querySelector(".recharts-area-curve");
    expect(area).toBeTruthy();
    expect(area?.getAttribute("stroke")).toBe("#abc123");
  });
});

describe("PieChart", () => {
  it("renders SVG", () => {
    const { container } = render(
      <PieChart data={pieData} width={CHART_WIDTH} height={CHART_HEIGHT} />
    );
    expect(container.querySelector("svg")).toBeTruthy();
  });

  it("uses theme palette colors by default", () => {
    const { container } = render(
      <PieChart data={pieData} width={CHART_WIDTH} height={CHART_HEIGHT} />
    );
    // Pie sectors don't render in jsdom, so check legend icons which carry the fill color
    const icons = container.querySelectorAll(".recharts-legend-icon");
    expect(icons.length).toBeGreaterThan(0);
    expect(icons[0].getAttribute("fill")).toMatch(/^var\(--trellis-chart-/);
  });

  it("custom colors prop overrides defaults", () => {
    const { container } = render(
      <PieChart
        data={pieData}
        colors={["#aaa", "#bbb", "#ccc"]}
        width={CHART_WIDTH}
        height={CHART_HEIGHT}
      />
    );
    const icons = container.querySelectorAll(".recharts-legend-icon");
    expect(icons.length).toBeGreaterThan(0);
    expect(icons[0].getAttribute("fill")).toBe("#aaa");
  });
});
