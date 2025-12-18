import React, { useRef } from "react";
import { useButton } from "react-aria";
import { colors, radius, typography, shadows, focusRing, focusRingOnColor } from "../theme";

type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps {
  text?: string;
  on_click?: () => void;
  disabled?: boolean;
  variant?: ButtonVariant;
  size?: ButtonSize;
  full_width?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const baseStyles: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  fontWeight: typography.fontWeight.medium,
  borderRadius: `${radius.sm}px`,
  border: "none",
  cursor: "pointer",
  transition: "all 150ms ease",
  fontFamily: "inherit",
  outline: "none",
};

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
  sm: {
    padding: "4px 8px",
    fontSize: `${typography.fontSize.sm}px`,
    minHeight: "26px",
  },
  md: {
    padding: "6px 12px",
    fontSize: `${typography.fontSize.md}px`,
    minHeight: "32px",
  },
  lg: {
    padding: "8px 16px",
    fontSize: `${typography.fontSize.lg}px`,
    minHeight: "38px",
  },
};

const variantStyles: Record<
  ButtonVariant,
  { normal: React.CSSProperties; hover: React.CSSProperties }
> = {
  primary: {
    normal: {
      backgroundColor: colors.accent.primary,
      color: colors.text.inverse,
      boxShadow: shadows.sm,
    },
    hover: {
      backgroundColor: colors.accent.primaryHover,
    },
  },
  secondary: {
    normal: {
      backgroundColor: colors.neutral[100],
      color: colors.text.primary,
      boxShadow: shadows.sm,
    },
    hover: {
      backgroundColor: colors.neutral[200],
    },
  },
  outline: {
    normal: {
      backgroundColor: "transparent",
      color: colors.text.primary,
      border: `1px solid ${colors.border.default}`,
    },
    hover: {
      backgroundColor: colors.neutral[50],
      borderColor: colors.border.strong,
    },
  },
  ghost: {
    normal: {
      backgroundColor: "transparent",
      color: colors.text.secondary,
    },
    hover: {
      backgroundColor: colors.neutral[100],
      color: colors.text.primary,
    },
  },
  danger: {
    normal: {
      backgroundColor: colors.semantic.error,
      color: colors.text.inverse,
      boxShadow: shadows.sm,
    },
    hover: {
      backgroundColor: "#b91c1c",
    },
  },
};

const disabledStyles: React.CSSProperties = {
  opacity: 0.5,
  cursor: "not-allowed",
};

export function Button({
  text = "",
  on_click,
  disabled = false,
  variant = "primary",
  size = "md",
  full_width = false,
  className,
  style,
}: ButtonProps): React.ReactElement {
  const ref = useRef<HTMLButtonElement>(null);
  const { buttonProps, isPressed } = useButton(
    {
      // Wrap on_click to avoid passing the PressEvent, which contains
      // DOM references that can't be serialized
      onPress: on_click ? () => on_click() : undefined,
      isDisabled: disabled,
    },
    ref
  );
  const [isHovered, setIsHovered] = React.useState(false);
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);

  const variantStyle = variantStyles[variant] || variantStyles.primary;
  const sizeStyle = sizeStyles[size] || sizeStyles.md;

  // Use double-ring focus indicator for colored backgrounds (primary, danger)
  const needsContrastFocusRing = variant === "primary" || variant === "danger";
  const activeFocusRing = needsContrastFocusRing ? focusRingOnColor : focusRing;

  const computedStyle: React.CSSProperties = {
    ...baseStyles,
    ...sizeStyle,
    ...variantStyle.normal,
    ...((isHovered || isPressed) && !disabled ? variantStyle.hover : {}),
    ...(disabled ? disabledStyles : {}),
    ...(full_width ? { width: "100%" } : {}),
    ...(isFocusVisible ? activeFocusRing : {}),
    ...style,
  };

  return (
    <button
      {...buttonProps}
      ref={ref}
      className={className}
      style={computedStyle}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={(e) => {
        buttonProps.onFocus?.(e);
        // Check if focus came from keyboard (not mouse)
        if (e.target.matches(":focus-visible")) {
          setIsFocusVisible(true);
        }
      }}
      onBlur={(e) => {
        buttonProps.onBlur?.(e);
        setIsFocusVisible(false);
      }}
    >
      {text}
    </button>
  );
}
