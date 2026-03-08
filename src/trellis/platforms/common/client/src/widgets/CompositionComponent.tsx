/** Generic wrapper for Python CompositionComponents.
 *
 * CompositionComponents are Python-only organizational components that have no
 * specific React implementation. This wrapper renders their children as a
 * React Fragment (no DOM node), with a dynamically-named component so the
 * Python component name appears in React DevTools as `Trellis(Name)`.
 *
 * Previous versions used a `<span style="display: contents">` wrapper with a
 * `data-trellis-component` attribute for debugging. That injected a real DOM
 * node which broke CSS child selectors like `& > * + *` — the selector matched
 * the invisible span instead of the actual children, and margin/padding
 * applied to a `display: contents` element has no visual effect.
 */

import React from "react";

interface CompositionComponentProps {
  /** Python component name for debugging */
  name?: string;
  children?: React.ReactNode;
}

const cache = new Map<string, React.FC<{ children?: React.ReactNode }>>();

function getNamedWrapper(name: string): React.FC<{ children?: React.ReactNode }> {
  let wrapper = cache.get(name);
  if (!wrapper) {
    wrapper = ({ children }: { children?: React.ReactNode }) => <>{children}</>;
    wrapper.displayName = `Trellis(${name})`;
    cache.set(name, wrapper);
  }
  return wrapper;
}

export function CompositionComponent({
  name,
  children,
}: CompositionComponentProps): React.ReactElement {
  const Wrapper = getNamedWrapper(name ?? "Anonymous");
  return <Wrapper>{children}</Wrapper>;
}
