import React from "react";
import { colors, typography, radius, shadows, spacing } from "../theme";

type TooltipPosition = "top" | "bottom" | "left" | "right";

interface TooltipProps {
  content?: string;
  position?: TooltipPosition;
  delay?: number;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

const tooltipStyles: React.CSSProperties = {
  position: "absolute",
  backgroundColor: colors.neutral[800],
  color: colors.text.inverse,
  padding: `${spacing.xs}px ${spacing.md}px`,
  borderRadius: `${radius.sm}px`,
  fontSize: `${typography.fontSize.sm}px`,
  fontWeight: typography.fontWeight.normal,
  boxShadow: shadows.lg,
  whiteSpace: "nowrap",
  zIndex: 1000,
  pointerEvents: "none",
};

const positionStyles: Record<TooltipPosition, React.CSSProperties> = {
  top: {
    bottom: "100%",
    left: "50%",
    transform: "translateX(-50%)",
    marginBottom: `${spacing.xs}px`,
  },
  bottom: {
    top: "100%",
    left: "50%",
    transform: "translateX(-50%)",
    marginTop: `${spacing.xs}px`,
  },
  left: {
    right: "100%",
    top: "50%",
    transform: "translateY(-50%)",
    marginRight: `${spacing.xs}px`,
  },
  right: {
    left: "100%",
    top: "50%",
    transform: "translateY(-50%)",
    marginLeft: `${spacing.xs}px`,
  },
};

export function Tooltip({
  content = "",
  position = "top",
  delay = 200,
  className,
  style,
  children,
}: TooltipProps): React.ReactElement {
  const [isVisible, setIsVisible] = React.useState(false);
  const timeoutRef = React.useRef<number | null>(null);

  const showTooltip = () => {
    timeoutRef.current = window.setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsVisible(false);
  };

  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <span
      className={className}
      style={{
        position: "relative",
        display: "inline-flex",
        ...style,
      }}
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
    >
      {children}
      {isVisible && content && (
        <span
          style={{
            ...tooltipStyles,
            ...positionStyles[position],
          }}
        >
          {content}
        </span>
      )}
    </span>
  );
}
