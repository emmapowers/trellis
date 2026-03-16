/**
 * Core tree rendering logic - shared between server client and playground.
 *
 * This module provides the tree rendering without depending on TrellisClient
 * or WebSocket communication, making it reusable in different contexts.
 */

import React from "react";
import {
  applyCompiledStyleProps,
  toReactDomProps,
  serializeEventArg,
  PREVENT_DEFAULT_HANDLERS,
  shouldLetBrowserHandleClick,
} from "./htmlProps";
import { SerializedElement, ElementKind, EventHandler, isCallbackRef, isMutableRef, Mutable } from "./types";

/** Widget component type. */
export type WidgetComponent = React.ComponentType<any>;

/** Widget registry for looking up components by type name. */
export type WidgetRegistry = (typeName: string) => WidgetComponent | undefined;

// Re-export for consumers that imported from this module
export { applyCompiledStyleProps, toReactDomProps } from "./htmlProps";

/**
 * Transform props, converting callback refs to handlers and mutable refs to Mutable objects.
 *
 * For mutable refs, wraps them in a Mutable<T> object that components can
 * explicitly handle via `.value` and `.setValue()`.
 */
/** Prop keys that are internal to the key handling system and should not be passed to components. */
const KEY_FILTER_PROPS = new Set(["__key_filters__", "__global_key_filters__"]);

export function processProps(
  props: Record<string, unknown>,
  onEvent: EventHandler
): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(props)) {
    // Skip internal key filter props — handled by TreeRenderer
    if (KEY_FILTER_PROPS.has(key)) continue;
    if (isCallbackRef(value)) {
      const shouldPreventDefault = PREVENT_DEFAULT_HANDLERS.has(key);
      result[key] = (...args: unknown[]) => {
        // For anchor clicks with modifier keys or middle-click, let browser handle.
        // This allows Cmd+click / Ctrl+click to open in new tab.
        // Note: This check is here because anchor tags use native DOM nodes (not
        // React components), so we handle their click behavior at the prop level.
        if (key === "on_click" && shouldLetBrowserHandleClick(args[0])) {
          return;
        }

        // Prevent default browser behavior for interactive events
        if (shouldPreventDefault && args[0] && typeof args[0] === "object") {
          const event = args[0] as { preventDefault?: () => void };
          event.preventDefault?.();
        }
        // Serialize any event objects before sending
        const serializedArgs = args.map(serializeEventArg);
        onEvent(value.__callback__, serializedArgs);
      };
    } else if (isMutableRef(value)) {
      // Wrap in Mutable object for explicit handling by components
      result[key] = new Mutable(value, onEvent);
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
  const processedProps = applyCompiledStyleProps(processProps(node.props, onEvent));

  // Plain text nodes
  if (node.kind === ElementKind.TEXT) {
    const textContent = (node.props as { _text?: string })._text ?? "";
    return <React.Fragment key={key}>{textContent}</React.Fragment>;
  }

  // Native HTML/JSX elements (div, span, p, etc.)
  if (node.kind === ElementKind.JSX_ELEMENT) {
    // HTML elements can have a _text prop containing inline text content.
    // This is extracted and prepended to children to support patterns like:
    //   <p _text="Hello "><strong>world</strong></p>
    // Which renders as: Hello <strong>world</strong>
    const { _text, ...htmlProps } = processedProps as Record<string, unknown> & {
      _text?: string;
    };
    const domProps = toReactDomProps(htmlProps);
    const allChildren = _text != null ? [_text, ...children] : children;
    return React.createElement(
      node.type,
      { ...domProps, key },
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
  // __name__ carries the Python component name for debugging (uses __ prefix to avoid conflicts)
  return (
    <Component key={key} {...processedProps} __name__={node.name}>
      {children}
    </Component>
  );
}
