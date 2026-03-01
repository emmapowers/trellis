import React, { useRef, useState, useLayoutEffect } from "react";
import { useTextField } from "react-aria";
import { colors, radius, typography, spacing, focusRing } from "@trellis/trellis-core/theme";
import { Mutable, unwrapMutable } from "@trellis/trellis-core/core/types";

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
  const { value: serverValue, setValue: sendToServer } = unwrapMutable(valueProp);
  const [localValue, setLocalValue] = useState(serverValue);

  const ref = useRef<HTMLInputElement>(null);
  const cursorRef = useRef<number | null>(null);
  const prevServerRef = useRef(serverValue);

  // Accept new server values (e.g. transforms like .upper())
  if (serverValue !== prevServerRef.current) {
    prevServerRef.current = serverValue;
    setLocalValue(serverValue);
  }

  const { inputProps } = useTextField(
    {
      value: localValue,
      onChange: (v) => {
        setLocalValue(v);
        sendToServer?.(v);
      },
      placeholder,
      isDisabled: disabled,
    },
    ref
  );
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);

  // Restore cursor position after React commits a value change while focused.
  useLayoutEffect(() => {
    if (ref.current && ref.current === document.activeElement && cursorRef.current !== null) {
      const pos = Math.min(cursorRef.current, localValue.length);
      ref.current.setSelectionRange(pos, pos);
    }
  }, [localValue]);

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
      onChange={(e) => {
        cursorRef.current = e.target.selectionStart;
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
