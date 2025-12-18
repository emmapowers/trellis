import React, { useRef } from "react";
import { useTextField } from "react-aria";
import { colors, radius, typography, spacing, focusRing } from "../theme";

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
  const ref = useRef<HTMLInputElement>(null);
  const { inputProps } = useTextField(
    {
      value,
      onChange: on_change,
      placeholder,
      isDisabled: disabled,
    },
    ref
  );
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);

  const computedStyle: React.CSSProperties = {
    ...inputStyles,
    ...(isFocusVisible && !disabled ? focusRing : {}),
    ...(disabled ? disabledStyles : {}),
    ...style,
  };

  return (
    <input
      {...inputProps}
      ref={ref}
      className={className}
      style={computedStyle}
      onFocus={(e) => {
        inputProps.onFocus?.(e);
        if (e.target.matches(":focus-visible")) {
          setIsFocusVisible(true);
        }
      }}
      onBlur={(e) => {
        inputProps.onBlur?.(e);
        setIsFocusVisible(false);
      }}
    />
  );
}
