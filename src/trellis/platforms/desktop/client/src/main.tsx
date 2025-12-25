/** Main entry point for Trellis desktop client. */

// Polyfill for Symbol.dispose (Explicit Resource Management)
// Required by @tauri-apps/api but not yet supported in all WebKit versions
(Symbol as any).dispose ??= Symbol("Symbol.dispose");
(Symbol as any).asyncDispose ??= Symbol("Symbol.asyncDispose");

import "../../../common/client/src/theme.css"; // Theme CSS variables

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
import { TrellisRoot } from "../../../common/client/src/TrellisRoot";

function App() {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [serverVersion, setServerVersion] = useState<string | null>(null);
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
      title="Trellis Desktop"
    />
  );
}

const root = createRoot(document.getElementById("root")!);
root.render(<App />);
