import React from "react";
import { colors, radius, typography, spacing } from "../theme";

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  value?: string;
  options?: SelectOption[];
  on_change?: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

// Arrow icon using secondary text color for light theme
const arrowIcon = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`;

const selectStyles: React.CSSProperties = {
  backgroundColor: colors.bg.input,
  border: `1px solid ${colors.border.default}`,
  borderRadius: `${radius.sm}px`,
  padding: `${spacing.sm}px ${spacing.md + 2}px`,
  color: colors.text.primary,
  fontSize: `${typography.fontSize.md}px`,
  outline: "none",
  width: "100%",
  boxSizing: "border-box",
  cursor: "pointer",
  transition: "border-color 150ms ease, box-shadow 150ms ease",
  appearance: "none",
  backgroundImage: arrowIcon,
  backgroundRepeat: "no-repeat",
  backgroundPosition: "right 10px center",
  paddingRight: "32px",
};

const disabledStyles: React.CSSProperties = {
  opacity: 0.5,
  cursor: "not-allowed",
  backgroundColor: colors.neutral[50],
};

export function Select({
  value,
  options = [],
  on_change,
  placeholder,
  disabled = false,
  className,
  style,
}: SelectProps): React.ReactElement {
  const [isFocused, setIsFocused] = React.useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (on_change) {
      on_change(e.target.value);
    }
  };

  const computedStyle: React.CSSProperties = {
    ...selectStyles,
    ...(isFocused && !disabled
      ? {
          borderColor: colors.border.focus,
          boxShadow: `0 0 0 2px ${colors.accent.subtle}`,
        }
      : {}),
    ...(disabled ? disabledStyles : {}),
    ...style,
  };

  return (
    <select
      value={value ?? ""}
      onChange={handleChange}
      disabled={disabled}
      className={className}
      style={computedStyle}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}
