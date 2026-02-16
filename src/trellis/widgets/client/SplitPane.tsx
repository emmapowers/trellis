import React from "react";
import { colors } from "@trellis/trellis-core/theme";

type SplitOrientation = "horizontal" | "vertical";

interface SplitPaneProps {
  orientation?: SplitOrientation;
  split?: number;
  min_size?: number;
  divider_size?: number;
  height?: number | string;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function toPercent(value: number): string {
  return `${(value * 100).toFixed(4).replace(/\.?0+$/, "")}%`;
}

function toCssLength(value: number | string | undefined, fallback: string): string {
  if (value === undefined) {
    return fallback;
  }
  return typeof value === "number" ? `${value}px` : value;
}

function clampSplitForBounds(rawSplit: number, containerSize: number, minSize: number): number {
  const normalized = clamp(rawSplit, 0, 1);
  if (containerSize <= 0) {
    return normalized;
  }
  const minRatio = clamp(minSize / containerSize, 0, 0.49);
  return clamp(normalized, minRatio, 1 - minRatio);
}

export function SplitPane({
  orientation = "horizontal",
  split = 0.5,
  min_size = 120,
  divider_size = 8,
  height,
  className,
  style,
  children,
}: SplitPaneProps): React.ReactElement {
  const rootRef = React.useRef<HTMLDivElement>(null);
  const isHorizontal = orientation === "horizontal";
  const [dragging, setDragging] = React.useState(false);
  const [ratio, setRatio] = React.useState(() => clamp(split, 0, 1));

  React.useEffect(() => {
    setRatio(clamp(split, 0, 1));
  }, [split]);

  React.useEffect(() => {
    if (!dragging) {
      return;
    }

    const onMouseMove = (event: MouseEvent): void => {
      const root = rootRef.current;
      if (!root) {
        return;
      }

      const rect = root.getBoundingClientRect();
      const containerSize = isHorizontal ? rect.width : rect.height;
      const relativePosition = isHorizontal ? event.clientX - rect.left : event.clientY - rect.top;
      const next = relativePosition / Math.max(containerSize, 1);
      setRatio(clampSplitForBounds(next, containerSize, min_size));
    };

    const onMouseUp = (): void => {
      setDragging(false);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [dragging, isHorizontal, min_size]);

  const childArray = React.Children.toArray(children);
  const firstChild = childArray[0] ?? null;
  const secondChild = childArray[1] ?? null;

  return (
    <div
      ref={rootRef}
      data-testid="split-pane-root"
      className={className}
      style={{
        display: "flex",
        flexDirection: isHorizontal ? "row" : "column",
        width: "100%",
        height: toCssLength(height, "100%"),
        minWidth: 0,
        minHeight: 0,
        overflow: "hidden",
        ...style,
      }}
    >
      <div
        data-testid="split-pane-first"
        style={{
          flexBasis: toPercent(ratio),
          flexShrink: 0,
          flexGrow: 0,
          minWidth: isHorizontal ? `${min_size}px` : 0,
          minHeight: isHorizontal ? 0 : `${min_size}px`,
          overflow: "auto",
        }}
      >
        {firstChild}
      </div>
      <div
        role="separator"
        aria-orientation={orientation}
        onMouseDown={() => {
          setDragging(true);
        }}
        style={{
          width: isHorizontal ? `${divider_size}px` : "100%",
          height: isHorizontal ? "100%" : `${divider_size}px`,
          flexShrink: 0,
          cursor: isHorizontal ? "col-resize" : "row-resize",
          backgroundColor: dragging ? colors.border.focus : colors.border.default,
          transition: "background-color 120ms ease",
        }}
      />
      <div
        data-testid="split-pane-second"
        style={{
          flex: 1,
          minWidth: isHorizontal ? `${min_size}px` : 0,
          minHeight: isHorizontal ? 0 : `${min_size}px`,
          overflow: "auto",
        }}
      >
        {secondChild}
      </div>
    </div>
  );
}
