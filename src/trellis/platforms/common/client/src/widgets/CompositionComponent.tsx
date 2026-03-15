/** Generic wrapper for Python CompositionComponents.
 *
 * CompositionComponents are Python-only organizational components that have no
 * specific React implementation. This wrapper renders their children as a
 * React Fragment (no DOM node), with a dynamically-named component so the
 * Python component name appears in React DevTools as `Trellis(Name)`.
 *
 * A Fragment is used instead of a wrapper DOM element to avoid breaking CSS
 * child selectors like `& > * + *` in parent layouts.
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
