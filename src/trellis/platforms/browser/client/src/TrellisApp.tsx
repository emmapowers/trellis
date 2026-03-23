/**
 * TrellisApp - React component for running Trellis apps in the browser.
 *
 * Runs Python code in a Web Worker via Pyodide. On re-run, the worker is
 * terminated and recreated for a clean restart.
 *
 * Unlike server/desktop platforms, this component manages the Pyodide lifecycle
 * (loading, initialization, Python execution) in addition to rendering.
 *
 * When `hydrated` is true (SSR content was pre-rendered at build time), the
 * component tree is rendered immediately with a loading overlay on top. The
 * overlay shows status text while Pyodide initializes, then dismisses when
 * the app connects.
 */

import React, { useEffect, useState, useMemo, useRef } from "react";
import { BrowserClient, ConnectionState } from "@trellis/trellis-browser/client/src/BrowserClient";
import {
  TrellisContext,
  HostThemeModeContext,
} from "@trellis/trellis-core/TrellisContext";
import { Message } from "@trellis/trellis-core/types";
import { TreeRenderer } from "@trellis/trellis-core/TreeRenderer";
import { useRootId } from "@trellis/trellis-core/core";
import { PyodideWorker } from "@trellis/trellis-browser/client/src/PyodideWorker";
import {
  INIT_TIMEOUT_MS,
  formatTimeoutError,
} from "@trellis/trellis-browser/client/src/pyodide-error-utils";
import { RoutingMode } from "@trellis/trellis-core/RouterManager";

export { RoutingMode };

export interface TrellisAppProps {
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
  /**
   * User-provided Python source code to run instead of the pre-bundled module.
   *
   * When provided, the worker runs this code via AppLoader.load_app_from_source()
   * instead of importing from the wheel. Used by the playground and TrellisDemo.
   */
  source?: { type: "code"; code: string };
  /**
   * Whether the app was hydrated from build-time SSR content.
   *
   * When true, the component tree is rendered immediately (the store is
   * already populated from SSR patches) with a loading overlay on top.
   */
  hydrated?: boolean;
}

type AppState =
  | { status: "loading"; message: string }
  | { status: "connected" }
  | { status: "error"; message: string };

/**
 * Default loading component — shown when there is no SSR content.
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
 * Loading overlay — shown on top of SSR content while Pyodide loads.
 *
 * Uses CSS classes matching the static HTML overlay from index.html.j2 so
 * the transition from static to React-managed overlay is seamless. The
 * dark mode adaptation is handled via prefers-color-scheme in the stylesheet.
 */
function LoadingOverlay({ message }: { message: string }) {
  return (
    <div className="ssr-loading-backdrop">
      <div className="ssr-loading-card">
        <div className="ssr-loading-spinner" />
        <p style={{ margin: 0, fontSize: "14px" }}>{message}</p>
      </div>
      <style>{`
        @keyframes trellis-spin { to { transform: rotate(360deg) } }
        .ssr-loading-backdrop { position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,0.75);z-index:99999 }
        .ssr-loading-card { display:flex;flex-direction:column;align-items:center;padding:24px 32px;border-radius:12px;background:#fff;box-shadow:0 4px 24px rgba(0,0,0,0.12);font-family:system-ui,-apple-system,sans-serif;color:#475569 }
        .ssr-loading-spinner { width:28px;height:28px;border:3px solid #e2e8f0;border-top-color:#3b82f6;border-radius:50%;animation:trellis-spin 1s linear infinite;margin-bottom:12px }
        @media (prefers-color-scheme: dark) {
          .ssr-loading-backdrop { background:rgba(0,0,0,0.6) }
          .ssr-loading-card { background:#1e293b;color:#cbd5e1;box-shadow:0 4px 24px rgba(0,0,0,0.4) }
          .ssr-loading-spinner { border-color:#334155;border-top-color:#60a5fa }
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
  routingMode = RoutingMode.Hash,
  onStatusChange,
  loadingComponent,
  errorComponent,
  themeMode,
  source,
  hydrated = false,
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
    // Remove the static HTML loading overlay (from index.html.j2) now that
    // React has mounted and will render its own dynamic overlay.
    document.getElementById("ssr-loading")?.remove();
  }, []);

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

        // 3. Run application (user-provided source or pre-bundled module)
        setState({ status: "loading", message: "Starting application..." });
        onStatusChange?.("Starting application...");
        worker.run(source?.code);

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

  // SSR hydrated path: show the tree immediately with a loading overlay
  if (hydrated) {
    return (
      <TrellisContext.Provider value={client}>
        <HostThemeModeContext.Provider value={themeMode}>
          {state.status === "loading" && <LoadingOverlay message={state.message} />}
          {state.status === "error" && (
            errorComponent ? (
              errorComponent(state.message) as React.ReactElement
            ) : (
              <DefaultError message={state.message} />
            )
          )}
          <HydratedContent />
        </HostThemeModeContext.Provider>
      </TrellisContext.Provider>
    );
  }

  // Non-SSR path: show loading/error states, then render tree
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

/**
 * Inner component for hydrated SSR mode.
 * The store is already populated from build-time patches, so useRootId
 * returns immediately. Renders TreeRenderer right away.
 */
function HydratedContent(): React.ReactElement | null {
  const rootId = useRootId();

  if (!rootId) {
    return null;
  }

  return <TreeRenderer />;
}

export default TrellisApp;
