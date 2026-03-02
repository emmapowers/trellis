import React from "react";
import {
  AreaChart as RechartsAreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { colors, typography } from "@trellis/trellis-core/theme";
import { getChartColors, withOpacity } from "@trellis/trellis-core/chartUtils";

interface AreaChartProps {
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
  curve_type?: "linear" | "monotone" | "step";
  className?: string;
  style?: React.CSSProperties;
}

export function AreaChart({
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
  curve_type = "monotone",
  className,
  style,
}: AreaChartProps): React.ReactElement {
  const chartColors = colorsProp || getChartColors(data_keys.length);

  const chartContent = (
    <RechartsAreaChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
      {show_grid && <CartesianGrid strokeDasharray="3 3" stroke={colors.border.subtle} />}
      <XAxis
        dataKey={x_key}
        tick={{ fontSize: typography.fontSize.xs, fill: colors.text.secondary }}
        stroke={colors.border.default}
      />
      <YAxis
        tick={{ fontSize: typography.fontSize.xs, fill: colors.text.secondary }}
        stroke={colors.border.default}
      />
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
      {data_keys.map((key, i) => {
        const color = chartColors[i % chartColors.length];
        return (
          <Area
            key={key}
            type={curve_type}
            dataKey={key}
            stroke={color}
            fill={withOpacity(color, 0.3)}
            strokeWidth={2}
            stackId={stacked ? "stack" : undefined}
          />
        );
      })}
    </RechartsAreaChart>
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
