"""Built-in widget components for Trellis.

Provides basic UI building blocks that map to React components on the client.
"""

# Re-export theme tokens for styling convenience
from trellis.app import ThemeTokens, theme
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
from trellis.widgets.icons import Icon, IconName
from trellis.widgets.layout import Card, Column, Row
from trellis.widgets.navigation import Breadcrumb, Tab, Tabs, Tree
from trellis.widgets.table import Table, TableColumn
from trellis.widgets.theme_switcher import ThemeSwitcher

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
    "IconName",
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
    "TableColumn",
    "Tabs",
    "Tag",
    "TextInput",
    "ThemeSwitcher",
    "ThemeTokens",
    "TimeSeriesChart",
    "Toolbar",
    "Tooltip",
    "Tree",
    "theme",
]
