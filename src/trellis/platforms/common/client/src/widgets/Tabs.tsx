import React, { useState, useCallback, Children, isValidElement, cloneElement } from "react";
import { colors, spacing, typography, radius } from "../theme";
import { Icon } from "./Icon";

interface TabsProps {
  selected?: string;
  on_change?: (id: string) => void;
  variant?: "line" | "enclosed" | "pills";
  size?: "sm" | "md";
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

interface TabProps {
  id: string;
  label: string;
  icon?: string;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
  // Injected by Tabs
  _selected?: boolean;
  _onSelect?: () => void;
  _variant?: "line" | "enclosed" | "pills";
  _size?: "sm" | "md";
}

const sizeConfig = {
  sm: {
    padding: `${spacing.xs}px ${spacing.md}px`,
    fontSize: typography.fontSize.xs,
    iconSize: 12,
    gap: spacing.xs,
  },
  md: {
    padding: `${spacing.sm}px ${spacing.lg}px`,
    fontSize: typography.fontSize.sm,
    iconSize: 14,
    gap: spacing.sm,
  },
};

export function Tab({
  id,
  label,
  icon,
  disabled = false,
  className,
  style,
  children,
  _selected,
  _onSelect,
  _variant = "line",
  _size = "md",
}: TabProps): React.ReactElement | null {
  const config = sizeConfig[_size];
  const isSelected = _selected;

  const getVariantStyles = (): React.CSSProperties => {
    const base: React.CSSProperties = {
      display: "flex",
      alignItems: "center",
      gap: config.gap,
      padding: config.padding,
      fontSize: config.fontSize,
      fontWeight: typography.fontWeight.medium,
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.5 : 1,
      transition: "all 0.15s ease",
      border: "none",
      outline: "none",
      background: "transparent",
    };

    switch (_variant) {
      case "line":
        return {
          ...base,
          color: isSelected ? colors.accent.primary : colors.text.secondary,
          borderBottom: `2px solid ${isSelected ? colors.accent.primary : "transparent"}`,
          marginBottom: -1,
        };
      case "enclosed":
        return {
          ...base,
          color: isSelected ? colors.text.primary : colors.text.secondary,
          backgroundColor: isSelected ? colors.bg.surface : "transparent",
          border: isSelected
            ? `1px solid ${colors.border.default}`
            : "1px solid transparent",
          borderBottom: isSelected ? `1px solid ${colors.bg.surface}` : "1px solid transparent",
          borderRadius: `${radius.sm}px ${radius.sm}px 0 0`,
          marginBottom: -1,
        };
      case "pills":
        return {
          ...base,
          color: isSelected ? colors.text.inverse : colors.text.secondary,
          backgroundColor: isSelected ? colors.accent.primary : "transparent",
          borderRadius: radius.full,
        };
      default:
        return base;
    }
  };

  // If used outside Tabs context, just render nothing
  if (!_onSelect) {
    return null;
  }

  return (
    <button
      className={className}
      style={{ ...getVariantStyles(), ...style }}
      onClick={!disabled ? _onSelect : undefined}
      disabled={disabled}
      role="tab"
      aria-selected={isSelected}
    >
      {icon && <Icon name={icon} size={config.iconSize} color="currentColor" />}
      {label}
    </button>
  );
}

export function Tabs({
  selected,
  on_change,
  variant = "line",
  size = "md",
  className,
  style,
  children,
}: TabsProps): React.ReactElement {
  // Find tabs and their content
  const tabs: { id: string; element: React.ReactElement<TabProps> }[] = [];
  const contents: Map<string, React.ReactNode> = new Map();

  Children.forEach(children, (child) => {
    if (isValidElement(child) && (child.type as any) === Tab) {
      const tabProps = child.props as TabProps;
      tabs.push({ id: tabProps.id, element: child });
      if (tabProps.children) {
        contents.set(tabProps.id, tabProps.children);
      }
    }
  });

  // Default to first tab if none selected
  const effectiveSelected = selected || (tabs.length > 0 ? tabs[0].id : undefined);

  const tabListStyles: React.CSSProperties = {
    display: "flex",
    gap: variant === "pills" ? spacing.xs : 0,
    borderBottom: variant === "line" ? `1px solid ${colors.border.default}` : undefined,
  };

  const contentStyles: React.CSSProperties = {
    paddingTop: spacing.lg,
  };

  return (
    <div className={className} style={style}>
      {/* Tab list */}
      <div role="tablist" style={tabListStyles}>
        {tabs.map(({ id, element }) =>
          cloneElement(element, {
            key: id,
            _selected: id === effectiveSelected,
            _onSelect: () => on_change?.(id),
            _variant: variant,
            _size: size,
          })
        )}
      </div>

      {/* Content */}
      {effectiveSelected && contents.has(effectiveSelected) && (
        <div role="tabpanel" style={contentStyles}>
          {contents.get(effectiveSelected)}
        </div>
      )}
    </div>
  );
}
