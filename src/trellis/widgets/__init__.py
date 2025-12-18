"""Built-in widget components for Trellis.

Provides basic UI building blocks that map to React components on the client.
"""

from trellis.widgets.actions import Menu, MenuDivider, MenuItem, Toolbar
from trellis.widgets.basic import (
    Badge,
    Button,
    Checkbox,
    Divider,
    Heading,
    Label,
    NumberInput,
    ProgressBar,
    Select,
    Slider,
    StatusIndicator,
    Table,
    TextInput,
    Tooltip,
)
from trellis.widgets.charts import (
    AreaChart,
    BarChart,
    LineChart,
    PieChart,
    Sparkline,
    TimeSeriesChart,
)
from trellis.widgets.data import Stat, Tag
from trellis.widgets.feedback import Callout, Collapsible
from trellis.widgets.icons import Icon
from trellis.widgets.layout import Card, Column, Row
from trellis.widgets.navigation import Breadcrumb, Tab, Tabs, Tree

__all__ = [
    "AreaChart",
    "Badge",
    "BarChart",
    "Breadcrumb",
    "Button",
    "Callout",
    "Card",
    "Checkbox",
    "Collapsible",
    "Column",
    "Divider",
    "Heading",
    "Icon",
    "Label",
    "LineChart",
    "Menu",
    "MenuDivider",
    "MenuItem",
    "NumberInput",
    "PieChart",
    "ProgressBar",
    "Row",
    "Select",
    "Slider",
    "Sparkline",
    "Stat",
    "StatusIndicator",
    "Tab",
    "Table",
    "Tabs",
    "Tag",
    "TextInput",
    "TimeSeriesChart",
    "Toolbar",
    "Tooltip",
    "Tree",
]
