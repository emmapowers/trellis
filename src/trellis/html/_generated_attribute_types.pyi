"""Generated HTML attribute type aliases.

Internal codegen artifact for trellis.html.
Reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes

Generated at: 2026-03-11T22:46:25.136Z
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

AutoCapitalize = (
    Literal["off"]
    | Literal["none"]
    | Literal["on"]
    | Literal["sentences"]
    | Literal["words"]
    | Literal["characters"]
    | str
)

Blocking = Literal["render"] | str

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

InputType = (
    Literal["button"]
    | Literal["checkbox"]
    | Literal["color"]
    | Literal["date"]
    | Literal["datetime-local"]
    | Literal["email"]
    | Literal["file"]
    | Literal["hidden"]
    | Literal["image"]
    | Literal["month"]
    | Literal["number"]
    | Literal["password"]
    | Literal["radio"]
    | Literal["range"]
    | Literal["reset"]
    | Literal["search"]
    | Literal["submit"]
    | Literal["tel"]
    | Literal["text"]
    | Literal["time"]
    | Literal["url"]
    | Literal["week"]
    | str
)

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

Role = (
    Literal["alert"]
    | Literal["alertdialog"]
    | Literal["application"]
    | Literal["article"]
    | Literal["banner"]
    | Literal["button"]
    | Literal["cell"]
    | Literal["checkbox"]
    | Literal["columnheader"]
    | Literal["combobox"]
    | Literal["complementary"]
    | Literal["contentinfo"]
    | Literal["definition"]
    | Literal["dialog"]
    | Literal["directory"]
    | Literal["document"]
    | Literal["feed"]
    | Literal["figure"]
    | Literal["form"]
    | Literal["grid"]
    | Literal["gridcell"]
    | Literal["group"]
    | Literal["heading"]
    | Literal["img"]
    | Literal["link"]
    | Literal["list"]
    | Literal["listbox"]
    | Literal["listitem"]
    | Literal["log"]
    | Literal["main"]
    | Literal["marquee"]
    | Literal["math"]
    | Literal["menu"]
    | Literal["menubar"]
    | Literal["menuitem"]
    | Literal["menuitemcheckbox"]
    | Literal["menuitemradio"]
    | Literal["navigation"]
    | Literal["none"]
    | Literal["note"]
    | Literal["option"]
    | Literal["presentation"]
    | Literal["progressbar"]
    | Literal["radio"]
    | Literal["radiogroup"]
    | Literal["region"]
    | Literal["row"]
    | Literal["rowgroup"]
    | Literal["rowheader"]
    | Literal["scrollbar"]
    | Literal["search"]
    | Literal["searchbox"]
    | Literal["separator"]
    | Literal["slider"]
    | Literal["spinbutton"]
    | Literal["status"]
    | Literal["switch"]
    | Literal["tab"]
    | Literal["table"]
    | Literal["tablist"]
    | Literal["tabpanel"]
    | Literal["term"]
    | Literal["textbox"]
    | Literal["timer"]
    | Literal["toolbar"]
    | Literal["tooltip"]
    | Literal["tree"]
    | Literal["treegrid"]
    | Literal["treeitem"]
    | str
)

Translate = Literal[
    "yes",
    "no",
]

Unselectable = Literal[
    "on",
    "off",
]
