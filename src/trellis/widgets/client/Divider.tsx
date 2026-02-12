import React from "react";
import { colors, spacing } from "@trellis/trellis-core/theme";

interface DividerProps {
  orientation?: "horizontal" | "vertical";
  margin?: number;
  color?: string;
  className?: string;
  style?: React.CSSProperties;
}

export function Divider({
  orientation = "horizontal",
  margin = spacing.lg,
  color = colors.border.default,
  className,
  style,
}: DividerProps): React.ReactElement {
  const isVertical = orientation === "vertical";

  const dividerStyle: React.CSSProperties = isVertical
    ? {
        border: "none",
        borderLeft: `1px solid ${color}`,
        margin: `0 ${margin}px`,
        height: "auto",
        alignSelf: "stretch",
        minHeight: "1em",
      }
    : {
        border: "none",
        borderTop: `1px solid ${color}`,
        margin: `${margin}px 0`,
        width: "100%",
      };

  return (
    <hr
      className={className}
      style={{
        ...dividerStyle,
        ...style,
      }}
    />
  );
}
