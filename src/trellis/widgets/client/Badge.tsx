import React from "react";
import { colors, typography, spacing, radius } from "@trellis/trellis-core/theme";

type BadgeVariant = "default" | "success" | "error" | "warning" | "info";
type BadgeSize = "sm" | "md";

interface BadgeProps {
  text?: string;
  variant?: BadgeVariant;
  size?: BadgeSize;
  className?: string;
  style?: React.CSSProperties;
}

const variantConfig: Record<
  BadgeVariant,
  { bgColor: string; textColor: string; borderColor: string }
> = {
  default: {
    bgColor: colors.neutral[100],
    textColor: colors.text.secondary,
    borderColor: colors.neutral[200],
  },
  success: {
    bgColor: colors.semantic.successBg,
    textColor: colors.semantic.success,
    borderColor: colors.semantic.successBorder,
  },
  error: {
    bgColor: colors.semantic.errorBg,
    textColor: colors.semantic.error,
    borderColor: colors.semantic.errorBorder,
  },
  warning: {
    bgColor: colors.semantic.warningBg,
    textColor: colors.semantic.warning,
    borderColor: colors.semantic.warningBorder,
  },
  info: {
    bgColor: colors.semantic.infoBg,
    textColor: colors.semantic.info,
    borderColor: colors.semantic.infoBorder,
  },
};

const sizeConfig: Record<BadgeSize, { fontSize: number; padding: string }> = {
  sm: {
    fontSize: typography.fontSize.xs,
    padding: `${spacing.xs - 2}px ${spacing.sm}px`,
  },
  md: {
    fontSize: typography.fontSize.sm,
    padding: `${spacing.xs}px ${spacing.md}px`,
  },
};

export function Badge({
  text = "",
  variant = "default",
  size = "sm",
  className,
  style,
}: BadgeProps): React.ReactElement {
  const variantStyle = variantConfig[variant] || variantConfig.default;
  const sizeStyle = sizeConfig[size] || sizeConfig.sm;

  return (
    <span
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        backgroundColor: variantStyle.bgColor,
        color: variantStyle.textColor,
        border: `1px solid ${variantStyle.borderColor}`,
        borderRadius: `${radius.sm}px`,
        fontSize: `${sizeStyle.fontSize}px`,
        fontWeight: typography.fontWeight.medium,
        padding: sizeStyle.padding,
        lineHeight: 1,
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {text}
    </span>
  );
}
