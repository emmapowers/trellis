"""Generated HTML attribute type aliases.

Generated at: 2026-03-07T23:41:03.418Z
"""

from __future__ import annotations

from typing import Literal

__all__ = [
    "AriaAutocomplete",
    "AriaChecked",
    "AriaCurrent",
    "AriaDropeffect",
    "AriaHaspopup",
    "AriaInvalid",
    "AriaLive",
    "AriaOrientation",
    "AriaPressed",
    "AriaRelevant",
    "AriaSort",
    "AutoCapitalize",
    "Blocking",
    "ContentEditable",
    "CrossOrigin",
    "EnterKeyHint",
    "FetchPriority",
    "InputMode",
    "InputType",
    "Loading",
    "Popover",
    "PopoverTargetAction",
    "ReferrerPolicy",
    "Role",
    "Translate",
    "Unselectable",
]

AriaAutocomplete = Literal[
    "none",
    "inline",
    "list",
    "both",
]

AriaChecked = bool | Literal["false"] | Literal["mixed"] | Literal["true"]

AriaCurrent = (
    bool
    | Literal["false"]
    | Literal["true"]
    | Literal["page"]
    | Literal["step"]
    | Literal["location"]
    | Literal["date"]
    | Literal["time"]
)

AriaDropeffect = Literal[
    "none",
    "copy",
    "execute",
    "link",
    "move",
    "popup",
]

AriaHaspopup = (
    bool
    | Literal["false"]
    | Literal["true"]
    | Literal["menu"]
    | Literal["listbox"]
    | Literal["tree"]
    | Literal["grid"]
    | Literal["dialog"]
)

AriaInvalid = bool | Literal["false"] | Literal["true"] | Literal["grammar"] | Literal["spelling"]

AriaLive = Literal[
    "off",
    "assertive",
    "polite",
]

AriaOrientation = Literal[
    "horizontal",
    "vertical",
]

AriaPressed = bool | Literal["false"] | Literal["mixed"] | Literal["true"]

AriaRelevant = Literal[
    "additions",
    "additions removals",
    "additions text",
    "all",
    "removals",
    "removals additions",
    "removals text",
    "text",
    "text additions",
    "text removals",
]

AriaSort = Literal[
    "none",
    "ascending",
    "descending",
    "other",
]

AutoCapitalize = Literal[
    "off",
    "none",
    "on",
    "sentences",
    "words",
    "characters",
]

Blocking = Literal["render"]

ContentEditable = bool | Literal["inherit"] | Literal["plaintext-only"]

CrossOrigin = Literal[
    "anonymous",
    "use-credentials",
    "",
]

EnterKeyHint = Literal[
    "enter",
    "done",
    "go",
    "next",
    "previous",
    "search",
    "send",
]

FetchPriority = Literal[
    "high",
    "low",
    "auto",
]

InputMode = Literal[
    "none",
    "text",
    "tel",
    "url",
    "email",
    "numeric",
    "decimal",
    "search",
]

InputType = Literal[
    "button",
    "checkbox",
    "color",
    "date",
    "datetime-local",
    "email",
    "file",
    "hidden",
    "image",
    "month",
    "number",
    "password",
    "radio",
    "range",
    "reset",
    "search",
    "submit",
    "tel",
    "text",
    "time",
    "url",
    "week",
]

Loading = Literal[
    "eager",
    "lazy",
]

Popover = Literal[
    "",
    "auto",
    "manual",
    "hint",
]

PopoverTargetAction = Literal[
    "toggle",
    "show",
    "hide",
]

ReferrerPolicy = Literal[
    "",
    "no-referrer",
    "no-referrer-when-downgrade",
    "origin",
    "origin-when-cross-origin",
    "same-origin",
    "strict-origin",
    "strict-origin-when-cross-origin",
    "unsafe-url",
]

Role = Literal[
    "alert",
    "alertdialog",
    "application",
    "article",
    "banner",
    "button",
    "cell",
    "checkbox",
    "columnheader",
    "combobox",
    "complementary",
    "contentinfo",
    "definition",
    "dialog",
    "directory",
    "document",
    "feed",
    "figure",
    "form",
    "grid",
    "gridcell",
    "group",
    "heading",
    "img",
    "link",
    "list",
    "listbox",
    "listitem",
    "log",
    "main",
    "marquee",
    "math",
    "menu",
    "menubar",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "navigation",
    "none",
    "note",
    "option",
    "presentation",
    "progressbar",
    "radio",
    "radiogroup",
    "region",
    "row",
    "rowgroup",
    "rowheader",
    "scrollbar",
    "search",
    "searchbox",
    "separator",
    "slider",
    "spinbutton",
    "status",
    "switch",
    "tab",
    "table",
    "tablist",
    "tabpanel",
    "term",
    "textbox",
    "timer",
    "toolbar",
    "tooltip",
    "tree",
    "treegrid",
    "treeitem",
]

Translate = Literal[
    "yes",
    "no",
]

Unselectable = Literal[
    "on",
    "off",
]
