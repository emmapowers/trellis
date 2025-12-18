import React, { useState } from "react";
import { colors, spacing, typography, radius } from "../theme";
import { Icon } from "./Icon";

interface CollapsibleProps {
  title?: string;
  expanded?: boolean;
  on_toggle?: (expanded: boolean) => void;
  icon?: string;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

export function Collapsible({
  title = "",
  expanded: expandedProp = true,
  on_toggle,
  icon,
  className,
  style,
  children,
}: CollapsibleProps): React.ReactElement {
  const [internalExpanded, setInternalExpanded] = useState(expandedProp);

  // Use controlled mode if on_toggle is provided
  const isExpanded = on_toggle ? expandedProp : internalExpanded;

  const handleToggle = () => {
    const newState = !isExpanded;
    if (on_toggle) {
      on_toggle(newState);
    } else {
      setInternalExpanded(newState);
    }
  };

  return (
    <div
      className={className}
      style={{
        border: `1px solid ${colors.border.default}`,
        borderRadius: radius.md,
        backgroundColor: colors.bg.surface,
        ...style,
      }}
    >
      {/* Header */}
      <button
        onClick={handleToggle}
        style={{
          display: "flex",
          alignItems: "center",
          gap: spacing.sm,
          width: "100%",
          padding: `${spacing.md}px ${spacing.lg}px`,
          border: "none",
          background: "transparent",
          cursor: "pointer",
          fontSize: typography.fontSize.sm,
          fontWeight: typography.fontWeight.medium,
          color: colors.text.primary,
          textAlign: "left",
        }}
      >
        <Icon
          name={isExpanded ? "chevron-down" : "chevron-right"}
          size={14}
          color={colors.text.secondary}
        />
        {icon && <Icon name={icon} size={16} color={colors.text.secondary} />}
        <span style={{ flex: 1 }}>{title}</span>
      </button>

      {/* Content */}
      {isExpanded && (
        <div
          style={{
            padding: `0 ${spacing.lg}px ${spacing.lg}px`,
            borderTop: `1px solid ${colors.border.subtle}`,
            paddingTop: spacing.lg,
          }}
        >
          {children}
        </div>
      )}
    </div>
  );
}
