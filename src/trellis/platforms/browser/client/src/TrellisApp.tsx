/**
 * TrellisApp - React component for running Trellis apps in the browser.
 *
 * Runs Python code in a Web Worker via Pyodide. On re-run, the worker is
 * terminated and recreated for a clean restart.
 *
 * Unlike server/desktop platforms, this component manages the Pyodide lifecycle
 * (loading, initialization, Python execution) in addition to rendering.
 */

import React, { useEffect, useState, useMemo, useRef } from "react";
import { BrowserClient, ConnectionState } from "@trellis/trellis-browser/client/src/BrowserClient";
import {
  TrellisContext,
  HostThemeModeContext,
} from "@trellis/trellis-core/client/src/TrellisContext";
import { Message } from "@trellis/trellis-core/client/src/types";
import { TreeRenderer } from "@trellis/trellis-core/client/src/TreeRenderer";
import { useRootId } from "@trellis/trellis-core/client/src/core";
import { PyodideWorker, type PythonSource } from "@trellis/trellis-browser/client/src/PyodideWorker";
import {
  INIT_TIMEOUT_MS,
  formatTimeoutError,
} from "@trellis/trellis-browser/client/src/pyodide-error-utils";
import { RoutingMode } from "@trellis/trellis-core/client/src/RouterManager";

// Re-export types for external use
export type { PythonSource };
export { RoutingMode };

export interface TrellisAppProps {
  /** Source of the Python code */
  source: PythonSource;
  /** Entry point like "myapp:app" (optional if code defines app = App(...)) */
  main?: string;
  /** Custom trellis wheel URL (optional, tries several paths by default) */
  trellisWheelUrl?: string;
  /** Routing mode for URL handling. Defaults to Hash. */
  routingMode?: RoutingMode;
  /** Callback when loading status changes */
  onStatusChange?: (status: string) => void;
  /** Custom loading component */
  loadingComponent?: React.ReactNode;
  /** Custom error component */
  errorComponent?: (error: string) => React.ReactNode;
  /**
   * Host-controlled theme mode.
   *
   * When provided, overrides the default "system" theme mode. The host application
   * can use this to sync Trellis with its own dark mode setting. When this prop
   * changes, Trellis will update its theme accordingly.
   *
   * - "system": Follow OS preference (default)
   * - "light": Force light mode
   * - "dark": Force dark mode
   */
  themeMode?: "system" | "light" | "dark";
}

type AppState =
  | { status: "loading"; message: string }
  | { status: "connected" }
  | { status: "error"; message: string };

/**
 * Default loading component
 */
function DefaultLoading({ message }: { message: string }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px",
        fontFamily: "system-ui, -apple-system, sans-serif",
        color: "#64748b",
      }}
    >
      <div
        style={{
          width: "32px",
          height: "32px",
          border: "3px solid #e2e8f0",
          borderTopColor: "#3b82f6",
          borderRadius: "50%",
          animation: "spin 1s linear infinite",
          marginBottom: "16px",
        }}
      />
      <p style={{ margin: 0 }}>{message}</p>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

/**
 * Default error component
 */
function DefaultError({ message }: { message: string }) {
  return (
    <div
      style={{
        padding: "20px",
        fontFamily: "ui-monospace, monospace",
        backgroundColor: "#fef2f2",
        border: "1px solid #fecaca",
        borderRadius: "8px",
        margin: "16px",
      }}
    >
      <h3 style={{ color: "#dc2626", margin: "0 0 12px 0" }}>Error</h3>
      <pre
        style={{
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          margin: 0,
          color: "#7f1d1d",
          fontSize: "13px",
          lineHeight: "1.5",
        }}
      >
        {message}
      </pre>
    </div>
  );
}


export function TrellisApp({
  source,
  main,
  trellisWheelUrl,
  routingMode = RoutingMode.Hash,
  onStatusChange,
  loadingComponent,
  errorComponent,
  themeMode,
}: TrellisAppProps): React.ReactElement {
  const [state, setState] = useState<AppState>({
    status: "loading",
    message: "Initializing...",
  });
  const workerRef = useRef<PyodideWorker | null>(null);
  const initializedRef = useRef(false);
  // Track the initial themeMode to include in HELLO message
  const initialThemeModeRef = useRef(themeMode);

  // Create client with callbacks and routing mode
  const client = useMemo(
    () =>
      new BrowserClient(
        {
          onConnected: () => {
            setState({ status: "connected" });
          },
          onError: (error) => {
            setState({ status: "error", message: error });
          },
        },
        undefined,
        { routingMode }
      ),
    [routingMode]
  );

  useEffect(() => {
    // Prevent double initialization in React StrictMode
    if (initializedRef.current) {
      return;
    }
    initializedRef.current = true;

    async function initialize() {
      // Set up initialization timeout
      const timeoutId = setTimeout(() => {
        setState({ status: "error", message: formatTimeoutError() });
        workerRef.current?.terminate();
        workerRef.current = null;
      }, INIT_TIMEOUT_MS);

      try {
        // 1. Create and initialize the Pyodide worker
        const worker = new PyodideWorker();
        workerRef.current = worker;

        await worker.create({
          onStatus: (msg) => {
            setState({ status: "loading", message: msg });
            onStatusChange?.(msg);
          },
          onError: (error) => {
            setState({ status: "error", message: error });
          },
          trellisWheelUrl,
        });

        clearTimeout(timeoutId);

        // 2. Wire up message passing between client and worker
        // Worker -> Client: Python sends HELLO_RESPONSE, RENDER, ERROR
        worker.onMessage((msg) => {
          client.handleMessage(msg as unknown as Message);
        });

        // Client -> Worker: JS sends HELLO, EVENT
        client.setSendCallback((msg) => {
          worker.sendMessage(msg);
        });

        // 3. Run Python code
        // The handler.run() loop starts and waits for HelloMessage
        setState({ status: "loading", message: "Starting application..." });
        onStatusChange?.("Starting application...");
        worker.run(source, main);

        // 4. Send HelloMessage to start the handshake
        // Note: The worker's bridge queues messages until Python's handler is set,
        // so early messages are not lost. This small delay provides buffer for
        // Python to initialize the handler before we send. If the message arrives
        // before handler.run() is called, it will be queued and processed when
        // Python is ready.
        await new Promise((resolve) => setTimeout(resolve, 50));
        client.sendHello(initialThemeModeRef.current);
      } catch (e) {
        clearTimeout(timeoutId);
        console.error("[TrellisApp] Error:", e);
        setState({ status: "error", message: (e as Error).message });
      }
    }

    initialize();

    return () => {
      // Terminate the worker to kill all Python execution
      workerRef.current?.terminate();
      workerRef.current = null;
      client.disconnect();
      // Reset so remount (e.g., StrictMode) can re-initialize
      initializedRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);  // Empty deps: runs once on mount. Re-run by remounting with new key.

  // Render based on state
  if (state.status === "loading") {
    return (
      loadingComponent ?? <DefaultLoading message={state.message} />
    ) as React.ReactElement;
  }

  if (state.status === "error") {
    const ErrorComponent = errorComponent;
    return ErrorComponent ? (
      ErrorComponent(state.message) as React.ReactElement
    ) : (
      <DefaultError message={state.message} />
    );
  }

  // Connected - render the tree within context
  return (
    <TrellisContext.Provider value={client}>
      <HostThemeModeContext.Provider value={themeMode}>
        <AppContent loadingComponent={loadingComponent} />
      </HostThemeModeContext.Provider>
    </TrellisContext.Provider>
  );
}

interface AppContentProps {
  loadingComponent?: React.ReactNode;
}

/**
 * Inner component that uses useRootId to render the tree.
 */
function AppContent({ loadingComponent }: AppContentProps): React.ReactElement {
  const rootId = useRootId();

  if (!rootId) {
    return (loadingComponent ?? <DefaultLoading message="Waiting for render..." />) as React.ReactElement;
  }

  return <TreeRenderer />;
}

export default TrellisApp;
