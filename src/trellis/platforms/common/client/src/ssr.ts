/**
 * Shared SSR utilities for all platform entry points.
 *
 * Provides the dehydration data type, global window declaration,
 * and the mountApp helper that handles hydration vs client-side rendering.
 */

import { createRoot, hydrateRoot } from "react-dom/client";
import { store } from "@trellis/trellis-core/core";
import type { Patch } from "@trellis/trellis-core/types";

/** SSR dehydration data embedded in the page by the server or build step. */
export interface TrellisSSRData {
  serverVersion: string;
  sessionId?: string;
  patches: Patch[];
}

declare global {
  interface Window {
    __TRELLIS_SSR__?: TrellisSSRData;
  }
}

/** Read SSR dehydration data from the page, if present. */
export const ssrData: TrellisSSRData | undefined = window.__TRELLIS_SSR__;

/**
 * Mount a React app with SSR hydration support.
 *
 * If SSR data is present, pre-populates the store with patches from the
 * server/build-time render and hydrates the existing DOM. Otherwise,
 * creates a fresh React root for client-side rendering.
 */
export function mountApp(
  container: HTMLElement,
  app: React.ReactElement
): void {
  if (ssrData) {
    store.applyPatches(ssrData.patches);
    hydrateRoot(container, app);
  } else {
    createRoot(container).render(app);
  }
}
