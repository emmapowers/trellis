/** Widget registry for mapping component names to React components. */

import React from "react";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { Callout } from "./Callout";
import { Card } from "./Card";
import { Checkbox } from "./Checkbox";
import { Collapsible } from "./Collapsible";
import { Column } from "./Column";
import { CompositionComponent } from "./CompositionComponent";
import { Divider } from "./Divider";
import { Heading } from "./Heading";
import { Icon } from "./Icon";
import { Label } from "./Label";
import { LineChart } from "./LineChart";
import { Menu, MenuItem, MenuDivider } from "./Menu";
import { AreaChart } from "./AreaChart";
import { BarChart } from "./BarChart";
import { PieChart } from "./PieChart";
import { Sparkline } from "./Sparkline";
import { Stat } from "./Stat";
import { Tabs, Tab } from "./Tabs";
import { Tag } from "./Tag";
import { TimeSeriesChart } from "./TimeSeriesChart";
import { Tree } from "./Tree";
import { NumberInput } from "./NumberInput";
import { ProgressBar } from "./ProgressBar";
import { Row } from "./Row";
import { Select } from "./Select";
import { Slider } from "./Slider";
import { StatusIndicator } from "./StatusIndicator";
import { TableInner, CellSlot } from "./Table";
import { TextInput } from "./TextInput";
import { ThemeProvider } from "./ThemeProvider";
import { Toolbar } from "./Toolbar";
import { Tooltip } from "./Tooltip";

// Registry maps component type names to React components
const widgetRegistry: Record<string, React.ComponentType<any>> = {
  AreaChart,
  Badge,
  BarChart,
  Button,
  Callout,
  Card,
  Checkbox,
  Collapsible,
  Column,
  CompositionComponent,
  Divider,
  Heading,
  Icon,
  Label,
  LineChart,
  Menu,
  MenuDivider,
  MenuItem,
  NumberInput,
  PieChart,
  ProgressBar,
  Row,
  Select,
  Slider,
  Sparkline,
  Stat,
  StatusIndicator,
  Tab,
  TableInner,
  CellSlot,
  Tabs,
  Tag,
  TextInput,
  ThemeProvider,
  TimeSeriesChart,
  Toolbar,
  Tooltip,
  Tree,
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
  AreaChart,
  Badge,
  BarChart,
  Button,
  Callout,
  Card,
  Checkbox,
  Collapsible,
  Column,
  CompositionComponent,
  Divider,
  Heading,
  Icon,
  Label,
  LineChart,
  Menu,
  MenuDivider,
  MenuItem,
  NumberInput,
  PieChart,
  ProgressBar,
  Row,
  Select,
  Slider,
  Sparkline,
  Stat,
  StatusIndicator,
  Tab,
  TableInner,
  CellSlot,
  Tabs,
  Tag,
  TextInput,
  ThemeProvider,
  TimeSeriesChart,
  Toolbar,
  Tooltip,
  Tree,
};
