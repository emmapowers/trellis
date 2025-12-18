import React from "react";
import { colors, spacing, typography, radius, shadows } from "../theme";
import { Icon } from "./Icon";

interface MenuProps {
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

interface MenuItemProps {
  text?: string;
  icon?: string;
  on_click?: () => void;
  disabled?: boolean;
  shortcut?: string;
  className?: string;
  style?: React.CSSProperties;
}

interface MenuDividerProps {
  className?: string;
  style?: React.CSSProperties;
}

export function Menu({
  className,
  style,
  children,
}: MenuProps): React.ReactElement {
  return (
    <div
      className={className}
      role="menu"
      style={{
        display: "flex",
        flexDirection: "column",
        padding: spacing.xs,
        backgroundColor: colors.bg.surface,
        border: `1px solid ${colors.border.default}`,
        borderRadius: radius.md,
        boxShadow: shadows.lg,
        minWidth: 180,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

export function MenuItem({
  text = "",
  icon,
  on_click,
  disabled = false,
  shortcut,
  className,
  style,
}: MenuItemProps): React.ReactElement {
  return (
    <button
      className={className}
      role="menuitem"
      onClick={disabled ? undefined : on_click}
      disabled={disabled}
      style={{
        display: "flex",
        alignItems: "center",
        gap: spacing.md,
        width: "100%",
        padding: `${spacing.sm}px ${spacing.md}px`,
        border: "none",
        background: "transparent",
        cursor: disabled ? "not-allowed" : "pointer",
        fontSize: typography.fontSize.sm,
        color: disabled ? colors.text.muted : colors.text.primary,
        borderRadius: radius.sm,
        textAlign: "left",
        transition: "background-color 0.1s ease",
        ...style,
      }}
      onMouseEnter={(e) => {
        if (!disabled) {
          e.currentTarget.style.backgroundColor = colors.bg.surfaceHover;
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = "transparent";
      }}
    >
      {icon && (
        <Icon
          name={icon}
          size={14}
          color={disabled ? colors.text.muted : colors.text.secondary}
        />
      )}
      <span style={{ flex: 1 }}>{text}</span>
      {shortcut && (
        <span
          style={{
            fontSize: typography.fontSize.xs,
            color: colors.text.muted,
          }}
        >
          {shortcut}
        </span>
      )}
    </button>
  );
}

export function MenuDivider({
  className,
  style,
}: MenuDividerProps): React.ReactElement {
  return (
    <div
      className={className}
      role="separator"
      style={{
        height: 1,
        margin: `${spacing.xs}px 0`,
        backgroundColor: colors.border.default,
        ...style,
      }}
    />
  );
}
