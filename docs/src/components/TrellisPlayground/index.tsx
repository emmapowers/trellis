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
// Counter for generating unique IDs per component instance
let instanceCounter = 0;

export default function TrellisPlayground({ code, title }: TrellisPlaygroundProps): JSX.Element {
  const [status, setStatus] = useState<'idle' | 'loading' | 'running' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [tree, setTree] = useState<SerializedElement | null>(null);
  const runtimeRef = useRef<PyProxy | null>(null);
  const pyodideRef = useRef<PyodideInterface | null>(null);
  // Unique ID for this component instance to isolate callbacks
  const instanceIdRef = useRef<string>(`trellis_${++instanceCounter}`);

  const handleEvent = useCallback((cbId: string, args?: unknown[]) => {
    if (!runtimeRef.current) return;
    try {
      // Post event to Python - render callback will update tree via setTree
      runtimeRef.current.post_event(cbId, args ?? []);
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

      const instanceId = instanceIdRef.current;

      // Execute user code and capture App in a unique variable
      await pyodide.runPythonAsync(`
${code}

# Capture App in instance-specific variable before it gets overwritten
${instanceId}_app = App
`);

      // Register JS callbacks with unique module name to isolate from other instances
      const callbacksModuleName = `${instanceId}_callbacks`;
      const jsCallbacks = {
        render: (treeProxy: PyProxy) => {
          const newTree = treeProxy.toJs({ dict_converter: Object.fromEntries }) as SerializedElement;
          setTree(newTree);
        },
        error: (errorMsg: string) => {
          setError(errorMsg);
          setStatus('error');
        }
      };
      pyodide.registerJsModule(callbacksModuleName, jsCallbacks);

      // Create runtime and start message loop in background
      runtimeRef.current = await pyodide.runPythonAsync(`
import asyncio

# Import callbacks module dynamically using unique name
_callbacks = __import__("${callbacksModuleName}")

from trellis_playground import PlaygroundMessageHandler

${instanceId}_handler = PlaygroundMessageHandler(${instanceId}_app)
${instanceId}_handler.set_render_callback(_callbacks.render)
${instanceId}_handler.set_error_callback(_callbacks.error)

# Start the message loop in the background
asyncio.ensure_future(${instanceId}_handler.run())

${instanceId}_handler
`) as PyProxy;

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
