/** Main entry point for Trellis server client. */

import "@trellis/trellis-core/init";

import React from "react";
import { ServerTrellisClient } from "@trellis/trellis-server/client/src/TrellisClient";
import { ClientApp } from "@trellis/trellis-core/ClientApp";
import { ssrData, mountApp } from "@trellis/trellis-core/ssr";

function App() {
  return (
    <ClientApp
      createClient={(onError) =>
        new ServerTrellisClient(
          { onError },
          undefined,
          ssrData?.sessionId
        )
      }
    />
  );
}

mountApp(document.getElementById("root")!, <App />);
