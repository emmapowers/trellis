import React from "react";
import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { colors, typography } from "@trellis/trellis-core/theme";

interface PieChartProps {
  data?: Record<string, any>[];
  data_key?: string;
  name_key?: string;
  width?: number;
  height?: number;
  inner_radius?: number;
  show_legend?: boolean;
  show_tooltip?: boolean;
  show_labels?: boolean;
  colors?: string[];
  className?: string;
  style?: React.CSSProperties;
}

const defaultColors = [
  colors.accent.primary,
  "#22c55e",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#ec4899",
  "#14b8a6",
];

export function PieChart({
  data = [],
  data_key = "value",
  name_key = "name",
  width,
  height = 200,
  inner_radius = 0,
  show_legend = true,
  show_tooltip = true,
  show_labels = false,
  colors: colorsProp,
  className,
  style,
}: PieChartProps): React.ReactElement {
  const chartColors = colorsProp || defaultColors;

  // Calculate outer radius based on height (leave room for legend)
  const outerRadius = Math.min(height / 2 - 20, 80);

  const chartContent = (
    <RechartsPieChart>
      <Pie
        data={data}
        dataKey={data_key}
        nameKey={name_key}
        cx="50%"
        cy="50%"
        innerRadius={inner_radius}
        outerRadius={outerRadius}
        label={show_labels ? { fontSize: typography.fontSize.xs } : false}
        labelLine={show_labels}
      >
        {data.map((_, index) => (
          <Cell
            key={`cell-${index}`}
            fill={chartColors[index % chartColors.length]}
          />
        ))}
      </Pie>
      {show_tooltip && (
        <Tooltip
          contentStyle={{
            backgroundColor: colors.bg.surface,
            border: `1px solid ${colors.border.default}`,
            borderRadius: 4,
            fontSize: typography.fontSize.sm,
          }}
        />
      )}
      {show_legend && (
        <Legend
          wrapperStyle={{ fontSize: typography.fontSize.sm }}
          layout="horizontal"
          align="center"
          verticalAlign="bottom"
        />
      )}
    </RechartsPieChart>
  );

  if (width) {
    return (
      <div className={className} style={{ width, height, ...style }}>
        {React.cloneElement(chartContent, { width, height })}
      </div>
    );
  }

  return (
    <div className={className} style={{ width: "100%", minWidth: 0, height, ...style }}>
      <ResponsiveContainer width="100%" height={height}>
        {chartContent}
      </ResponsiveContainer>
    </div>
  );
}
