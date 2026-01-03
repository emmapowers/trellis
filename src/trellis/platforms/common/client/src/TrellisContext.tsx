/** React contexts for Trellis components. */

import { createContext, useContext } from "react";
import { TrellisClient } from "./TrellisClient";

// =============================================================================
// TrellisClient context
// =============================================================================

export const TrellisContext = createContext<TrellisClient | null>(null);

/** Hook to access the TrellisClient from any component. */
export function useTrellisClient(): TrellisClient {
  const client = useContext(TrellisContext);
  if (!client) {
    throw new Error(
      "useTrellisClient must be used within a TrellisContext.Provider"
    );
  }
  return client;
}

// =============================================================================
// Host theme mode context (for browser extension use)
// =============================================================================

export type HostThemeMode = "system" | "light" | "dark" | undefined;

/**
 * Context for host-controlled theme mode.
 *
 * When Trellis is embedded in a host application (via TrellisApp React component),
 * the host can control the theme mode. This context passes the host's theme mode
 * to ThemeProvider, which invokes on_theme_mode_change when it changes.
 */
export const HostThemeModeContext = createContext<HostThemeMode>(undefined);

/** Hook to access the host-controlled theme mode. */
export function useHostThemeMode(): HostThemeMode {
  return useContext(HostThemeModeContext);
}
