/** Main entry point for Trellis client. */

import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { TrellisClient, ConnectionState } from "./TrellisClient";

function App() {
  const [state, setState] = useState<ConnectionState>("disconnected");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [serverVersion, setServerVersion] = useState<string | null>(null);

  useEffect(() => {
    const client = new TrellisClient({
      onStateChange: setState,
      onConnected: (response) => {
        setSessionId(response.session_id);
        setServerVersion(response.server_version);
      },
    });

    client.connect().catch((err) => {
      console.error("Failed to connect:", err);
    });

    return () => client.disconnect();
  }, []);

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
