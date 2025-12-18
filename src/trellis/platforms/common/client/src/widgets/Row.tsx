import React from "react";

interface RowProps {
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

export function Row({
  gap = 12,
  padding = 0,
  align = "center",
  justify = "start",
  className,
  style,
  children,
}: RowProps): React.ReactElement {
  return (
    <div
      className={className}
      style={{
        display: "flex",
        flexDirection: "row",
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
