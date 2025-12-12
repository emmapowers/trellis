/** Widget registry for mapping component names to React components. */

import React from "react";
import { Column } from "./Column";
import { Row } from "./Row";
import { Label } from "./Label";
import { Button } from "./Button";
import { Slider } from "./Slider";
import { FunctionalComponent } from "./FunctionalComponent";

// Registry maps component type names to React components
const widgetRegistry: Record<string, React.ComponentType<any>> = {
  Column,
  Row,
  Label,
  Button,
  Slider,
  FunctionalComponent,
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

export { Column, Row, Label, Button, Slider, FunctionalComponent };
