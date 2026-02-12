import React from "react";
import { spacing } from "@trellis/trellis-core/theme";
import { Divider } from "./Divider";

interface ColumnProps {
  gap?: number;
  padding?: number;
  align?: "start" | "center" | "end" | "stretch";
  justify?: "start" | "center" | "end" | "between" | "around";
  divider?: boolean;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

const justifyMap = {
  start: "flex-start",
  center: "center",
  end: "flex-end",
  between: "space-between",
  around: "space-around",
};

const alignMap = {
  start: "flex-start",
  center: "center",
  end: "flex-end",
  stretch: "stretch",
};

export function Column({
  gap = spacing.md,
  padding = 0,
  align = "stretch",
  justify = "start",
  divider = false,
  className,
  style,
  children,
}: ColumnProps): React.ReactElement {
  // Intersperse dividers between children if enabled
  const content = divider
    ? React.Children.toArray(children).flatMap((child, i, arr) =>
        i < arr.length - 1
          ? [child, <Divider key={`divider-${i}`} orientation="horizontal" margin={0} />]
          : [child]
      )
    : children;

  return (
    <div
      className={className}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: `${gap}px`,
        padding: `${padding}px`,
        alignItems: alignMap[align],
        justifyContent: justifyMap[justify],
        ...style,
      }}
    >
      {content}
    </div>
  );
}
