import React from "react";
import { colors, typography } from "../theme";

interface HeadingProps {
  text?: string;
  level?: 1 | 2 | 3 | 4 | 5 | 6;
  color?: string;
  className?: string;
  style?: React.CSSProperties;
}

// Font sizes for each heading level (compact scale)
const levelFontSizes: Record<number, number> = {
  1: typography.fontSize.xxxl, // 24px
  2: typography.fontSize.xxl, // 20px
  3: typography.fontSize.xl, // 16px
  4: typography.fontSize.lg, // 14px
  5: typography.fontSize.md, // 13px
  6: typography.fontSize.sm, // 12px
};

// Font weights for each heading level
const levelFontWeights: Record<number, number> = {
  1: typography.fontWeight.bold,
  2: typography.fontWeight.semibold,
  3: typography.fontWeight.semibold,
  4: typography.fontWeight.medium,
  5: typography.fontWeight.medium,
  6: typography.fontWeight.medium,
};

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
        color: color ?? colors.text.primary,
        margin: 0,
        fontSize: `${levelFontSizes[level]}px`,
        fontWeight: levelFontWeights[level],
        lineHeight: typography.lineHeight.tight,
        ...style,
      }}
    >
      {text}
    </Tag>
  );
}
