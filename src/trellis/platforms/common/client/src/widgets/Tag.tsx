import React from "react";
import { colors, spacing, typography, radius } from "../theme";
import { Icon } from "./Icon";

interface TagProps {
  text?: string;
  variant?: "default" | "primary" | "success" | "warning" | "error";
  removable?: boolean;
  on_remove?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

const variantStyles = {
  default: {
    backgroundColor: colors.neutral[100],
    color: colors.text.primary,
    borderColor: colors.border.default,
  },
  primary: {
    backgroundColor: colors.accent.subtle,
    color: colors.accent.primary,
    borderColor: colors.accent.primary,
  },
  success: {
    backgroundColor: colors.semantic.successBg,
    color: colors.semantic.success,
    borderColor: colors.semantic.successBorder,
  },
  warning: {
    backgroundColor: colors.semantic.warningBg,
    color: colors.semantic.warning,
    borderColor: colors.semantic.warningBorder,
  },
  error: {
    backgroundColor: colors.semantic.errorBg,
    color: colors.semantic.error,
    borderColor: colors.semantic.errorBorder,
  },
};

export function Tag({
  text = "",
  variant = "default",
  removable = false,
  on_remove,
  className,
  style,
}: TagProps): React.ReactElement {
  const variantStyle = variantStyles[variant];

  return (
    <span
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: spacing.xs,
        padding: `${spacing.xs}px ${spacing.sm}px`,
        fontSize: typography.fontSize.xs,
        fontWeight: typography.fontWeight.medium,
        lineHeight: 1,
        borderRadius: radius.sm,
        border: `1px solid ${variantStyle.borderColor}`,
        backgroundColor: variantStyle.backgroundColor,
        color: variantStyle.color,
        ...style,
      }}
    >
      {text}
      {removable && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            on_remove?.();
          }}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 0,
            margin: 0,
            marginLeft: 2,
            border: "none",
            background: "transparent",
            cursor: "pointer",
            color: "inherit",
            opacity: 0.6,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.opacity = "1";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.opacity = "0.6";
          }}
        >
          <Icon name="x" size={12} color="currentColor" />
        </button>
      )}
    </span>
  );
}
