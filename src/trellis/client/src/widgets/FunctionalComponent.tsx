/** Generic wrapper for Python FunctionalComponents.
 *
 * FunctionalComponents are Python-only organizational components that have no
 * specific React implementation. This wrapper simply renders their children
 * while providing a data attribute for debugging purposes.
 */

import React from "react";

interface FunctionalComponentProps {
  /** Python component name for debugging */
  name?: string;
  children?: React.ReactNode;
}

export function FunctionalComponent({
  name,
  children,
}: FunctionalComponentProps): React.ReactElement {
  // Render children in a fragment with a data attribute for debugging
  // Using a span with display:contents to be invisible in the DOM while
  // providing a hook for debugging tools
  return (
    <span data-trellis-component={name} style={{ display: "contents" }}>
      {children}
    </span>
  );
}
