import React from "react";
import { colors } from "@trellis/trellis-core/theme";

interface SparklineProps {
  data?: number[];
  width?: number;
  height?: number;
  color?: string;
  show_area?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function Sparkline({
  data = [],
  width = 80,
  height = 24,
  color,
  show_area = false,
  className,
  style,
}: SparklineProps): React.ReactElement {
  if (data.length === 0) {
    return <div className={className} style={{ width, height, ...style }} />;
  }

  const strokeColor = color || colors.accent.primary;
  const fillColor = show_area ? strokeColor : "none";

  // Calculate min/max for scaling
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  // Add padding
  const padding = 2;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  // Generate path points
  const points = data.map((value, index) => {
    const x = padding + (index / (data.length - 1)) * chartWidth;
    const y = padding + chartHeight - ((value - min) / range) * chartHeight;
    return { x, y };
  });

  // Create SVG path
  const linePath = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");

  // Create area path (line path + close to bottom)
  const areaPath = show_area
    ? `${linePath} L ${points[points.length - 1].x} ${height - padding} L ${padding} ${height - padding} Z`
    : "";

  return (
    <svg
      className={className}
      width={width}
      height={height}
      style={{ display: "block", ...style }}
    >
      {show_area && (
        <path
          d={areaPath}
          fill={fillColor}
          fillOpacity={0.2}
        />
      )}
      <path
        d={linePath}
        fill="none"
        stroke={strokeColor}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
