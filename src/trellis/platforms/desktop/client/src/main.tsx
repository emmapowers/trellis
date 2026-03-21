/** Main entry point for Trellis desktop client. */

import "@trellis/trellis-core/init";

// Forward console messages to Python stdout
import { addConsoleHandler } from "@trellis/trellis-core/console";
import { pyInvoke } from "tauri-plugin-pytauri-api";

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

import React, { useCallback } from "react";
import { DesktopClient } from "@trellis/trellis-desktop/client/src/DesktopClient";
import { ClientApp } from "@trellis/trellis-core/ClientApp";
import { mountApp } from "@trellis/trellis-core/ssr";
import { installExternalLinkDelegation } from "./externalLinks";

function App() {
  const createClient = useCallback(
    (onError: (error: string) => void) => new DesktopClient({ onError }),
    []
  );

  return (
    <ClientApp
      createClient={createClient}
      onMount={installExternalLinkDelegation}
    />
  );
}

mountApp(document.getElementById("root")!, <App />);
