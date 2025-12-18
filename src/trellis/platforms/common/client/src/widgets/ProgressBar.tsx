import React from "react";
import { colors, radius } from "../theme";

interface ProgressBarProps {
  value?: number;
  min?: number;
  max?: number;
  loading?: boolean;
  disabled?: boolean;
  color?: string;
  height?: number;
  className?: string;
  style?: React.CSSProperties;
}

const trackStyles: React.CSSProperties = {
  backgroundColor: colors.border.default,
  borderRadius: `${radius.sm}px`,
  overflow: "hidden",
};

const fillStyles: React.CSSProperties = {
  height: "100%",
  borderRadius: `${radius.sm}px`,
  transition: "width 200ms ease",
};

const loadingKeyframes = `
@keyframes progress-loading {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}
`;

export function ProgressBar({
  value = 0,
  min = 0,
  max = 100,
  loading = false,
  disabled = false,
  color = colors.accent.primary,
  height = 4,
  className,
  style,
}: ProgressBarProps): React.ReactElement {
  const percent = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  const fillColor = disabled ? colors.text.muted : color;

  return (
    <>
      {loading && <style>{loadingKeyframes}</style>}
      <div
        className={className}
        style={{
          ...trackStyles,
          height: `${height}px`,
          opacity: disabled ? 0.5 : 1,
          ...style,
        }}
      >
        <div
          style={{
            ...fillStyles,
            backgroundColor: fillColor,
            width: loading ? "50%" : `${percent}%`,
            animation: loading ? "progress-loading 1.5s ease-in-out infinite" : undefined,
          }}
        />
      </div>
    </>
  );
}
