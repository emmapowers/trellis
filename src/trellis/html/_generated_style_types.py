"""Generated CSS style type declarations.

Internal codegen artifact for trellis.html CSS typing.
Reference: https://developer.mozilla.org/en-US/docs/Web/CSS

Generated at: 2026-03-08T20:20:29.213Z
"""

from __future__ import annotations

import builtins
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from trellis.html._css_primitives import (
    CssAngle,
    CssColor,
    CssLength,
    CssPercent,
    CssTime,
    CssValue,
)

if TYPE_CHECKING:
    from trellis.html._style_runtime import Style

Length = CssLength | CssValue
Percent = CssPercent | CssValue
LengthPercentage = Length | Percent
TimeValue = CssTime | CssValue
AngleValue = CssAngle | CssValue
NamedColor = Literal[
    "aliceblue",
    "antiquewhite",
    "aqua",
    "aquamarine",
    "azure",
    "beige",
    "bisque",
    "black",
    "blanchedalmond",
    "blue",
    "blueviolet",
    "brown",
    "burlywood",
    "cadetblue",
    "chartreuse",
    "chocolate",
    "coral",
    "cornflowerblue",
    "cornsilk",
    "crimson",
    "cyan",
    "darkblue",
    "darkcyan",
    "darkgoldenrod",
    "darkgray",
    "darkgreen",
    "darkgrey",
    "darkkhaki",
    "darkmagenta",
    "darkolivegreen",
    "darkorange",
    "darkorchid",
    "darkred",
    "darksalmon",
    "darkseagreen",
    "darkslateblue",
    "darkslategray",
    "darkslategrey",
    "darkturquoise",
    "darkviolet",
    "deeppink",
    "deepskyblue",
    "dimgray",
    "dimgrey",
    "dodgerblue",
    "firebrick",
    "floralwhite",
    "forestgreen",
    "fuchsia",
    "gainsboro",
    "ghostwhite",
    "gold",
    "goldenrod",
    "gray",
    "green",
    "greenyellow",
    "grey",
    "honeydew",
    "hotpink",
    "indianred",
    "indigo",
    "ivory",
    "khaki",
    "lavender",
    "lavenderblush",
    "lawngreen",
    "lemonchiffon",
    "lightblue",
    "lightcoral",
    "lightcyan",
    "lightgoldenrodyellow",
    "lightgray",
    "lightgreen",
    "lightgrey",
    "lightpink",
    "lightsalmon",
    "lightseagreen",
    "lightskyblue",
    "lightslategray",
    "lightslategrey",
    "lightsteelblue",
    "lightyellow",
    "lime",
    "limegreen",
    "linen",
    "magenta",
    "maroon",
    "mediumaquamarine",
    "mediumblue",
    "mediumorchid",
    "mediumpurple",
    "mediumseagreen",
    "mediumslateblue",
    "mediumspringgreen",
    "mediumturquoise",
    "mediumvioletred",
    "midnightblue",
    "mintcream",
    "mistyrose",
    "moccasin",
    "navajowhite",
    "navy",
    "oldlace",
    "olive",
    "olivedrab",
    "orange",
    "orangered",
    "orchid",
    "palegoldenrod",
    "palegreen",
    "paleturquoise",
    "palevioletred",
    "papayawhip",
    "peachpuff",
    "peru",
    "pink",
    "plum",
    "powderblue",
    "purple",
    "rebeccapurple",
    "red",
    "rosybrown",
    "royalblue",
    "saddlebrown",
    "salmon",
    "sandybrown",
    "seagreen",
    "seashell",
    "sienna",
    "silver",
    "skyblue",
    "slateblue",
    "slategray",
    "slategrey",
    "snow",
    "springgreen",
    "steelblue",
    "tan",
    "teal",
    "thistle",
    "tomato",
    "turquoise",
    "violet",
    "wheat",
    "white",
    "whitesmoke",
    "yellow",
    "yellowgreen",
]
ColorKeyword = NamedColor | Literal["transparent"] | Literal["currentColor"]
ColorValue = ColorKeyword | str | CssColor | CssValue
Display = (
    Literal["block"]
    | Literal["inline"]
    | Literal["inline-block"]
    | Literal["flex"]
    | Literal["inline-flex"]
    | Literal["grid"]
    | Literal["inline-grid"]
    | Literal["none"]
    | Literal["contents"]
    | CssValue
)
Position = (
    Literal["static"]
    | Literal["relative"]
    | Literal["absolute"]
    | Literal["fixed"]
    | Literal["sticky"]
    | CssValue
)
Overflow = (
    Literal["visible"]
    | Literal["hidden"]
    | Literal["clip"]
    | Literal["scroll"]
    | Literal["auto"]
    | CssValue
)
TextAlign = (
    Literal["left"]
    | Literal["right"]
    | Literal["center"]
    | Literal["justify"]
    | Literal["start"]
    | Literal["end"]
    | CssValue
)
FontWeight = (
    int | Literal["normal"] | Literal["bold"] | Literal["lighter"] | Literal["bolder"] | CssValue
)
FlexDirection = (
    Literal["row"]
    | Literal["row-reverse"]
    | Literal["column"]
    | Literal["column-reverse"]
    | CssValue
)
FlexWrap = Literal["nowrap"] | Literal["wrap"] | Literal["wrap-reverse"] | CssValue
JustifyContent = (
    Literal["flex-start"]
    | Literal["flex-end"]
    | Literal["center"]
    | Literal["space-between"]
    | Literal["space-around"]
    | Literal["space-evenly"]
    | Literal["start"]
    | Literal["end"]
    | CssValue
)
AlignItems = (
    Literal["stretch"]
    | Literal["center"]
    | Literal["start"]
    | Literal["end"]
    | Literal["flex-start"]
    | Literal["flex-end"]
    | Literal["baseline"]
    | CssValue
)
WidthValue = (
    LengthPercentage
    | Literal["auto"]
    | Literal["min-content"]
    | Literal["max-content"]
    | Literal["fit-content"]
    | Literal["stretch"]
    | Literal["contain"]
    | CssValue
)
HeightValue = (
    LengthPercentage
    | Literal["auto"]
    | Literal["min-content"]
    | Literal["max-content"]
    | Literal["fit-content"]
    | Literal["stretch"]
    | Literal["contain"]
    | CssValue
)
BorderRadiusValue = LengthPercentage | CssValue
SpacingShorthand = LengthPercentage | CssValue
GapValue = LengthPercentage | Literal["normal"] | CssValue
LineHeightValue = LengthPercentage | float | Literal["normal"] | CssValue
ShadowValue = CssValue
TransformValue = CssValue
TransitionValue = CssValue
Opacity = float | CssValue
ZIndex = int | Literal["auto"] | CssValue
Orientation = Literal["portrait"] | Literal["landscape"] | CssValue
PrefersColorScheme = Literal["light"] | Literal["dark"] | CssValue
PrefersReducedMotion = Literal["reduce"] | Literal["no-preference"] | CssValue
PointerCapability = Literal["none"] | Literal["coarse"] | Literal["fine"] | CssValue
HoverCapability = Literal["none"] | Literal["hover"] | CssValue


@dataclass(kw_only=True)
class _GeneratedStyleFields:
    """Generated CSS style field definitions.

    Internal base class for `trellis.html.Style`.
    Reference: https://developer.mozilla.org/en-US/docs/Web/CSS
    """

    accent_color: ColorValue | None = None
    align_content: CssValue | str | None = None
    align_items: AlignItems | None = None
    align_self: CssValue | str | None = None
    alignment_baseline: CssValue | str | None = None
    all: CssValue | str | None = None
    anchor_name: CssValue | str | None = None
    anchor_scope: CssValue | str | None = None
    animation: CssValue | str | None = None
    animation_composition: CssValue | str | None = None
    animation_delay: TimeValue | None = None
    animation_direction: CssValue | str | None = None
    animation_duration: TimeValue | None = None
    animation_fill_mode: CssValue | str | None = None
    animation_iteration_count: CssValue | str | None = None
    animation_name: CssValue | str | None = None
    animation_play_state: CssValue | str | None = None
    animation_range: CssValue | str | None = None
    animation_range_center: LengthPercentage | builtins.int | builtins.float | None = None
    animation_range_end: LengthPercentage | builtins.int | builtins.float | None = None
    animation_range_start: LengthPercentage | builtins.int | builtins.float | None = None
    animation_timeline: CssValue | str | None = None
    animation_timing_function: CssValue | str | None = None
    animation_trigger: CssValue | str | None = None
    appearance: CssValue | str | None = None
    aspect_ratio: CssValue | str | None = None
    backdrop_filter: CssValue | str | None = None
    backface_visibility: CssValue | str | None = None
    background: CssValue | str | None = None
    background_attachment: CssValue | str | None = None
    background_blend_mode: CssValue | str | None = None
    background_clip: CssValue | str | None = None
    background_color: ColorValue | None = None
    background_image: CssValue | str | None = None
    background_origin: CssValue | str | None = None
    background_position: CssValue | str | None = None
    background_position_block: LengthPercentage | builtins.int | builtins.float | None = None
    background_position_inline: LengthPercentage | builtins.int | builtins.float | None = None
    background_position_x: LengthPercentage | builtins.int | builtins.float | None = None
    background_position_y: LengthPercentage | builtins.int | builtins.float | None = None
    background_repeat: CssValue | str | None = None
    background_repeat_block: CssValue | str | None = None
    background_repeat_inline: CssValue | str | None = None
    background_repeat_x: CssValue | str | None = None
    background_repeat_y: CssValue | str | None = None
    background_size: CssValue | str | None = None
    background_tbd: CssValue | str | None = None
    baseline_shift: LengthPercentage | builtins.int | builtins.float | None = None
    baseline_source: CssValue | str | None = None
    block_ellipsis: CssValue | str | None = None
    block_size: CssValue | str | None = None
    block_step: CssValue | str | None = None
    block_step_align: CssValue | str | None = None
    block_step_insert: CssValue | str | None = None
    block_step_round: CssValue | str | None = None
    block_step_size: Length | builtins.int | builtins.float | None = None
    bookmark_label: CssValue | str | None = None
    bookmark_level: CssValue | str | None = None
    bookmark_state: CssValue | str | None = None
    border: ColorValue | CssValue | None = None
    border_block: CssValue | str | None = None
    border_block_clip: CssValue | str | None = None
    border_block_color: ColorValue | CssValue | None = None
    border_block_end: ColorValue | CssValue | None = None
    border_block_end_clip: LengthPercentage | builtins.int | builtins.float | None = None
    border_block_end_color: ColorValue | None = None
    border_block_end_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_block_end_style: CssValue | str | None = None
    border_block_end_width: WidthValue | builtins.int | builtins.float | None = None
    border_block_start: ColorValue | CssValue | None = None
    border_block_start_clip: LengthPercentage | builtins.int | builtins.float | None = None
    border_block_start_color: ColorValue | None = None
    border_block_start_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_block_start_style: CssValue | str | None = None
    border_block_start_width: WidthValue | builtins.int | builtins.float | None = None
    border_block_style: CssValue | str | None = None
    border_block_width: WidthValue | builtins.int | builtins.float | None = None
    border_bottom: ColorValue | CssValue | None = None
    border_bottom_clip: LengthPercentage | builtins.int | builtins.float | None = None
    border_bottom_color: ColorValue | None = None
    border_bottom_left_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_bottom_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_bottom_right_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_bottom_style: CssValue | str | None = None
    border_bottom_width: WidthValue | builtins.int | builtins.float | None = None
    border_boundary: CssValue | str | None = None
    border_clip: CssValue | str | None = None
    border_collapse: CssValue | str | None = None
    border_color: ColorValue | CssValue | None = None
    border_end_end_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_end_start_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_image: CssValue | str | None = None
    border_image_outset: Length | builtins.int | builtins.float | None = None
    border_image_repeat: CssValue | str | None = None
    border_image_slice: CssValue | str | None = None
    border_image_source: CssValue | str | None = None
    border_image_width: WidthValue | builtins.int | builtins.float | None = None
    border_inline: CssValue | str | None = None
    border_inline_clip: CssValue | str | None = None
    border_inline_color: ColorValue | CssValue | None = None
    border_inline_end: ColorValue | CssValue | None = None
    border_inline_end_clip: LengthPercentage | builtins.int | builtins.float | None = None
    border_inline_end_color: ColorValue | None = None
    border_inline_end_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_inline_end_style: CssValue | str | None = None
    border_inline_end_width: WidthValue | builtins.int | builtins.float | None = None
    border_inline_start: ColorValue | CssValue | None = None
    border_inline_start_clip: LengthPercentage | builtins.int | builtins.float | None = None
    border_inline_start_color: ColorValue | None = None
    border_inline_start_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_inline_start_style: CssValue | str | None = None
    border_inline_start_width: WidthValue | builtins.int | builtins.float | None = None
    border_inline_style: CssValue | str | None = None
    border_inline_width: WidthValue | builtins.int | builtins.float | None = None
    border_left: ColorValue | CssValue | None = None
    border_left_clip: LengthPercentage | builtins.int | builtins.float | None = None
    border_left_color: ColorValue | None = None
    border_left_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_left_style: CssValue | str | None = None
    border_left_width: WidthValue | builtins.int | builtins.float | None = None
    border_limit: LengthPercentage | builtins.int | builtins.float | None = None
    border_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_right: ColorValue | CssValue | None = None
    border_right_clip: LengthPercentage | builtins.int | builtins.float | None = None
    border_right_color: ColorValue | None = None
    border_right_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_right_style: CssValue | str | None = None
    border_right_width: WidthValue | builtins.int | builtins.float | None = None
    border_shape: CssValue | str | None = None
    border_spacing: Length | builtins.int | builtins.float | None = None
    border_start_end_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_start_start_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_style: CssValue | str | None = None
    border_top: ColorValue | CssValue | None = None
    border_top_clip: LengthPercentage | builtins.int | builtins.float | None = None
    border_top_color: ColorValue | None = None
    border_top_left_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_top_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_top_right_radius: BorderRadiusValue | builtins.int | builtins.float | None = None
    border_top_style: CssValue | str | None = None
    border_top_width: WidthValue | builtins.int | builtins.float | None = None
    border_width: WidthValue | builtins.int | builtins.float | None = None
    bottom: LengthPercentage | builtins.int | builtins.float | None = None
    box_decoration_break: CssValue | str | None = None
    box_shadow: ShadowValue | None = None
    box_shadow_blur: Length | builtins.int | builtins.float | None = None
    box_shadow_color: ColorValue | None = None
    box_shadow_offset: Length | builtins.int | builtins.float | None = None
    box_shadow_position: CssValue | str | None = None
    box_shadow_spread: Length | builtins.int | builtins.float | None = None
    box_sizing: CssValue | str | None = None
    box_snap: CssValue | str | None = None
    break_after: CssValue | str | None = None
    break_before: CssValue | str | None = None
    break_inside: CssValue | str | None = None
    caption_side: CssValue | str | None = None
    caret: CssValue | str | None = None
    caret_animation: CssValue | str | None = None
    caret_color: ColorValue | None = None
    caret_shape: CssValue | str | None = None
    clear: CssValue | str | None = None
    clip: CssValue | str | None = None
    clip_path: CssValue | str | None = None
    clip_rule: CssValue | str | None = None
    color: ColorValue | None = None
    color_adjust: CssValue | str | None = None
    color_interpolation: CssValue | str | None = None
    color_interpolation_filters: CssValue | str | None = None
    color_scheme: CssValue | str | None = None
    column_count: CssValue | str | None = None
    column_fill: CssValue | str | None = None
    column_gap: GapValue | builtins.int | builtins.float | None = None
    column_height: HeightValue | builtins.int | builtins.float | None = None
    column_rule: CssValue | str | None = None
    column_rule_break: CssValue | str | None = None
    column_rule_color: ColorValue | None = None
    column_rule_edge_inset: LengthPercentage | CssValue | builtins.int | builtins.float | None = (
        None
    )
    column_rule_edge_inset_end: LengthPercentage | builtins.int | builtins.float | None = None
    column_rule_edge_inset_start: LengthPercentage | builtins.int | builtins.float | None = None
    column_rule_inset: CssValue | str | None = None
    column_rule_inset_end: LengthPercentage | CssValue | builtins.int | builtins.float | None = None
    column_rule_inset_start: LengthPercentage | CssValue | builtins.int | builtins.float | None = (
        None
    )
    column_rule_interior_inset: (
        LengthPercentage | CssValue | builtins.int | builtins.float | None
    ) = None
    column_rule_interior_inset_end: LengthPercentage | builtins.int | builtins.float | None = None
    column_rule_interior_inset_start: LengthPercentage | builtins.int | builtins.float | None = None
    column_rule_style: CssValue | str | None = None
    column_rule_visibility_items: CssValue | str | None = None
    column_rule_width: WidthValue | builtins.int | builtins.float | None = None
    column_span: CssValue | str | None = None
    column_width: WidthValue | builtins.int | builtins.float | None = None
    column_wrap: CssValue | str | None = None
    columns: CssValue | str | None = None
    contain: CssValue | str | None = None
    contain_intrinsic_block_size: Length | builtins.int | builtins.float | None = None
    contain_intrinsic_height: HeightValue | builtins.int | builtins.float | None = None
    contain_intrinsic_inline_size: Length | builtins.int | builtins.float | None = None
    contain_intrinsic_size: Length | CssValue | builtins.int | builtins.float | None = None
    contain_intrinsic_width: WidthValue | builtins.int | builtins.float | None = None
    container: CssValue | str | None = None
    container_name: CssValue | str | None = None
    container_type: CssValue | str | None = None
    content: CssValue | str | None = None
    content_visibility: CssValue | str | None = None
    continue_: CssValue | str | None = None
    copy_into: CssValue | str | None = None
    corner: CssValue | str | None = None
    corner_block_end: CssValue | str | None = None
    corner_block_end_shape: CssValue | str | None = None
    corner_block_start: CssValue | str | None = None
    corner_block_start_shape: CssValue | str | None = None
    corner_bottom: CssValue | str | None = None
    corner_bottom_left: CssValue | str | None = None
    corner_bottom_left_shape: CssValue | str | None = None
    corner_bottom_right: CssValue | str | None = None
    corner_bottom_right_shape: CssValue | str | None = None
    corner_bottom_shape: CssValue | str | None = None
    corner_end_end: CssValue | str | None = None
    corner_end_end_shape: CssValue | str | None = None
    corner_end_start: CssValue | str | None = None
    corner_end_start_shape: CssValue | str | None = None
    corner_inline_end: CssValue | str | None = None
    corner_inline_end_shape: CssValue | str | None = None
    corner_inline_start: CssValue | str | None = None
    corner_inline_start_shape: CssValue | str | None = None
    corner_left: CssValue | str | None = None
    corner_left_shape: CssValue | str | None = None
    corner_right: CssValue | str | None = None
    corner_right_shape: CssValue | str | None = None
    corner_shape: CssValue | str | None = None
    corner_start_end: CssValue | str | None = None
    corner_start_end_shape: CssValue | str | None = None
    corner_start_start: CssValue | str | None = None
    corner_start_start_shape: CssValue | str | None = None
    corner_top: CssValue | str | None = None
    corner_top_left: CssValue | str | None = None
    corner_top_left_shape: CssValue | str | None = None
    corner_top_right: CssValue | str | None = None
    corner_top_right_shape: CssValue | str | None = None
    corner_top_shape: CssValue | str | None = None
    counter_increment: CssValue | str | None = None
    counter_reset: CssValue | str | None = None
    counter_set: CssValue | str | None = None
    cue: CssValue | str | None = None
    cue_after: CssValue | str | None = None
    cue_before: CssValue | str | None = None
    cursor: CssValue | str | None = None
    cx: LengthPercentage | builtins.int | builtins.float | None = None
    cy: LengthPercentage | builtins.int | builtins.float | None = None
    d: CssValue | str | None = None
    direction: CssValue | str | None = None
    display: Display | None = None
    dominant_baseline: CssValue | str | None = None
    dynamic_range_limit: CssValue | str | None = None
    empty_cells: CssValue | str | None = None
    event_trigger: CssValue | str | None = None
    event_trigger_name: CssValue | str | None = None
    event_trigger_source: CssValue | str | None = None
    field_sizing: CssValue | str | None = None
    fill: CssValue | str | None = None
    fill_break: CssValue | str | None = None
    fill_color: ColorValue | None = None
    fill_image: CssValue | str | None = None
    fill_opacity: CssValue | str | None = None
    fill_origin: CssValue | str | None = None
    fill_position: CssValue | str | None = None
    fill_repeat: CssValue | str | None = None
    fill_rule: CssValue | str | None = None
    fill_size: CssValue | str | None = None
    filter: CssValue | str | None = None
    flex: CssValue | str | None = None
    flex_basis: CssValue | str | None = None
    flex_direction: FlexDirection | None = None
    flex_flow: CssValue | str | None = None
    flex_grow: CssValue | str | None = None
    flex_shrink: CssValue | str | None = None
    flex_wrap: FlexWrap | None = None
    float: CssValue | str | None = None
    float_defer: CssValue | str | None = None
    float_offset: LengthPercentage | builtins.int | builtins.float | None = None
    float_reference: CssValue | str | None = None
    flood_color: ColorValue | None = None
    flood_opacity: CssValue | str | None = None
    flow_from: CssValue | str | None = None
    flow_into: CssValue | str | None = None
    flow_tolerance: LengthPercentage | builtins.int | builtins.float | None = None
    font: CssValue | str | None = None
    font_family: CssValue | str | None = None
    font_feature_settings: CssValue | str | None = None
    font_kerning: CssValue | str | None = None
    font_language_override: CssValue | str | None = None
    font_optical_sizing: CssValue | str | None = None
    font_palette: CssValue | str | None = None
    font_size: LengthPercentage | builtins.int | builtins.float | None = None
    font_size_adjust: CssValue | str | None = None
    font_stretch: CssValue | str | None = None
    font_style: AngleValue | None = None
    font_synthesis: CssValue | str | None = None
    font_synthesis_position: CssValue | str | None = None
    font_synthesis_small_caps: CssValue | str | None = None
    font_synthesis_style: CssValue | str | None = None
    font_synthesis_weight: CssValue | str | None = None
    font_variant: CssValue | str | None = None
    font_variant_alternates: CssValue | str | None = None
    font_variant_caps: CssValue | str | None = None
    font_variant_east_asian: CssValue | str | None = None
    font_variant_emoji: CssValue | str | None = None
    font_variant_ligatures: CssValue | str | None = None
    font_variant_numeric: CssValue | str | None = None
    font_variant_position: CssValue | str | None = None
    font_variation_settings: CssValue | str | None = None
    font_weight: FontWeight | None = None
    font_width: WidthValue | builtins.int | builtins.float | None = None
    footnote_display: CssValue | str | None = None
    footnote_policy: CssValue | str | None = None
    forced_color_adjust: CssValue | str | None = None
    gap: GapValue | builtins.int | builtins.float | None = None
    glyph_orientation_vertical: CssValue | str | None = None
    grid: CssValue | str | None = None
    grid_area: CssValue | str | None = None
    grid_auto_columns: CssValue | str | None = None
    grid_auto_flow: CssValue | str | None = None
    grid_auto_rows: CssValue | str | None = None
    grid_column: CssValue | str | None = None
    grid_column_end: CssValue | str | None = None
    grid_column_gap: GapValue | builtins.int | builtins.float | None = None
    grid_column_start: CssValue | str | None = None
    grid_gap: GapValue | builtins.int | builtins.float | None = None
    grid_row: CssValue | str | None = None
    grid_row_end: CssValue | str | None = None
    grid_row_gap: GapValue | builtins.int | builtins.float | None = None
    grid_row_start: CssValue | str | None = None
    grid_template: CssValue | str | None = None
    grid_template_areas: CssValue | str | None = None
    grid_template_columns: CssValue | str | None = None
    grid_template_rows: CssValue | str | None = None
    hanging_punctuation: CssValue | str | None = None
    height: HeightValue | builtins.int | builtins.float | None = None
    hyphenate_character: CssValue | str | None = None
    hyphenate_limit_chars: CssValue | str | None = None
    hyphenate_limit_last: CssValue | str | None = None
    hyphenate_limit_lines: CssValue | str | None = None
    hyphenate_limit_zone: LengthPercentage | builtins.int | builtins.float | None = None
    hyphens: CssValue | str | None = None
    image_animation: CssValue | str | None = None
    image_orientation: AngleValue | None = None
    image_rendering: CssValue | str | None = None
    image_resolution: CssValue | str | None = None
    initial_letter: CssValue | str | None = None
    initial_letter_align: CssValue | str | None = None
    initial_letter_wrap: LengthPercentage | builtins.int | builtins.float | None = None
    inline_size: CssValue | str | None = None
    inline_sizing: CssValue | str | None = None
    input_security: CssValue | str | None = None
    inset: SpacingShorthand | builtins.int | builtins.float | None = None
    inset_block: SpacingShorthand | builtins.int | builtins.float | None = None
    inset_block_end: SpacingShorthand | builtins.int | builtins.float | None = None
    inset_block_start: SpacingShorthand | builtins.int | builtins.float | None = None
    inset_inline: SpacingShorthand | builtins.int | builtins.float | None = None
    inset_inline_end: SpacingShorthand | builtins.int | builtins.float | None = None
    inset_inline_start: SpacingShorthand | builtins.int | builtins.float | None = None
    interactivity: CssValue | str | None = None
    interest_delay: CssValue | str | None = None
    interest_delay_end: TimeValue | None = None
    interest_delay_start: TimeValue | None = None
    interpolate_size: CssValue | str | None = None
    isolation: CssValue | str | None = None
    justify_content: JustifyContent | None = None
    justify_items: CssValue | str | None = None
    justify_self: CssValue | str | None = None
    left: LengthPercentage | builtins.int | builtins.float | None = None
    letter_spacing: LengthPercentage | builtins.int | builtins.float | None = None
    lighting_color: ColorValue | None = None
    line_break: CssValue | str | None = None
    line_clamp: CssValue | str | None = None
    line_fit_edge: CssValue | str | None = None
    line_grid: CssValue | str | None = None
    line_height: LineHeightValue | builtins.int | builtins.float | None = None
    line_height_step: Length | builtins.int | builtins.float | None = None
    line_padding: Length | builtins.int | builtins.float | None = None
    line_snap: CssValue | str | None = None
    link_parameters: CssValue | str | None = None
    list_style: CssValue | str | None = None
    list_style_image: CssValue | str | None = None
    list_style_position: CssValue | str | None = None
    list_style_type: CssValue | str | None = None
    margin: SpacingShorthand | builtins.int | builtins.float | None = None
    margin_block: SpacingShorthand | builtins.int | builtins.float | None = None
    margin_block_end: SpacingShorthand | builtins.int | builtins.float | None = None
    margin_block_start: SpacingShorthand | builtins.int | builtins.float | None = None
    margin_bottom: SpacingShorthand | builtins.int | builtins.float | None = None
    margin_break: SpacingShorthand | builtins.int | builtins.float | None = None
    margin_inline: SpacingShorthand | builtins.int | builtins.float | None = None
    margin_inline_end: SpacingShorthand | builtins.int | builtins.float | None = None
    margin_inline_start: SpacingShorthand | builtins.int | builtins.float | None = None
    margin_left: SpacingShorthand | builtins.int | builtins.float | None = None
    margin_right: SpacingShorthand | builtins.int | builtins.float | None = None
    margin_top: SpacingShorthand | builtins.int | builtins.float | None = None
    margin_trim: SpacingShorthand | builtins.int | builtins.float | None = None
    marker: CssValue | str | None = None
    marker_end: CssValue | str | None = None
    marker_mid: CssValue | str | None = None
    marker_side: CssValue | str | None = None
    marker_start: CssValue | str | None = None
    mask: CssValue | str | None = None
    mask_border: CssValue | str | None = None
    mask_border_mode: CssValue | str | None = None
    mask_border_outset: Length | builtins.int | builtins.float | None = None
    mask_border_repeat: CssValue | str | None = None
    mask_border_slice: CssValue | str | None = None
    mask_border_source: CssValue | str | None = None
    mask_border_width: WidthValue | builtins.int | builtins.float | None = None
    mask_clip: CssValue | str | None = None
    mask_composite: CssValue | str | None = None
    mask_image: CssValue | str | None = None
    mask_mode: CssValue | str | None = None
    mask_origin: CssValue | str | None = None
    mask_position: CssValue | str | None = None
    mask_repeat: CssValue | str | None = None
    mask_size: CssValue | str | None = None
    mask_type: CssValue | str | None = None
    math_depth: CssValue | str | None = None
    math_shift: CssValue | str | None = None
    math_style: CssValue | str | None = None
    max_block_size: CssValue | str | None = None
    max_height: HeightValue | builtins.int | builtins.float | None = None
    max_inline_size: CssValue | str | None = None
    max_lines: CssValue | str | None = None
    max_width: WidthValue | builtins.int | builtins.float | None = None
    min_block_size: CssValue | str | None = None
    min_height: HeightValue | builtins.int | builtins.float | None = None
    min_inline_size: CssValue | str | None = None
    min_intrinsic_sizing: CssValue | str | None = None
    min_width: WidthValue | builtins.int | builtins.float | None = None
    mix_blend_mode: CssValue | str | None = None
    nav_down: CssValue | str | None = None
    nav_left: CssValue | str | None = None
    nav_right: CssValue | str | None = None
    nav_up: CssValue | str | None = None
    object_fit: CssValue | str | None = None
    object_position: CssValue | str | None = None
    object_view_box: CssValue | str | None = None
    offset: CssValue | str | None = None
    offset_anchor: CssValue | str | None = None
    offset_distance: LengthPercentage | builtins.int | builtins.float | None = None
    offset_path: CssValue | str | None = None
    offset_position: CssValue | str | None = None
    offset_rotate: AngleValue | None = None
    opacity: builtins.float | None = None
    order: CssValue | str | None = None
    orphans: CssValue | str | None = None
    outline: CssValue | str | None = None
    outline_color: ColorValue | None = None
    outline_offset: Length | builtins.int | builtins.float | None = None
    outline_style: CssValue | str | None = None
    outline_width: WidthValue | builtins.int | builtins.float | None = None
    overflow: Overflow | CssValue | None = None
    overflow_anchor: Overflow | None = None
    overflow_block: Overflow | None = None
    overflow_clip_margin: Overflow | CssValue | builtins.int | builtins.float | None = None
    overflow_clip_margin_block: Overflow | CssValue | builtins.int | builtins.float | None = None
    overflow_clip_margin_block_end: Overflow | builtins.int | builtins.float | None = None
    overflow_clip_margin_block_start: Overflow | builtins.int | builtins.float | None = None
    overflow_clip_margin_bottom: Overflow | builtins.int | builtins.float | None = None
    overflow_clip_margin_inline: Overflow | CssValue | builtins.int | builtins.float | None = None
    overflow_clip_margin_inline_end: Overflow | builtins.int | builtins.float | None = None
    overflow_clip_margin_inline_start: Overflow | builtins.int | builtins.float | None = None
    overflow_clip_margin_left: Overflow | builtins.int | builtins.float | None = None
    overflow_clip_margin_right: Overflow | builtins.int | builtins.float | None = None
    overflow_clip_margin_top: Overflow | builtins.int | builtins.float | None = None
    overflow_inline: Overflow | None = None
    overflow_wrap: Overflow | None = None
    overflow_x: Overflow | None = None
    overflow_y: Overflow | None = None
    overlay: CssValue | str | None = None
    overscroll_behavior: CssValue | str | None = None
    overscroll_behavior_block: CssValue | str | None = None
    overscroll_behavior_inline: CssValue | str | None = None
    overscroll_behavior_x: CssValue | str | None = None
    overscroll_behavior_y: CssValue | str | None = None
    padding: SpacingShorthand | builtins.int | builtins.float | None = None
    padding_block: SpacingShorthand | builtins.int | builtins.float | None = None
    padding_block_end: SpacingShorthand | builtins.int | builtins.float | None = None
    padding_block_start: SpacingShorthand | builtins.int | builtins.float | None = None
    padding_bottom: SpacingShorthand | builtins.int | builtins.float | None = None
    padding_inline: SpacingShorthand | builtins.int | builtins.float | None = None
    padding_inline_end: SpacingShorthand | builtins.int | builtins.float | None = None
    padding_inline_start: SpacingShorthand | builtins.int | builtins.float | None = None
    padding_left: SpacingShorthand | builtins.int | builtins.float | None = None
    padding_right: SpacingShorthand | builtins.int | builtins.float | None = None
    padding_top: SpacingShorthand | builtins.int | builtins.float | None = None
    page: CssValue | str | None = None
    page_break_after: CssValue | str | None = None
    page_break_before: CssValue | str | None = None
    page_break_inside: CssValue | str | None = None
    paint_order: CssValue | str | None = None
    pause: CssValue | str | None = None
    pause_after: TimeValue | None = None
    pause_before: TimeValue | None = None
    perspective: Length | builtins.int | builtins.float | None = None
    perspective_origin: CssValue | str | None = None
    place_content: CssValue | str | None = None
    place_items: CssValue | str | None = None
    place_self: CssValue | str | None = None
    pointer_events: CssValue | str | None = None
    pointer_timeline: CssValue | str | None = None
    pointer_timeline_axis: CssValue | str | None = None
    pointer_timeline_name: CssValue | str | None = None
    position: Position | None = None
    position_anchor: CssValue | str | None = None
    position_area: CssValue | str | None = None
    position_try: CssValue | str | None = None
    position_try_fallbacks: CssValue | str | None = None
    position_try_order: CssValue | str | None = None
    position_visibility: CssValue | str | None = None
    print_color_adjust: CssValue | str | None = None
    quotes: CssValue | str | None = None
    r: LengthPercentage | builtins.int | builtins.float | None = None
    reading_flow: CssValue | str | None = None
    reading_order: CssValue | str | None = None
    region_fragment: CssValue | str | None = None
    resize: CssValue | str | None = None
    rest: CssValue | str | None = None
    rest_after: TimeValue | None = None
    rest_before: TimeValue | None = None
    right: LengthPercentage | builtins.int | builtins.float | None = None
    rotate: AngleValue | None = None
    row_gap: GapValue | builtins.int | builtins.float | None = None
    row_rule: CssValue | str | None = None
    row_rule_break: CssValue | str | None = None
    row_rule_color: ColorValue | None = None
    row_rule_edge_inset: LengthPercentage | CssValue | builtins.int | builtins.float | None = None
    row_rule_edge_inset_end: LengthPercentage | builtins.int | builtins.float | None = None
    row_rule_edge_inset_start: LengthPercentage | builtins.int | builtins.float | None = None
    row_rule_inset: CssValue | str | None = None
    row_rule_inset_end: LengthPercentage | CssValue | builtins.int | builtins.float | None = None
    row_rule_inset_start: LengthPercentage | CssValue | builtins.int | builtins.float | None = None
    row_rule_interior_inset: LengthPercentage | CssValue | builtins.int | builtins.float | None = (
        None
    )
    row_rule_interior_inset_end: LengthPercentage | builtins.int | builtins.float | None = None
    row_rule_interior_inset_start: LengthPercentage | builtins.int | builtins.float | None = None
    row_rule_style: CssValue | str | None = None
    row_rule_visibility_items: CssValue | str | None = None
    row_rule_width: WidthValue | builtins.int | builtins.float | None = None
    ruby_align: CssValue | str | None = None
    ruby_merge: CssValue | str | None = None
    ruby_overhang: CssValue | str | None = None
    ruby_position: CssValue | str | None = None
    rule: CssValue | str | None = None
    rule_break: CssValue | str | None = None
    rule_color: ColorValue | CssValue | None = None
    rule_edge_inset: CssValue | str | None = None
    rule_inset: CssValue | str | None = None
    rule_inset_end: CssValue | str | None = None
    rule_inset_start: CssValue | str | None = None
    rule_interior_inset: CssValue | str | None = None
    rule_overlap: CssValue | str | None = None
    rule_style: CssValue | str | None = None
    rule_visibility_items: CssValue | str | None = None
    rule_width: WidthValue | builtins.int | builtins.float | None = None
    rx: LengthPercentage | builtins.int | builtins.float | None = None
    ry: LengthPercentage | builtins.int | builtins.float | None = None
    scale: CssValue | str | None = None
    scroll_behavior: CssValue | str | None = None
    scroll_initial_target: CssValue | str | None = None
    scroll_margin: Length | CssValue | builtins.int | builtins.float | None = None
    scroll_margin_block: Length | CssValue | builtins.int | builtins.float | None = None
    scroll_margin_block_end: Length | builtins.int | builtins.float | None = None
    scroll_margin_block_start: Length | builtins.int | builtins.float | None = None
    scroll_margin_bottom: Length | builtins.int | builtins.float | None = None
    scroll_margin_inline: Length | CssValue | builtins.int | builtins.float | None = None
    scroll_margin_inline_end: Length | builtins.int | builtins.float | None = None
    scroll_margin_inline_start: Length | builtins.int | builtins.float | None = None
    scroll_margin_left: Length | builtins.int | builtins.float | None = None
    scroll_margin_right: Length | builtins.int | builtins.float | None = None
    scroll_margin_top: Length | builtins.int | builtins.float | None = None
    scroll_marker_group: CssValue | str | None = None
    scroll_padding: LengthPercentage | CssValue | builtins.int | builtins.float | None = None
    scroll_padding_block: LengthPercentage | CssValue | builtins.int | builtins.float | None = None
    scroll_padding_block_end: LengthPercentage | builtins.int | builtins.float | None = None
    scroll_padding_block_start: LengthPercentage | builtins.int | builtins.float | None = None
    scroll_padding_bottom: LengthPercentage | builtins.int | builtins.float | None = None
    scroll_padding_inline: LengthPercentage | CssValue | builtins.int | builtins.float | None = None
    scroll_padding_inline_end: LengthPercentage | builtins.int | builtins.float | None = None
    scroll_padding_inline_start: LengthPercentage | builtins.int | builtins.float | None = None
    scroll_padding_left: LengthPercentage | builtins.int | builtins.float | None = None
    scroll_padding_right: LengthPercentage | builtins.int | builtins.float | None = None
    scroll_padding_top: LengthPercentage | builtins.int | builtins.float | None = None
    scroll_snap_align: CssValue | str | None = None
    scroll_snap_stop: CssValue | str | None = None
    scroll_snap_type: CssValue | str | None = None
    scroll_target_group: CssValue | str | None = None
    scroll_timeline: CssValue | str | None = None
    scroll_timeline_axis: CssValue | str | None = None
    scroll_timeline_name: CssValue | str | None = None
    scrollbar_color: ColorValue | None = None
    scrollbar_gutter: CssValue | str | None = None
    scrollbar_width: WidthValue | builtins.int | builtins.float | None = None
    shape_image_threshold: CssValue | str | None = None
    shape_inside: CssValue | str | None = None
    shape_margin: LengthPercentage | builtins.int | builtins.float | None = None
    shape_outside: CssValue | str | None = None
    shape_padding: LengthPercentage | builtins.int | builtins.float | None = None
    shape_rendering: CssValue | str | None = None
    shape_subtract: CssValue | str | None = None
    slider_orientation: CssValue | str | None = None
    spatial_navigation_action: CssValue | str | None = None
    spatial_navigation_contain: CssValue | str | None = None
    spatial_navigation_function: CssValue | str | None = None
    speak: CssValue | str | None = None
    speak_as: CssValue | str | None = None
    stop_color: ColorValue | None = None
    stop_opacity: CssValue | str | None = None
    string_set: CssValue | str | None = None
    stroke: CssValue | str | None = None
    stroke_align: CssValue | str | None = None
    stroke_alignment: CssValue | str | None = None
    stroke_break: CssValue | str | None = None
    stroke_color: ColorValue | None = None
    stroke_dash_corner: Length | builtins.int | builtins.float | None = None
    stroke_dash_justify: CssValue | str | None = None
    stroke_dashadjust: CssValue | str | None = None
    stroke_dasharray: LengthPercentage | builtins.int | builtins.float | None = None
    stroke_dashcorner: Length | builtins.int | builtins.float | None = None
    stroke_dashoffset: LengthPercentage | builtins.int | builtins.float | None = None
    stroke_image: CssValue | str | None = None
    stroke_linecap: CssValue | str | None = None
    stroke_linejoin: CssValue | str | None = None
    stroke_miterlimit: CssValue | str | None = None
    stroke_opacity: CssValue | str | None = None
    stroke_origin: CssValue | str | None = None
    stroke_position: CssValue | str | None = None
    stroke_repeat: CssValue | str | None = None
    stroke_size: CssValue | str | None = None
    stroke_width: WidthValue | builtins.int | builtins.float | None = None
    tab_size: Length | builtins.int | builtins.float | None = None
    table_layout: CssValue | str | None = None
    text_align: TextAlign | CssValue | None = None
    text_align_all: CssValue | str | None = None
    text_align_last: CssValue | str | None = None
    text_anchor: CssValue | str | None = None
    text_autospace: CssValue | str | None = None
    text_box: CssValue | str | None = None
    text_box_edge: CssValue | str | None = None
    text_box_trim: CssValue | str | None = None
    text_combine_upright: CssValue | str | None = None
    text_decoration: CssValue | str | None = None
    text_decoration_color: ColorValue | None = None
    text_decoration_inset: Length | builtins.int | builtins.float | None = None
    text_decoration_line: CssValue | str | None = None
    text_decoration_skip: CssValue | str | None = None
    text_decoration_skip_box: CssValue | str | None = None
    text_decoration_skip_ink: CssValue | str | None = None
    text_decoration_skip_self: CssValue | str | None = None
    text_decoration_skip_spaces: CssValue | str | None = None
    text_decoration_style: CssValue | str | None = None
    text_decoration_thickness: LengthPercentage | builtins.int | builtins.float | None = None
    text_emphasis: CssValue | str | None = None
    text_emphasis_color: ColorValue | None = None
    text_emphasis_position: CssValue | str | None = None
    text_emphasis_skip: CssValue | str | None = None
    text_emphasis_style: CssValue | str | None = None
    text_group_align: CssValue | str | None = None
    text_indent: LengthPercentage | builtins.int | builtins.float | None = None
    text_justify: CssValue | str | None = None
    text_orientation: CssValue | str | None = None
    text_overflow: CssValue | str | None = None
    text_rendering: CssValue | str | None = None
    text_shadow: CssValue | str | None = None
    text_size_adjust: CssValue | str | None = None
    text_spacing: CssValue | str | None = None
    text_spacing_trim: CssValue | str | None = None
    text_transform: CssValue | str | None = None
    text_underline_offset: LengthPercentage | builtins.int | builtins.float | None = None
    text_underline_position: CssValue | str | None = None
    text_wrap: CssValue | str | None = None
    text_wrap_mode: CssValue | str | None = None
    text_wrap_style: CssValue | str | None = None
    timeline_scope: CssValue | str | None = None
    timeline_trigger: CssValue | str | None = None
    timeline_trigger_activation_range: CssValue | str | None = None
    timeline_trigger_activation_range_end: (
        LengthPercentage | builtins.int | builtins.float | None
    ) = None
    timeline_trigger_activation_range_start: (
        LengthPercentage | builtins.int | builtins.float | None
    ) = None
    timeline_trigger_active_range: CssValue | str | None = None
    timeline_trigger_active_range_end: LengthPercentage | builtins.int | builtins.float | None = (
        None
    )
    timeline_trigger_active_range_start: LengthPercentage | builtins.int | builtins.float | None = (
        None
    )
    timeline_trigger_name: CssValue | str | None = None
    timeline_trigger_source: CssValue | str | None = None
    top: LengthPercentage | builtins.int | builtins.float | None = None
    touch_action: CssValue | str | None = None
    transform: TransformValue | None = None
    transform_box: CssValue | str | None = None
    transform_origin: LengthPercentage | builtins.int | builtins.float | None = None
    transform_style: CssValue | str | None = None
    transition: TransitionValue | None = None
    transition_behavior: TransitionValue | None = None
    transition_delay: TransitionValue | None = None
    transition_duration: TransitionValue | None = None
    transition_property: TransitionValue | None = None
    transition_timing_function: TransitionValue | None = None
    translate: LengthPercentage | builtins.int | builtins.float | None = None
    trigger_scope: CssValue | str | None = None
    unicode_bidi: CssValue | str | None = None
    user_select: CssValue | str | None = None
    vector_effect: CssValue | str | None = None
    vertical_align: CssValue | str | None = None
    view_timeline: CssValue | str | None = None
    view_timeline_axis: CssValue | str | None = None
    view_timeline_inset: LengthPercentage | builtins.int | builtins.float | None = None
    view_timeline_name: CssValue | str | None = None
    view_transition_class: CssValue | str | None = None
    view_transition_group: CssValue | str | None = None
    view_transition_name: CssValue | str | None = None
    view_transition_scope: CssValue | str | None = None
    visibility: CssValue | str | None = None
    voice_balance: CssValue | str | None = None
    voice_duration: TimeValue | None = None
    voice_family: CssValue | str | None = None
    voice_pitch: CssValue | str | None = None
    voice_range: CssValue | str | None = None
    voice_rate: CssValue | str | None = None
    voice_stress: CssValue | str | None = None
    voice_volume: CssValue | str | None = None
    white_space: CssValue | str | None = None
    white_space_collapse: CssValue | str | None = None
    white_space_trim: CssValue | str | None = None
    widows: CssValue | str | None = None
    width: WidthValue | builtins.int | builtins.float | None = None
    will_change: CssValue | str | None = None
    word_break: CssValue | str | None = None
    word_space_transform: CssValue | str | None = None
    word_spacing: LengthPercentage | builtins.int | builtins.float | None = None
    word_wrap: CssValue | str | None = None
    wrap_after: CssValue | str | None = None
    wrap_before: CssValue | str | None = None
    wrap_flow: CssValue | str | None = None
    wrap_inside: CssValue | str | None = None
    wrap_through: CssValue | str | None = None
    writing_mode: CssValue | str | None = None
    x: LengthPercentage | builtins.int | builtins.float | None = None
    y: LengthPercentage | builtins.int | builtins.float | None = None
    z_index: builtins.int | Literal["auto"] | None = None
    zoom: CssValue | str | None = None


@dataclass(frozen=True, kw_only=True)
class MediaRule:
    """Generated media query rule for `h.media(...)`.

    Represents a typed subset of standard CSS media features.
    Reference: https://developer.mozilla.org/en-US/docs/Web/CSS/@media
    """

    style: Style
    any_hover: HoverCapability | None = None
    any_pointer: PointerCapability | None = None
    aspect_ratio: CssValue | None = None
    color: CssValue | None = None
    color_gamut: CssValue | None = None
    color_index: CssValue | None = None
    device_aspect_ratio: CssValue | None = None
    device_height: CssValue | None = None
    device_width: CssValue | None = None
    display_mode: CssValue | None = None
    dynamic_range: CssValue | None = None
    environment_blending: CssValue | None = None
    forced_colors: CssValue | None = None
    grid: CssValue | None = None
    height: CssValue | None = None
    horizontal_viewport_segments: CssValue | None = None
    hover: HoverCapability | None = None
    inverted_colors: CssValue | None = None
    max_height: Length | None = None
    max_width: Length | None = None
    min_height: Length | None = None
    min_width: Length | None = None
    monochrome: CssValue | None = None
    nav_controls: CssValue | None = None
    orientation: Orientation | None = None
    overflow_block: CssValue | None = None
    overflow_inline: CssValue | None = None
    pointer: PointerCapability | None = None
    prefers_color_scheme: PrefersColorScheme | None = None
    prefers_contrast: CssValue | None = None
    prefers_reduced_data: CssValue | None = None
    prefers_reduced_motion: PrefersReducedMotion | None = None
    prefers_reduced_transparency: CssValue | None = None
    resolution: CssValue | None = None
    scan: CssValue | None = None
    scripting: CssValue | None = None
    shape: CssValue | None = None
    update: CssValue | None = None
    vertical_viewport_segments: CssValue | None = None
    video_color_gamut: CssValue | None = None
    video_dynamic_range: CssValue | None = None
    width: CssValue | None = None
    query: str | None = None
