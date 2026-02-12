import React from "react";
import { colors, typography, spacing } from "@trellis/trellis-core/theme";

type StatusType = "success" | "error" | "warning" | "pending" | "info";
type StatusSize = "sm" | "md";

interface StatusIndicatorProps {
  status?: StatusType;
  label?: string;
  show_icon?: boolean;
  size?: StatusSize;
  className?: string;
  style?: React.CSSProperties;
}

const statusConfig: Record<
  StatusType,
  { color: string; icon: string; bgColor: string }
> = {
  success: {
    color: colors.semantic.success,
    icon: "✓",
    bgColor: colors.semantic.successBg,
  },
  error: {
    color: colors.semantic.error,
    icon: "✗",
    bgColor: colors.semantic.errorBg,
  },
  warning: {
    color: colors.semantic.warning,
    icon: "⚠",
    bgColor: colors.semantic.warningBg,
  },
  pending: {
    color: colors.text.muted,
    icon: "○",
    bgColor: colors.neutral[100],
  },
  info: {
    color: colors.semantic.info,
    icon: "ℹ",
    bgColor: colors.semantic.infoBg,
  },
};

const sizeConfig: Record<StatusSize, { iconSize: number; fontSize: number; gap: number }> = {
  sm: {
    iconSize: 12,
    fontSize: typography.fontSize.xs,
    gap: spacing.xs,
  },
  md: {
    iconSize: 14,
    fontSize: typography.fontSize.sm,
    gap: spacing.sm,
  },
};

export function StatusIndicator({
  status = "pending",
  label,
  show_icon = true,
  size = "md",
  className,
  style,
}: StatusIndicatorProps): React.ReactElement {
  const config = statusConfig[status] || statusConfig.pending;
  const sizes = sizeConfig[size] || sizeConfig.md;

  return (
    <span
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: `${sizes.gap}px`,
        ...style,
      }}
    >
      {show_icon && (
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: `${sizes.iconSize}px`,
            height: `${sizes.iconSize}px`,
            fontSize: `${sizes.iconSize - 2}px`,
            color: config.color,
            fontWeight: typography.fontWeight.bold,
          }}
        >
          {config.icon}
        </span>
      )}
      {label && (
        <span
          style={{
            fontSize: `${sizes.fontSize}px`,
            color: config.color,
          }}
        >
          {label}
        </span>
      )}
    </span>
  );
}
