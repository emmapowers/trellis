import React from "react";
import { colors, radius, shadows, spacing } from "@trellis/trellis-core/theme";

interface CardProps {
  padding?: number;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

const cardStyles: React.CSSProperties = {
  backgroundColor: colors.bg.surface,
  borderRadius: `${radius.md}px`,
  border: `1px solid ${colors.border.default}`,
  boxShadow: shadows.md,
};

export function Card({
  padding = spacing.xl,
  className,
  style,
  children,
}: CardProps): React.ReactElement {
  return (
    <div
      className={className}
      style={{
        ...cardStyles,
        padding: `${padding}px`,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
