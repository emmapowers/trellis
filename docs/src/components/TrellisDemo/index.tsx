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

  // Mount on first render
  useEffect(() => {
    if (!containerRef.current) return;

    let mounted = true;

    async function setup() {
      if (!containerRef.current || !mounted) return;

      try {
        const lib = await import("../../../static/trellis");
        if (!mounted || !containerRef.current) return;

        instanceRef.current = lib.mount(containerRef.current, {
          source,
          themeMode,
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

  // Update theme when it changes
  useEffect(() => {
    instanceRef.current?.update({ themeMode });
  }, [themeMode]);

  return <div ref={containerRef} className={styles.trellisHost} />;
}

/**
 * Wrap user code with Trellis boilerplate.
 *
 * The docs examples expect an `App` component to be defined. This wrapper
 * adds the @async_main entry point that runs the app.
 */
function wrapWithBoilerplate(code: string): string {
  return `${code}

from trellis import Trellis, async_main

@async_main
async def _trellis_main():
    app = Trellis(top=App)
    await app.serve()
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
