/**
 * Renders a serialized element tree as React components.
 *
 * Uses the ID-keyed store for efficient incremental updates.
 * Each NodeRenderer subscribes only to its own node, so only
 * affected nodes re-render when patches arrive.
 */

import React, { useEffect, useMemo, useRef } from "react";
import {
  applyCompiledStyleProps,
  useNode,
  useRootId,
  NodeData,
  processProps,
  toReactDomProps,
  ElementKind,
  store,
} from "./core";
import { KeyBindingRegistry } from "./core/keyBindingRegistry";
import {
  isTextInput,
  matchesKeyFilter,
  SerializedKeyBinding,
  SerializedSequenceBinding,
} from "./core/keyFilters";
import { KeyState } from "./core/keyState";
import { getWidget } from "./widgets";
import { useTrellisClient } from "./TrellisContext";
import { TrellisClient } from "./TrellisClient";

/**
 * Shared key state and binding registry, created once per TreeRenderer.
 */
function useKeyBindingRegistry(client: TrellisClient) {
  const ref = useRef<{ keyState: KeyState; registry: KeyBindingRegistry } | null>(null);
  if (!ref.current) {
    const keyState = new KeyState();
    const registry = new KeyBindingRegistry(
      keyState,
      (callbackId, requestId, args) =>
        client.sendKeyEvent(callbackId, requestId, args)
    );
    ref.current = { keyState, registry };
  }

  useEffect(() => {
    return () => {
      ref.current?.registry.dispose();
      ref.current?.keyState.dispose();
    };
  }, []);

  return ref.current;
}

/**
 * Root component that renders the Trellis tree.
 * Subscribes to the root ID and renders the tree when available.
 */
export function TreeRenderer(): React.ReactElement | null {
  const rootId = useRootId();
  const client = useTrellisClient();
  const { keyState, registry } = useKeyBindingRegistry(client);

  if (!rootId) {
    return null;
  }

  return (
    <KeyBindingContext.Provider value={{ keyState, registry, client }}>
      <NodeRenderer id={rootId} />
    </KeyBindingContext.Provider>
  );
}

interface KeyBindingContextValue {
  keyState: KeyState;
  registry: KeyBindingRegistry;
  client: TrellisClient;
}

const KeyBindingContext = React.createContext<KeyBindingContextValue | null>(null);

interface NodeRendererProps {
  id: string;
}

/**
 * Wrapper that exposes the underlying component type for parent inspection.
 * Used by compound components like Menu that need to identify child types.
 */
interface ChildWrapperProps {
  __componentType__: string;
  __componentProps__: Record<string, unknown>;
  children: React.ReactNode;
}

function ChildWrapper({ children }: ChildWrapperProps): React.ReactElement {
  return <>{children}</>;
}

// Expose type for parent component inspection
ChildWrapper.__isChildWrapper__ = true;

/**
 * Renders a single node by ID.
 * Subscribes to that node's data and only re-renders when it changes.
 */
const NodeRenderer = React.memo(function NodeRenderer({
  id,
}: NodeRendererProps): React.ReactElement | null {
  const node = useNode(id);
  const client = useTrellisClient();
  const keyCtx = React.useContext(KeyBindingContext);

  if (!node) {
    return null;
  }

  // Process props (transforms callback refs to functions)
  const processedProps = applyCompiledStyleProps(
    processProps(node.props, (callbackId, args) => client.sendEvent(callbackId, args))
  );

  // Recursively render children by ID, wrapped with type metadata for compound components
  const children = node.childIds.map((childId) => {
    const childNode = store.getNode(childId);
    const componentType = childNode?.type ?? "Unknown";
    // Process props (convert callback refs to functions) for compound component inspection
    const componentProps = childNode
      ? applyCompiledStyleProps(
          processProps(childNode.props, (callbackId, args) =>
            client.sendEvent(callbackId, args)
          )
        )
      : {};
    return (
      <ChildWrapper
        key={childId}
        __componentType__={componentType}
        __componentProps__={componentProps}
      >
        <NodeRenderer id={childId} />
      </ChildWrapper>
    );
  });

  let rendered = renderNodeElement(node, processedProps, children, id);

  // Wrap with on_key handler div if __key_filters__ present
  const rawKeyFilters = node.props.__key_filters__ as unknown[] | undefined;
  if (rawKeyFilters && rawKeyFilters.length > 0 && keyCtx) {
    rendered = (
      <OnKeyWrapper
        keyFilters={rawKeyFilters}
        keyState={keyCtx.keyState}
        client={keyCtx.client}
      >
        {rendered}
      </OnKeyWrapper>
    );
  }

  // Register/unregister global key filters with the binding registry
  const rawGlobalFilters = node.props.__global_key_filters__ as unknown[] | undefined;
  if (rawGlobalFilters && keyCtx) {
    rendered = (
      <GlobalKeyRegistrar
        elementId={id}
        globalFilters={rawGlobalFilters}
        registry={keyCtx.registry}
      >
        {rendered}
      </GlobalKeyRegistrar>
    );
  }

  return rendered;
});

/**
 * Wrapper div for focus-scoped .on_key() handlers.
 * Uses display:contents so it doesn't affect layout.
 */
function OnKeyWrapper({
  keyFilters,
  keyState,
  client,
  children,
}: {
  keyFilters: unknown[];
  keyState: KeyState;
  client: TrellisClient;
  children: React.ReactElement;
}): React.ReactElement {
  const handler = useMemo(() => {
    return createOnKeyHandler(keyFilters, keyState, client);
  }, [keyFilters, keyState, client]);

  return (
    <div style={{ display: "contents" }} onKeyDown={handler} onKeyUp={handler}>
      {children}
    </div>
  );
}

function createOnKeyHandler(
  rawBindings: unknown[],
  keyState: KeyState,
  client: TrellisClient,
): (event: React.KeyboardEvent) => void {
  return (event: React.KeyboardEvent) => {
    const native = event.nativeEvent;
    // Skip re-dispatched events
    if ((native as any).__trellis_redispatch__) return;
    if (native.isComposing) return;

    const eventType = native.type as "keydown" | "keyup";

    for (const raw of rawBindings) {
      const entry = raw as Record<string, unknown>;
      if ((entry.event_type as string) !== eventType) continue;
      if (
        (entry.ignore_in_inputs as boolean) &&
        isTextInput(document.activeElement)
      ) continue;

      // Sequence binding
      if (entry.sequence) {
        const seq = entry.sequence as { steps: any[]; timeout_ms: number };
        const handlerRef = entry.handler as { __callback__: string };
        const bindingId = `onkey-seq-${handlerRef.__callback__}`;
        const complete = keyState.advanceSequence(
          bindingId,
          seq.steps,
          seq.timeout_ms,
          native
        );
        if (complete) {
          event.preventDefault();
          event.stopPropagation();
          fireOnKeyEvent(client, handlerRef.__callback__, native, event);
          return;
        }
        continue;
      }

      // Single filter binding
      const filter = entry.filter as any;
      if (!filter || !matchesKeyFilter(native, filter)) continue;

      const handlerRef = entry.handler as { __callback__: string };
      const bindingId = `onkey-${handlerRef.__callback__}`;
      const shouldFire = keyState.shouldFire(
        bindingId,
        entry.require_reset as boolean,
        native
      );

      // Always preventDefault for matched bindings
      event.preventDefault();
      event.stopPropagation();

      if (!shouldFire) return;

      fireOnKeyEvent(client, handlerRef.__callback__, native, event);
      return;
    }
  };
}

async function fireOnKeyEvent(
  client: TrellisClient,
  callbackId: string,
  native: KeyboardEvent,
  reactEvent: React.KeyboardEvent
): Promise<void> {
  // Capture target before await — React recycles synthetic events.
  const target = reactEvent.currentTarget;
  const requestId = crypto.randomUUID();
  const serialized = {
    type: native.type,
    key: native.key,
    code: native.code,
    alt_key: native.altKey,
    ctrl_key: native.ctrlKey,
    shift_key: native.shiftKey,
    meta_key: native.metaKey,
    repeat: native.repeat,
    timestamp: native.timeStamp,
  };
  const handled = await client.sendKeyEvent(callbackId, requestId, [serialized]);

  if (!handled) {
    // Re-dispatch event from wrapper div so DOM bubbling resumes to parent
    const clone = new KeyboardEvent(native.type, native);
    (clone as any).__trellis_redispatch__ = true;
    target?.dispatchEvent(clone);
  }
}

/**
 * Registers/unregisters global key filters with the KeyBindingRegistry.
 */
function GlobalKeyRegistrar({
  elementId,
  globalFilters,
  registry,
  children,
}: {
  elementId: string;
  globalFilters: unknown[];
  registry: KeyBindingRegistry;
  children: React.ReactElement;
}): React.ReactElement {
  useEffect(() => {
    registry.updateElement(elementId, globalFilters);
    return () => {
      registry.removeElement(elementId);
    };
  }, [elementId, globalFilters, registry]);

  return children;
}

/**
 * Render a node to a React element based on its kind.
 */
function renderNodeElement(
  node: NodeData,
  processedProps: Record<string, unknown>,
  children: React.ReactElement[],
  key: string
): React.ReactElement {
  // Plain text nodes
  if (node.kind === ElementKind.TEXT) {
    const textContent = (node.props as { _text?: string })._text ?? "";
    return <React.Fragment key={key}>{textContent}</React.Fragment>;
  }

  // Native HTML/JSX elements (div, span, p, etc.)
  if (node.kind === ElementKind.JSX_ELEMENT) {
    // HTML elements can have a _text prop containing inline text content.
    const { _text, ...htmlProps } = processedProps as Record<string, unknown> & {
      _text?: string;
    };
    const domProps = toReactDomProps(htmlProps);
    const allChildren = _text != null ? [_text, ...children] : children;
    return React.createElement(node.type, { ...domProps, key }, ...allChildren);
  }

  // Custom components via widget registry
  const Component = getWidget(node.type);

  if (!Component) {
    // Unknown component type - render a warning placeholder
    return (
      <div
        key={key}
        style={{
          color: "red",
          border: "1px solid red",
          padding: "4px",
          margin: "2px",
          fontSize: "12px",
        }}
      >
        Unknown component: {node.type}
      </div>
    );
  }

  // Pass props and children to the component
  // __name__ carries the Python component name for debugging
  return (
    <Component key={key} {...processedProps} __name__={node.name}>
      {children}
    </Component>
  );
}
