/** Main entry point for Trellis server client. */

// Polyfill for Symbol.dispose (Explicit Resource Management)
// Not yet supported in Safari/older WebKit versions
(Symbol as any).dispose ??= Symbol("Symbol.dispose");
(Symbol as any).asyncDispose ??= Symbol("Symbol.asyncDispose");

// Initialize widget registry before any rendering
import { initRegistry } from "@trellis/_registry";
initRegistry();

import "@trellis/trellis-core/client/src/theme.css"; // Theme CSS variables
import "@trellis/trellis-core/client/src/console"; // Set up console filtering
import React, { useEffect, useState, useMemo } from "react";
import { createRoot } from "react-dom/client";
import { ServerTrellisClient, ConnectionState } from "@trellis/trellis-server/client/src/TrellisClient";
import { TrellisRoot } from "@trellis/trellis-core/client/src/TrellisRoot";

function App() {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [serverVersion, setServerVersion] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Create client once (stable reference for context)
  const client = useMemo(
    () =>
      new ServerTrellisClient({
        onConnectionStateChange: setConnectionState,
        onConnected: (response) => {
          setSessionId(response.session_id);
          setServerVersion(response.server_version);
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

  return (
    <TrellisRoot
      client={client}
      connectionState={connectionState}
      error={error}
      sessionId={sessionId}
      serverVersion={serverVersion}
      title="Trellis"
    />
  );
}

const root = createRoot(document.getElementById("root")!);
root.render(<App />);
