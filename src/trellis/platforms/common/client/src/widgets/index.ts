/** Widget registry for mapping component names to React components. */

import React from "react";
import { CompositionComponent } from "./CompositionComponent";

// Registry maps component type names to React components
const widgetRegistry: Record<string, React.ComponentType<any>> = {
  CompositionComponent,
};

export function getWidget(
  typeName: string
): React.ComponentType<any> | undefined {
  return widgetRegistry[typeName];
}

export function registerWidget(
  name: string,
  component: React.ComponentType<any>
): void {
  widgetRegistry[name] = component;
}
