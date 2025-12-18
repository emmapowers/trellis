import React from "react";

interface TextInputProps {
  value?: string;
  placeholder?: string;
  on_change?: (value: string) => void;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const inputStyles: React.CSSProperties = {
  backgroundColor: "#0f172a",
  border: "1px solid #334155",
  borderRadius: "8px",
  padding: "10px 14px",
  color: "#f1f5f9",
  fontSize: "14px",
  outline: "none",
  width: "100%",
  boxSizing: "border-box",
  transition: "border-color 150ms ease",
};

const disabledStyles: React.CSSProperties = {
  opacity: 0.5,
  cursor: "not-allowed",
};

export function TextInput({
  value = "",
  placeholder,
  on_change,
  disabled = false,
  className,
  style,
}: TextInputProps): React.ReactElement {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (on_change) {
      on_change(e.target.value);
    }
  };

  const computedStyle: React.CSSProperties = {
    ...inputStyles,
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
    />
  );
}
