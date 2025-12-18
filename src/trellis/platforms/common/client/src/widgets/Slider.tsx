import React, { useRef } from "react";
import { useSlider, useSliderThumb, useLocale } from "react-aria";
import { useSliderState } from "react-stately";
import { NumberFormatter } from "@internationalized/number";
import { colors, focusRing } from "../theme";

interface SliderProps {
  value?: number;
  min?: number;
  max?: number;
  step?: number;
  on_change?: (value: number) => void;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const trackStyles: React.CSSProperties = {
  position: "relative",
  width: "100%",
  height: "4px",
  borderRadius: "2px",
  background: colors.border.default,
};

const thumbStyles: React.CSSProperties = {
  width: "14px",
  height: "14px",
  borderRadius: "50%",
  background: colors.accent.primary,
  border: "2px solid white",
  boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
  cursor: "pointer",
};

const disabledStyles: React.CSSProperties = {
  opacity: 0.5,
  cursor: "not-allowed",
};

function Thumb({
  state,
  trackRef,
  index,
  isDisabled,
}: {
  state: ReturnType<typeof useSliderState>;
  trackRef: React.RefObject<HTMLDivElement | null>;
  index: number;
  isDisabled: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const { thumbProps, inputProps } = useSliderThumb(
    { index, trackRef, inputRef, isDisabled },
    state
  );
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);

  return (
    <div
      {...thumbProps}
      style={{
        ...thumbStyles,
        ...(isFocusVisible ? focusRing : {}),
        ...(isDisabled ? { cursor: "not-allowed" } : {}),
        position: "absolute",
        top: "50%",
        transform: "translate(-50%, -50%)",
        left: `${state.getThumbPercent(index) * 100}%`,
      }}
    >
      <input
        {...inputProps}
        ref={inputRef}
        style={{ opacity: 0, width: 0, height: 0, position: "absolute" }}
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
    </div>
  );
}

export function Slider({
  value = 50,
  min = 0,
  max = 100,
  step = 1,
  on_change,
  disabled = false,
  className,
  style,
}: SliderProps): React.ReactElement {
  const trackRef = useRef<HTMLDivElement>(null);
  const { locale } = useLocale();
  const state = useSliderState({
    value: [value],
    minValue: min,
    maxValue: max,
    step,
    onChange: (values) => on_change?.(values[0]),
    isDisabled: disabled,
    numberFormatter: new NumberFormatter(locale),
  });
  const { groupProps, trackProps } = useSlider(
    {
      value: [value],
      minValue: min,
      maxValue: max,
      step,
      onChange: (values) => on_change?.(values[0]),
      isDisabled: disabled,
    },
    state,
    trackRef
  );

  const percentage = state.getThumbPercent(0) * 100;

  return (
    <div
      {...groupProps}
      className={className}
      style={{
        ...(disabled ? disabledStyles : {}),
        ...style,
      }}
    >
      <div
        {...trackProps}
        ref={trackRef}
        style={{
          ...trackStyles,
          background: `linear-gradient(to right, ${colors.accent.primary} 0%, ${colors.accent.primary} ${percentage}%, ${colors.border.default} ${percentage}%, ${colors.border.default} 100%)`,
        }}
      >
        <Thumb state={state} trackRef={trackRef} index={0} isDisabled={disabled} />
      </div>
    </div>
  );
}
