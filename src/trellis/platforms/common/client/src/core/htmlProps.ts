/**
 * HTML/CSS prop conversion and event serialization for native DOM elements.
 *
 * Converts snake_case Python props to React-compatible DOM props,
 * normalizes inline styles, injects dynamic CSS rules, and serializes
 * React SyntheticEvents to plain objects matching Python dataclasses.
 */

import React from "react";

function camelToSnakeKey(key: string): string {
  return key.replace(/[A-Z]/g, (char) => `_${char.toLowerCase()}`);
}

function snakeToCamelKey(key: string): string {
  return key.replace(/_([a-z])/g, (_, char: string) => char.toUpperCase());
}

function cssNameToCamelKey(key: string): string {
  return key.replace(/-([a-z])/g, (_, char: string) => char.toUpperCase());
}

export function convertDeepKeysToSnake(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(convertDeepKeysToSnake);
  }

  if (value && typeof value === "object" && value.constructor === Object) {
    const obj = value as Record<string, unknown>;
    return Object.fromEntries(
      Object.entries(obj).map(([key, nestedValue]) => [
        camelToSnakeKey(key),
        convertDeepKeysToSnake(nestedValue),
      ])
    );
  }

  return value;
}

function domPropNameFromSnake(prop: string): string {
  if (prop === "data_") {
    return "data";
  }
  if (prop.startsWith("aria_") || prop.startsWith("data_")) {
    return prop.replaceAll("_", "-");
  }
  if (prop === "item_id") {
    return "itemID";
  }
  if (prop === "popover_target") {
    return "popovertarget";
  }
  if (prop === "popover_target_action") {
    return "popovertargetaction";
  }
  return snakeToCamelKey(prop);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function normalizeInlineStyle(value: unknown): unknown {
  if (!isRecord(value)) {
    return value;
  }

  return Object.fromEntries(
    Object.entries(value).map(([key, nestedValue]) => [
      key.startsWith("--") ? key : cssNameToCamelKey(key),
      normalizeInlineStyle(nestedValue),
    ])
  );
}

export function applyCompiledStyleProps(
  props: Record<string, unknown>
): Record<string, unknown> {
  return props;
}

export function toReactDomProps(props: Record<string, unknown>): Record<string, unknown> {
  const mapped: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(props)) {
    if (key === "style") {
      mapped.style = normalizeInlineStyle(value);
      continue;
    }

    if (key === "data") {
      if (!isRecord(value)) {
        continue;
      }

      for (const [suffix, dataValue] of Object.entries(value)) {
        mapped[`data-${suffix}`] = dataValue;
      }
      continue;
    }

    mapped[domPropNameFromSnake(key)] = value;
  }
  return mapped;
}

/**
 * Extract serializable data from a DOM event.
 * Converts React SyntheticEvents to plain objects matching Python dataclasses.
 */
export function serializeEventArg(arg: unknown): unknown {
  if (arg && typeof arg === "object" && "type" in arg && "nativeEvent" in arg) {
    const syntheticEvent = arg as React.SyntheticEvent;
    const nativeEvent = syntheticEvent.nativeEvent;
    const eventType = syntheticEvent.type;

    const base = {
      type: eventType,
      timeStamp: syntheticEvent.timeStamp,
      bubbles: syntheticEvent.bubbles,
      cancelable: syntheticEvent.cancelable,
      defaultPrevented: syntheticEvent.defaultPrevented,
      eventPhase: syntheticEvent.eventPhase,
      isTrusted: syntheticEvent.isTrusted,
    };

    if (nativeEvent instanceof WheelEvent) {
      return convertDeepKeysToSnake({
        ...base,
        clientX: nativeEvent.clientX,
        clientY: nativeEvent.clientY,
        screenX: nativeEvent.screenX,
        screenY: nativeEvent.screenY,
        button: nativeEvent.button,
        buttons: nativeEvent.buttons,
        altKey: nativeEvent.altKey,
        ctrlKey: nativeEvent.ctrlKey,
        shiftKey: nativeEvent.shiftKey,
        metaKey: nativeEvent.metaKey,
        deltaX: nativeEvent.deltaX,
        deltaY: nativeEvent.deltaY,
        deltaZ: nativeEvent.deltaZ,
        deltaMode: nativeEvent.deltaMode,
      });
    }

    if (typeof InputEvent !== "undefined" && nativeEvent instanceof InputEvent) {
      return convertDeepKeysToSnake({
        ...base,
        data: nativeEvent.data,
        isComposing: nativeEvent.isComposing,
        inputType: nativeEvent.inputType,
      });
    }

    if (typeof DragEvent !== "undefined" && nativeEvent instanceof DragEvent) {
      const dt = nativeEvent.dataTransfer;
      return convertDeepKeysToSnake({
        ...base,
        clientX: nativeEvent.clientX,
        clientY: nativeEvent.clientY,
        screenX: nativeEvent.screenX,
        screenY: nativeEvent.screenY,
        button: nativeEvent.button,
        buttons: nativeEvent.buttons,
        altKey: nativeEvent.altKey,
        ctrlKey: nativeEvent.ctrlKey,
        shiftKey: nativeEvent.shiftKey,
        metaKey: nativeEvent.metaKey,
        dataTransfer: dt ? {
          dropEffect: dt.dropEffect,
          effectAllowed: dt.effectAllowed,
          types: Array.from(dt.types),
          files: Array.from(dt.files).map(f => ({ name: f.name, size: f.size, type: f.type })),
        } : null,
      });
    }

    if (nativeEvent instanceof MouseEvent) {
      return convertDeepKeysToSnake({
        ...base,
        clientX: nativeEvent.clientX,
        clientY: nativeEvent.clientY,
        screenX: nativeEvent.screenX,
        screenY: nativeEvent.screenY,
        button: nativeEvent.button,
        buttons: nativeEvent.buttons,
        altKey: nativeEvent.altKey,
        ctrlKey: nativeEvent.ctrlKey,
        shiftKey: nativeEvent.shiftKey,
        metaKey: nativeEvent.metaKey,
      });
    }

    if (nativeEvent instanceof KeyboardEvent) {
      return convertDeepKeysToSnake({
        ...base,
        key: nativeEvent.key,
        code: nativeEvent.code,
        location: nativeEvent.location,
        altKey: nativeEvent.altKey,
        ctrlKey: nativeEvent.ctrlKey,
        shiftKey: nativeEvent.shiftKey,
        metaKey: nativeEvent.metaKey,
        repeat: nativeEvent.repeat,
        isComposing: nativeEvent.isComposing,
      });
    }

    return convertDeepKeysToSnake(base);
  }

  return arg;
}

/** Event handler prop names that should call preventDefault before invoking callback. */
export const PREVENT_DEFAULT_HANDLERS = new Set(["on_click", "on_submit", "on_drag_over", "on_drop"]);

/**
 * Check if a click event should be handled by the browser instead of our handler.
 * Allows Cmd+click (Mac) / Ctrl+click (Win/Linux) to open links in new tabs.
 */
export function shouldLetBrowserHandleClick(event: unknown): boolean {
  if (!event || typeof event !== "object") return false;

  const syntheticEvent = event as React.MouseEvent;
  const nativeEvent = syntheticEvent.nativeEvent;

  if (!(nativeEvent instanceof MouseEvent)) return false;

  const target = syntheticEvent.currentTarget;
  if (!(target instanceof HTMLAnchorElement) || !target.href) return false;

  if (nativeEvent.button === 1) return true;

  const { metaKey, ctrlKey, shiftKey, altKey } = nativeEvent;
  if (metaKey || ctrlKey || shiftKey || altKey) return true;

  return false;
}
