import React, { useState, useCallback, useEffect, useRef } from "react";
import CodeBlock from "@theme/CodeBlock";
import BrowserOnly from "@docusaurus/BrowserOnly";
import { useColorMode } from "@docusaurus/theme-common";
import styles from "./styles.module.css";
import type { TrellisInstance, TrellisAppProps } from "../../../static/trellis";

interface TrellisDemoProps {
  code: string;
  title?: string;
}

interface TrellisMountProps {
  source: TrellisAppProps["source"];
  themeMode: "light" | "dark";
  onStatusChange?: (status: string) => void;
  onError?: (error: string) => void;
}

/**
 * Component that mounts TrellisApp using the library's mount() API.
 *
 * The mount() API creates a shadow DOM for CSS isolation and sets up
 * event forwarding for React Aria compatibility automatically.
 */
function TrellisMount({
  source,
  themeMode,
  onStatusChange,
  onError,
}: TrellisMountProps): React.ReactElement {
  const containerRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<TrellisInstance | null>(null);
  // Track latest theme to avoid race condition between mount and theme update
  const latestThemeRef = useRef(themeMode);

  // Keep ref in sync with prop
  useEffect(() => {
    latestThemeRef.current = themeMode;
    instanceRef.current?.update({ themeMode });
  }, [themeMode]);

  // Mount on first render
  useEffect(() => {
    if (!containerRef.current) return;

    let mounted = true;

    async function setup() {
      if (!containerRef.current || !mounted) return;

      try {
        const lib = await import("../../../static/trellis");
        if (!mounted || !containerRef.current) return;

        // Use latestThemeRef to get current theme even if async load took time
        instanceRef.current = lib.mount(containerRef.current, {
          source,
          themeMode: latestThemeRef.current,
          onStatusChange,
          // Path is /trellis/trellis/ because:
          // - Docusaurus baseUrl is /trellis/
          // - CSS is in static/trellis/index.css
          cssUrl: "/trellis/trellis/index.css",
          errorComponent: onError
            ? (msg: string) => {
                onError(msg);
                return null;
              }
            : undefined,
        });
      } catch (e) {
        console.error("[TrellisMount] Failed to load library:", e);
        onError?.((e as Error).message);
      }
    }

    setup();

    return () => {
      mounted = false;
      instanceRef.current?.unmount();
      instanceRef.current = null;
    };
  }, []); // Run once on mount

  return <div ref={containerRef} className={styles.trellisHost} />;
}

/**
 * Wrap user code with Trellis boilerplate.
 *
 * The docs examples expect an `App` component to be defined. This wrapper
 * adds the app definition.
 */
function wrapWithBoilerplate(code: string): string {
  return `${code}

from trellis import App as TrellisApp

app = TrellisApp(App)
`;
}

/**
 * Inline demo component for docs.
 *
 * Wraps user code with Trellis boilerplate and runs it via TrellisApp.
 */
export default function TrellisDemo({
  code,
  title,
}: TrellisDemoProps): JSX.Element {
  const [runId, setRunId] = useState(0);
  const [status, setStatus] = useState<string>("idle");
  const [error, setError] = useState<string | null>(null);
  const { colorMode } = useColorMode();

  const runCode = useCallback(() => {
    setError(null);
    setRunId((id) => id + 1);
  }, []);

  // Encode code for playground URL
  const encodedCode =
    typeof window !== "undefined" ? btoa(encodeURIComponent(code)) : "";
  const playgroundUrl = `/trellis/playground/#code=${encodedCode}`;

  const isLoading = status.includes("Loading") || status.includes("Setting");

  // Wrap the user code with boilerplate
  const wrappedCode = wrapWithBoilerplate(code);

  return (
    <div className={styles.playgroundContainer}>
      <div className={styles.header}>
        {title && <span className={styles.title}>{title}</span>}
        <div className={styles.actions}>
          <button
            onClick={runCode}
            disabled={isLoading}
            className={styles.runButton}
          >
            {isLoading ? status : runId > 0 ? "Re-run" : "Run"}
          </button>
          <a
            href={playgroundUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.openLink}
          >
            Edit in Playground
          </a>
        </div>
      </div>

      <CodeBlock language="python" showLineNumbers>
        {code.trim()}
      </CodeBlock>

      {runId > 0 && (
        <div className={styles.preview}>
          <div className={styles.previewHeader}>Preview</div>
          <div className={styles.previewContent}>
            {error ? (
              <div className={styles.error}>{error}</div>
            ) : (
              <BrowserOnly fallback={<div>Loading...</div>}>
                {() => (
                  <TrellisMount
                    key={runId}
                    source={{ type: "code", code: wrappedCode }}
                    themeMode={colorMode}
                    onStatusChange={setStatus}
                    onError={setError}
                  />
                )}
              </BrowserOnly>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
