/** Widget registry for mapping component names to React components. */

import React from "react";
import { Button } from "./Button";
import { Card } from "./Card";
import { Checkbox } from "./Checkbox";
import { Column } from "./Column";
import { CompositionComponent } from "./CompositionComponent";
import { Divider } from "./Divider";
import { Label } from "./Label";
import { NumberInput } from "./NumberInput";
import { Row } from "./Row";
import { Select } from "./Select";
import { Slider } from "./Slider";
import { TextInput } from "./TextInput";

// Registry maps component type names to React components
const widgetRegistry: Record<string, React.ComponentType<any>> = {
  Button,
  Card,
  Checkbox,
  Column,
  CompositionComponent,
  Divider,
  Label,
  NumberInput,
  Row,
  Select,
  Slider,
  TextInput,
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

export {
  Button,
  Card,
  Checkbox,
  Column,
  CompositionComponent,
  Divider,
  Label,
  NumberInput,
  Row,
  Select,
  Slider,
  TextInput,
};
