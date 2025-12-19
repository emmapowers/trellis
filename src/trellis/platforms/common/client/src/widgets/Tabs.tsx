import React, { useRef, Children, isValidElement } from "react";
import { useTabList, useTab, useTabPanel } from "react-aria";
import { useTabListState, Item } from "react-stately";
import { colors, spacing, typography, radius, focusRing } from "../theme";
import { Icon } from "./Icon";
import { Mutable, unwrapMutable } from "../core/types";

interface TabsProps {
  selected?: string | Mutable<string>;
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

// Tab is now just a marker component - Tabs extracts its props
export function Tab(_props: TabProps): React.ReactElement | null {
  return null;
}

function TabButton({
  item,
  state,
  variant,
  size,
  icon,
}: {
  item: { key: React.Key; rendered: React.ReactNode };
  state: ReturnType<typeof useTabListState>;
  variant: "line" | "enclosed" | "pills";
  size: "sm" | "md";
  icon?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const { tabProps } = useTab({ key: item.key }, state, ref);
  const isSelected = state.selectedKey === item.key;
  const isDisabled = state.disabledKeys.has(item.key);
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);

  const config = sizeConfig[size];

  const getVariantStyles = (): React.CSSProperties => {
    const base: React.CSSProperties = {
      display: "flex",
      alignItems: "center",
      gap: config.gap,
      padding: config.padding,
      fontSize: config.fontSize,
      fontWeight: typography.fontWeight.medium,
      cursor: isDisabled ? "not-allowed" : "pointer",
      opacity: isDisabled ? 0.5 : 1,
      transition: "all 0.15s ease",
      border: "none",
      outline: "none",
      background: "transparent",
    };

    switch (variant) {
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

  return (
    <div
      {...tabProps}
      ref={ref}
      style={{
        ...getVariantStyles(),
        ...(isFocusVisible ? focusRing : {}),
      }}
      onFocus={(e) => {
        tabProps.onFocus?.(e);
        if (e.target.matches(":focus-visible")) {
          setIsFocusVisible(true);
        }
      }}
      onBlur={(e) => {
        tabProps.onBlur?.(e);
        setIsFocusVisible(false);
      }}
    >
      {icon && <Icon name={icon} size={config.iconSize} color="currentColor" />}
      {item.rendered}
    </div>
  );
}

function TabPanel({
  state,
  contents,
}: {
  state: ReturnType<typeof useTabListState>;
  contents: Map<string, React.ReactNode>;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const { tabPanelProps } = useTabPanel({}, state, ref);

  const contentStyles: React.CSSProperties = {
    paddingTop: spacing.lg,
  };

  const selectedKey = state.selectedKey as string;

  if (!selectedKey || !contents.has(selectedKey)) {
    return null;
  }

  return (
    <div {...tabPanelProps} ref={ref} style={contentStyles}>
      {contents.get(selectedKey)}
    </div>
  );
}

export function Tabs({
  selected: selectedProp,
  variant = "line",
  size = "md",
  className,
  style,
  children,
}: TabsProps): React.ReactElement {
  // Unwrap mutable binding if present
  const { value: selected, setValue } = unwrapMutable(selectedProp);

  const ref = useRef<HTMLDivElement>(null);

  // Extract tab data from children
  const tabData: { id: string; label: string; icon?: string; disabled?: boolean; content?: React.ReactNode }[] = [];

  Children.forEach(children, (child) => {
    if (isValidElement(child) && (child.type as any) === Tab) {
      const tabProps = child.props as TabProps;
      tabData.push({
        id: tabProps.id,
        label: tabProps.label,
        icon: tabProps.icon,
        disabled: tabProps.disabled,
        content: tabProps.children,
      });
    }
  });

  const contents = new Map<string, React.ReactNode>();
  tabData.forEach((tab) => {
    if (tab.content) {
      contents.set(tab.id, tab.content);
    }
  });

  const state = useTabListState({
    selectedKey: selected,
    onSelectionChange: (key) => setValue?.(key as string),
    disabledKeys: tabData.filter((t) => t.disabled).map((t) => t.id),
    children: tabData.map((tab) => <Item key={tab.id}>{tab.label}</Item>),
  });

  const { tabListProps } = useTabList(
    {
      selectedKey: selected,
      onSelectionChange: (key) => setValue?.(key as string),
      disabledKeys: tabData.filter((t) => t.disabled).map((t) => t.id),
      children: tabData.map((tab) => <Item key={tab.id}>{tab.label}</Item>),
    },
    state,
    ref
  );

  const tabListStyles: React.CSSProperties = {
    display: "flex",
    gap: variant === "pills" ? spacing.xs : 0,
    borderBottom: variant === "line" ? `1px solid ${colors.border.default}` : undefined,
  };

  return (
    <div className={className} style={style}>
      <div {...tabListProps} ref={ref} style={tabListStyles}>
        {[...state.collection].map((item) => {
          const tabInfo = tabData.find((t) => t.id === item.key);
          return (
            <TabButton
              key={item.key}
              item={item}
              state={state}
              variant={variant}
              size={size}
              icon={tabInfo?.icon}
            />
          );
        })}
      </div>
      <TabPanel state={state} contents={contents} />
    </div>
  );
}
