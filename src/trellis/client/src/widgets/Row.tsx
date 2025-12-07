import React from "react";

interface RowProps {
  gap?: number;
  padding?: number;
  children?: React.ReactNode;
}

export function Row({
  gap = 8,
  padding = 0,
  children,
}: RowProps): React.ReactElement {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "row",
        gap: `${gap}px`,
        padding: `${padding}px`,
      }}
    >
      {children}
    </div>
  );
}
