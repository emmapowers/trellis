import React from "react";
import { colors, radius, typography, spacing, focusRing } from "@trellis/trellis-core/theme";
import { Mutable, unwrapMutable } from "@trellis/trellis-core/core/types";

interface MultilineInputProps {
  value?: string | Mutable<string>;
  placeholder?: string;
  rows?: number;
  disabled?: boolean;
  read_only?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const textareaStyles: React.CSSProperties = {
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
  resize: "vertical",
  minHeight: "72px",
  fontFamily: "inherit",
  lineHeight: 1.4,
};

const disabledStyles: React.CSSProperties = {
  opacity: 0.5,
  cursor: "not-allowed",
  backgroundColor: colors.neutral[50],
};

const readOnlyStyles: React.CSSProperties = {
  backgroundColor: colors.neutral[50],
};

export function MultilineInput({
  value: valueProp = "",
  placeholder,
  rows = 4,
  disabled = false,
  read_only = false,
  className,
  style,
}: MultilineInputProps): React.ReactElement {
  const { value, setValue } = unwrapMutable(valueProp);
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);

  const computedStyle: React.CSSProperties = {
    ...textareaStyles,
    ...(isFocusVisible && !disabled ? focusRing : {}),
    ...(disabled ? disabledStyles : {}),
    ...(read_only ? readOnlyStyles : {}),
    ...style,
  };

  return (
    <textarea
      className={className}
      style={computedStyle}
      value={value}
      placeholder={placeholder}
      rows={rows}
      disabled={disabled}
      readOnly={read_only}
      onChange={(event) => setValue?.(event.target.value)}
      onFocus={(event) => {
        if (event.target.matches(":focus-visible")) {
          setIsFocusVisible(true);
        }
      }}
      onBlur={() => {
        setIsFocusVisible(false);
      }}
    />
  );
}
