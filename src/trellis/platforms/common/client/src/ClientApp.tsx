/**
 * Shared App component for server and desktop platforms.
 *
 * Wraps a TrellisClient with connection lifecycle management and
 * renders TrellisRoot. Platform entry points provide their specific
 * client instance via the createClient prop.
 */

import React, { useEffect, useState, useMemo } from "react";
import { TrellisRoot } from "@trellis/trellis-core/TrellisRoot";
import type { TrellisClient } from "@trellis/trellis-core/TrellisClient";

export interface ClientAppProps {
  /** Factory that creates the platform-specific client. Called once. */
  createClient: (onError: (error: string) => void) => TrellisClient;
  /** Optional extra effects to run on mount (e.g. external link delegation). */
  onMount?: () => (() => void) | void;
}

export function ClientApp({
  createClient,
  onMount,
}: ClientAppProps): React.ReactElement {
  const [error, setError] = useState<string | null>(null);

  const client = useMemo(() => createClient(setError), [createClient]);

  useEffect(() => {
    client.connect().catch((err) => {
      console.error("Failed to connect:", err);
    });
    return () => client.disconnect();
  }, [client]);

  useEffect(() => {
    if (onMount) {
      return onMount() ?? undefined;
    }
  }, [onMount]);

  return <TrellisRoot client={client} error={error} />;
}
