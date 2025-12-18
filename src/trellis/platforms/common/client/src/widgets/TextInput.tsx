import React from "react";
import { colors, radius, typography, spacing } from "../theme";

interface TextInputProps {
  value?: string;
  placeholder?: string;
  on_change?: (value: string) => void;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const inputStyles: React.CSSProperties = {
  backgroundColor: colors.bg.input,
  border: `1px solid ${colors.border.default}`,
  borderRadius: `${radius.sm}px`,
  padding: `${spacing.sm}px ${spacing.md + 2}px`,
  color: colors.text.primary,
  fontSize: `${typography.fontSize.md}px`,
  outline: "none",
  width: "100%",
  boxSizing: "border-box",
  transition: "border-color 150ms ease, box-shadow 150ms ease",
};

const disabledStyles: React.CSSProperties = {
  opacity: 0.5,
  cursor: "not-allowed",
  backgroundColor: colors.neutral[50],
};

export function TextInput({
  value = "",
  placeholder,
  on_change,
  disabled = false,
  className,
  style,
}: TextInputProps): React.ReactElement {
  const [isFocused, setIsFocused] = React.useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (on_change) {
      on_change(e.target.value);
    }
  };

  const computedStyle: React.CSSProperties = {
    ...inputStyles,
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
    <input
      type="text"
      value={value}
      placeholder={placeholder}
      onChange={handleChange}
      disabled={disabled}
      className={className}
      style={computedStyle}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
    />
  );
}
