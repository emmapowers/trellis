import React from "react";
import { colors, typography, spacing, radius } from "../theme";

interface TableColumn {
  key: string;
  label: string;
  width?: string;
  align?: "left" | "center" | "right";
}

interface TableProps {
  columns?: TableColumn[];
  data?: Record<string, unknown>[];
  striped?: boolean;
  compact?: boolean;
  bordered?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const tableStyles: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: `${typography.fontSize.md}px`,
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

// Note: This table is presentational-only (no selection/interaction).
// Semantic HTML table elements provide native accessibility.
// For interactive tables with selection, sorting, or keyboard navigation,
// use react-aria's useTable hooks with a proper collection.
export function Table({
  columns = [],
  data = [],
  striped = false,
  compact = true,
  bordered = false,
  className,
  style,
}: TableProps): React.ReactElement {
  const rowHeight = compact ? 28 : 36;
  const cellPadding = compact
    ? `${spacing.xs}px ${spacing.md}px`
    : `${spacing.sm}px ${spacing.lg}px`;

  return (
    <table
      className={className}
      style={{
        ...tableStyles,
        border: bordered ? `1px solid ${colors.border.default}` : undefined,
        borderRadius: bordered ? `${radius.sm}px` : undefined,
        overflow: bordered ? "hidden" : undefined,
        ...style,
      }}
    >
      <thead>
        <tr>
          {columns.map((col) => (
            <th
              key={col.key}
              scope="col"
              style={{
                ...headerCellStyles,
                padding: cellPadding,
                textAlign: col.align || "left",
                width: col.width,
                borderRight:
                  bordered && col !== columns[columns.length - 1]
                    ? `1px solid ${colors.border.subtle}`
                    : undefined,
              }}
            >
              {col.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, rowIndex) => (
          <tr
            key={rowIndex}
            style={{
              backgroundColor:
                striped && rowIndex % 2 === 1
                  ? colors.bg.surfaceRaised
                  : undefined,
              height: `${rowHeight}px`,
            }}
          >
            {columns.map((col) => (
              <td
                key={col.key}
                style={{
                  ...cellStyles,
                  padding: cellPadding,
                  textAlign: col.align || "left",
                  borderRight:
                    bordered && col !== columns[columns.length - 1]
                      ? `1px solid ${colors.border.subtle}`
                      : undefined,
                }}
              >
                {row[col.key] as React.ReactNode}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
