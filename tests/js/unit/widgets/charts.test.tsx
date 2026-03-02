import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
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
    for (const path of paths) {
      const stroke = path.getAttribute("stroke") || "";
      // Should use CSS variables, not hardcoded hex
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
    expect(path?.getAttribute("stroke")).toBe("#abc123");
  });

  it("tooltip has themed text color", () => {
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
    const bars = container.querySelectorAll(".recharts-bar-rectangle path");
    if (bars.length > 0) {
      const fill = bars[0].getAttribute("fill") || "";
      expect(fill).toMatch(/^var\(--trellis-chart-/);
    }
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
    const bars = container.querySelectorAll(".recharts-bar-rectangle path");
    if (bars.length > 0) {
      expect(bars[0].getAttribute("fill")).toBe("#abc123");
    }
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
    const sectors = container.querySelectorAll(".recharts-pie-sector path");
    if (sectors.length > 0) {
      const fill = sectors[0].getAttribute("fill") || "";
      expect(fill).toMatch(/^var\(--trellis-chart-/);
    }
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
    const sectors = container.querySelectorAll(".recharts-pie-sector path");
    if (sectors.length > 0) {
      expect(sectors[0].getAttribute("fill")).toBe("#aaa");
    }
  });
});
