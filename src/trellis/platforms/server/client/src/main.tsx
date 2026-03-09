/** Main entry point for Trellis server client. */

// Polyfill for Symbol.dispose (Explicit Resource Management)
// Not yet supported in Safari/older WebKit versions
(Symbol as any).dispose ??= Symbol("Symbol.dispose");
(Symbol as any).asyncDispose ??= Symbol("Symbol.asyncDispose");

// Initialize widget registry before any rendering
import { initRegistry } from "@trellis/_registry";
initRegistry();

import "@trellis/trellis-core/theme.css"; // Theme CSS variables
import "@trellis/trellis-core/console"; // Set up console filtering
import React, { useEffect, useState, useMemo } from "react";
import { createRoot, hydrateRoot } from "react-dom/client";
import { ServerTrellisClient } from "@trellis/trellis-server/client/src/TrellisClient";
import { TrellisRoot } from "@trellis/trellis-core/TrellisRoot";
import { store } from "@trellis/trellis-core/core";
import type { Patch } from "@trellis/trellis-core/types";

/** SSR dehydration data injected by the server. */
interface TrellisSSRData {
  sessionId: string;
  serverVersion: string;
  patches: Patch[];
}

declare global {
  interface Window {
    __TRELLIS_SSR__?: TrellisSSRData;
  }
}

const ssrData = window.__TRELLIS_SSR__;

function App() {
  const [error, setError] = useState<string | null>(null);

  // Create client once (stable reference for context)
  const client = useMemo(
    () =>
      new ServerTrellisClient(
        {
          onError: (errorMsg) => {
            setError(errorMsg);
          },
        },
        undefined,
        ssrData?.sessionId
      ),
    []
  );

  useEffect(() => {
    client.connect().catch((err) => {
      console.error("Failed to connect:", err);
    });

    return () => client.disconnect();
  }, [client]);

  return <TrellisRoot client={client} error={error} />;
}

const container = document.getElementById("root")!;

if (ssrData) {
  // SSR path: pre-populate the store with patches from the server,
  // then hydrate the existing DOM.
  store.applyPatches(ssrData.patches);
  hydrateRoot(container, <App />);
} else {
  // CSR path: create a fresh root.
  const root = createRoot(container);
  root.render(<App />);
}
