import React from "react";

interface ColumnProps {
  gap?: number;
  padding?: number;
  children?: React.ReactNode;
}

export function Column({
  gap = 8,
  padding = 0,
  children,
}: ColumnProps): React.ReactElement {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: `${gap}px`,
        padding: `${padding}px`,
      }}
    >
      {children}
    </div>
  );
}
