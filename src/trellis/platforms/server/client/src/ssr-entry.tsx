/**
 * Bun SSR worker entry point.
 *
 * Starts a Bun HTTP server on a Unix socket that accepts serialized element
 * trees and returns rendered HTML using React's renderToString.
 */

// Polyfill for Symbol.dispose
(Symbol as any).dispose ??= Symbol("Symbol.dispose");
(Symbol as any).asyncDispose ??= Symbol("Symbol.asyncDispose");

import { initRegistry } from "@trellis/_registry";
initRegistry();

import React from "react";
import { renderToString } from "react-dom/server";
import { renderNode } from "@trellis/trellis-core/core";
import { getWidget } from "@trellis/trellis-core/widgets/index";
import type { SerializedElement } from "@trellis/trellis-core/types";

const socketPath = process.env.TRELLIS_SSR_SOCKET;
if (!socketPath) {
  console.error("TRELLIS_SSR_SOCKET env var is required");
  process.exit(1);
}

/** No-op event handler — SSR doesn't process events. */
function noop(_callbackId: string, _args: unknown[]): void {}

Bun.serve({
  unix: socketPath,
  async fetch(req: Request): Promise<Response> {
    const url = new URL(req.url, "http://localhost");

    if (url.pathname === "/health") {
      return new Response("ok");
    }

    if (url.pathname === "/render" && req.method === "POST") {
      try {
        const tree = (await req.json()) as SerializedElement;
        const element = renderNode(tree, { onEvent: noop, getWidget });
        const html = renderToString(element);
        return new Response(html, {
          headers: { "Content-Type": "text/html" },
        });
      } catch (err) {
        console.error("SSR render error:", err);
        return new Response(
          JSON.stringify({ error: String(err) }),
          { status: 500, headers: { "Content-Type": "application/json" } }
        );
      }
    }

    return new Response("Not Found", { status: 404 });
  },
});

console.log(`SSR worker listening on ${socketPath}`);
