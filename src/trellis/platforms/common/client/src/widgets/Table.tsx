import React, { useMemo } from "react";
import { colors, typography, spacing, radius } from "../theme";
import { Icon } from "./Icon";

interface TableColumn {
  name: string;
  label: string;
  icon?: string;
  width?: string;
  align?: "left" | "center" | "right";
}

interface TableInnerProps {
  columns?: TableColumn[];
  data?: Record<string, unknown>[];
  striped?: boolean;
  compact?: boolean;
  bordered?: boolean;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

const tableStyles: React.CSSProperties = {
  width: "100%",
  color: colors.text.primary,
};

const headerCellStyles: React.CSSProperties = {
  backgroundColor: colors.bg.surfaceRaised,
  color: colors.text.secondary,
  fontSize: `${typography.fontSize.xs}px`,
  fontWeight: typography.fontWeight.semibold,
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  borderBottom: `1px solid ${colors.border.default}`,
};

const cellStyles: React.CSSProperties = {
  borderBottom: `1px solid ${colors.border.subtle}`,
};

/**
 * Extract cell slot content from children.
 * Children are CellSlot components with a `slot` prop of format "rowKey:columnName".
 */
function useCellSlots(children: React.ReactNode): Map<string, React.ReactNode> {
  return useMemo(() => {
    const slots = new Map<string, React.ReactNode>();
    React.Children.forEach(children, (child) => {
      if (
        React.isValidElement(child) &&
        typeof child.props.slot === "string"
      ) {
        // The CellSlot's children are the actual content to render
        slots.set(child.props.slot, child.props.children);
      }
    });
    return slots;
  }, [children]);
}

/**
 * Escape colons in a string for use in slot keys.
 * This prevents collision when row keys contain colons.
 */
function escapeSlotKeyPart(s: string): string {
  return s.replace(/\\/g, "\\\\").replace(/:/g, "\\:");
}

/**
 * Get the row key for a data row.
 * Uses _key field if present, otherwise falls back to index.
 */
function getRowKey(row: Record<string, unknown>, index: number): string {
  if ("_key" in row && row._key != null) {
    return String(row._key);
  }
  return String(index);
}

// Note: This table is presentational-only (no selection/interaction).
// Semantic HTML table elements provide native accessibility.
// For interactive tables with selection, sorting, or keyboard navigation,
// use react-aria's useTable hooks with a proper collection.
export function TableInner({
  columns = [],
  data = [],
  striped = false,
  compact = true,
  bordered = false,
  className,
  style,
  children,
}: TableInnerProps): React.ReactElement {
  const cellSlots = useCellSlots(children);

  const rowHeight = compact ? 24 : 36;
  const cellPadding = compact
    ? `${spacing.xs}px ${spacing.sm}px`
    : `${spacing.sm}px ${spacing.lg}px`;
  const fontSize = compact
    ? `${typography.fontSize.sm}px`
    : `${typography.fontSize.md}px`;

  return (
    <table
      className={className}
      style={{
        ...tableStyles,
        fontSize,
        borderCollapse: bordered ? "separate" : "collapse",
        borderSpacing: 0,
        border: bordered ? `1px solid ${colors.border.default}` : undefined,
        borderRadius: bordered ? `${radius.md}px` : undefined,
        overflow: bordered ? "hidden" : undefined,
        ...style,
      }}
    >
      <thead>
        <tr>
          {columns.map((col, colIndex) => (
            <th
              key={col.name}
              scope="col"
              style={{
                ...headerCellStyles,
                padding: cellPadding,
                textAlign: col.align || "left",
                width: col.width,
                borderRight:
                  bordered && colIndex < columns.length - 1
                    ? `1px solid ${colors.border.subtle}`
                    : undefined,
              }}
            >
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: `${spacing.xs}px`,
                }}
              >
                {col.icon && (
                  <Icon name={col.icon} size={12} color={colors.text.secondary} />
                )}
                {col.label}
              </span>
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, rowIndex) => {
          const rowKey = getRowKey(row, rowIndex);
          return (
            <tr
              key={rowKey}
              style={{
                backgroundColor:
                  striped && rowIndex % 2 === 1
                    ? colors.bg.surfaceRaised
                    : undefined,
                height: `${rowHeight}px`,
              }}
            >
              {columns.map((col, colIndex) => {
                // Escape colons in row key to match Python-side slot key generation
                const slotKey = `${escapeSlotKeyPart(rowKey)}:${col.name}`;
                const slotContent = cellSlots.get(slotKey);
                const defaultContent = row[col.name];

                return (
                  <td
                    key={col.name}
                    style={{
                      ...cellStyles,
                      padding: cellPadding,
                      textAlign: col.align || "left",
                      borderRight:
                        bordered && colIndex < columns.length - 1
                          ? `1px solid ${colors.border.subtle}`
                          : undefined,
                    }}
                  >
                    {slotContent !== undefined
                      ? slotContent
                      : defaultContent != null
                        ? String(defaultContent)
                        : ""}
                  </td>
                );
              })}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

/**
 * CellSlot is a marker component for custom cell content.
 * It carries a slot identifier and renders its children.
 * The TableInner component extracts these and positions them in the right cells.
 */
interface CellSlotProps {
  slot: string;
  children?: React.ReactNode;
}

export function CellSlot({ children }: CellSlotProps): React.ReactElement {
  return <>{children}</>;
}
