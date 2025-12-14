/** Generic wrapper for Python CompositionComponents.
 *
 * CompositionComponents are Python-only organizational components that have no
 * specific React implementation. This wrapper simply renders their children
 * while providing a data attribute for debugging purposes.
 */

import React from "react";

interface CompositionComponentProps {
  /** Python component name for debugging */
  name?: string;
  children?: React.ReactNode;
}

export function CompositionComponent({
  name,
  children,
}: CompositionComponentProps): React.ReactElement {
  // Render children in a span with display:contents to be invisible in the DOM
  // while providing a data attribute for debugging tools
  return (
    <span data-trellis-component={name} style={{ display: "contents" }}>
      {children}
    </span>
  );
}
