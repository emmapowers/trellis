import React, { useState, useRef } from "react";
import { useButton } from "react-aria";
import { colors, spacing, typography, radius, focusRing } from "../theme";
import { Icon } from "./Icon";
import { Mutable, unwrapMutable, isMutable } from "../core/types";

interface CollapsibleProps {
  title?: string;
  expanded?: boolean | Mutable<boolean>;
  icon?: string;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

export function Collapsible({
  title = "",
  expanded: expandedProp = true,
  icon,
  className,
  style,
  children,
}: CollapsibleProps): React.ReactElement {
  // Unwrap mutable binding if present
  const { value: expandedValue, setValue } = unwrapMutable(expandedProp);

  const [internalExpanded, setInternalExpanded] = useState(expandedValue);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Use controlled mode if mutable is provided
  const isExpanded = setValue ? expandedValue : internalExpanded;

  const handleToggle = () => {
    const newState = !isExpanded;
    if (setValue) {
      setValue(newState);
    } else {
      setInternalExpanded(newState);
    }
  };

  const { buttonProps } = useButton(
    {
      onPress: handleToggle,
      "aria-expanded": isExpanded,
    },
    buttonRef
  );
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);

  const panelId = React.useId();

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
        {...buttonProps}
        ref={buttonRef}
        aria-controls={panelId}
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
          outline: "none",
          ...(isFocusVisible ? focusRing : {}),
        }}
        onFocus={(e) => {
          buttonProps.onFocus?.(e);
          if (e.target.matches(":focus-visible")) {
            setIsFocusVisible(true);
          }
        }}
        onBlur={(e) => {
          buttonProps.onBlur?.(e);
          setIsFocusVisible(false);
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
          id={panelId}
          role="region"
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
