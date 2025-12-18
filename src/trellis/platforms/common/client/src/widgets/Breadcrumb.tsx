import React, { useRef } from "react";
import { useBreadcrumbs, useBreadcrumbItem } from "react-aria";
import { colors, spacing, typography, focusRing } from "../theme";
import { Icon } from "./Icon";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items?: BreadcrumbItem[];
  separator?: string;
  on_click?: (index: number) => void;
  className?: string;
  style?: React.CSSProperties;
}

function BreadcrumbLink({
  item,
  index,
  isLast,
  on_click,
}: {
  item: BreadcrumbItem;
  index: number;
  isLast: boolean;
  on_click?: (index: number) => void;
}) {
  const ref = useRef<HTMLAnchorElement>(null);
  const { itemProps } = useBreadcrumbItem(
    {
      isCurrent: isLast,
      elementType: isLast ? "span" : "a",
    },
    ref
  );
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);
  const [isHovered, setIsHovered] = React.useState(false);

  const handleClick = (e: React.MouseEvent) => {
    if (on_click && !isLast) {
      e.preventDefault();
      on_click(index);
    }
  };

  if (isLast) {
    return (
      <span
        {...itemProps}
        ref={ref as React.RefObject<HTMLSpanElement>}
        style={{
          color: colors.text.primary,
          fontWeight: typography.fontWeight.medium,
        }}
      >
        {item.label}
      </span>
    );
  }

  return (
    <a
      {...itemProps}
      ref={ref}
      href={item.href || "#"}
      onClick={handleClick}
      style={{
        color: isHovered ? colors.accent.primary : colors.text.secondary,
        textDecoration: "none",
        cursor: "pointer",
        transition: "color 0.1s ease",
        outline: "none",
        ...(isFocusVisible ? focusRing : {}),
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={(e) => {
        itemProps.onFocus?.(e);
        if (e.target.matches(":focus-visible")) {
          setIsFocusVisible(true);
        }
      }}
      onBlur={(e) => {
        itemProps.onBlur?.(e);
        setIsFocusVisible(false);
      }}
    >
      {item.label}
    </a>
  );
}

export function Breadcrumb({
  items = [],
  separator = "/",
  on_click,
  className,
  style,
}: BreadcrumbProps): React.ReactElement {
  const { navProps } = useBreadcrumbs({});

  const isLast = (index: number) => index === items.length - 1;

  return (
    <nav
      {...navProps}
      className={className}
      style={{
        display: "flex",
        alignItems: "center",
        gap: spacing.sm,
        fontFamily: typography.fontFamily,
        fontSize: typography.fontSize.sm,
        ...style,
      }}
    >
      <ol style={{ display: "flex", alignItems: "center", gap: spacing.sm, listStyle: "none", margin: 0, padding: 0 }}>
        {items.map((item, index) => (
          <li key={index} style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
            {index > 0 && (
              <span
                aria-hidden="true"
                style={{
                  color: colors.text.muted,
                  userSelect: "none",
                }}
              >
                {separator === "/" ? (
                  <Icon name="chevron-right" size={14} color={colors.text.muted} />
                ) : (
                  separator
                )}
              </span>
            )}
            <BreadcrumbLink item={item} index={index} isLast={isLast(index)} on_click={on_click} />
          </li>
        ))}
      </ol>
    </nav>
  );
}
