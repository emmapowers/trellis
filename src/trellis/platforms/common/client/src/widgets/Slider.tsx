import React from "react";
import { colors } from "../theme";

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

const sliderStyles: React.CSSProperties = {
  width: "100%",
  height: "4px",
  borderRadius: "2px",
  appearance: "none",
  background: colors.border.default,
  outline: "none",
  cursor: "pointer",
};

const disabledStyles: React.CSSProperties = {
  opacity: 0.5,
  cursor: "not-allowed",
};

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
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (on_change) {
      on_change(parseFloat(e.target.value));
    }
  };

  // Calculate percentage for styling the filled portion
  const percentage = ((value - min) / (max - min)) * 100;

  const computedStyle: React.CSSProperties = {
    ...sliderStyles,
    ...(disabled ? disabledStyles : {}),
    background: `linear-gradient(to right, ${colors.accent.primary} 0%, ${colors.accent.primary} ${percentage}%, ${colors.border.default} ${percentage}%, ${colors.border.default} 100%)`,
    ...style,
  };

  return (
    <input
      type="range"
      value={value}
      min={min}
      max={max}
      step={step}
      onChange={handleChange}
      disabled={disabled}
      className={className}
      style={computedStyle}
    />
  );
}
