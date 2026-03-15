"""Standalone trellis.html showcase for semantic HTML and typed CSS."""

from __future__ import annotations

from dataclasses import dataclass

from trellis import component
from trellis import html as h
from trellis import widgets as w
from trellis.app import App
from trellis.widgets import IconName


@dataclass(frozen=True)
class FeatureCard:
    eyebrow: str
    title: str
    body: str
    points: tuple[str, ...]
    accent: str
    icon: IconName


@dataclass(frozen=True)
class ReleaseNote:
    title: str
    body: str
    stamp: str


FEATURE_CARDS: tuple[FeatureCard, ...] = (
    FeatureCard(
        eyebrow="Native semantics",
        title="Author the DOM directly",
        body=(
            "Build pages with header, section, article, figure, details, and form elements "
            "instead of hiding everything behind a widget layer."
        ),
        points=("Semantic structure", "Typed attributes", "Predictable DOM output"),
        accent="--lagoon",
        icon=IconName.BRACES,
    ),
    FeatureCard(
        eyebrow="Typed styling",
        title="Use CSS as a language, not a string blob",
        body=(
            "Reach for Style, border, padding, media, and modern color helpers first, "
            "then drop to raw dicts only when you need a browser-specific edge."
        ),
        points=("Structured shorthands", "Pseudo states", "Custom properties"),
        accent="--ember",
        icon=IconName.SLIDERS_HORIZONTAL,
    ),
    FeatureCard(
        eyebrow="Responsive by default",
        title="Keep layout decisions in the component tree",
        body=(
            "Typed media helpers make responsive changes visible at the call site, "
            "which keeps component behavior and presentation in one place."
        ),
        points=("Responsive grids", "Focus states", "Selector support"),
        accent="--violet",
        icon=IconName.LAYOUT_GRID,
    ),
)

RELEASE_NOTES: tuple[ReleaseNote, ...] = (
    ReleaseNote(
        title="Hero layout",
        body="The opening panel uses custom properties, typed media queries, and an editorial two-column composition.",
        stamp="March 8, 2026",
    ),
    ReleaseNote(
        title="Card interactions",
        body="Feature cards use hover and focus-within rules compiled into scoped classes instead of inline-only styles.",
        stamp="March 8, 2026",
    ),
    ReleaseNote(
        title="HTML-first form",
        body="The closing form demonstrates native labels, inputs, buttons, placeholders, and keyboard-visible focus styling.",
        stamp="March 8, 2026",
    ),
)

FONT_DISPLAY = '"Didot", "Bodoni MT", "Noto Serif Display", "URW Palladio L", serif'
FONT_BODY = '"Optima", Candara, "Noto Sans", system-ui, sans-serif'
FONT_MONO = '"SF Mono", "Cascadia Mono", "IBM Plex Mono", monospace'

HERO_IMAGE = (
    "https://images.unsplash.com/photo-1518005020951-eccb494ad742?auto=format&fit=crop&w=1200&q=80"
)

DETAIL_IMAGE = (
    "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1200&q=80"
)


_shell_cls = h.CssClass(
    "shell",
    selection=h.Css(
        background_color=h.var("--lagoon"),
        color="white",
    ),
    media=[
        h.media(
            min_width=880,
            style=h.Css(padding=h.padding(64, 48, 120)),
        )
    ],
)


def _shell_style() -> h.Css:
    return h.Css(
        vars={
            "--paper": h.oklch(0.979, 0.008, 92),
            "--ink": h.oklch(0.25, 0.024, 258),
            "--muted": h.oklch(0.55, 0.02, 250),
            "--panel": h.rgba(255, 252, 248, 0.84),
            "--line": h.rgba(31, 28, 37, 0.09),
            "--lagoon": h.oklch(0.71, 0.13, 214),
            "--ember": h.oklch(0.73, 0.15, 42),
            "--violet": h.oklch(0.69, 0.12, 312),
            "--shadow": h.rgba(15, 19, 32, 0.08),
        },
        min_height=h.vh(100),
        color=h.var("--ink"),
        background_color=h.var("--paper"),
        background_image=h.raw(
            "radial-gradient(circle at 0% 0%, color-mix(in srgb, var(--lagoon) 14%, transparent) 0, transparent 30%), "
            "radial-gradient(circle at 100% 0%, color-mix(in srgb, var(--ember) 12%, transparent) 0, transparent 28%), "
            "linear-gradient(180deg, rgba(255,255,255,0.78), rgba(255,250,244,0.96))"
        ),
        padding=h.padding(48, 28, 96),
        font_family=FONT_BODY,
        line_height=1.6,
    )


_page_frame_cls = h.CssClass(
    "page-frame",
    media=[h.media(min_width=960, style=h.Css(gap=72))],
)


def _page_frame_style() -> h.Css:
    # Use flex + gap instead of "& > * + *" margin because Trellis wraps
    # each component in a <span display="contents">, which swallows margin.
    return h.Css(
        display="flex",
        flex_direction="column",
        gap=56,
        width=h.min_(h.px(1220), h.pct(100)),
        margin=h.raw("0 auto"),
    )


_panel_cls = h.CssClass(
    "panel",
    media=[
        h.media(
            min_width=960,
            style=h.Css(padding=40),
        ),
    ],
)

_panel_accent_classes: dict[str, h.CssClass] = {}


def _panel_accent_cls(accent: str) -> h.CssClass:
    """Return a CssClass for a panel with an accent-colored ::before bar."""
    if accent not in _panel_accent_classes:
        _panel_accent_classes[accent] = h.CssClass(
            f"panel-accent-{accent.strip('-')}",
            before=h.Css(
                content='""',
                display="block",
                width=48,
                height=2,
                border_radius=999,
                background_color=h.var(accent),
                margin_bottom=24,
            ),
        )
    return _panel_accent_classes[accent]


def _panel_style() -> h.Css:
    # Use flex + gap for internal spacing: inline margin=0 on headings
    # would override a class-level "& > * + *" margin-top rule.
    return h.Css(
        display="flex",
        flex_direction="column",
        gap=20,
        background_color=h.var("--panel"),
        border=h.border(1, "solid", h.var("--line")),
        border_radius=14,
        padding=32,
        box_shadow="0 2px 4px -2px var(--shadow), 0 16px 40px -16px var(--shadow)",
    )


def _eyebrow_style() -> h.Style:
    return h.Style(
        margin=0,
        color=h.var("--muted"),
        font_size=12,
        font_family=FONT_MONO,
        letter_spacing=h.em(0.14),
        text_transform=h.raw("uppercase"),
    )


def _section_title_style() -> h.Style:
    return h.Style(
        margin=0,
        font_family=FONT_DISPLAY,
        font_size=h.clamp(h.px(30), h.vw(3.6), h.px(48)),
        line_height=1.1,
        letter_spacing=h.em(-0.02),
        max_width=h.ch(18),
    )


def _headline_style() -> h.Style:
    return h.Style(
        margin=0,
        font_family=FONT_DISPLAY,
        font_size=h.clamp(h.px(44), h.vw(6.6), h.px(80)),
        line_height=1.02,
        letter_spacing=h.em(-0.025),
        max_width=h.ch(14),
    )


def _body_copy_style() -> h.Style:
    return h.Style(
        margin=0,
        font_size=h.clamp(h.px(17), h.vw(1.8), h.px(20)),
        line_height=1.65,
        color=h.var("--muted"),
        max_width=h.rem(38),
    )


_hero_grid_cls = h.CssClass(
    "hero-grid",
    media=[
        h.media(
            min_width=980,
            style=h.Css(
                grid_template_columns="minmax(0, 1.1fr) minmax(23rem, 0.95fr)",
                gap=48,
            ),
        )
    ],
)


def _hero_grid_style() -> h.Css:
    return h.Css(
        display="grid",
        gap=36,
        align_items="start",
    )


_cta_link_cls = h.CssClass(
    "cta-link",
    hover=h.Css(transform=h.translate(0, -1), opacity=0.96),
    active=h.Css(transform=h.translate(0, 0)),
    focus_visible=h.Css(outline=h.border(2, "solid", h.var("--ink")), outline_offset=3),
)


def _cta_link_style(*, tone: str) -> h.Css:
    return h.Css(
        display="inline-flex",
        align_items="center",
        justify_content="center",
        gap=10,
        padding=h.padding(14, 24),
        border_radius=999,
        border=h.border(1, "solid", h.var("--line")),
        background_color=h.var(tone),
        color="white",
        text_decoration="none",
        font_size=15,
        font_weight=600,
        letter_spacing=h.em(0.01),
        transition="transform 160ms ease, opacity 160ms ease",
    )


_ghost_link_cls = h.CssClass(
    "ghost-link",
    hover=h.Css(background_color=h.rgba(255, 255, 255, 0.88)),
    focus_visible=h.Css(outline=h.border(2, "solid", h.var("--lagoon")), outline_offset=3),
)


def _ghost_link_style() -> h.Css:
    return h.Css(
        display="inline-flex",
        align_items="center",
        gap=8,
        padding=h.padding(14, 24),
        border_radius=999,
        border=h.border(1, "solid", h.var("--line")),
        color=h.var("--ink"),
        text_decoration="none",
        font_size=15,
        background_color=h.rgba(255, 255, 255, 0.58),
    )


def _hero_media_shell_style() -> h.Style:
    return h.Style(
        display="grid",
        gap=20,
        align_content=h.raw("start"),
    )


def _hero_figure_style() -> h.Style:
    return h.Style(
        margin=0,
        background_color=h.rgba(255, 255, 255, 0.58),
        border=h.border(1, "solid", h.var("--line")),
        border_radius=14,
        box_shadow="0 2px 4px -2px var(--shadow), 0 16px 40px -16px var(--shadow)",
        overflow="hidden",
    )


def _figure_caption_style() -> h.Style:
    return h.Style(
        display="flex",
        justify_content="space-between",
        gap=12,
        padding=h.padding(14, 20, 16),
        color=h.var("--muted"),
        font_size=13,
        background_color=h.rgba(255, 255, 255, 0.64),
    )


_metrics_cls = h.CssClass(
    "metrics",
    media=[
        h.media(
            min_width=560,
            style=h.Css(grid_template_columns="repeat(3, minmax(0, 1fr))"),
        ),
    ],
)


def _metrics_style() -> h.Css:
    return h.Css(
        display="grid",
        gap=14,
        margin=0,
    )


def _metrics_panel_style() -> h.Style:
    return h.Style(
        background_color=h.rgba(255, 255, 255, 0.72),
        border=h.border(1, "solid", h.var("--line")),
        border_radius=14,
        padding=24,
        box_shadow="0 2px 4px -2px var(--shadow), 0 12px 28px -16px var(--shadow)",
    )


_feature_grid_cls = h.CssClass(
    "feature-grid",
    media=[
        h.media(
            min_width=760,
            style=h.Css(grid_template_columns="repeat(2, minmax(0, 1fr))"),
        ),
        h.media(
            min_width=1120,
            style=h.Css(grid_template_columns="repeat(3, minmax(0, 1fr))"),
        ),
    ],
)


def _feature_grid_style() -> h.Css:
    return h.Css(
        display="grid",
        gap=24,
        align_items="stretch",
    )


_feature_card_classes: dict[str, h.CssClass] = {}


def _feature_card_cls(accent: str) -> h.CssClass:
    """Return a CssClass for a feature card with accent-colored hover/focus."""
    if accent not in _feature_card_classes:
        _feature_card_classes[accent] = h.CssClass(
            f"feature-card-{accent.strip('-')}",
            hover=h.Css(
                transform=h.translate(0, -2),
                border_color=h.var(accent),
                background_color=h.rgba(255, 255, 255, 0.8),
            ),
            focus_visible=h.Css(outline=h.border(2, "solid", h.var(accent)), outline_offset=3),
        )
    return _feature_card_classes[accent]


def _feature_card_style() -> h.Css:
    return h.Css(
        display="flex",
        flex_direction="column",
        gap=18,
        text_decoration="none",
        color=h.var("--ink"),
        background_color=h.rgba(255, 255, 255, 0.68),
        border=h.border(1, "solid", h.var("--line")),
        border_radius=14,
        padding=28,
        min_height=h.px(320),
        box_shadow="0 2px 4px -2px var(--shadow), 0 12px 30px -16px var(--shadow)",
        transition="transform 160ms ease, border-color 160ms ease, background-color 160ms ease",
    )


def _chip_style(accent: str) -> h.Style:
    return h.Style(
        display="inline-flex",
        align_items="center",
        border_radius=999,
        padding=h.padding(6, 14),
        background_color=f"color-mix(in srgb, var({accent}) 13%, white)",
        color=h.var(accent),
        font_size=12,
        font_family=FONT_MONO,
    )


def _timeline_style() -> h.Style:
    return h.Style(
        display="grid",
        gap=20,
    )


_input_cls = h.CssClass(
    "dispatch-input",
    placeholder=h.Css(color=h.var("--muted")),
    focus_visible=h.Css(
        border_color=h.var("--lagoon"),
        outline=h.border(2, "solid", h.rgba(0, 0, 0, 0)),
        box_shadow="0 0 0 3px color-mix(in srgb, var(--lagoon) 18%, transparent)",
    ),
)


def _input_style() -> h.Css:
    return h.Css(
        width=h.pct(100),
        padding=h.padding(14, 20),
        border=h.border(1, "solid", h.var("--line")),
        border_radius=12,
        background_color=h.rgba(255, 255, 255, 0.76),
        color=h.var("--ink"),
        font_size=16,
    )


_button_cls = h.CssClass(
    "dispatch-button",
    hover=h.Css(transform=h.translate(0, -1), opacity=0.96),
    active=h.Css(transform=h.translate(0, 0)),
    focus_visible=h.Css(outline=h.border(2, "solid", h.var("--lagoon")), outline_offset=3),
)


def _button_style() -> h.Css:
    return h.Css(
        padding=h.padding(14, 28),
        border=h.border(1, "solid", h.var("--ink")),
        border_radius=12,
        background_color=h.var("--ink"),
        color="white",
        font_size=15,
        font_weight=600,
        letter_spacing=h.em(0.02),
        cursor="pointer",
        transition="transform 160ms ease, opacity 160ms ease",
    )


_chrome_header_cls = h.CssClass(
    "chrome-header",
    media=[
        h.media(
            min_width=760,
            style=h.Css(
                flex_direction="row",
                align_items="end",
                justify_content="space-between",
            ),
        )
    ],
)

_nav_link_cls = h.CssClass(
    "nav-link",
    hover=h.Css(
        color=h.var("--ink"),
        background_color=h.rgba(255, 255, 255, 0.48),
    ),
    focus_visible=h.Css(
        outline=h.border(2, "solid", h.var("--lagoon")),
        outline_offset=3,
    ),
)


@component
def ChromeHeader() -> None:
    """Render the editorial header and compact navigation."""
    h.StyleTag(str(_chrome_header_cls) + str(_nav_link_cls))
    with h.Header(
        style=h.Css(
            display="flex",
            flex_direction="column",
            gap=20,
            padding_bottom=12,
            border_bottom=h.border(1, "solid", h.rgba(31, 28, 37, 0.06)),
        ),
        class_name=_chrome_header_cls.class_name,
    ):
        with h.Div(style=h.Style(display="flex", flex_direction="column", gap=10)):
            h.P(
                "HTML Studio",
                style=_eyebrow_style(),
            )
            h.H2(
                "A semantic page built directly with trellis.html.",
                style=h.Style(
                    margin=0,
                    font_family=FONT_DISPLAY,
                    font_size=h.clamp(h.px(22), h.vw(2.2), h.px(30)),
                    line_height=1.08,
                    max_width=h.ch(18),
                ),
            )
        with h.Nav(aria_label="Section links"):
            with h.Ul(
                style=h.Style(
                    display="flex",
                    flex_wrap="wrap",
                    gap=12,
                    list_style="none",
                    margin=0,
                    padding=0,
                )
            ):
                for href, label in (
                    ("#capabilities", "Capabilities"),
                    ("#notes", "Notes"),
                    ("#dispatch", "Dispatch"),
                ):
                    with h.Li():
                        h.A(
                            label,
                            href=href,
                            use_router=False,
                            style=h.Css(
                                color=h.var("--muted"),
                                text_decoration="none",
                                padding=h.padding(8, 14),
                                border_radius=999,
                            ),
                            class_name=_nav_link_cls.class_name,
                        )


@component
def HeroSection() -> None:
    """Render the hero with structured styles and a responsive metrics panel."""
    h.StyleTag(str(_hero_grid_cls) + str(_cta_link_cls) + str(_ghost_link_cls) + str(_metrics_cls))
    with h.Section(style=_hero_grid_style(), class_name=_hero_grid_cls.class_name):
        with h.Div(style=h.Style(display="flex", flex_direction="column", gap=24)):
            h.P("March field notes / typed HTML + CSS", style=_eyebrow_style())
            h.H1(
                "Compose rich pages with semantic tags, structured style, and full typed CSS coverage.",
                style=_headline_style(),
            )
            h.P(
                "This example demonstrates how trellis.html feels when you treat HTML and CSS as first-class authoring tools instead of a thin transport layer.",
                style=_body_copy_style(),
            )
            with h.Div(
                style=h.Style(
                    display="flex",
                    flex_wrap="wrap",
                    gap=14,
                    padding_top=12,
                )
            ):
                h.A(
                    "Inspect the source",
                    href="https://developer.mozilla.org/en-US/docs/Web/HTML",
                    target="_blank",
                    rel="noreferrer",
                    style=_cta_link_style(tone="--lagoon"),
                    class_name=_cta_link_cls.class_name,
                )
                h.A(
                    "Review the CSS model",
                    href="#dispatch",
                    use_router=False,
                    style=_ghost_link_style(),
                    class_name=_ghost_link_cls.class_name,
                )

        with h.Div(style=_hero_media_shell_style()):
            with h.Figure(style=_hero_figure_style()):
                h.Img(
                    src=HERO_IMAGE,
                    alt="Warm daylight falling across a contemporary studio building interior.",
                    style=h.Style(
                        display="block",
                        width=h.pct(100),
                        height=360,
                        object_fit=h.raw("cover"),
                        object_position=h.raw("center"),
                    ),
                )
                with h.Figcaption(style=_figure_caption_style()):
                    h.Span("Editorial reference")
                    h.Span("Photo: Unsplash")
            with h.Div(style=_metrics_panel_style()):
                h.P(
                    "What this page is exercising",
                    style=h.Style(margin=0, color=h.var("--muted"), font_size=13),
                )
                with h.Dl(style=_metrics_style(), class_name=_metrics_cls.class_name):
                    for value, label in (
                        ("12", "semantic tags"),
                        ("5", "CSS helper families"),
                        ("0", "raw dict escape hatches"),
                    ):
                        with h.Div(
                            style=h.Style(
                                padding_top=16,
                                border_top=h.border(1, "solid", h.var("--line")),
                            )
                        ):
                            h.Dt(
                                value,
                                style=h.Style(
                                    margin=0,
                                    font_family=FONT_DISPLAY,
                                    font_size=36,
                                    line_height=1,
                                ),
                            )
                            h.Dd(
                                label,
                                style=h.Style(margin=0, color=h.var("--muted")),
                            )


@component
def CapabilityCard(card: FeatureCard) -> None:
    """Render a feature card for a single HTML/CSS capability."""
    card_cls = _feature_card_cls(card.accent)
    h.StyleTag(str(card_cls))
    with h.Article(style=_feature_card_style(), class_name=card_cls.class_name):
        with h.Div(style=h.Style(display="flex", align_items="center", gap=12)):
            w.Icon(name=card.icon, size=18, color=f"var({card.accent})")
            h.P(card.eyebrow, style=_eyebrow_style())
        h.H3(
            card.title,
            style=h.Style(
                margin=0,
                font_family=FONT_DISPLAY,
                font_size=26,
                line_height=1.1,
                max_width=h.ch(15),
            ),
        )
        h.P(card.body, style=h.Style(margin=0, color=h.var("--muted"), font_size=15))
        with h.Ul(
            style=h.Style(
                list_style="none",
                margin=0,
                padding=0,
                display="flex",
                flex_wrap="wrap",
                gap=10,
            )
        ):
            for point in card.points:
                with h.Li():
                    h.Span(point, style=_chip_style(card.accent))


@component
def CapabilitiesSection() -> None:
    """Render the capability cards and a semantic note panel."""
    h.StyleTag(str(_feature_grid_cls))
    with h.Section(
        id="capabilities", style=h.Style(display="flex", flex_direction="column", gap=24)
    ):
        h.P("Feature sample", style=_eyebrow_style())
        h.H2(
            "A single page can show the full authoring model without pretending to be a CSS playground.",
            style=_section_title_style(),
        )
        with h.Div(style=_feature_grid_style(), class_name=_feature_grid_cls.class_name):
            for card in FEATURE_CARDS:
                CapabilityCard(card=card)


_notes_section_cls = h.CssClass(
    "notes-section",
    media=[
        h.media(
            min_width=980,
            style=h.Css(grid_template_columns="minmax(0, 1.08fr) minmax(22rem, 0.92fr)"),
        )
    ],
)

_summary_cls = h.CssClass(
    "details-summary",
    hover=h.Css(color=h.var("--violet")),
    focus_visible=h.Css(outline=h.border(2, "solid", h.var("--violet")), outline_offset=3),
)


@component
def NotesSection() -> None:
    """Render release notes plus an explainer details block."""
    ember_accent_cls = _panel_accent_cls("--ember")
    violet_accent_cls = _panel_accent_cls("--violet")
    h.StyleTag(
        str(_notes_section_cls)
        + str(_panel_cls)
        + str(ember_accent_cls)
        + str(violet_accent_cls)
        + str(_summary_cls)
    )
    with h.Section(
        id="notes",
        style=h.Css(
            display="grid",
            gap=24,
        ),
        class_name=_notes_section_cls.class_name,
    ):
        with h.Div(
            style=_panel_style(),
            class_name=f"{_panel_cls.class_name} {ember_accent_cls.class_name}",
        ):
            h.P("Release notes", style=_eyebrow_style())
            h.H2(
                "The CSS layer stays close to the DOM, so layout decisions remain visible in component code.",
                style=_section_title_style(),
            )
            with h.Figure(
                style=h.Style(
                    margin=0,
                    border_radius=12,
                    overflow="hidden",
                    border=h.border(1, "solid", h.var("--line")),
                    background_color=h.rgba(255, 255, 255, 0.5),
                )
            ):
                h.Img(
                    src=DETAIL_IMAGE,
                    alt="A soft-focus design workspace with notebooks, a table lamp, and neutral materials.",
                    style=h.Style(
                        display="block",
                        width=h.pct(100),
                        height=260,
                        object_fit=h.raw("cover"),
                        object_position=h.raw("center"),
                    ),
                )
            with h.Div(style=_timeline_style()):
                for note in RELEASE_NOTES:
                    with h.Article(
                        style=h.Style(
                            display="flex",
                            flex_direction="column",
                            gap=8,
                            padding_top=18,
                            border_top=h.border(1, "solid", h.var("--line")),
                        )
                    ):
                        h.Time(
                            note.stamp,
                            date_time="2026-03-08",
                            style=h.Style(color=h.var("--muted"), font_size=12),
                        )
                        h.H3(note.title, style=h.Style(margin=0, font_size=20, line_height=1.1))
                        h.P(note.body, style=h.Style(margin=0, color=h.var("--muted")))

        with h.Details(
            open=True,
            style=_panel_style(),
            class_name=f"{_panel_cls.class_name} {violet_accent_cls.class_name}",
        ):
            h.Summary(
                "What this page is intentionally showing",
                style=h.Css(
                    cursor="pointer",
                    font_weight=600,
                    list_style="none",
                ),
                class_name=_summary_cls.class_name,
            )
            with h.Div(
                style=h.Style(display="flex", flex_direction="column", gap=14, margin_top=24)
            ):
                h.P(
                    "Use typed Style values for the common path and selectors for scoped composition. Raw dicts are available as an escape hatch but this page uses none.",
                    style=h.Style(margin=0, color=h.var("--muted")),
                )
                with h.Ul(
                    style=h.Style(
                        display="flex",
                        flex_direction="column",
                        gap=12,
                        margin=0,
                        padding_left=20,
                    )
                ):
                    h.Li("Semantic tags drive the structure instead of generic container widgets.")
                    h.Li("Pseudo states and media rules compile into scoped classes automatically.")
                    h.Li(
                        "Custom properties keep a page-level palette reusable without introducing a theme system."
                    )
                    h.Li(
                        "The editorial images use typed object-fit and object-position alongside CSS variables and typed helpers."
                    )


_dispatch_form_cls = h.CssClass(
    "dispatch-form",
    media=[
        h.media(
            min_width=760,
            style=h.Css(
                grid_template_columns="minmax(0, 1fr) minmax(12rem, auto)",
                align_items="end",
            ),
        )
    ],
)


@component
def DispatchSection() -> None:
    """Render a native HTML form with typed CSS helpers and focus states."""
    lagoon_accent_cls = _panel_accent_cls("--lagoon")
    h.StyleTag(
        str(_panel_cls)
        + str(lagoon_accent_cls)
        + str(_dispatch_form_cls)
        + str(_input_cls)
        + str(_button_cls)
    )
    with h.Section(
        id="dispatch",
        style=_panel_style(),
        class_name=f"{_panel_cls.class_name} {lagoon_accent_cls.class_name}",
    ):
        h.P("Dispatch form", style=_eyebrow_style())
        h.H2(
            "Finish with native form controls and typed focus styling.",
            style=_section_title_style(),
        )
        h.P(
            "The form is static, but it demonstrates native labels, placeholders, button states, and a typed media layout inside the same HTML layer.",
            style=h.Style(margin=0, color=h.var("--muted"), max_width=h.rem(34)),
        )
        with h.Form(
            action="#",
            style=h.Css(
                display="grid",
                gap=16,
                margin_top=16,
            ),
            class_name=_dispatch_form_cls.class_name,
        ):
            with h.Div(style=h.Style(display="flex", flex_direction="column", gap=12)):
                h.Label(
                    "Email dispatch",
                    html_for="dispatch-email",
                    style=h.Style(display="block", font_weight=600),
                )
                h.Input(
                    id="dispatch-email",
                    name="email",
                    type="email",
                    placeholder="you@studio.dev",
                    auto_complete="email",
                    style=_input_style(),
                    class_name=_input_cls.class_name,
                )
            h.Button(
                "Request notes",
                type="button",
                style=_button_style(),
                class_name=_button_cls.class_name,
            )


_footer_cls = h.CssClass(
    "footer-rail",
    media=[
        h.media(
            min_width=760,
            style=h.Css(
                flex_direction="row",
                align_items="center",
                justify_content="space-between",
            ),
        )
    ],
)


@component
def FooterRail() -> None:
    """Render the closing note and link rail."""
    h.StyleTag(str(_footer_cls) + str(_ghost_link_cls))
    with h.Footer(
        style=h.Css(
            display="flex",
            flex_direction="column",
            gap=20,
            padding_top=24,
            border_top=h.border(1, "solid", h.var("--line")),
        ),
        class_name=_footer_cls.class_name,
    ):
        h.P(
            "HTML Studio is intentionally small: it shows how semantic trellis.html and typed CSS feel in a real page without collapsing into a widget demo.",
            style=h.Style(margin=0, color=h.var("--muted"), max_width=h.rem(46)),
        )
        with h.Div(style=h.Style(display="flex", gap=14, flex_wrap="wrap")):
            h.A(
                "MDN HTML",
                href="https://developer.mozilla.org/en-US/docs/Web/HTML",
                target="_blank",
                rel="noreferrer",
                style=_ghost_link_style(),
                class_name=_ghost_link_cls.class_name,
            )
            h.A(
                "MDN CSS",
                href="https://developer.mozilla.org/en-US/docs/Web/CSS",
                target="_blank",
                rel="noreferrer",
                style=_ghost_link_style(),
                class_name=_ghost_link_cls.class_name,
            )


@component
def HtmlStudio() -> None:
    """Render the standalone trellis.html example."""
    h.StyleTag(str(_shell_cls) + str(_page_frame_cls))
    with h.Main(style=_shell_style(), class_name=_shell_cls.class_name):
        with h.Div(style=_page_frame_style(), class_name=_page_frame_cls.class_name):
            ChromeHeader()
            HeroSection()
            CapabilitiesSection()
            NotesSection()
            DispatchSection()
            FooterRail()


app = App(HtmlStudio)
