/**
 * Renders a serialized element tree as React components.
 *
 * Uses the ID-keyed store for efficient incremental updates.
 * Each NodeRenderer subscribes only to its own node, so only
 * affected nodes re-render when patches arrive.
 */

import React from "react";
import { useNode, useRootId, NodeData, processProps, ElementKind, store } from "./core";
import { getWidget } from "./widgets";
import { useTrellisClient } from "./TrellisContext";

/**
 * Root component that renders the Trellis tree.
 * Subscribes to the root ID and renders the tree when available.
 */
export function TreeRenderer(): React.ReactElement | null {
  const rootId = useRootId();

  if (!rootId) {
    return null;
  }

  return <NodeRenderer id={rootId} />;
}

interface NodeRendererProps {
  id: string;
}

/**
 * Wrapper that exposes the underlying component type for parent inspection.
 * Used by compound components like Menu that need to identify child types.
 */
interface ChildWrapperProps {
  __componentType__: string;
  __componentProps__: Record<string, unknown>;
  children: React.ReactNode;
}

function ChildWrapper({ children }: ChildWrapperProps): React.ReactElement {
  return <>{children}</>;
}

// Expose type for parent component inspection
ChildWrapper.__isChildWrapper__ = true;

/**
 * Renders a single node by ID.
 * Subscribes to that node's data and only re-renders when it changes.
 */
const NodeRenderer = React.memo(function NodeRenderer({
  id,
}: NodeRendererProps): React.ReactElement | null {
  const node = useNode(id);
  const client = useTrellisClient();

  if (!node) {
    return null;
  }

  // Process props (transforms callback refs to functions)
  const processedProps = processProps(node.props, (callbackId, args) =>
    client.sendEvent(callbackId, args)
  );

  // Recursively render children by ID, wrapped with type metadata for compound components
  const children = node.childIds.map((childId) => {
    const childNode = store.getNode(childId);
    const componentType = childNode?.type ?? "Unknown";
    // Process props (convert callback refs to functions) for compound component inspection
    const componentProps = childNode
      ? processProps(childNode.props, (callbackId, args) =>
          client.sendEvent(callbackId, args)
        )
      : {};
    return (
      <ChildWrapper
        key={childId}
        __componentType__={componentType}
        __componentProps__={componentProps}
      >
        <NodeRenderer id={childId} />
      </ChildWrapper>
    );
  });

  return renderNodeElement(node, processedProps, children, id);
});

/**
 * Render a node to a React element based on its kind.
 */
function renderNodeElement(
  node: NodeData,
  processedProps: Record<string, unknown>,
  children: React.ReactElement[],
  key: string
): React.ReactElement {
  // Plain text nodes
  if (node.kind === ElementKind.TEXT) {
    const textContent = (node.props as { _text?: string })._text ?? "";
    return <React.Fragment key={key}>{textContent}</React.Fragment>;
  }

  // Native HTML/JSX elements (div, span, p, etc.)
  if (node.kind === ElementKind.JSX_ELEMENT) {
    // HTML elements can have a _text prop containing inline text content.
    const { _text, ...htmlProps } = processedProps as Record<string, unknown> & {
      _text?: string;
    };
    const allChildren = _text != null ? [_text, ...children] : children;
    return React.createElement(node.type, { ...htmlProps, key }, ...allChildren);
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
  // __name__ carries the Python component name for debugging
  return (
    <Component key={key} {...processedProps} __name__={node.name}>
      {children}
    </Component>
  );
}
