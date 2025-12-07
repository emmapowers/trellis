import React from "react";

interface LabelProps {
  text?: string;
  font_size?: number;
  color?: string;
}

export function Label({
  text = "",
  font_size,
  color,
}: LabelProps): React.ReactElement {
  return (
    <span
      style={{
        fontSize: font_size ? `${font_size}px` : undefined,
        color: color,
      }}
    >
      {text}
    </span>
  );
}
