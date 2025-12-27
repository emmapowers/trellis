"""Icon widget and icon names for rendering Lucide icons.

Provides the Icon widget and strongly-typed IconName enum.

Usage:
    from trellis.widgets import Icon, IconName

    Icon(name=IconName.CHECK, size=24)
"""

from __future__ import annotations

import typing as tp
from enum import StrEnum

from trellis.core.element_node import ElementNode
from trellis.core.react_component import react_component_base
from trellis.core.style_props import Margin


class IconName(StrEnum):
    """Lucide icon names with autocomplete support.

    Icons are rendered using Lucide React on the client side.
    See https://lucide.dev/icons for the full icon reference.
    """

    # Arrows
    ARROW_UP = "arrow-up"
    ARROW_DOWN = "arrow-down"
    ARROW_LEFT = "arrow-left"
    ARROW_RIGHT = "arrow-right"
    ARROW_UP_RIGHT = "arrow-up-right"
    ARROW_DOWN_LEFT = "arrow-down-left"
    CHEVRON_UP = "chevron-up"
    CHEVRON_DOWN = "chevron-down"
    CHEVRON_LEFT = "chevron-left"
    CHEVRON_RIGHT = "chevron-right"
    CHEVRONS_UP = "chevrons-up"
    CHEVRONS_DOWN = "chevrons-down"
    CHEVRONS_LEFT = "chevrons-left"
    CHEVRONS_RIGHT = "chevrons-right"
    CORNER_DOWN_LEFT = "corner-down-left"
    CORNER_DOWN_RIGHT = "corner-down-right"
    CORNER_UP_LEFT = "corner-up-left"
    CORNER_UP_RIGHT = "corner-up-right"
    MOVE = "move"
    MOVE_HORIZONTAL = "move-horizontal"
    MOVE_VERTICAL = "move-vertical"

    # Actions
    CHECK = "check"
    X = "x"
    PLUS = "plus"
    MINUS = "minus"
    EDIT = "edit"
    EDIT_2 = "edit-2"
    EDIT_3 = "edit-3"
    TRASH = "trash"
    TRASH_2 = "trash-2"
    COPY = "copy"
    CLIPBOARD = "clipboard"
    CLIPBOARD_CHECK = "clipboard-check"
    CLIPBOARD_COPY = "clipboard-copy"
    SAVE = "save"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    REFRESH_CW = "refresh-cw"
    REFRESH_CCW = "refresh-ccw"
    ROTATE_CW = "rotate-cw"
    ROTATE_CCW = "rotate-ccw"
    SEARCH = "search"
    FILTER = "filter"
    SORT_ASC = "arrow-up-narrow-wide"
    SORT_DESC = "arrow-down-wide-narrow"
    UNDO = "undo"
    REDO = "redo"
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"
    MAXIMIZE_2 = "maximize-2"
    MINIMIZE_2 = "minimize-2"
    ZOOM_IN = "zoom-in"
    ZOOM_OUT = "zoom-out"

    # Status
    INFO = "info"
    ALERT_CIRCLE = "alert-circle"
    ALERT_TRIANGLE = "alert-triangle"
    CHECK_CIRCLE = "check-circle"
    CHECK_CIRCLE_2 = "check-circle-2"
    X_CIRCLE = "x-circle"
    HELP_CIRCLE = "help-circle"
    CLOCK = "clock"
    LOADER = "loader"
    LOADER_2 = "loader-2"
    HOURGLASS = "hourglass"
    TIMER = "timer"

    # Objects
    FILE = "file"
    FILE_TEXT = "file-text"
    FILE_CODE = "file-code"
    FILE_PLUS = "file-plus"
    FILE_MINUS = "file-minus"
    FILE_X = "file-x"
    FILES = "files"
    FOLDER = "folder"
    FOLDER_OPEN = "folder-open"
    FOLDER_PLUS = "folder-plus"
    FOLDER_MINUS = "folder-minus"
    FOLDER_X = "folder-x"
    ARCHIVE = "archive"
    BOX = "box"
    PACKAGE = "package"
    SETTINGS = "settings"
    SETTINGS_2 = "settings-2"
    SLIDERS = "sliders"
    SLIDERS_HORIZONTAL = "sliders-horizontal"
    HOME = "home"
    BUILDING = "building"
    BUILDING_2 = "building-2"
    USER = "user"
    USER_PLUS = "user-plus"
    USER_MINUS = "user-minus"
    USER_X = "user-x"
    USER_CHECK = "user-check"
    USERS = "users"
    DATABASE = "database"
    SERVER = "server"
    HARD_DRIVE = "hard-drive"
    CPU = "cpu"
    MEMORY_STICK = "memory-stick"
    TERMINAL = "terminal"
    TERMINAL_SQUARE = "terminal-square"
    CODE = "code"
    CODE_2 = "code-2"
    BRACES = "braces"
    BRACKETS = "brackets"
    HASH = "hash"
    AT_SIGN = "at-sign"

    # Charts/Data
    BAR_CHART = "bar-chart"
    BAR_CHART_2 = "bar-chart-2"
    BAR_CHART_3 = "bar-chart-3"
    BAR_CHART_4 = "bar-chart-4"
    BAR_CHART_HORIZONTAL = "bar-chart-horizontal"
    LINE_CHART = "line-chart"
    PIE_CHART = "pie-chart"
    AREA_CHART = "area-chart"
    TRENDING_UP = "trending-up"
    TRENDING_DOWN = "trending-down"
    ACTIVITY = "activity"
    GAUGE = "gauge"
    PERCENT = "percent"
    CALCULATOR = "calculator"
    SIGMA = "sigma"
    BINARY = "binary"

    # Navigation
    MENU = "menu"
    SIDEBAR = "sidebar"
    PANEL_LEFT = "panel-left"
    PANEL_RIGHT = "panel-right"
    PANEL_TOP = "panel-top"
    PANEL_BOTTOM = "panel-bottom"
    LAYOUT_GRID = "layout-grid"
    LAYOUT_LIST = "layout-list"
    LAYOUT_DASHBOARD = "layout-dashboard"
    MORE_HORIZONTAL = "more-horizontal"
    MORE_VERTICAL = "more-vertical"
    EXTERNAL_LINK = "external-link"
    LINK = "link"
    LINK_2 = "link-2"
    UNLINK = "unlink"
    UNLINK_2 = "unlink-2"
    LOG_IN = "log-in"
    LOG_OUT = "log-out"
    DOOR_OPEN = "door-open"
    DOOR_CLOSED = "door-closed"

    # Media
    PLAY = "play"
    PAUSE = "pause"
    STOP = "stop"
    SQUARE = "square"
    CIRCLE = "circle"
    SKIP_BACK = "skip-back"
    SKIP_FORWARD = "skip-forward"
    REWIND = "rewind"
    FAST_FORWARD = "fast-forward"
    VOLUME = "volume"
    VOLUME_1 = "volume-1"
    VOLUME_2 = "volume-2"
    VOLUME_X = "volume-x"
    MIC = "mic"
    MIC_OFF = "mic-off"
    CAMERA = "camera"
    CAMERA_OFF = "camera-off"
    VIDEO = "video"
    VIDEO_OFF = "video-off"
    IMAGE = "image"
    IMAGES = "images"
    FILM = "film"
    MUSIC = "music"
    HEADPHONES = "headphones"
    RADIO = "radio"
    TV = "tv"
    MONITOR = "monitor"
    SMARTPHONE = "smartphone"
    TABLET = "tablet"

    # Communication
    MAIL = "mail"
    MAIL_OPEN = "mail-open"
    INBOX = "inbox"
    SEND = "send"
    MESSAGE_CIRCLE = "message-circle"
    MESSAGE_SQUARE = "message-square"
    MESSAGES_SQUARE = "messages-square"
    PHONE = "phone"
    PHONE_CALL = "phone-call"
    PHONE_INCOMING = "phone-incoming"
    PHONE_OUTGOING = "phone-outgoing"
    PHONE_MISSED = "phone-missed"
    PHONE_OFF = "phone-off"
    SHARE = "share"
    SHARE_2 = "share-2"
    REPLY = "reply"
    REPLY_ALL = "reply-all"
    FORWARD = "forward"

    # Security
    EYE = "eye"
    EYE_OFF = "eye-off"
    LOCK = "lock"
    UNLOCK = "unlock"
    KEY = "key"
    KEY_ROUND = "key-round"
    SHIELD = "shield"
    SHIELD_CHECK = "shield-check"
    SHIELD_X = "shield-x"
    SHIELD_ALERT = "shield-alert"
    FINGERPRINT = "fingerprint"
    SCAN = "scan"

    # Weather
    SUN = "sun"
    MOON = "moon"
    CLOUD = "cloud"
    CLOUD_SUN = "cloud-sun"
    CLOUD_MOON = "cloud-moon"
    CLOUD_RAIN = "cloud-rain"
    CLOUD_SNOW = "cloud-snow"
    CLOUD_LIGHTNING = "cloud-lightning"
    THERMOMETER = "thermometer"
    WIND = "wind"
    DROPLETS = "droplets"

    # Misc
    STAR = "star"
    STAR_HALF = "star-half"
    HEART = "heart"
    THUMBS_UP = "thumbs-up"
    THUMBS_DOWN = "thumbs-down"
    FLAG = "flag"
    BOOKMARK = "bookmark"
    TAG = "tag"
    TAGS = "tags"
    BELL = "bell"
    BELL_OFF = "bell-off"
    BELL_RING = "bell-ring"
    CALENDAR = "calendar"
    CALENDAR_DAYS = "calendar-days"
    CALENDAR_PLUS = "calendar-plus"
    CALENDAR_MINUS = "calendar-minus"
    CALENDAR_CHECK = "calendar-check"
    CALENDAR_X = "calendar-x"
    MAP = "map"
    MAP_PIN = "map-pin"
    NAVIGATION = "navigation"
    COMPASS = "compass"
    GLOBE = "globe"
    GLOBE_2 = "globe-2"
    LAYERS = "layers"
    GRID = "grid"
    GRID_2X2 = "grid-2x2"
    GRID_3X3 = "grid-3x3"
    LIST = "list"
    LIST_ORDERED = "list-ordered"
    LIST_CHECKS = "list-checks"
    LIST_TODO = "list-todo"
    LIST_TREE = "list-tree"
    TABLE = "table"
    TABLE_2 = "table-2"
    KANBAN = "kanban"
    COLUMNS = "columns"
    ROWS = "rows"
    ALIGN_LEFT = "align-left"
    ALIGN_CENTER = "align-center"
    ALIGN_RIGHT = "align-right"
    ALIGN_JUSTIFY = "align-justify"
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    TYPE = "type"
    HEADING_1 = "heading-1"
    HEADING_2 = "heading-2"
    HEADING_3 = "heading-3"
    QUOTE = "quote"
    CODE_BLOCK = "square-code"
    PALETTE = "palette"
    PAINTBRUSH = "paintbrush"
    PIPETTE = "pipette"
    ERASER = "eraser"
    SCISSORS = "scissors"
    RULER = "ruler"
    WRENCH = "wrench"
    HAMMER = "hammer"
    SCREWDRIVER = "screwdriver"
    NUT = "nut"
    COG = "cog"
    ZOOMABLE = "scan-search"
    EXPAND = "expand"
    SHRINK = "shrink"
    FULLSCREEN = "fullscreen"
    GRIP_VERTICAL = "grip-vertical"
    GRIP_HORIZONTAL = "grip-horizontal"
    GRAB = "grab"
    POINTER = "pointer"
    HAND = "hand"
    MOUSE_POINTER = "mouse-pointer"
    MOUSE_POINTER_2 = "mouse-pointer-2"
    CURSOR = "text-cursor"
    CROSSHAIR = "crosshair"
    TARGET = "target"
    APERTURE = "aperture"
    FOCUS = "focus"
    SPARKLES = "sparkles"
    ZAP = "zap"
    FLAME = "flame"
    ROCKET = "rocket"
    GIFT = "gift"
    AWARD = "award"
    TROPHY = "trophy"
    MEDAL = "medal"
    CROWN = "crown"
    GEM = "gem"
    DIAMOND = "diamond"
    LIGHTBULB = "lightbulb"
    PUZZLE = "puzzle"
    BUG = "bug"
    TEST_TUBE = "test-tube"
    FLASK = "flask-conical"
    MICROSCOPE = "microscope"
    DNA = "dna"
    ATOM = "atom"
    WIFI = "wifi"
    WIFI_OFF = "wifi-off"
    BLUETOOTH = "bluetooth"
    BLUETOOTH_OFF = "bluetooth-off"
    SIGNAL = "signal"
    ANTENNA = "antenna"
    SATELLITE = "satellite"
    PLUG = "plug"
    PLUG_ZAP = "plug-zap"
    BATTERY = "battery"
    BATTERY_LOW = "battery-low"
    BATTERY_MEDIUM = "battery-medium"
    BATTERY_FULL = "battery-full"
    BATTERY_CHARGING = "battery-charging"
    POWER = "power"
    POWER_OFF = "power-off"


@react_component_base("Icon")
def Icon(
    name: IconName | str,
    *,
    size: int = 16,
    color: str | None = None,
    stroke_width: float = 2,
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Render a Lucide icon.

    Args:
        name: Icon name from IconName enum or string (e.g., IconName.CHECK or "check").
        size: Icon size in pixels. Defaults to 16.
        color: Icon color (CSS color string). Defaults to theme text color.
        stroke_width: Stroke width for the icon. Defaults to 2.
        margin: Margin around the icon (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Icon component.

    Example:
        from trellis.widgets import Icon, IconName

        Icon(name=IconName.CHECK, size=24, color="green")
        Icon(name=IconName.ALERT_TRIANGLE, color="#d97706")
    """
    ...
