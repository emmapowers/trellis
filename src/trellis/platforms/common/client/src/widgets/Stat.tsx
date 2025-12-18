import React from "react";
import { colors, spacing, typography, radius } from "../theme";
import { Icon } from "./Icon";

interface StatProps {
  label?: string;
  value?: string;
  delta?: string;
  delta_type?: "increase" | "decrease" | "neutral";
  icon?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
  style?: React.CSSProperties;
}

const sizeConfig = {
  sm: {
    padding: spacing.md,
    labelSize: typography.fontSize.xs,
    valueSize: typography.fontSize.lg,
    deltaSize: typography.fontSize.xs,
    iconSize: 14,
    gap: spacing.xs,
  },
  md: {
    padding: spacing.lg,
    labelSize: typography.fontSize.sm,
    valueSize: typography.fontSize.xxl,
    deltaSize: typography.fontSize.sm,
    iconSize: 18,
    gap: spacing.sm,
  },
  lg: {
    padding: spacing.xl,
    labelSize: typography.fontSize.md,
    valueSize: typography.fontSize.xxxl,
    deltaSize: typography.fontSize.md,
    iconSize: 22,
    gap: spacing.md,
  },
};

export function Stat({
  label = "",
  value = "",
  delta,
  delta_type,
  icon,
  size = "md",
  className,
  style,
}: StatProps): React.ReactElement {
  const config = sizeConfig[size];

  const deltaColor =
    delta_type === "increase"
      ? colors.semantic.success
      : delta_type === "decrease"
        ? colors.semantic.error
        : colors.text.secondary;

  const deltaArrow =
    delta_type === "increase"
      ? "trending-up"
      : delta_type === "decrease"
        ? "trending-down"
        : null;

  return (
    <div
      className={className}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: config.gap,
        padding: config.padding,
        backgroundColor: colors.bg.surface,
        border: `1px solid ${colors.border.default}`,
        borderRadius: radius.md,
        ...style,
      }}
    >
      {/* Label row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: spacing.sm,
        }}
      >
        {icon && (
          <Icon
            name={icon}
            size={config.iconSize}
            color={colors.text.secondary}
          />
        )}
        <span
          style={{
            fontSize: config.labelSize,
            fontWeight: typography.fontWeight.medium,
            color: colors.text.secondary,
          }}
        >
          {label}
        </span>
      </div>

      {/* Value row */}
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: spacing.md,
        }}
      >
        <span
          style={{
            fontSize: config.valueSize,
            fontWeight: typography.fontWeight.semibold,
            color: colors.text.primary,
            lineHeight: 1,
          }}
        >
          {value}
        </span>

        {/* Delta indicator */}
        {delta && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 2,
            }}
          >
            {deltaArrow && (
              <Icon name={deltaArrow} size={config.iconSize - 4} color={deltaColor} />
            )}
            <span
              style={{
                fontSize: config.deltaSize,
                fontWeight: typography.fontWeight.medium,
                color: deltaColor,
              }}
            >
              {delta}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
