import React from "react";
import { colors, spacing, typography, radius } from "../theme";
import { Icon } from "./Icon";

interface CalloutProps {
  title?: string;
  intent?: "info" | "success" | "warning" | "error";
  icon?: string;
  dismissible?: boolean;
  on_dismiss?: () => void;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

const intentConfig = {
  info: {
    bg: colors.semantic.infoBg,
    border: colors.semantic.infoBorder,
    color: colors.semantic.info,
    icon: "info",
  },
  success: {
    bg: colors.semantic.successBg,
    border: colors.semantic.successBorder,
    color: colors.semantic.success,
    icon: "check-circle",
  },
  warning: {
    bg: colors.semantic.warningBg,
    border: colors.semantic.warningBorder,
    color: colors.semantic.warning,
    icon: "alert-triangle",
  },
  error: {
    bg: colors.semantic.errorBg,
    border: colors.semantic.errorBorder,
    color: colors.semantic.error,
    icon: "alert-circle",
  },
};

export function Callout({
  title,
  intent = "info",
  icon: iconProp,
  dismissible = false,
  on_dismiss,
  className,
  style,
  children,
}: CalloutProps): React.ReactElement {
  const config = intentConfig[intent];
  const iconName = iconProp || config.icon;

  return (
    <div
      className={className}
      role="alert"
      style={{
        display: "flex",
        gap: spacing.md,
        padding: spacing.lg,
        backgroundColor: config.bg,
        border: `1px solid ${config.border}`,
        borderRadius: radius.md,
        ...style,
      }}
    >
      {/* Icon */}
      <Icon name={iconName} size={18} color={config.color} />

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {title && (
          <div
            style={{
              fontSize: typography.fontSize.sm,
              fontWeight: typography.fontWeight.semibold,
              color: config.color,
              marginBottom: children ? spacing.xs : 0,
            }}
          >
            {title}
          </div>
        )}
        {children && (
          <div
            style={{
              fontSize: typography.fontSize.sm,
              color: colors.text.primary,
              lineHeight: typography.lineHeight.normal,
            }}
          >
            {children}
          </div>
        )}
      </div>

      {/* Dismiss button */}
      {dismissible && (
        <button
          onClick={on_dismiss}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: spacing.xs,
            margin: -spacing.xs,
            border: "none",
            background: "transparent",
            cursor: "pointer",
            borderRadius: radius.sm,
            color: colors.text.secondary,
            transition: "background-color 0.1s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = colors.bg.surfaceHover;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "transparent";
          }}
        >
          <Icon name="x" size={16} color="currentColor" />
        </button>
      )}
    </div>
  );
}
