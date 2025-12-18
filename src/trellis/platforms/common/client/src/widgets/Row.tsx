import React from "react";
import { spacing } from "../theme";
import { Divider } from "./Divider";

interface RowProps {
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

export function Row({
  gap = spacing.md,
  padding = 0,
  align = "center",
  justify = "start",
  divider = false,
  className,
  style,
  children,
}: RowProps): React.ReactElement {
  // Intersperse dividers between children if enabled
  const content = divider
    ? React.Children.toArray(children).flatMap((child, i, arr) =>
        i < arr.length - 1
          ? [child, <Divider key={`divider-${i}`} orientation="vertical" margin={0} />]
          : [child]
      )
    : children;

  return (
    <div
      className={className}
      style={{
        display: "flex",
        flexDirection: "row",
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
