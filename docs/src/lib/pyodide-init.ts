/**
 * Shared Pyodide initialization for Trellis playground and inline examples.
 *
 * This module handles loading Pyodide and installing the trellis wheel,
 * shared between the full playground and inline TrellisPlayground component.
 */

// Pyodide types
export interface PyodideInterface {
  loadPackage(packages: string | string[]): Promise<void>;
  pyimport(name: string): PyProxy;
  runPythonAsync(code: string): Promise<unknown>;
}

export interface PyProxy {
  install(pkg: string): Promise<void>;
  toJs(options?: { dict_converter: typeof Object.fromEntries }): unknown;
  render(): PyProxy;
  handle_event(callbackId: string): PyProxy;
}

// Global Pyodide instance (shared across all playground instances on the page)
let pyodidePromise: Promise<PyodideInterface> | null = null;

declare const loadPyodide: () => Promise<PyodideInterface>;

// Pyodide version - must match index.html in playground
const PYODIDE_VERSION = '0.29.0';
const PYODIDE_CDN = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.js`;

/**
 * Load the Pyodide script from CDN if not already loaded.
 */
async function loadPyodideScript(): Promise<void> {
  if (typeof loadPyodide !== 'undefined') {
    return; // Already loaded
  }

  await new Promise<void>((resolve, reject) => {
    const script = document.createElement('script');
    script.src = PYODIDE_CDN;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Pyodide'));
    document.head.appendChild(script);
  });
}

/**
 * Wheel sources to try, in order of preference.
 * The wheel must be built and copied to docs/static/ before this will work.
 */
const WHEEL_SOURCES = [
  '/trellis/trellis-0.1.0-py3-none-any.whl',  // Docusaurus (GitHub Pages or local)
  '../trellis-0.1.0-py3-none-any.whl',         // Relative path (for playground)
  'https://emmapowers.github.io/trellis/trellis-0.1.0-py3-none-any.whl',  // Fallback
];

/**
 * Initialize Pyodide with all required packages for Trellis.
 *
 * This function is idempotent - calling it multiple times returns the same
 * Pyodide instance.
 *
 * @param onStatus - Optional callback for status updates
 * @returns The initialized Pyodide instance
 */
export async function initPyodide(
  onStatus?: (status: string) => void
): Promise<PyodideInterface> {
  if (pyodidePromise) return pyodidePromise;

  const updateStatus = onStatus || (() => {});

  pyodidePromise = (async () => {
    updateStatus('Loading Pyodide...');
    await loadPyodideScript();

    const pyodide = await loadPyodide();

    updateStatus('Installing packages...');
    // Load packages built into Pyodide
    await pyodide.loadPackage(['micropip', 'msgspec', 'pygments']);

    // Install rich from PyPI (pure Python, works in Pyodide)
    // pygments is already loaded above, so rich's dependency is satisfied
    const micropip = pyodide.pyimport('micropip');
    await micropip.install('rich');

    updateStatus('Installing Trellis...');
    // Install trellis wheel - try multiple sources
    // deps=False because server dependencies (uvicorn, fastapi, httpx) don't work in Pyodide
    let installed = false;
    for (const wheelUrl of WHEEL_SOURCES) {
      try {
        console.log(`Trying to install trellis from ${wheelUrl}...`);
        // Call micropip.install via Python to use deps=False correctly
        await pyodide.runPythonAsync(`
import micropip
await micropip.install("${wheelUrl}", deps=False)
`);
        console.log(`Successfully installed from ${wheelUrl}`);
        installed = true;
        break;
      } catch (e) {
        console.log(`Failed to install from ${wheelUrl}:`, (e as Error).message);
      }
    }

    if (!installed) {
      throw new Error(
        'Could not install trellis wheel. For local development, run: pixi run build-wheel && pixi run copy-wheel-to-docs'
      );
    }

    updateStatus('Ready');
    return pyodide;
  })();

  return pyodidePromise;
}

/**
 * Check if Pyodide is already initialized.
 */
export function isPyodideReady(): boolean {
  return pyodidePromise !== null;
}
