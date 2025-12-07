/** Renders a serialized element tree as React components. */

import React from "react";
import { SerializedElement, isCallbackRef } from "./types";
import { getWidget } from "./widgets";
import { useTrellisClient } from "./TrellisContext";
import { TrellisClient } from "./TrellisClient";

/** Set of native HTML element tags that can be rendered directly. */
const HTML_TAGS = new Set([
  // Layout
  "div",
  "span",
  "section",
  "article",
  "header",
  "footer",
  "nav",
  "main",
  "aside",
  // Text
  "p",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "strong",
  "em",
  "code",
  "pre",
  // Lists
  "ul",
  "ol",
  "li",
  // Links/Media
  "a",
  "img",
  // Forms
  "form",
  "input",
  "button",
  "textarea",
  "select",
  "option",
  "label",
  // Tables
  "table",
  "thead",
  "tbody",
  "tr",
  "th",
  "td",
]);

/**
 * Transform props, converting callback refs to actual event handler functions.
 *
 * This allows both HTML elements and custom React components to receive
 * real functions instead of callback reference objects.
 */
function processProps(
  props: Record<string, unknown>,
  client: TrellisClient
): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(props)) {
    if (isCallbackRef(value)) {
      // Convert callback ref to actual event handler
      result[key] = () => client.sendEvent(value.__callback__);
    } else {
      result[key] = value;
    }
  }
  return result;
}

interface TreeRendererProps {
  node: SerializedElement;
}

export function TreeRenderer({ node }: TreeRendererProps): React.ReactElement {
  const client = useTrellisClient();

  // Recursively render children
  const children = node.children.map((child, index) => (
    <TreeRenderer key={child.key ?? index} node={child} />
  ));

  // Process props for ALL components (transforms callback refs to functions)
  const processedProps = processProps(node.props, client);

  // Native HTML elements - render directly with React.createElement
  if (HTML_TAGS.has(node.type)) {
    // Extract _text prop for text content (since 'children' prop is reserved)
    const { _text, ...htmlProps } = processedProps as Record<string, unknown> & {
      _text?: string;
    };
    // Include text content as first child if present
    const allChildren = _text != null ? [_text, ...children] : children;
    return React.createElement(
      node.type,
      { ...htmlProps, key: node.key },
      ...allChildren
    );
  }

  // Custom components via widget registry
  const Component = getWidget(node.type);

  if (!Component) {
    // Unknown component type - render a warning placeholder
    return (
      <div
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
  // Include name for FunctionalComponent debugging
  return (
    <Component {...processedProps} name={node.name}>
      {children}
    </Component>
  );
}
