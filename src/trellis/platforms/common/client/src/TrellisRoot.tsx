/**
 * Common React root component for Trellis applications.
 *
 * Provides the TrellisContext and renders the component tree once available.
 * Shows an error display only for catastrophic errors.
 * Used by server and desktop platforms. Browser platform has its own
 * TrellisApp component due to unique Pyodide lifecycle requirements.
 */

import React from "react";
import { TrellisClient } from "./TrellisClient";
import { TrellisContext } from "./TrellisContext";
import { TreeRenderer } from "./TreeRenderer";
import { useRootId } from "./core";

export interface TrellisRootProps {
  /** The platform-specific client instance */
  client: TrellisClient;
  /** Error message if a catastrophic error occurred */
  error: string | null;
}

/**
 * Root component that provides context and handles app states.
 *
 * Renders nothing until the component tree is available (SSR content
 * remains visible during this time). Shows an error display only for
 * catastrophic failures.
 */
export function TrellisRoot({
  client,
  error,
}: TrellisRootProps): React.ReactElement | null {
  // Show error if present
  if (error) {
    return <ErrorDisplay error={error} />;
  }

  // Provide context and render tree when available
  return (
    <TrellisContext.Provider value={client}>
      <TrellisContent />
    </TrellisContext.Provider>
  );
}

/**
 * Inner component that uses hooks depending on TrellisContext.
 * Renders nothing until the tree root is available.
 */
function TrellisContent(): React.ReactElement | null {
  const rootId = useRootId();

  if (!rootId) {
    return null;
  }

  return <TreeRenderer />;
}

interface ErrorDisplayProps {
  error: string;
}

/**
 * Error display for catastrophic failures (WebSocket death, server errors).
 */
function ErrorDisplay({ error }: ErrorDisplayProps): React.ReactElement {
  return (
    <div style={{ padding: "20px", fontFamily: "monospace" }}>
      <h2 style={{ color: "#d32f2f", margin: "0 0 16px 0" }}>Error</h2>
      <pre
        style={{
          whiteSpace: "pre-wrap",
          background: "#ffebee",
          padding: "16px",
          borderRadius: "4px",
          border: "1px solid #ef9a9a",
          overflow: "auto",
        }}
      >
        {error}
      </pre>
    </div>
  );
}
