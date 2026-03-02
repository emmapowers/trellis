import React, { useRef, useEffect, useLayoutEffect, useCallback } from "react";
import uPlot from "uplot";
import "uplot/dist/uPlot.min.css";
import { colors, typography } from "@trellis/trellis-core/theme";
import { useResolvedTheme } from "@trellis/trellis-core/chartUtils";

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

  const seriesCount = series.length || (data && data.length > 1 ? data.length - 1 : 0);
  const { ref: themeRef, chartColors, resolveColor, themeVersion } = useResolvedTheme(seriesCount);

  // Merge themeRef + containerRef via callback ref
  const mergedRef = useCallback(
    (node: HTMLDivElement | null) => {
      (containerRef as React.MutableRefObject<HTMLDivElement | null>).current = node;
      themeRef(node);
    },
    [themeRef],
  );

  // Build uPlot series config with resolved colors
  const uplotSeries: uPlot.Series[] = [
    { label: "Time" }, // X axis
    ...series.map((s, i) => ({
      label: s.label || `Series ${i + 1}`,
      stroke: s.stroke || chartColors[i % chartColors.length],
      fill: s.fill,
      width: s.width || 2,
    })),
  ];

  // If no series config provided, create default for each data series
  if (series.length === 0 && data && data.length > 1) {
    for (let i = 1; i < data.length; i++) {
      uplotSeries.push({
        label: `Series ${i}`,
        stroke: chartColors[(i - 1) % chartColors.length],
        width: 2,
      });
    }
  }

  const axisStroke = resolveColor(colors.text.secondary);
  const gridStroke = resolveColor(colors.border.subtle);
  const tickStroke = resolveColor(colors.border.default);

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
        stroke: axisStroke,
        grid: { stroke: gridStroke },
        ticks: { stroke: tickStroke },
        font: `${typography.fontSize.xs}px ${typography.fontFamily}`,
      },
      {
        stroke: axisStroke,
        grid: { stroke: gridStroke },
        ticks: { stroke: tickStroke },
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

  // Create/update chart — re-creates on theme change via themeVersion
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
    chartRef.current = new uPlot(opts, data as uPlot.AlignedData, containerRef.current);

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [data, series, width, height, title, show_legend, show_tooltip, themeVersion]);

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
      ref={mergedRef}
      className={className}
      style={{
        width: width ? `${width}px` : "100%",
        minHeight: `${height}px`,
        ...style,
      }}
    />
  );
}
