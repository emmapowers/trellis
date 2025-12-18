/** Widget registry for mapping component names to React components. */

import React from "react";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { Card } from "./Card";
import { Checkbox } from "./Checkbox";
import { Column } from "./Column";
import { CompositionComponent } from "./CompositionComponent";
import { Divider } from "./Divider";
import { Heading } from "./Heading";
import { Label } from "./Label";
import { NumberInput } from "./NumberInput";
import { ProgressBar } from "./ProgressBar";
import { Row } from "./Row";
import { Select } from "./Select";
import { Slider } from "./Slider";
import { StatusIndicator } from "./StatusIndicator";
import { Table } from "./Table";
import { TextInput } from "./TextInput";
import { Tooltip } from "./Tooltip";

// Registry maps component type names to React components
const widgetRegistry: Record<string, React.ComponentType<any>> = {
  Badge,
  Button,
  Card,
  Checkbox,
  Column,
  CompositionComponent,
  Divider,
  Heading,
  Label,
  NumberInput,
  ProgressBar,
  Row,
  Select,
  Slider,
  StatusIndicator,
  Table,
  TextInput,
  Tooltip,
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
  Badge,
  Button,
  Card,
  Checkbox,
  Column,
  CompositionComponent,
  Divider,
  Heading,
  Label,
  NumberInput,
  ProgressBar,
  Row,
  Select,
  Slider,
  StatusIndicator,
  Table,
  TextInput,
  Tooltip,
};
