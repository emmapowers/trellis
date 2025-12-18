/** Main entry point for Trellis desktop client. */

// Polyfill for Symbol.dispose (Explicit Resource Management)
// Required by @tauri-apps/api but not yet supported in all WebKit versions
(Symbol as any).dispose ??= Symbol("Symbol.dispose");
(Symbol as any).asyncDispose ??= Symbol("Symbol.asyncDispose");

// Set up shared console (filtering, etc.) before other imports
import { addConsoleHandler } from "../../../common/client/src/console";
import { pyInvoke } from "tauri-plugin-pytauri-api";

// Forward console messages to Python stdout
const stringify = (arg: unknown): string => {
  if (arg instanceof Error) {
    return `${arg.name}: ${arg.message}${arg.stack ? "\n" + arg.stack : ""}`;
  }
  if (typeof arg === "object" && arg !== null) {
    try {
      return JSON.stringify(arg);
    } catch {
      return String(arg);
    }
  }
  return String(arg);
};

addConsoleHandler((level, args) => {
  const message = args.map(stringify).join(" ");
  pyInvoke("trellis_log", { level, message }).catch(() => {
    // Ignore errors from logging itself
  });
});

import React, { useEffect, useState, useMemo } from "react";
import { createRoot } from "react-dom/client";
import { DesktopClient, ConnectionState } from "./DesktopClient";
import { TrellisContext } from "../../../common/client/src/TrellisContext";
import { SerializedElement } from "../../../common/client/src/types";
import { TreeRenderer } from "../../../common/client/src/TreeRenderer";

function App() {
  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [serverVersion, setServerVersion] = useState<string | null>(null);
  const [tree, setTree] = useState<SerializedElement | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Create client once (stable reference for context)
  const client = useMemo(
    () =>
      new DesktopClient({
        onConnectionStateChange: setConnectionState,
        onConnected: (response) => {
          setSessionId(response.session_id);
          setServerVersion(response.server_version);
        },
        onRender: (newTree) => {
          setTree(newTree);
          setError(null); // Clear error on successful render
        },
        onError: (errorMsg) => {
          setError(errorMsg);
        },
      }),
    []
  );

  useEffect(() => {
    client.connect().catch((err) => {
      console.error("Failed to connect:", err);
    });

    return () => client.disconnect();
  }, [client]);

  // Show error if present
  if (error) {
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

  // If we have a tree, render it within context
  if (tree) {
    return (
      <TrellisContext.Provider value={client}>
        <TreeRenderer node={tree} />
      </TrellisContext.Provider>
    );
  }

  // Otherwise show connection status
  return (
    <div style={{ fontFamily: "system-ui, sans-serif", padding: "20px" }}>
      <h1>Trellis Desktop</h1>
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
          <p>Version: {serverVersion}</p>
        </>
      )}
    </div>
  );
}

const root = createRoot(document.getElementById("root")!);
root.render(<App />);
