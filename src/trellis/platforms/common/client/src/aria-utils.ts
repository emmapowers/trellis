/**
 * React Aria utilities for Trellis widgets.
 *
 * Provides helpers for prop conversion and shared styling patterns.
 */

import React from "react";
import { focusRing } from "./theme";

/**
 * Focus visible style to apply when element has keyboard focus.
 * Uses the theme's focus ring token.
 */
export const focusVisibleStyle: React.CSSProperties = focusRing;

/**
 * Merge props objects, combining style and className appropriately.
 */
export function mergeProps<T extends Record<string, unknown>>(
  ...propsList: (T | undefined)[]
): T {
  const result: Record<string, unknown> = {};

  for (const props of propsList) {
    if (!props) continue;

    for (const [key, value] of Object.entries(props)) {
      if (key === "style" && result.style) {
        // Merge style objects
        result.style = { ...(result.style as object), ...(value as object) };
      } else if (key === "className" && result.className) {
        // Concatenate classNames
        result.className = `${result.className} ${value}`;
      } else if (typeof value === "function" && typeof result[key] === "function") {
        // Chain event handlers
        const existingHandler = result[key] as (...args: unknown[]) => void;
        result[key] = (...args: unknown[]) => {
          existingHandler(...args);
          (value as (...args: unknown[]) => void)(...args);
        };
      } else if (value !== undefined) {
        result[key] = value;
      }
    }
  }

  return result as T;
}
