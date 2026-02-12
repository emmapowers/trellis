import React, { useRef } from "react";
import { useCheckbox } from "react-aria";
import { useToggleState } from "react-stately";
import { colors, typography, spacing, focusRing } from "@trellis/trellis-core/theme";
import { Mutable, unwrapMutable } from "@trellis/trellis-core/core/types";

interface CheckboxProps {
  checked?: boolean | Mutable<boolean>;
  label?: string;
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
  checked: checkedProp = false,
  label,
  disabled = false,
  className,
  style,
}: CheckboxProps): React.ReactElement {
  // Unwrap mutable binding if present
  const { value: checked, setValue } = unwrapMutable(checkedProp);

  const ref = useRef<HTMLInputElement>(null);
  const state = useToggleState({
    isSelected: checked,
    onChange: setValue,
  });
  const { inputProps, labelProps } = useCheckbox(
    {
      isDisabled: disabled,
      isSelected: checked,
      onChange: setValue,
      children: label,
    },
    state,
    ref
  );
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);

  const computedContainerStyle: React.CSSProperties = {
    ...containerStyles,
    ...(disabled ? disabledStyles : {}),
    ...style,
  };

  const computedCheckboxStyle: React.CSSProperties = {
    ...checkboxStyles,
    ...(isFocusVisible ? focusRing : {}),
  };

  return (
    <label {...labelProps} className={className} style={computedContainerStyle}>
      <input
        {...inputProps}
        ref={ref}
        style={computedCheckboxStyle}
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
      {label && <span style={labelStyles}>{label}</span>}
    </label>
  );
}
