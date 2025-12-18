import React, { useRef, Children, isValidElement } from "react";
import { useMenu, useMenuItem, useSeparator } from "react-aria";
import { useTreeState, Item } from "react-stately";
import { colors, spacing, typography, radius, shadows, focusRing } from "../theme";
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

// Marker component for declarative menu items
export function MenuItem(_props: MenuItemProps): React.ReactElement | null {
  return null;
}

export function MenuDivider(_props: MenuDividerProps): React.ReactElement | null {
  return null;
}

function MenuItemComponent({
  item,
  state,
  itemData,
}: {
  item: { key: React.Key };
  state: ReturnType<typeof useTreeState>;
  itemData: { text: string; icon?: string; shortcut?: string; on_click?: () => void };
}) {
  const ref = useRef<HTMLLIElement>(null);
  const { menuItemProps, isFocused, isDisabled } = useMenuItem(
    {
      key: item.key,
      onAction: itemData.on_click,
    },
    state,
    ref
  );
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);

  return (
    <li
      {...menuItemProps}
      ref={ref}
      style={{
        display: "flex",
        alignItems: "center",
        gap: spacing.md,
        width: "100%",
        padding: `${spacing.sm}px ${spacing.md}px`,
        border: "none",
        background: isFocused ? colors.bg.surfaceHover : "transparent",
        cursor: isDisabled ? "not-allowed" : "pointer",
        fontSize: typography.fontSize.sm,
        color: isDisabled ? colors.text.muted : colors.text.primary,
        borderRadius: radius.sm,
        textAlign: "left",
        outline: "none",
        listStyle: "none",
        ...(isFocusVisible ? focusRing : {}),
      }}
      onFocus={(e) => {
        menuItemProps.onFocus?.(e);
        if (e.target.matches(":focus-visible")) {
          setIsFocusVisible(true);
        }
      }}
      onBlur={(e) => {
        menuItemProps.onBlur?.(e);
        setIsFocusVisible(false);
      }}
    >
      {itemData.icon && (
        <Icon
          name={itemData.icon}
          size={14}
          color={isDisabled ? colors.text.muted : colors.text.secondary}
        />
      )}
      <span style={{ flex: 1 }}>{itemData.text}</span>
      {itemData.shortcut && (
        <span
          style={{
            fontSize: typography.fontSize.xs,
            color: colors.text.muted,
          }}
        >
          {itemData.shortcut}
        </span>
      )}
    </li>
  );
}

function SeparatorComponent() {
  const { separatorProps } = useSeparator({ elementType: "li" });

  return (
    <li
      {...separatorProps}
      style={{
        height: 1,
        margin: `${spacing.xs}px 0`,
        backgroundColor: colors.border.default,
        listStyle: "none",
      }}
    />
  );
}

export function Menu({
  className,
  style,
  children,
}: MenuProps): React.ReactElement {
  const ref = useRef<HTMLUListElement>(null);

  // Extract menu items from children
  const items: { key: string; type: "item" | "divider"; data?: MenuItemProps }[] = [];
  let itemIndex = 0;

  Children.forEach(children, (child) => {
    if (isValidElement(child)) {
      if ((child.type as any) === MenuItem) {
        const props = child.props as MenuItemProps;
        items.push({
          key: `item-${itemIndex}`,
          type: "item",
          data: props,
        });
        itemIndex++;
      } else if ((child.type as any) === MenuDivider) {
        items.push({
          key: `divider-${itemIndex}`,
          type: "divider",
        });
        itemIndex++;
      }
    }
  });

  const state = useTreeState({
    selectionMode: "none",
    disabledKeys: items
      .filter((item) => item.type === "item" && item.data?.disabled)
      .map((item) => item.key),
    children: items
      .filter((item) => item.type === "item")
      .map((item) => <Item key={item.key}>{item.data?.text}</Item>),
  });

  const { menuProps } = useMenu({}, state, ref);

  return (
    <ul
      {...menuProps}
      ref={ref}
      className={className}
      style={{
        display: "flex",
        flexDirection: "column",
        padding: spacing.xs,
        backgroundColor: colors.bg.surface,
        border: `1px solid ${colors.border.default}`,
        borderRadius: radius.md,
        boxShadow: shadows.lg,
        minWidth: 180,
        margin: 0,
        listStyle: "none",
        ...style,
      }}
    >
      {items.map((item) => {
        if (item.type === "divider") {
          return <SeparatorComponent key={item.key} />;
        }
        const collectionItem = [...state.collection].find((i) => i.key === item.key);
        if (!collectionItem || !item.data) return null;
        return (
          <MenuItemComponent
            key={item.key}
            item={collectionItem}
            state={state}
            itemData={{
              text: item.data.text || "",
              icon: item.data.icon,
              shortcut: item.data.shortcut,
              on_click: item.data.on_click,
            }}
          />
        );
      })}
    </ul>
  );
}
