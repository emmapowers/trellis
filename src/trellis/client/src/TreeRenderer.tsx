/** Renders a serialized element tree as React components. */

import React from "react";
import { SerializedElement } from "./types";
import { getWidget } from "./widgets";

interface TreeRendererProps {
  node: SerializedElement;
}

export function TreeRenderer({ node }: TreeRendererProps): React.ReactElement {
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

  // Recursively render children
  const children = node.children.map((child, index) => (
    <TreeRenderer key={child.key ?? index} node={child} />
  ));

  // Pass props and children to the component
  // Include name for FunctionalComponent debugging
  return (
    <Component {...node.props} name={node.name}>
      {children}
    </Component>
  );
}
