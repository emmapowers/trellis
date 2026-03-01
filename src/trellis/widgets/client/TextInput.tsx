import React from "react";
import { useTextField } from "react-aria";
import { colors, radius, typography, spacing, focusRing } from "@trellis/trellis-core/theme";
import { Mutable } from "@trellis/trellis-core/core/types";
import { useTextValue } from "@trellis/trellis-core/core/useTextValue";

interface TextInputProps {
  value?: string | Mutable<string>;
  placeholder?: string;
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
  value: valueProp = "",
  placeholder,
  disabled = false,
  className,
  style,
}: TextInputProps): React.ReactElement {
  const tv = useTextValue<HTMLInputElement>(valueProp);

  const { inputProps } = useTextField(
    {
      value: tv.value,
      onChange: tv.setValue,
      placeholder,
      isDisabled: disabled,
    },
    tv.ref
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
      ref={tv.ref}
      className={className}
      style={computedStyle}
      onChange={(e) => {
        tv.saveCursor(e);
        inputProps.onChange?.(e);
      }}
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
