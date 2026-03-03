import React from "react";
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { colors, typography } from "@trellis/trellis-core/theme";
import { getChartColors } from "./chartUtils";

interface BarChartProps {
  data?: Record<string, any>[];
  data_keys?: string[];
  x_key?: string;
  width?: number;
  height?: number;
  show_grid?: boolean;
  show_legend?: boolean;
  show_tooltip?: boolean;
  colors?: string[];
  stacked?: boolean;
  layout?: "horizontal" | "vertical";
  className?: string;
  style?: React.CSSProperties;
}

export function BarChart({
  data = [],
  data_keys = ["value"],
  x_key = "name",
  width,
  height = 200,
  show_grid = true,
  show_legend = true,
  show_tooltip = true,
  colors: colorsProp,
  stacked = false,
  layout = "horizontal",
  className,
  style,
}: BarChartProps): React.ReactElement {
  const chartColors = colorsProp?.length ? colorsProp : getChartColors(data_keys.length);
  const isVertical = layout === "vertical";

  const chartContent = (
    <RechartsBarChart
      data={data}
      layout={isVertical ? "vertical" : "horizontal"}
      margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
    >
      {show_grid && <CartesianGrid strokeDasharray="3 3" stroke={colors.border.subtle} />}
      {isVertical ? (
        <>
          <XAxis
            type="number"
            tick={{ fontSize: typography.fontSize.xs, fill: colors.text.secondary }}
            stroke={colors.border.default}
          />
          <YAxis
            dataKey={x_key}
            type="category"
            tick={{ fontSize: typography.fontSize.xs, fill: colors.text.secondary }}
            stroke={colors.border.default}
          />
        </>
      ) : (
        <>
          <XAxis
            dataKey={x_key}
            tick={{ fontSize: typography.fontSize.xs, fill: colors.text.secondary }}
            stroke={colors.border.default}
          />
          <YAxis
            tick={{ fontSize: typography.fontSize.xs, fill: colors.text.secondary }}
            stroke={colors.border.default}
          />
        </>
      )}
      {show_tooltip && (
        <Tooltip
          contentStyle={{
            backgroundColor: colors.bg.surface,
            border: `1px solid ${colors.border.default}`,
            borderRadius: 4,
            fontSize: typography.fontSize.sm,
            color: colors.text.primary,
          }}
        />
      )}
      {show_legend && (
        <Legend wrapperStyle={{ fontSize: typography.fontSize.sm, color: colors.text.secondary }} />
      )}
      {data_keys.map((key, i) => (
        <Bar
          key={key}
          dataKey={key}
          fill={chartColors[i % chartColors.length]}
          stackId={stacked ? "stack" : undefined}
          radius={[2, 2, 0, 0]}
        />
      ))}
    </RechartsBarChart>
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
