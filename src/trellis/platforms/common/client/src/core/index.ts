/** Core tree rendering - shared between server client and playground. */

// Type-only exports (erased at runtime)
export type { SerializedElement, CallbackRef, EventHandler } from "./types";
export type { WidgetComponent, WidgetRegistry } from "./renderTree";
export type { NodeData } from "./store";

// Value exports (exist at runtime)
export { ElementKind, isCallbackRef } from "./types";
export { applyCompiledStyleProps, renderNode, processProps, toReactDomProps } from "./renderTree";
export { store, useNode, useRootId, TrellisStore } from "./store";
