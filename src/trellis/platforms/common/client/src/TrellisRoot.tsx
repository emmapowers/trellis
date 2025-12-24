/**
 * Common React root component for Trellis applications.
 *
 * Provides the TrellisContext and handles the loading/connected/error states.
 * Used by server and desktop platforms. Browser platform has its own
 * TrellisApp component due to unique Pyodide lifecycle requirements.
 */

import React from "react";
import { TrellisClient } from "./TrellisClient";
import { TrellisContext } from "./TrellisContext";
import { TreeRenderer } from "./TreeRenderer";
import { useRootId } from "./core";
import { ConnectionState } from "./ClientMessageHandler";

export interface TrellisRootProps {
  /** The platform-specific client instance */
  client: TrellisClient;
  /** Current connection state */
  connectionState: ConnectionState;
  /** Error message if an error occurred */
  error: string | null;
  /** Session ID from server */
  sessionId?: string | null;
  /** Server version string */
  serverVersion?: string | null;
  /** Title to show in connection status (e.g., "Trellis" or "Trellis Desktop") */
  title?: string;
}

/**
 * Root component that provides context and handles app states.
 */
export function TrellisRoot({
  client,
  connectionState,
  error,
  sessionId,
  serverVersion,
  title = "Trellis",
}: TrellisRootProps): React.ReactElement {
  // Show error if present
  if (error) {
    return <ErrorDisplay error={error} />;
  }

  // Provide context and render content
  return (
    <TrellisContext.Provider value={client}>
      <TrellisContent
        connectionState={connectionState}
        sessionId={sessionId}
        serverVersion={serverVersion}
        title={title}
      />
    </TrellisContext.Provider>
  );
}

interface TrellisContentProps {
  connectionState: ConnectionState;
  sessionId?: string | null;
  serverVersion?: string | null;
  title: string;
}

/**
 * Inner component that uses hooks depending on TrellisContext.
 */
function TrellisContent({
  connectionState,
  sessionId,
  serverVersion,
  title,
}: TrellisContentProps): React.ReactElement {
  const rootId = useRootId();

  // If we have a tree, render it
  if (rootId) {
    return <TreeRenderer />;
  }

  // Otherwise show connection status
  return (
    <ConnectionStatus
      connectionState={connectionState}
      sessionId={sessionId}
      serverVersion={serverVersion}
      title={title}
    />
  );
}

interface ConnectionStatusProps {
  connectionState: ConnectionState;
  sessionId?: string | null;
  serverVersion?: string | null;
  title: string;
}

/**
 * Connection status display shown before tree is available.
 */
function ConnectionStatus({
  connectionState,
  sessionId,
  serverVersion,
  title,
}: ConnectionStatusProps): React.ReactElement {
  return (
    <div style={{ fontFamily: "system-ui, sans-serif", padding: "20px" }}>
      <h1>{title}</h1>
      <p>
        Status:{" "}
        <strong
          style={{
            color:
              connectionState === "connected"
                ? "green"
                : connectionState === "connecting"
                  ? "orange"
                  : "red",
          }}
        >
          {connectionState}
        </strong>
      </p>
      {sessionId && (
        <>
          <p>Session ID: {sessionId}</p>
          <p>Server Version: {serverVersion}</p>
        </>
      )}
    </div>
  );
}

interface ErrorDisplayProps {
  error: string;
}

/**
 * Error display component.
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
