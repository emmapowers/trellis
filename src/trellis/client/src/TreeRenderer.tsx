/** Renders a serialized element tree as React components. */

import React from "react";
import { SerializedElement } from "./core";
import { renderNode } from "./core";
import { getWidget } from "./widgets";
import { useTrellisClient } from "./TrellisContext";

interface TreeRendererProps {
  node: SerializedElement;
}

/**
 * React component that renders a serialized Trellis element tree.
 *
 * Uses TrellisContext to get the client for sending events back to the server.
 */
export function TreeRenderer({ node }: TreeRendererProps): React.ReactElement {
  const client = useTrellisClient();

  return renderNode(node, {
    onEvent: (callbackId) => client.sendEvent(callbackId),
    getWidget,
  });
}
