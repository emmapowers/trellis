import React, { useRef } from "react";
import { useTooltipTrigger, useTooltip } from "react-aria";
import { useTooltipTriggerState } from "react-stately";
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

function TooltipContent({
  state,
  content,
  position,
}: {
  state: ReturnType<typeof useTooltipTriggerState>;
  content: string;
  position: TooltipPosition;
}) {
  const { tooltipProps } = useTooltip({}, state);

  return (
    <span
      {...tooltipProps}
      style={{
        ...tooltipStyles,
        ...positionStyles[position],
      }}
    >
      {content}
    </span>
  );
}

export function Tooltip({
  content = "",
  position = "top",
  delay = 200,
  className,
  style,
  children,
}: TooltipProps): React.ReactElement {
  const triggerRef = useRef<HTMLSpanElement>(null);
  const state = useTooltipTriggerState({ delay });
  const { triggerProps, tooltipProps } = useTooltipTrigger(
    { delay },
    state,
    triggerRef
  );

  return (
    <span
      className={className}
      style={{
        position: "relative",
        display: "inline-flex",
        ...style,
      }}
    >
      <span {...triggerProps} ref={triggerRef}>
        {children}
      </span>
      {state.isOpen && content && (
        <TooltipContent state={state} content={content} position={position} />
      )}
    </span>
  );
}
