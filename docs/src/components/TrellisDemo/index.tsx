import React, { useState, useCallback, lazy, Suspense } from "react";
import CodeBlock from "@theme/CodeBlock";
import BrowserOnly from "@docusaurus/BrowserOnly";
import { useColorMode } from "@docusaurus/theme-common";
import styles from "./styles.module.css";
import { ShadowDomWrapper } from "./ShadowDomWrapper";

// Lazy load TrellisApp to avoid SSR issues with Web Workers
const TrellisApp = lazy(
  () => import("../../../../src/trellis/platforms/browser/client/src/TrellisApp")
);

interface TrellisDemoProps {
  code: string;
  title?: string;
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
                  <Suspense fallback={<div>Loading demo...</div>}>
                    <ShadowDomWrapper initialTheme={colorMode}>
                      <TrellisApp
                        key={runId}
                        source={{ type: "code", code: wrappedCode }}
                        onStatusChange={setStatus}
                        themeMode={colorMode}
                        errorComponent={(msg) => {
                          setError(msg);
                          return null;
                        }}
                      />
                    </ShadowDomWrapper>
                  </Suspense>
                )}
              </BrowserOnly>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
