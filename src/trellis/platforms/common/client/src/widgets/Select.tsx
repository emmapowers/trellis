import React from "react";

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

const selectStyles: React.CSSProperties = {
  backgroundColor: "#0f172a",
  border: "1px solid #334155",
  borderRadius: "8px",
  padding: "10px 14px",
  color: "#f1f5f9",
  fontSize: "14px",
  outline: "none",
  width: "100%",
  boxSizing: "border-box",
  cursor: "pointer",
  transition: "border-color 150ms ease",
  appearance: "none",
  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2394a3b8' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
  backgroundRepeat: "no-repeat",
  backgroundPosition: "right 12px center",
  paddingRight: "36px",
};

const disabledStyles: React.CSSProperties = {
  opacity: 0.5,
  cursor: "not-allowed",
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
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (on_change) {
      on_change(e.target.value);
    }
  };

  const computedStyle: React.CSSProperties = {
    ...selectStyles,
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
