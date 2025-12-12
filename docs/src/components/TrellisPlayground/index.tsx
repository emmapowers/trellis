import React, { useState, useCallback, useRef } from 'react';
import CodeBlock from '@theme/CodeBlock';
import styles from './styles.module.css';
import { initPyodide, PyodideInterface, PyProxy } from '../../lib/pyodide-init';
import { SerializedElement, renderNode } from '@trellis/client/core';
import { getWidget } from '@trellis/client/widgets';

interface TrellisPlaygroundProps {
  code: string;
  title?: string;
}

/**
 * Inline playground component with lazy Pyodide loading.
 */
export default function TrellisPlayground({ code, title }: TrellisPlaygroundProps): JSX.Element {
  const [status, setStatus] = useState<'idle' | 'loading' | 'running' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [tree, setTree] = useState<SerializedElement | null>(null);
  const runtimeRef = useRef<PyProxy | null>(null);
  const pyodideRef = useRef<PyodideInterface | null>(null);

  const handleEvent = useCallback(async (cbId: string) => {
    if (!runtimeRef.current) return;
    try {
      const updatedTree = runtimeRef.current
        .handle_event(cbId)
        .toJs({ dict_converter: Object.fromEntries }) as SerializedElement;
      setTree(updatedTree);
    } catch (e) {
      setError(`Event error: ${(e as Error).message}`);
    }
  }, []);

  const runCode = useCallback(async () => {
    setStatus('loading');
    setError(null);

    try {
      // Initialize Pyodide if needed
      if (!pyodideRef.current) {
        pyodideRef.current = await initPyodide();
      }
      const pyodide = pyodideRef.current;

      setStatus('running');

      // Execute user code
      await pyodide.runPythonAsync(code);

      // Create runtime and render
      runtimeRef.current = await pyodide.runPythonAsync(`
from trellis_playground import BrowserRuntime
BrowserRuntime(App)
`) as PyProxy;

      const renderedTree = runtimeRef.current
        .render()
        .toJs({ dict_converter: Object.fromEntries }) as SerializedElement;

      setTree(renderedTree);
      setStatus('idle');
    } catch (e) {
      setError((e as Error).message);
      setStatus('error');
    }
  }, [code]);

  // Encode code for playground URL
  const encodedCode = typeof window !== 'undefined' ? btoa(encodeURIComponent(code)) : '';
  const playgroundUrl = `/trellis/playground/#code=${encodedCode}`;

  return (
    <div className={styles.playgroundContainer}>
      <div className={styles.header}>
        {title && <span className={styles.title}>{title}</span>}
        <div className={styles.actions}>
          <button
            onClick={runCode}
            disabled={status === 'loading' || status === 'running'}
            className={styles.runButton}
          >
            {status === 'loading' ? 'Loading Pyodide...' :
             status === 'running' ? 'Running...' :
             tree ? 'Re-run' : 'Run'}
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

      {(tree || error) && (
        <div className={styles.preview}>
          <div className={styles.previewHeader}>Preview</div>
          <div className={styles.previewContent}>
            {error ? (
              <div className={styles.error}>{error}</div>
            ) : tree ? (
              renderNode(tree, { onEvent: handleEvent, getWidget }, 'root')
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
