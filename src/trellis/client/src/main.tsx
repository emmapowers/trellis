/** Main entry point for Trellis client. */

import React, { useEffect, useState, useMemo } from "react";
import { createRoot } from "react-dom/client";
import { TrellisClient, ConnectionState } from "./TrellisClient";
import { TrellisContext } from "./TrellisContext";
import { SerializedElement } from "./types";
import { TreeRenderer } from "./TreeRenderer";

function App() {
  const [state, setState] = useState<ConnectionState>("disconnected");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [serverVersion, setServerVersion] = useState<string | null>(null);
  const [tree, setTree] = useState<SerializedElement | null>(null);

  // Create client once (stable reference for context)
  const client = useMemo(
    () =>
      new TrellisClient({
        onStateChange: setState,
        onConnected: (response) => {
          setSessionId(response.session_id);
          setServerVersion(response.server_version);
        },
        onRender: (newTree) => {
          setTree(newTree);
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
      <h1>Trellis</h1>
      <p>
        Status:{" "}
        <strong
          style={{
            color:
              state === "connected"
                ? "green"
                : state === "connecting"
                  ? "orange"
                  : "red",
          }}
        >
          {state}
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

const root = createRoot(document.getElementById("root")!);
root.render(<App />);
