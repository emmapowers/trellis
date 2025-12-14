import React from "react";

interface CardProps {
  padding?: number;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

const cardStyles: React.CSSProperties = {
  backgroundColor: "#1e293b",
  borderRadius: "12px",
  border: "1px solid #334155",
  boxShadow:
    "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)",
};

export function Card({
  padding = 24,
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
