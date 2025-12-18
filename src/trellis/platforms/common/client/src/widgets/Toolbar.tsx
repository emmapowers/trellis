import React from "react";
import { colors, spacing, radius } from "../theme";

interface ToolbarProps {
  variant?: "default" | "minimal";
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

export function Toolbar({
  variant = "default",
  className,
  style,
  children,
}: ToolbarProps): React.ReactElement {
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
      className={className}
      role="toolbar"
      style={{
        display: "flex",
        alignItems: "center",
        gap: spacing.xs,
        ...variantStyles,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
