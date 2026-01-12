/**
 * Legacy Breadcrumb widget.
 *
 * The Breadcrumb component is now implemented server-side in Python using
 * native HTML elements (Nav, Ol, Li, Span, A). This file is kept for the
 * legacy API which may still be referenced in some applications.
 */

import React, { useId } from "react";
import { useBreadcrumbs } from "react-aria";
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

/**
 * Legacy Breadcrumb component.
 *
 * Prefer using the Python Breadcrumb widget which generates server-side
 * HTML with router-integrated links.
 */
export function Breadcrumb({
  items = [],
  separator = "/",
  on_click,
  className,
  style,
}: BreadcrumbProps): React.ReactElement {
  const { navProps } = useBreadcrumbs({});
  const scopeId = `breadcrumb${useId()}`;

  const isLast = (index: number) => index === items.length - 1;

  return (
    <nav
      {...navProps}
      className={`${scopeId} ${className || ""}`.trim()}
      style={{
        display: "flex",
        alignItems: "center",
        fontFamily: typography.fontFamily,
        fontSize: typography.fontSize.sm,
        ...style,
      }}
    >
      {/* Scoped styles for anchor elements */}
      <style>
        {`
          .${scopeId} a {
            color: ${colors.text.secondary};
            text-decoration: none;
            cursor: pointer;
            transition: color 0.15s ease;
          }
          .${scopeId} a:hover {
            color: ${colors.accent.primary};
          }
        `}
      </style>
      <ol
        style={{
          display: "flex",
          alignItems: "center",
          gap: spacing.xs,
          listStyle: "none",
          margin: 0,
          padding: 0,
        }}
      >
        {items.map((item, index) => (
          <li
            key={index}
            style={{
              display: "flex",
              alignItems: "center",
              gap: spacing.xs,
            }}
          >
            {index > 0 && (
              <span
                aria-hidden="true"
                style={{
                  color: colors.text.muted,
                  userSelect: "none",
                  display: "flex",
                  alignItems: "center",
                }}
              >
                {separator === "/" ? (
                  <Icon name="chevron-right" size={14} color={colors.text.muted} />
                ) : (
                  separator
                )}
              </span>
            )}
            <BreadcrumbLink
              item={item}
              index={index}
              isLast={isLast(index)}
              on_click={on_click}
            />
          </li>
        ))}
      </ol>
    </nav>
  );
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
  const handleClick = (e: React.MouseEvent) => {
    if (on_click && !isLast) {
      e.preventDefault();
      on_click(index);
    }
  };

  if (isLast) {
    return (
      <span
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
    <a href={item.href || "#"} onClick={handleClick}>
      {item.label}
    </a>
  );
}
