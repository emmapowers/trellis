/** React context for accessing the TrellisClient from any component. */

import { createContext, useContext } from "react";
import { TrellisClient } from "./TrellisClient";

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
