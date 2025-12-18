import React from "react";
import { colors, spacing, typography } from "../theme";
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

export function Breadcrumb({
  items = [],
  separator = "/",
  on_click,
  className,
  style,
}: BreadcrumbProps): React.ReactElement {
  const isLast = (index: number) => index === items.length - 1;

  const handleClick = (index: number, e: React.MouseEvent) => {
    if (on_click) {
      e.preventDefault();
      on_click(index);
    }
  };

  return (
    <nav
      className={className}
      aria-label="Breadcrumb"
      style={{
        display: "flex",
        alignItems: "center",
        gap: spacing.sm,
        fontFamily: typography.fontFamily,
        fontSize: typography.fontSize.sm,
        ...style,
      }}
    >
      {items.map((item, index) => (
        <React.Fragment key={index}>
          {index > 0 && (
            <span
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
          {isLast(index) ? (
            <span
              style={{
                color: colors.text.primary,
                fontWeight: typography.fontWeight.medium,
              }}
              aria-current="page"
            >
              {item.label}
            </span>
          ) : (
            <a
              href={item.href || "#"}
              onClick={(e) => handleClick(index, e)}
              style={{
                color: colors.text.secondary,
                textDecoration: "none",
                cursor: "pointer",
                transition: "color 0.1s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = colors.accent.primary;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = colors.text.secondary;
              }}
            >
              {item.label}
            </a>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}
