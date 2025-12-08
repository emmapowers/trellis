import React from "react";

interface LabelProps {
  text?: string;
  font_size?: number;
  color?: string;
  className?: string;
  style?: React.CSSProperties;
}

export function Label({
  text = "",
  font_size,
  color,
  className,
  style,
}: LabelProps): React.ReactElement {
  return (
    <span
      className={className}
      style={{
        fontSize: font_size ? `${font_size}px` : undefined,
        color: color,
        ...style,
      }}
    >
      {text}
    </span>
  );
}
