import React from "react";

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
  height: "8px",
  borderRadius: "4px",
  appearance: "none",
  background: "#374151",
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
    background: `linear-gradient(to right, #6366f1 0%, #6366f1 ${percentage}%, #374151 ${percentage}%, #374151 100%)`,
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
