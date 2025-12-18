import React, { useRef, useEffect, useLayoutEffect } from "react";
import uPlot from "uplot";
import "uplot/dist/uPlot.min.css";
import { colors, typography } from "../theme";

interface SeriesConfig {
  label?: string;
  stroke?: string;
  fill?: string;
  width?: number;
}

interface TimeSeriesChartProps {
  data?: number[][];
  series?: SeriesConfig[];
  width?: number;
  height?: number;
  title?: string;
  show_legend?: boolean;
  show_tooltip?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

// Default color palette
const defaultColors = [
  colors.accent.primary,
  "#22c55e", // green
  "#f59e0b", // amber
  "#ef4444", // red
  "#8b5cf6", // violet
  "#06b6d4", // cyan
];

export function TimeSeriesChart({
  data,
  series = [],
  width,
  height = 200,
  title,
  show_legend = true,
  show_tooltip = true,
  className,
  style,
}: TimeSeriesChartProps): React.ReactElement {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<uPlot | null>(null);

  // Build uPlot series config
  const uplotSeries: uPlot.Series[] = [
    { label: "Time" }, // X axis
    ...series.map((s, i) => ({
      label: s.label || `Series ${i + 1}`,
      stroke: s.stroke || defaultColors[i % defaultColors.length],
      fill: s.fill,
      width: s.width || 2,
    })),
  ];

  // If no series config provided, create default for each data series
  if (series.length === 0 && data && data.length > 1) {
    for (let i = 1; i < data.length; i++) {
      uplotSeries.push({
        label: `Series ${i}`,
        stroke: defaultColors[(i - 1) % defaultColors.length],
        width: 2,
      });
    }
  }

  const opts: uPlot.Options = {
    width: width || 400,
    height,
    title: title || undefined,
    series: uplotSeries,
    scales: {
      x: { time: true },
    },
    axes: [
      {
        stroke: colors.text.secondary,
        grid: { stroke: colors.border.subtle },
        ticks: { stroke: colors.border.default },
        font: `${typography.fontSize.xs}px ${typography.fontFamily}`,
      },
      {
        stroke: colors.text.secondary,
        grid: { stroke: colors.border.subtle },
        ticks: { stroke: colors.border.default },
        font: `${typography.fontSize.xs}px ${typography.fontFamily}`,
      },
    ],
    legend: {
      show: show_legend,
    },
    cursor: {
      show: show_tooltip,
    },
  };

  // Create/update chart
  useLayoutEffect(() => {
    if (!containerRef.current || !data || data.length === 0) return;

    // Destroy existing chart
    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }

    // Determine width
    const containerWidth = width || containerRef.current.clientWidth || 400;
    opts.width = containerWidth;

    // Create new chart
    chartRef.current = new uPlot(opts, data, containerRef.current);

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [data, series, width, height, title, show_legend, show_tooltip]);

  // Handle resize
  useEffect(() => {
    if (!containerRef.current || width) return; // Skip if fixed width

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (chartRef.current) {
          chartRef.current.setSize({
            width: entry.contentRect.width,
            height,
          });
        }
      }
    });

    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, [height, width]);

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        width: width ? `${width}px` : "100%",
        minHeight: `${height}px`,
        ...style,
      }}
    />
  );
}
