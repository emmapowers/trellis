import React from "react";
import { colors, typography, spacing } from "../theme";

interface CheckboxProps {
  checked?: boolean;
  label?: string;
  on_change?: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const containerStyles: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: `${spacing.sm}px`,
  cursor: "pointer",
};

const checkboxStyles: React.CSSProperties = {
  width: "14px",
  height: "14px",
  accentColor: colors.accent.primary,
  cursor: "pointer",
};

const labelStyles: React.CSSProperties = {
  color: colors.text.primary,
  fontSize: `${typography.fontSize.md}px`,
};

const disabledStyles: React.CSSProperties = {
  opacity: 0.5,
  cursor: "not-allowed",
};

export function Checkbox({
  checked = false,
  label,
  on_change,
  disabled = false,
  className,
  style,
}: CheckboxProps): React.ReactElement {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (on_change) {
      on_change(e.target.checked);
    }
  };

  const computedContainerStyle: React.CSSProperties = {
    ...containerStyles,
    ...(disabled ? disabledStyles : {}),
    ...style,
  };

  return (
    <label className={className} style={computedContainerStyle}>
      <input
        type="checkbox"
        checked={checked}
        onChange={handleChange}
        disabled={disabled}
        style={checkboxStyles}
      />
      {label && <span style={labelStyles}>{label}</span>}
    </label>
  );
}
