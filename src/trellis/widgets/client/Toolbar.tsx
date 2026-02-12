import React, { useRef } from "react";
import { useToolbar } from "@react-aria/toolbar";
import { colors, spacing, radius } from "@trellis/trellis-core/theme";

interface ToolbarProps {
  variant?: "default" | "minimal";
  orientation?: "horizontal" | "vertical";
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

export function Toolbar({
  variant = "default",
  orientation = "horizontal",
  className,
  style,
  children,
}: ToolbarProps): React.ReactElement {
  const ref = useRef<HTMLDivElement>(null);
  const { toolbarProps } = useToolbar(
    {
      "aria-label": "Toolbar",
      orientation,
    },
    ref
  );

  const variantStyles: React.CSSProperties =
    variant === "default"
      ? {
          backgroundColor: colors.bg.surfaceRaised,
          border: `1px solid ${colors.border.default}`,
          borderRadius: radius.md,
          padding: spacing.xs,
        }
      : {
          padding: spacing.xs,
        };

  return (
    <div
      {...toolbarProps}
      ref={ref}
      className={className}
      style={{
        display: "flex",
        flexDirection: orientation === "vertical" ? "column" : "row",
        alignItems: orientation === "vertical" ? "stretch" : "center",
        gap: spacing.xs,
        ...variantStyles,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
