import React, { useRef } from "react";
import { useNumberField, useLocale, useButton } from "react-aria";
import { useNumberFieldState } from "react-stately";
import { colors, radius, typography, spacing, focusRing, inputHeight } from "../theme";

interface NumberInputProps {
  value?: number;
  min?: number;
  max?: number;
  step?: number;
  on_change?: (value: number) => void;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const wrapperStyles: React.CSSProperties = {
  display: "flex",
  alignItems: "stretch",
  width: "100%",
  height: `${inputHeight}px`,
};

const inputStyles: React.CSSProperties = {
  backgroundColor: colors.bg.input,
  border: `1px solid ${colors.border.default}`,
  borderRadius: `${radius.sm}px 0 0 ${radius.sm}px`,
  borderRight: "none",
  padding: `${spacing.sm}px ${spacing.md + 2}px`,
  color: colors.text.primary,
  fontSize: `${typography.fontSize.md}px`,
  outline: "none",
  flex: 1,
  minWidth: 0,
  height: `${inputHeight}px`,
  boxSizing: "border-box",
  transition: "border-color 150ms ease, box-shadow 150ms ease",
};

const buttonGroupStyles: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
};

const stepButtonStyles: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  width: "24px",
  backgroundColor: colors.bg.input,
  border: `1px solid ${colors.border.default}`,
  color: colors.text.secondary,
  cursor: "pointer",
  padding: 0,
  outline: "none",
  transition: "background-color 150ms ease",
  boxSizing: "border-box",
};

const disabledStyles: React.CSSProperties = {
  opacity: 0.5,
  cursor: "not-allowed",
  backgroundColor: colors.neutral[50],
};

function StepButton({
  children,
  isDisabled,
  style,
  ...props
}: {
  children: React.ReactNode;
  isDisabled: boolean;
  style?: React.CSSProperties;
} & React.HTMLAttributes<HTMLButtonElement>) {
  const ref = useRef<HTMLButtonElement>(null);
  const { buttonProps } = useButton({ ...props, isDisabled } as never, ref);
  const [isHovered, setIsHovered] = React.useState(false);

  return (
    <button
      {...buttonProps}
      ref={ref}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        ...stepButtonStyles,
        ...(isHovered && !isDisabled ? { backgroundColor: colors.bg.surfaceHover } : {}),
        ...(isDisabled ? { cursor: "not-allowed", opacity: 0.5 } : {}),
        ...style,
      }}
    >
      {children}
    </button>
  );
}

export function NumberInput({
  value,
  min,
  max,
  step,
  on_change,
  disabled = false,
  className,
  style,
}: NumberInputProps): React.ReactElement {
  const inputRef = useRef<HTMLInputElement>(null);
  const { locale } = useLocale();
  const state = useNumberFieldState({
    value,
    minValue: min,
    maxValue: max,
    step,
    onChange: on_change,
    isDisabled: disabled,
    locale,
  });
  const { inputProps, incrementButtonProps, decrementButtonProps } = useNumberField(
    {
      value,
      minValue: min,
      maxValue: max,
      step,
      onChange: on_change,
      isDisabled: disabled,
    },
    state,
    inputRef
  );
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);

  const computedInputStyle: React.CSSProperties = {
    ...inputStyles,
    ...(isFocusVisible && !disabled ? focusRing : {}),
    ...(disabled ? disabledStyles : {}),
  };

  return (
    <div className={className} style={{ ...wrapperStyles, ...style }}>
      <input
        {...inputProps}
        ref={inputRef}
        style={computedInputStyle}
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
      <div style={buttonGroupStyles}>
        <StepButton {...incrementButtonProps} isDisabled={disabled} style={{ borderTopRightRadius: `${radius.sm}px`, height: `${inputHeight / 2}px` }}>
          <svg width="10" height="6" viewBox="0 0 10 6">
            <path fill="currentColor" d="M5 0l5 6H0z" />
          </svg>
        </StepButton>
        <StepButton {...decrementButtonProps} isDisabled={disabled} style={{ borderBottomRightRadius: `${radius.sm}px`, borderTop: "none", height: `${inputHeight / 2}px` }}>
          <svg width="10" height="6" viewBox="0 0 10 6">
            <path fill="currentColor" d="M5 6L0 0h10z" />
          </svg>
        </StepButton>
      </div>
    </div>
  );
}
