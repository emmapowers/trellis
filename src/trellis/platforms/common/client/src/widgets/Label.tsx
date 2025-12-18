import React from "react";
import { colors, typography } from "../theme";

interface LabelProps {
  text?: string;
  font_size?: number;
  color?: string;
  bold?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function Label({
  text = "",
  font_size,
  color,
  bold = false,
  className,
  style,
}: LabelProps): React.ReactElement {
  return (
    <span
      className={className}
      style={{
        fontSize: font_size ? `${font_size}px` : `${typography.fontSize.md}px`,
        color: color ?? colors.text.primary,
        fontWeight: bold ? typography.fontWeight.semibold : undefined,
        ...style,
      }}
    >
      {text}
    </span>
  );
}
