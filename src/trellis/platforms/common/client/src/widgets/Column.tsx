import React from "react";

interface ColumnProps {
  gap?: number;
  padding?: number;
  align?: "start" | "center" | "end" | "stretch";
  justify?: "start" | "center" | "end" | "between" | "around";
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

export function Column({
  gap = 12,
  padding = 0,
  align = "stretch",
  justify = "start",
  className,
  style,
  children,
}: ColumnProps): React.ReactElement {
  return (
    <div
      className={className}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: `${gap}px`,
        padding: `${padding}px`,
        alignItems: alignMap[align],
        justifyContent: justifyMap[justify],
        ...style,
      }}
    >
      {children}
    </div>
  );
}
