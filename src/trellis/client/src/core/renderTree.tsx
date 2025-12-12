/**
 * Core tree rendering logic - shared between server client and playground.
 *
 * This module provides the tree rendering without depending on TrellisClient
 * or WebSocket communication, making it reusable in different contexts.
 */

import React from "react";
import { SerializedElement, EventHandler, isCallbackRef } from "./types";
import { HTML_TAGS } from "./htmlTags";

/** Widget component type. */
export type WidgetComponent = React.ComponentType<any>;

/** Widget registry for looking up components by type name. */
export type WidgetRegistry = (typeName: string) => WidgetComponent | undefined;

/**
 * Extract serializable data from a DOM event.
 * Converts React SyntheticEvents to plain objects matching Python dataclasses.
 */
function serializeEventArg(arg: unknown): unknown {
  // Check if this looks like a React SyntheticEvent or DOM Event
  if (arg && typeof arg === "object" && "type" in arg && "nativeEvent" in arg) {
    // React SyntheticEvent - get the native event for instanceof checks
    const syntheticEvent = arg as React.SyntheticEvent;
    const nativeEvent = syntheticEvent.nativeEvent;
    const eventType = syntheticEvent.type;

    const base = {
      type: eventType,
      timestamp: syntheticEvent.timeStamp,
    };

    // Mouse events
    if (nativeEvent instanceof MouseEvent) {
      return {
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
      };
    }

    // Keyboard events
    if (nativeEvent instanceof KeyboardEvent) {
      return {
        ...base,
        key: nativeEvent.key,
        code: nativeEvent.code,
        altKey: nativeEvent.altKey,
        ctrlKey: nativeEvent.ctrlKey,
        shiftKey: nativeEvent.shiftKey,
        metaKey: nativeEvent.metaKey,
        repeat: nativeEvent.repeat,
      };
    }

    // Input/Change events - extract target value
    if (
      "target" in syntheticEvent &&
      syntheticEvent.target &&
      typeof syntheticEvent.target === "object"
    ) {
      const target = syntheticEvent.target as HTMLInputElement;
      return {
        ...base,
        value: target.value ?? "",
        checked: target.checked ?? false,
      };
    }

    // Generic event fallback
    return base;
  }

  // Non-event args pass through as-is
  return arg;
}

/**
 * Transform props, converting callback refs to actual event handler functions.
 */
export function processProps(
  props: Record<string, unknown>,
  onEvent: EventHandler
): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(props)) {
    if (isCallbackRef(value)) {
      result[key] = (...args: unknown[]) => {
        // Serialize any event objects before sending
        const serializedArgs = args.map(serializeEventArg);
        onEvent(value.__callback__, serializedArgs);
      };
    } else {
      result[key] = value;
    }
  }
  return result;
}

interface RenderNodeOptions {
  onEvent: EventHandler;
  getWidget: WidgetRegistry;
}

/**
 * Render a serialized element tree node to a React element.
 *
 * This is the core rendering function that recursively converts a serialized
 * tree into React elements, handling HTML tags, custom widgets, and text nodes.
 */
export function renderNode(
  node: SerializedElement,
  options: RenderNodeOptions,
  key?: string | number
): React.ReactElement {
  const { onEvent, getWidget } = options;

  // Recursively render children
  const children = node.children.map((child, index) =>
    renderNode(child, options, child.key ?? index)
  );

  // Process props (transforms callback refs to functions)
  const processedProps = processProps(node.props, onEvent);

  // Plain text nodes
  if (node.type === "_text") {
    const textContent = (node.props as { _text?: string })._text ?? "";
    return <React.Fragment key={key}>{textContent}</React.Fragment>;
  }

  // Native HTML elements
  if (HTML_TAGS.has(node.type)) {
    const { _text, ...htmlProps } = processedProps as Record<string, unknown> & {
      _text?: string;
    };
    const allChildren = _text != null ? [_text, ...children] : children;
    return React.createElement(
      node.type,
      { ...htmlProps, key },
      ...allChildren
    );
  }

  // Custom components via widget registry
  const Component = getWidget(node.type);

  if (!Component) {
    // Unknown component type - render a warning placeholder
    return (
      <div
        key={key}
        style={{
          color: "red",
          border: "1px solid red",
          padding: "4px",
          margin: "2px",
          fontSize: "12px",
        }}
      >
        Unknown component: {node.type}
      </div>
    );
  }

  // Pass props and children to the component
  return (
    <Component key={key} {...processedProps} name={node.name}>
      {children}
    </Component>
  );
}
