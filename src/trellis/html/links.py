"""Link and media HTML elements.

Elements for hyperlinks and images.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, overload

from trellis.core.rendering.element import Element
from trellis.html._generated_attribute_types import (
    AriaAutocomplete,
    AriaChecked,
    AriaCurrent,
    AriaDropeffect,
    AriaHaspopup,
    AriaInvalid,
    AriaLive,
    AriaOrientation,
    AriaPressed,
    AriaRelevant,
    AriaSort,
    AutoCapitalize,
    ContentEditable,
    EnterKeyHint,
    InputMode,
    Popover,
    PopoverTargetAction,
    ReferrerPolicy,
    Role,
    Translate,
    Unselectable,
)
from trellis.html._generated_events import (
    DragEventHandler,
    EventHandler,
    FocusEventHandler,
    InputEventHandler,
    KeyboardEventHandler,
    MouseEventHandler,
    SubmitEventHandler,
    UIEventHandler,
    WheelEventHandler,
)
from trellis.html._generated_runtime import _A, Img
from trellis.html._style_runtime import StyleInput
from trellis.html.base import HtmlContainerElement
from trellis.routing.state import router

__all__ = [
    "A",
    "Img",
]

DataValue = str | int | float | bool | None


def _is_relative_url(href: str) -> bool:
    """Check if a URL is relative (no host/protocol).

    Relative URLs should use client-side router navigation.
    Absolute URLs (http://, https://, //) and special schemes (mailto:, tel:, etc.)
    should use browser navigation.

    Fragment-only (#section) and query-only (?foo=bar) URLs also bypass the router
    since they modify the current page rather than navigating to a new route.

    Args:
        href: The URL to check

    Returns:
        True if the URL is relative (should use router), False if absolute or special scheme
    """
    # Protocol-relative, fragment-only, and query-only URLs bypass the router.
    if href.startswith(("//", "#", "?")):
        return False

    # Explicit schemes bypass the router. We check a known set rather than using
    # urlparse because urlparse treats any "word:rest" as a scheme (e.g.
    # "localhost:3000" parses as scheme="localhost").
    _NON_RELATIVE_PREFIXES = (
        "http://",
        "https://",
        "mailto:",
        "tel:",
        "javascript:",
        "data:",
        "file:",
        "ftp://",
    )
    if href.startswith(_NON_RELATIVE_PREFIXES):
        return False

    # Catch any other URI scheme pattern (e.g. "tauri://...", "custom:...")
    # by checking for "word:" where the word contains only valid scheme chars.
    colon_pos = href.find(":")
    if colon_pos > 0:
        before_colon = href[:colon_pos]
        if (
            before_colon.isascii()
            and before_colon.replace("+", "").replace("-", "").replace(".", "").isalnum()
        ):
            # Looks like a URI scheme - but exclude port-like patterns (e.g. "localhost:3000")
            after_colon = href[colon_pos + 1 :]
            if after_colon.startswith("//") or not after_colon[:1].isdigit():
                return False

    return True


@overload
def A(
    inner_text: str,
    /,
    *,
    about: str | None = None,
    access_key: str | None = None,
    aria_activedescendant: str | None = None,
    aria_atomic: bool | None = None,
    aria_autocomplete: AriaAutocomplete | None = None,
    aria_braillelabel: str | None = None,
    aria_brailleroledescription: str | None = None,
    aria_busy: bool | None = None,
    aria_checked: AriaChecked | None = None,
    aria_colcount: int | float | None = None,
    aria_colindex: int | float | None = None,
    aria_colindextext: str | None = None,
    aria_colspan: int | float | None = None,
    aria_controls: str | None = None,
    aria_current: AriaCurrent | None = None,
    aria_describedby: str | None = None,
    aria_description: str | None = None,
    aria_details: str | None = None,
    aria_disabled: bool | None = None,
    aria_dropeffect: AriaDropeffect | None = None,
    aria_errormessage: str | None = None,
    aria_expanded: bool | None = None,
    aria_flowto: str | None = None,
    aria_grabbed: bool | None = None,
    aria_haspopup: AriaHaspopup | None = None,
    aria_hidden: bool | None = None,
    aria_invalid: AriaInvalid | None = None,
    aria_keyshortcuts: str | None = None,
    aria_label: str | None = None,
    aria_labelledby: str | None = None,
    aria_level: int | float | None = None,
    aria_live: AriaLive | None = None,
    aria_modal: bool | None = None,
    aria_multiline: bool | None = None,
    aria_multiselectable: bool | None = None,
    aria_orientation: AriaOrientation | None = None,
    aria_owns: str | None = None,
    aria_placeholder: str | None = None,
    aria_posinset: int | float | None = None,
    aria_pressed: AriaPressed | None = None,
    aria_readonly: bool | None = None,
    aria_relevant: AriaRelevant | None = None,
    aria_required: bool | None = None,
    aria_roledescription: str | None = None,
    aria_rowcount: int | float | None = None,
    aria_rowindex: int | float | None = None,
    aria_rowindextext: str | None = None,
    aria_rowspan: int | float | None = None,
    aria_selected: bool | None = None,
    aria_setsize: int | float | None = None,
    aria_sort: AriaSort | None = None,
    aria_valuemax: int | float | None = None,
    aria_valuemin: int | float | None = None,
    aria_valuenow: int | float | None = None,
    aria_valuetext: str | None = None,
    auto_capitalize: AutoCapitalize | None = None,
    auto_correct: str | None = None,
    auto_focus: bool | None = None,
    auto_save: str | None = None,
    class_name: str | None = None,
    color: str | None = None,
    content: str | None = None,
    content_editable: ContentEditable | None = None,
    context_menu: str | None = None,
    datatype: str | None = None,
    default_checked: bool | None = None,
    default_value: str | int | float | list[str] | None = None,
    dir: str | None = None,
    download: str | bool | None = None,
    draggable: bool | None = None,
    enter_key_hint: EnterKeyHint | None = None,
    exportparts: str | None = None,
    hidden: bool | None = None,
    href: str | None = None,
    href_lang: str | None = None,
    id: str | None = None,
    inert: bool | None = None,
    inlist: str | None = None,
    input_mode: InputMode | None = None,
    is_: str | None = None,
    item_id: str | None = None,
    item_prop: str | None = None,
    item_ref: str | None = None,
    item_scope: bool | None = None,
    item_type: str | None = None,
    lang: str | None = None,
    media: str | None = None,
    nonce: str | None = None,
    part: str | None = None,
    ping: str | None = None,
    popover: Popover | None = None,
    popover_target: str | None = None,
    popover_target_action: PopoverTargetAction | None = None,
    prefix: str | None = None,
    property: str | None = None,
    radio_group: str | None = None,
    referrer_policy: ReferrerPolicy | None = None,
    rel: str | None = None,
    resource: str | None = None,
    results: int | float | None = None,
    rev: str | None = None,
    role: Role | None = None,
    security: str | None = None,
    slot: str | None = None,
    spell_check: bool | None = None,
    style: StyleInput | None = None,
    suppress_content_editable_warning: bool | None = None,
    suppress_hydration_warning: bool | None = None,
    tab_index: int | float | None = None,
    target: Literal["_self", "_blank", "_parent", "_top"] | None = None,
    title: str | None = None,
    translate: Translate | None = None,
    type: str | None = None,
    typeof: str | None = None,
    unselectable: Unselectable | None = None,
    vocab: str | None = None,
    on_blur: FocusEventHandler | None = None,
    on_change: EventHandler | None = None,
    on_click: MouseEventHandler | None = None,
    on_context_menu: MouseEventHandler | None = None,
    on_double_click: MouseEventHandler | None = None,
    on_drag: DragEventHandler | None = None,
    on_drag_end: DragEventHandler | None = None,
    on_drag_enter: DragEventHandler | None = None,
    on_drag_leave: DragEventHandler | None = None,
    on_drag_over: DragEventHandler | None = None,
    on_drag_start: DragEventHandler | None = None,
    on_drop: DragEventHandler | None = None,
    on_focus: FocusEventHandler | None = None,
    on_input: InputEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    on_mouse_down: MouseEventHandler | None = None,
    on_mouse_enter: MouseEventHandler | None = None,
    on_mouse_leave: MouseEventHandler | None = None,
    on_mouse_move: MouseEventHandler | None = None,
    on_mouse_out: MouseEventHandler | None = None,
    on_mouse_over: MouseEventHandler | None = None,
    on_mouse_up: MouseEventHandler | None = None,
    on_scroll: UIEventHandler | None = None,
    on_submit: SubmitEventHandler | None = None,
    on_wheel: WheelEventHandler | None = None,
    use_router: bool = True,
    data: Mapping[str, DataValue] | None = None,
) -> Element: ...


@overload
def A(
    *,
    about: str | None = None,
    access_key: str | None = None,
    aria_activedescendant: str | None = None,
    aria_atomic: bool | None = None,
    aria_autocomplete: AriaAutocomplete | None = None,
    aria_braillelabel: str | None = None,
    aria_brailleroledescription: str | None = None,
    aria_busy: bool | None = None,
    aria_checked: AriaChecked | None = None,
    aria_colcount: int | float | None = None,
    aria_colindex: int | float | None = None,
    aria_colindextext: str | None = None,
    aria_colspan: int | float | None = None,
    aria_controls: str | None = None,
    aria_current: AriaCurrent | None = None,
    aria_describedby: str | None = None,
    aria_description: str | None = None,
    aria_details: str | None = None,
    aria_disabled: bool | None = None,
    aria_dropeffect: AriaDropeffect | None = None,
    aria_errormessage: str | None = None,
    aria_expanded: bool | None = None,
    aria_flowto: str | None = None,
    aria_grabbed: bool | None = None,
    aria_haspopup: AriaHaspopup | None = None,
    aria_hidden: bool | None = None,
    aria_invalid: AriaInvalid | None = None,
    aria_keyshortcuts: str | None = None,
    aria_label: str | None = None,
    aria_labelledby: str | None = None,
    aria_level: int | float | None = None,
    aria_live: AriaLive | None = None,
    aria_modal: bool | None = None,
    aria_multiline: bool | None = None,
    aria_multiselectable: bool | None = None,
    aria_orientation: AriaOrientation | None = None,
    aria_owns: str | None = None,
    aria_placeholder: str | None = None,
    aria_posinset: int | float | None = None,
    aria_pressed: AriaPressed | None = None,
    aria_readonly: bool | None = None,
    aria_relevant: AriaRelevant | None = None,
    aria_required: bool | None = None,
    aria_roledescription: str | None = None,
    aria_rowcount: int | float | None = None,
    aria_rowindex: int | float | None = None,
    aria_rowindextext: str | None = None,
    aria_rowspan: int | float | None = None,
    aria_selected: bool | None = None,
    aria_setsize: int | float | None = None,
    aria_sort: AriaSort | None = None,
    aria_valuemax: int | float | None = None,
    aria_valuemin: int | float | None = None,
    aria_valuenow: int | float | None = None,
    aria_valuetext: str | None = None,
    auto_capitalize: AutoCapitalize | None = None,
    auto_correct: str | None = None,
    auto_focus: bool | None = None,
    auto_save: str | None = None,
    class_name: str | None = None,
    color: str | None = None,
    content: str | None = None,
    content_editable: ContentEditable | None = None,
    context_menu: str | None = None,
    datatype: str | None = None,
    default_checked: bool | None = None,
    default_value: str | int | float | list[str] | None = None,
    dir: str | None = None,
    download: str | bool | None = None,
    draggable: bool | None = None,
    enter_key_hint: EnterKeyHint | None = None,
    exportparts: str | None = None,
    hidden: bool | None = None,
    href: str | None = None,
    href_lang: str | None = None,
    id: str | None = None,
    inert: bool | None = None,
    inlist: str | None = None,
    input_mode: InputMode | None = None,
    is_: str | None = None,
    item_id: str | None = None,
    item_prop: str | None = None,
    item_ref: str | None = None,
    item_scope: bool | None = None,
    item_type: str | None = None,
    lang: str | None = None,
    media: str | None = None,
    nonce: str | None = None,
    part: str | None = None,
    ping: str | None = None,
    popover: Popover | None = None,
    popover_target: str | None = None,
    popover_target_action: PopoverTargetAction | None = None,
    prefix: str | None = None,
    property: str | None = None,
    radio_group: str | None = None,
    referrer_policy: ReferrerPolicy | None = None,
    rel: str | None = None,
    resource: str | None = None,
    results: int | float | None = None,
    rev: str | None = None,
    role: Role | None = None,
    security: str | None = None,
    slot: str | None = None,
    spell_check: bool | None = None,
    style: StyleInput | None = None,
    suppress_content_editable_warning: bool | None = None,
    suppress_hydration_warning: bool | None = None,
    tab_index: int | float | None = None,
    target: Literal["_self", "_blank", "_parent", "_top"] | None = None,
    title: str | None = None,
    translate: Translate | None = None,
    type: str | None = None,
    typeof: str | None = None,
    unselectable: Unselectable | None = None,
    vocab: str | None = None,
    on_blur: FocusEventHandler | None = None,
    on_change: EventHandler | None = None,
    on_click: MouseEventHandler | None = None,
    on_context_menu: MouseEventHandler | None = None,
    on_double_click: MouseEventHandler | None = None,
    on_drag: DragEventHandler | None = None,
    on_drag_end: DragEventHandler | None = None,
    on_drag_enter: DragEventHandler | None = None,
    on_drag_leave: DragEventHandler | None = None,
    on_drag_over: DragEventHandler | None = None,
    on_drag_start: DragEventHandler | None = None,
    on_drop: DragEventHandler | None = None,
    on_focus: FocusEventHandler | None = None,
    on_input: InputEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    on_mouse_down: MouseEventHandler | None = None,
    on_mouse_enter: MouseEventHandler | None = None,
    on_mouse_leave: MouseEventHandler | None = None,
    on_mouse_move: MouseEventHandler | None = None,
    on_mouse_out: MouseEventHandler | None = None,
    on_mouse_over: MouseEventHandler | None = None,
    on_mouse_up: MouseEventHandler | None = None,
    on_scroll: UIEventHandler | None = None,
    on_submit: SubmitEventHandler | None = None,
    on_wheel: WheelEventHandler | None = None,
    use_router: bool = True,
    data: Mapping[str, DataValue] | None = None,
) -> HtmlContainerElement: ...


def A(
    inner_text: str | None = None,
    /,
    *,
    about: str | None = None,
    access_key: str | None = None,
    aria_activedescendant: str | None = None,
    aria_atomic: bool | None = None,
    aria_autocomplete: AriaAutocomplete | None = None,
    aria_braillelabel: str | None = None,
    aria_brailleroledescription: str | None = None,
    aria_busy: bool | None = None,
    aria_checked: AriaChecked | None = None,
    aria_colcount: int | float | None = None,
    aria_colindex: int | float | None = None,
    aria_colindextext: str | None = None,
    aria_colspan: int | float | None = None,
    aria_controls: str | None = None,
    aria_current: AriaCurrent | None = None,
    aria_describedby: str | None = None,
    aria_description: str | None = None,
    aria_details: str | None = None,
    aria_disabled: bool | None = None,
    aria_dropeffect: AriaDropeffect | None = None,
    aria_errormessage: str | None = None,
    aria_expanded: bool | None = None,
    aria_flowto: str | None = None,
    aria_grabbed: bool | None = None,
    aria_haspopup: AriaHaspopup | None = None,
    aria_hidden: bool | None = None,
    aria_invalid: AriaInvalid | None = None,
    aria_keyshortcuts: str | None = None,
    aria_label: str | None = None,
    aria_labelledby: str | None = None,
    aria_level: int | float | None = None,
    aria_live: AriaLive | None = None,
    aria_modal: bool | None = None,
    aria_multiline: bool | None = None,
    aria_multiselectable: bool | None = None,
    aria_orientation: AriaOrientation | None = None,
    aria_owns: str | None = None,
    aria_placeholder: str | None = None,
    aria_posinset: int | float | None = None,
    aria_pressed: AriaPressed | None = None,
    aria_readonly: bool | None = None,
    aria_relevant: AriaRelevant | None = None,
    aria_required: bool | None = None,
    aria_roledescription: str | None = None,
    aria_rowcount: int | float | None = None,
    aria_rowindex: int | float | None = None,
    aria_rowindextext: str | None = None,
    aria_rowspan: int | float | None = None,
    aria_selected: bool | None = None,
    aria_setsize: int | float | None = None,
    aria_sort: AriaSort | None = None,
    aria_valuemax: int | float | None = None,
    aria_valuemin: int | float | None = None,
    aria_valuenow: int | float | None = None,
    aria_valuetext: str | None = None,
    auto_capitalize: AutoCapitalize | None = None,
    auto_correct: str | None = None,
    auto_focus: bool | None = None,
    auto_save: str | None = None,
    class_name: str | None = None,
    color: str | None = None,
    content: str | None = None,
    content_editable: ContentEditable | None = None,
    context_menu: str | None = None,
    datatype: str | None = None,
    default_checked: bool | None = None,
    default_value: str | int | float | list[str] | None = None,
    dir: str | None = None,
    download: str | bool | None = None,
    draggable: bool | None = None,
    enter_key_hint: EnterKeyHint | None = None,
    exportparts: str | None = None,
    hidden: bool | None = None,
    href: str | None = None,
    href_lang: str | None = None,
    id: str | None = None,
    inert: bool | None = None,
    inlist: str | None = None,
    input_mode: InputMode | None = None,
    is_: str | None = None,
    item_id: str | None = None,
    item_prop: str | None = None,
    item_ref: str | None = None,
    item_scope: bool | None = None,
    item_type: str | None = None,
    lang: str | None = None,
    media: str | None = None,
    nonce: str | None = None,
    part: str | None = None,
    ping: str | None = None,
    popover: Popover | None = None,
    popover_target: str | None = None,
    popover_target_action: PopoverTargetAction | None = None,
    prefix: str | None = None,
    property: str | None = None,
    radio_group: str | None = None,
    referrer_policy: ReferrerPolicy | None = None,
    rel: str | None = None,
    resource: str | None = None,
    results: int | float | None = None,
    rev: str | None = None,
    role: Role | None = None,
    security: str | None = None,
    slot: str | None = None,
    spell_check: bool | None = None,
    style: StyleInput | None = None,
    suppress_content_editable_warning: bool | None = None,
    suppress_hydration_warning: bool | None = None,
    tab_index: int | float | None = None,
    target: Literal["_self", "_blank", "_parent", "_top"] | None = None,
    title: str | None = None,
    translate: Translate | None = None,
    type: str | None = None,
    typeof: str | None = None,
    unselectable: Unselectable | None = None,
    vocab: str | None = None,
    on_blur: FocusEventHandler | None = None,
    on_change: EventHandler | None = None,
    on_click: MouseEventHandler | None = None,
    on_context_menu: MouseEventHandler | None = None,
    on_double_click: MouseEventHandler | None = None,
    on_drag: DragEventHandler | None = None,
    on_drag_end: DragEventHandler | None = None,
    on_drag_enter: DragEventHandler | None = None,
    on_drag_leave: DragEventHandler | None = None,
    on_drag_over: DragEventHandler | None = None,
    on_drag_start: DragEventHandler | None = None,
    on_drop: DragEventHandler | None = None,
    on_focus: FocusEventHandler | None = None,
    on_input: InputEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    on_mouse_down: MouseEventHandler | None = None,
    on_mouse_enter: MouseEventHandler | None = None,
    on_mouse_leave: MouseEventHandler | None = None,
    on_mouse_move: MouseEventHandler | None = None,
    on_mouse_out: MouseEventHandler | None = None,
    on_mouse_over: MouseEventHandler | None = None,
    on_mouse_up: MouseEventHandler | None = None,
    on_scroll: UIEventHandler | None = None,
    on_submit: SubmitEventHandler | None = None,
    on_wheel: WheelEventHandler | None = None,
    use_router: bool = True,
    data: Mapping[str, DataValue] | None = None,
) -> Element | HtmlContainerElement:
    """An anchor (link) element.

    For relative URLs (paths without http://, https://, or //), automatically
    uses client-side router navigation instead of full page reload. This
    enables SPA-style navigation when used within a RouterState context.

    For absolute URLs, uses normal browser navigation.

    Can be used as text-only or as a container:
        h.A("Click here", href="/path")  # Text only
        with h.A(href="/path"):          # Container with children
            h.Img(src="icon.png")
            h.Span("Link text")

    Args:
        inner_text: Text content for the link
        href: URL to navigate to. Relative URLs use router, absolute use browser.
        target: Target window/frame (e.g., "_blank")
        rel: Relationship to linked document (e.g., "noopener")
        class_name: CSS class name
        style: Inline styles
        on_click: Custom click handler (overrides auto-routing for relative URLs)
        use_router: Whether to use client-side router for relative URLs (default True).
            Set to False to force browser navigation for relative URLs.
        data: Custom data-* attributes keyed by DOM suffix (e.g. ``{"test-id": "x"}``)
    """
    props = locals().copy()
    inner_text = props.pop("inner_text")
    use_router = props.pop("use_router")

    effective_on_click = props["on_click"]
    effective_data = dict(props["data"]) if props["data"] is not None else None
    if (
        props["href"]
        and props["on_click"] is None
        and use_router
        and props["target"] != "_blank"
        and (props["download"] is None or props["download"] is False)
        and _is_relative_url(props["href"])
    ):
        nav_href = props["href"]

        async def router_click(_event: object) -> None:
            await router().navigate(nav_href)

        effective_on_click = router_click
        if effective_data is None:
            effective_data = {}
        effective_data["trellis-router-link"] = "true"

    props["on_click"] = effective_on_click
    props["data"] = effective_data

    if inner_text is None:
        return _A(**props)
    return _A(inner_text, **props)
