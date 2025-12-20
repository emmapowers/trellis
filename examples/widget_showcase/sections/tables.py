"""Table section of the widget showcase."""

from trellis import component
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


# Stock data for the showcase table (prices as of Dec 2024)
STOCKS = [
    {
        "_key": "AAPL",
        "company": "Apple Inc.",
        "ticker": "AAPL",
        "price": 248.13,
        "change": 2.35,
        "change_pct": 0.96,
        "history": [
            221, 218, 223, 220, 225, 222, 219, 226, 231, 228,
            233, 229, 235, 232, 238, 241, 237, 244, 240, 248,
        ],
    },
    {
        "_key": "WMT",
        "company": "Walmart Inc.",
        "ticker": "WMT",
        "price": 91.36,
        "change": 0.45,
        "change_pct": 0.50,
        "history": [
            65, 64, 67, 66, 69, 68, 71, 70, 73, 72,
            75, 74, 78, 76, 80, 82, 85, 87, 90, 91,
        ],
    },
    {
        "_key": "KO",
        "company": "Coca-Cola Co.",
        "ticker": "KO",
        "price": 62.85,
        "change": -0.18,
        "change_pct": -0.29,
        "history": [
            59, 60, 58, 61, 60, 62, 61, 63, 64, 62,
            65, 64, 66, 65, 67, 66, 64, 63, 64, 63,
        ],
    },
    {
        "_key": "AMZN",
        "company": "Amazon.com Inc.",
        "ticker": "AMZN",
        "price": 225.94,
        "change": -3.10,
        "change_pct": -1.35,
        "history": [
            186, 191, 188, 195, 192, 199, 204, 210, 215, 220,
            225, 230, 235, 232, 228, 233, 229, 225, 228, 226,
        ],
    },
]


def TickerCell(row: dict) -> None:
    """Ticker symbol in bold monospace."""
    w.Label(text=row["ticker"], bold=True, style={"fontFamily": "monospace"})


def PriceCell(row: dict) -> None:
    """Current price with change indicator."""
    price = row["price"]
    change = row["change"]
    change_pct = row["change_pct"]
    is_positive = change >= 0

    color = "#16a34a" if is_positive else "#dc2626"
    icon = w.IconName.TRENDING_UP if is_positive else w.IconName.TRENDING_DOWN
    sign = "+" if is_positive else ""

    with w.Column(gap=2, align="end"):
        w.Label(text=f"${price:.2f}", bold=True)
        with w.Row(gap=4, align="center"):
            w.Icon(name=icon, size=14, color=color)
            w.Label(
                text=f"{sign}{change:.2f} ({sign}{change_pct:.2f}%)",
                color=color,
                size="sm",
            )


def HistoryCell(row: dict) -> None:
    """Sparkline showing price history."""
    history = row["history"]
    # Color based on overall trend
    color = "#16a34a" if history[-1] >= history[0] else "#dc2626"
    w.Sparkline(data=history, width=100, height=28, color=color)


def ActionsCell(row: dict) -> None:
    """Action buttons."""
    with w.Row(gap=8, justify="end"):
        w.Button(text="Buy", size="sm", variant="primary")
        w.Button(text="Watch", size="sm", variant="outline")


@example("Stock Watchlist", includes=["STOCKS", TickerCell, PriceCell, HistoryCell, ActionsCell])
def StockWatchlist() -> None:
    """Full-featured table with custom cell rendering, icons, and sparklines."""
    w.Table(
        columns=[
            w.TableColumn(name="company", label="Company", width="180px"),
            w.TableColumn(name="ticker", label="Ticker", render=TickerCell),
            w.TableColumn(
                name="price", label="Price", align="right", render=PriceCell
            ),
            w.TableColumn(name="history", label="History", render=HistoryCell),
            w.TableColumn(
                name="actions", label="Actions", align="right", render=ActionsCell
            ),
        ],
        data=STOCKS,
        striped=True,
        compact=False,
    )


@example("Default Table")
def DefaultTable() -> None:
    """Basic table with string columns."""
    w.Table(
        columns=["name", "status", "value"],
        data=[
            {"name": "Revenue", "status": "Active", "value": "$12,450"},
            {"name": "Users", "status": "Active", "value": "1,234"},
            {"name": "Orders", "status": "Pending", "value": "456"},
        ],
        compact=False,
    )


@example("Striped Table")
def StripedTable() -> None:
    """Table with alternating row colors."""
    w.Table(
        columns=["name", "status", "value"],
        data=[
            {"name": "Revenue", "status": "Active", "value": "$12,450"},
            {"name": "Users", "status": "Active", "value": "1,234"},
            {"name": "Orders", "status": "Pending", "value": "456"},
        ],
        striped=True,
        compact=False,
    )


@example("Compact Table")
def CompactTable() -> None:
    """Table with smaller row height."""
    w.Table(
        columns=["name", "status", "value"],
        data=[
            {"name": "Revenue", "status": "Active", "value": "$12,450"},
            {"name": "Users", "status": "Active", "value": "1,234"},
            {"name": "Orders", "status": "Pending", "value": "456"},
        ],
        compact=True,
    )


@example("Bordered Table")
def BorderedTable() -> None:
    """Table with cell borders and rounded corners."""
    w.Table(
        columns=["name", "status", "value"],
        data=[
            {"name": "Revenue", "status": "Active", "value": "$12,450"},
            {"name": "Users", "status": "Active", "value": "1,234"},
            {"name": "Orders", "status": "Pending", "value": "456"},
        ],
        bordered=True,
        compact=False,
    )


@example("Table with Column Config")
def TableWithColumnConfig() -> None:
    """Table using TableColumn for alignment and width."""
    w.Table(
        columns=[
            w.TableColumn(name="name", label="Name", width="120px"),
            w.TableColumn(name="status", label="Status", align="center"),
            w.TableColumn(name="value", label="Value", align="right"),
        ],
        data=[
            {"name": "Revenue", "status": "Active", "value": "$12,450"},
            {"name": "Users", "status": "Active", "value": "1,234"},
            {"name": "Orders", "status": "Pending", "value": "456"},
        ],
    )


@example("Table with Icons")
def TableWithIcons() -> None:
    """Table with icons in column headers."""
    w.Table(
        columns=[
            w.TableColumn(name="name", label="Name", icon=w.IconName.TAG),
            w.TableColumn(name="status", label="Status", icon=w.IconName.ACTIVITY, align="center"),
            w.TableColumn(name="value", label="Value", icon=w.IconName.HASH, align="right"),
        ],
        data=[
            {"name": "Revenue", "status": "Active", "value": "$12,450"},
            {"name": "Users", "status": "Active", "value": "1,234"},
            {"name": "Orders", "status": "Pending", "value": "456"},
        ],
    )


def StatusCell(row: dict) -> None:
    """Custom status cell with icon."""
    status = row["status"]
    if status == "Active":
        icon = w.IconName.CHECK_CIRCLE
        color = "#16a34a"
    else:
        icon = w.IconName.CLOCK
        color = "#d97706"
    with w.Row(gap=4, align="center"):
        w.Icon(name=icon, size=14, color=color)
        w.Label(text=status, color=color)


@example("Custom Cell Rendering", includes=[StatusCell])
def CustomCellRendering() -> None:
    """Table with custom status cell rendering."""
    w.Table(
        columns=[
            w.TableColumn(name="name", label="Name"),
            w.TableColumn(name="status", label="Status", render=StatusCell),
            w.TableColumn(name="value", label="Value", align="right"),
        ],
        data=[
            {"_key": "revenue", "name": "Revenue", "status": "Active", "value": "$12,450"},
            {"_key": "users", "name": "Users", "status": "Active", "value": "1,234"},
            {"_key": "orders", "name": "Orders", "status": "Pending", "value": "456"},
        ],
    )


@component
def TableSection() -> None:
    """Showcase table widget."""
    with w.Column(gap=16):
        ExampleCard(example=StockWatchlist)
        ExampleCard(example=DefaultTable)
        ExampleCard(example=StripedTable)
        ExampleCard(example=CompactTable)
        ExampleCard(example=BorderedTable)
        ExampleCard(example=TableWithColumnConfig)
        ExampleCard(example=TableWithIcons)
        ExampleCard(example=CustomCellRendering)
