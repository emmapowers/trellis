import React from "react";

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
  fontWeight: 500,
  borderRadius: "8px",
  border: "none",
  cursor: "pointer",
  transition: "all 150ms ease",
  fontFamily: "inherit",
  outline: "none",
};

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
  sm: {
    padding: "6px 12px",
    fontSize: "13px",
    minHeight: "32px",
  },
  md: {
    padding: "10px 18px",
    fontSize: "14px",
    minHeight: "40px",
  },
  lg: {
    padding: "12px 24px",
    fontSize: "16px",
    minHeight: "48px",
  },
};

const variantStyles: Record<
  ButtonVariant,
  { normal: React.CSSProperties; hover: React.CSSProperties }
> = {
  primary: {
    normal: {
      backgroundColor: "#6366f1",
      color: "#ffffff",
      boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    },
    hover: {
      backgroundColor: "#4f46e5",
    },
  },
  secondary: {
    normal: {
      backgroundColor: "#374151",
      color: "#ffffff",
      boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    },
    hover: {
      backgroundColor: "#4b5563",
    },
  },
  outline: {
    normal: {
      backgroundColor: "transparent",
      color: "#d1d5db",
      border: "1px solid #4b5563",
    },
    hover: {
      backgroundColor: "rgba(75, 85, 99, 0.3)",
      borderColor: "#6b7280",
    },
  },
  ghost: {
    normal: {
      backgroundColor: "transparent",
      color: "#d1d5db",
    },
    hover: {
      backgroundColor: "rgba(75, 85, 99, 0.3)",
    },
  },
  danger: {
    normal: {
      backgroundColor: "#dc2626",
      color: "#ffffff",
      boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
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
  const [isHovered, setIsHovered] = React.useState(false);

  const variantStyle = variantStyles[variant] || variantStyles.primary;
  const sizeStyle = sizeStyles[size] || sizeStyles.md;

  const computedStyle: React.CSSProperties = {
    ...baseStyles,
    ...sizeStyle,
    ...variantStyle.normal,
    ...(isHovered && !disabled ? variantStyle.hover : {}),
    ...(disabled ? disabledStyles : {}),
    ...(full_width ? { width: "100%" } : {}),
    ...style,
  };

  return (
    <button
      className={className}
      onClick={on_click}
      disabled={disabled}
      style={computedStyle}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {text}
    </button>
  );
}
