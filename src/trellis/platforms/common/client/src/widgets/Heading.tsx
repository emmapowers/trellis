import React from "react";

interface HeadingProps {
  text?: string;
  level?: 1 | 2 | 3 | 4 | 5 | 6;
  color?: string;
  className?: string;
  style?: React.CSSProperties;
}

export function Heading({
  text = "",
  level = 1,
  color,
  className,
  style,
}: HeadingProps): React.ReactElement {
  const Tag = `h${level}` as keyof JSX.IntrinsicElements;

  return (
    <Tag
      className={className}
      style={{
        color: color,
        margin: 0,
        ...style,
      }}
    >
      {text}
    </Tag>
  );
}
