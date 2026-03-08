"""Standalone trellis.html showcase for semantic HTML and typed CSS."""

from __future__ import annotations

from dataclasses import dataclass

from trellis import component
from trellis import html as h
from trellis.app import App


@dataclass(frozen=True)
class FeatureCard:
    eyebrow: str
    title: str
    body: str
    points: tuple[str, ...]
    accent: str


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
    ),
)

RELEASE_NOTES: tuple[ReleaseNote, ...] = (
    ReleaseNote(
        title="Hero layout",
        body="The opening panel uses custom properties, typed media queries, and an asymmetrical grid.",
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


def _shell_style() -> h.Style:
    return h.Style(
        vars={
            "--paper": h.oklch(0.98, 0.01, 95),
            "--ink": h.oklch(0.27, 0.03, 260),
            "--muted": h.oklch(0.55, 0.03, 250),
            "--panel": h.rgba(255, 252, 247, 0.82),
            "--line": h.rgba(36, 31, 41, 0.12),
            "--lagoon": h.oklch(0.71, 0.13, 214),
            "--ember": h.oklch(0.73, 0.16, 42),
            "--violet": h.oklch(0.7, 0.12, 312),
            "--shadow": h.rgba(22, 17, 35, 0.16),
        },
        min_height=h.vh(100),
        color=h.var("--ink"),
        background_color=h.var("--paper"),
        background_image=(
            "radial-gradient(circle at top left, color-mix(in srgb, var(--lagoon) 18%, transparent) 0, transparent 38%), "
            "radial-gradient(circle at top right, color-mix(in srgb, var(--ember) 20%, transparent) 0, transparent 34%), "
            "linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,250,244,0.94))"
        ),
        padding=h.padding(24, 18, 48),
        font_family='"Avenir Next", "Segoe UI", sans-serif',
        line_height=1.5,
        selection=h.Style(
            background_color=h.var("--lagoon"),
            color="white",
        ),
        media=[
            h.media(
                min_width=880,
                style=h.Style(padding=h.padding(32, 28, 72)),
            )
        ],
    )


def _page_frame_style() -> h.Style:
    return h.Style(
        width="min(1180px, 100%)",
        margin="0 auto",
        selectors={"& > * + *": h.Style(margin_top=24)},
        media=[
            h.media(min_width=960, style=h.Style(selectors={"& > * + *": h.Style(margin_top=32)}))
        ],
    )


def _panel_style(*, accent: str | None = None) -> h.Style:
    return h.Style(
        background_color=h.var("--panel"),
        border=h.border(1, "solid", h.var("--line")),
        border_radius=28,
        padding=22,
        box_shadow="0 18px 60px -28px var(--shadow)",
        selectors={"& > * + *": h.Style(margin_top=12)},
        media=[
            h.media(
                min_width=960,
                style=h.Style(padding=28),
            ),
        ],
        before=(
            h.Style(
                content='""',
                display="block",
                width=42,
                height=4,
                border_radius=999,
                background_color=h.var(accent),
                margin_bottom=18,
            )
            if accent is not None
            else None
        ),
    )


def _eyebrow_style() -> h.Style:
    return h.Style(
        margin=0,
        color=h.var("--muted"),
        font_size=12,
        font_family='"IBM Plex Mono", "SFMono-Regular", monospace',
        letter_spacing="0.16em",
        text_transform="uppercase",
    )


def _headline_style() -> h.Style:
    return h.Style(
        margin=0,
        font_family='"Iowan Old Style", "Palatino Linotype", Georgia, serif',
        font_size=h.clamp(h.px(52), "9vw", h.px(108)),
        line_height=0.92,
        letter_spacing="-0.05em",
        max_width="10ch",
    )


def _body_copy_style() -> h.Style:
    return h.Style(
        margin=0,
        font_size=h.clamp(h.px(18), "2.2vw", h.px(22)),
        color=h.var("--muted"),
        max_width="38rem",
    )


def _hero_grid_style() -> h.Style:
    return h.Style(
        display="grid",
        gap=20,
        align_items="end",
        media=[
            h.media(
                min_width=920,
                style=h.Style(
                    grid_template_columns="minmax(0, 1.3fr) minmax(22rem, 0.95fr)",
                    gap=28,
                ),
            )
        ],
    )


def _cta_link_style(*, tone: str) -> h.Style:
    return h.Style(
        display="inline-flex",
        align_items="center",
        justify_content="center",
        gap=10,
        padding=h.padding(12, 18),
        border_radius=999,
        border=h.border(1, "solid", h.var("--line")),
        background_color=h.var(tone),
        color="white",
        text_decoration="none",
        font_weight=600,
        transition="transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease",
        hover=h.Style(transform=h.translate(0, -2), box_shadow="0 14px 28px -18px var(--shadow)"),
        active=h.Style(transform=h.translate(0, 0)),
        focus_visible=h.Style(outline=h.border(2, "solid", h.var("--ink")), outline_offset=4),
    )


def _ghost_link_style() -> h.Style:
    return h.Style(
        display="inline-flex",
        align_items="center",
        gap=8,
        padding=h.padding(12, 18),
        border_radius=999,
        border=h.border(1, "solid", h.var("--line")),
        color=h.var("--ink"),
        text_decoration="none",
        background_color=h.rgba(255, 255, 255, 0.58),
        hover=h.Style(background_color=h.rgba(255, 255, 255, 0.86)),
        focus_visible=h.Style(outline=h.border(2, "solid", h.var("--lagoon")), outline_offset=4),
    )


def _metrics_style() -> h.Style:
    return h.Style(
        display="grid",
        gap=12,
        margin=0,
        media=[
            h.media(
                min_width=600,
                style=h.Style(grid_template_columns="repeat(3, minmax(0, 1fr))"),
            ),
        ],
    )


def _feature_grid_style() -> h.Style:
    return h.Style(
        display="grid",
        gap=18,
        media=[
            h.media(
                min_width=760,
                style=h.Style(grid_template_columns="repeat(2, minmax(0, 1fr))"),
            ),
            h.media(
                min_width=1100,
                style=h.Style(grid_template_columns="repeat(3, minmax(0, 1fr))"),
            ),
        ],
    )


def _feature_card_style(accent: str) -> h.Style:
    return h.Style(
        display="block",
        text_decoration="none",
        color=h.var("--ink"),
        background_color=h.rgba(255, 255, 255, 0.72),
        border=h.border(1, "solid", h.var("--line")),
        border_radius=24,
        padding=20,
        min_height=h.px(270),
        box_shadow="0 14px 42px -28px var(--shadow)",
        transition="transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease",
        selectors={"& > * + *": h.Style(margin_top=12)},
        hover=h.Style(
            transform=h.translate(0, -4),
            border_color=h.var(accent),
            box_shadow="0 24px 48px -28px var(--shadow)",
        ),
        focus_visible=h.Style(outline=h.border(2, "solid", h.var(accent)), outline_offset=4),
    )


def _chip_style(accent: str) -> h.Style:
    return h.Style(
        display="inline-flex",
        align_items="center",
        border_radius=999,
        padding=h.padding(6, 10),
        background_color=f"color-mix(in srgb, var({accent}) 16%, white)",
        color=h.var(accent),
        font_size=12,
        font_family='"IBM Plex Mono", "SFMono-Regular", monospace',
    )


def _timeline_style() -> h.Style:
    return h.Style(
        display="grid",
        gap=12,
        selectors={"& > * + *": h.Style(margin_top=8)},
    )


def _input_style() -> h.Style:
    return h.Style(
        width="100%",
        padding=h.padding(14, 16),
        border=h.border(1, "solid", h.var("--line")),
        border_radius=18,
        background_color=h.rgba(255, 255, 255, 0.7),
        color=h.var("--ink"),
        font_size=16,
        placeholder=h.Style(color=h.var("--muted")),
        focus_visible=h.Style(
            border_color=h.var("--lagoon"),
            outline=h.border(2, "solid", h.rgba(0, 0, 0, 0)),
            box_shadow="0 0 0 4px color-mix(in srgb, var(--lagoon) 20%, transparent)",
        ),
    )


def _button_style() -> h.Style:
    return h.Style(
        padding=h.padding(14, 18),
        border=h.border(1, "solid", h.var("--ink")),
        border_radius=18,
        background_color=h.var("--ink"),
        color="white",
        font_weight=600,
        cursor="pointer",
        transition="transform 160ms ease, opacity 160ms ease",
        hover=h.Style(transform=h.translate(0, -2), opacity=0.96),
        active=h.Style(transform=h.translate(0, 0)),
        focus_visible=h.Style(outline=h.border(2, "solid", h.var("--lagoon")), outline_offset=4),
    )


@component
def ChromeHeader() -> None:
    """Render the editorial header and compact navigation."""
    with h.Header(
        style=h.Style(
            display="flex",
            flex_direction="column",
            gap=16,
            margin_bottom=12,
            media=[
                h.media(
                    min_width=760,
                    style=h.Style(
                        flex_direction="row",
                        align_items="center",
                        justify_content="space-between",
                    ),
                )
            ],
        )
    ):
        with h.Div(style=h.Style(selectors={"& > * + *": h.Style(margin_top=8)})):
            h.P(
                "HTML Studio",
                style=_eyebrow_style(),
            )
            h.H2(
                "A semantic page built directly with trellis.html.",
                style=h.Style(
                    margin=0,
                    font_family='"Iowan Old Style", "Palatino Linotype", Georgia, serif',
                    font_size=h.clamp(h.px(28), "3vw", h.px(42)),
                    line_height=0.98,
                    max_width="16ch",
                ),
            )
        with h.Nav(aria_label="Section links"):
            with h.Ul(
                style=h.Style(
                    display="flex",
                    flex_wrap="wrap",
                    gap=10,
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
                            style=h.Style(
                                color=h.var("--muted"),
                                text_decoration="none",
                                padding=h.padding(8, 12),
                                border_radius=999,
                                hover=h.Style(
                                    color=h.var("--ink"),
                                    background_color=h.rgba(255, 255, 255, 0.5),
                                ),
                                focus_visible=h.Style(
                                    outline=h.border(2, "solid", h.var("--lagoon")),
                                    outline_offset=4,
                                ),
                            ),
                        )


@component
def HeroSection() -> None:
    """Render the hero with structured styles and a responsive metrics panel."""
    with h.Section(style=_hero_grid_style()):
        with h.Div(style=h.Style(selectors={"& > * + *": h.Style(margin_top=18)})):
            h.P("March field notes / typed HTML + CSS", style=_eyebrow_style())
            h.H1(
                "Compose rich pages with semantic tags, structured style, and only one escape hatch when the browser gets weird.",
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
                    gap=12,
                    padding_top=8,
                )
            ):
                h.A(
                    "Inspect the source",
                    href="https://developer.mozilla.org/en-US/docs/Web/HTML",
                    target="_blank",
                    rel="noreferrer",
                    style=_cta_link_style(tone="--lagoon"),
                )
                h.A(
                    "Review the CSS model",
                    href="#dispatch",
                    use_router=False,
                    style=_ghost_link_style(),
                )

        with h.Figure(
            style={
                "backdrop-filter": "blur(16px)",
                "-webkit-backdrop-filter": "blur(16px)",
                "background": "linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,255,255,0.54))",
                "border": "1px solid rgba(36, 31, 41, 0.12)",
                "border-radius": "28px",
                "box-shadow": "0 20px 64px -30px rgba(22, 17, 35, 0.2)",
                "padding": "22px",
            },
        ):
            h.Figcaption(
                "What this page is exercising",
                style=h.Style(margin=0, color=h.var("--muted"), font_size=14),
            )
            with h.Dl(style=_metrics_style()):
                for value, label in (
                    ("12", "semantic tags"),
                    ("5", "CSS helper families"),
                    ("1", "raw dict escape hatch"),
                ):
                    with h.Div(
                        style=h.Style(
                            padding=h.padding(14, 0, 0),
                            border_top=h.border(1, "solid", h.var("--line")),
                        )
                    ):
                        h.Dt(
                            value,
                            style=h.Style(
                                margin=0,
                                font_family='"Iowan Old Style", "Palatino Linotype", Georgia, serif',
                                font_size=36,
                                line_height=0.94,
                            ),
                        )
                        h.Dd(
                            label,
                            style=h.Style(margin=0, color=h.var("--muted")),
                        )


@component
def CapabilityCard(card: FeatureCard) -> None:
    """Render a feature card for a single HTML/CSS capability."""
    with h.Article(style=_feature_card_style(card.accent)):
        h.P(card.eyebrow, style=_eyebrow_style())
        h.H3(
            card.title,
            style=h.Style(
                margin=0,
                font_family='"Iowan Old Style", "Palatino Linotype", Georgia, serif',
                font_size=30,
                line_height=0.98,
                max_width="14ch",
            ),
        )
        h.P(card.body, style=h.Style(margin=0, color=h.var("--muted"), font_size=16))
        with h.Ul(
            style=h.Style(
                list_style="none",
                margin=0,
                padding=0,
                display="flex",
                flex_wrap="wrap",
                gap=8,
            )
        ):
            for point in card.points:
                with h.Li():
                    h.Code(point, style=_chip_style(card.accent))


@component
def CapabilitiesSection() -> None:
    """Render the capability cards and a semantic note panel."""
    with h.Section(
        id="capabilities", style=h.Style(selectors={"& > * + *": h.Style(margin_top=18)})
    ):
        h.P("Feature sample", style=_eyebrow_style())
        h.H2(
            "A single page can show the full authoring model without pretending to be a CSS playground.",
            style=h.Style(
                margin=0,
                font_family='"Iowan Old Style", "Palatino Linotype", Georgia, serif',
                font_size=h.clamp(h.px(34), "4vw", h.px(56)),
                line_height=0.96,
                max_width="18ch",
            ),
        )
        with h.Div(style=_feature_grid_style()):
            for card in FEATURE_CARDS:
                CapabilityCard(card=card)


@component
def NotesSection() -> None:
    """Render release notes plus an explainer details block."""
    with h.Section(
        id="notes",
        style=h.Style(
            display="grid",
            gap=18,
            media=[
                h.media(
                    min_width=960,
                    style=h.Style(grid_template_columns="minmax(0, 1.1fr) minmax(20rem, 0.9fr)"),
                )
            ],
        ),
    ):
        with h.Div(style=_panel_style(accent="--ember")):
            h.P("Release notes", style=_eyebrow_style())
            h.H2(
                "The CSS layer stays close to the DOM, so layout decisions remain visible in component code.",
                style=h.Style(
                    margin=0,
                    font_family='"Iowan Old Style", "Palatino Linotype", Georgia, serif',
                    font_size=h.clamp(h.px(30), "3.6vw", h.px(48)),
                    line_height=0.98,
                    max_width="18ch",
                ),
            )
            with h.Div(style=_timeline_style()):
                for note in RELEASE_NOTES:
                    with h.Article(
                        style=h.Style(
                            padding_top=14,
                            border_top=h.border(1, "solid", h.var("--line")),
                            selectors={"& > * + *": h.Style(margin_top=6)},
                        )
                    ):
                        h.Time(
                            note.stamp,
                            date_time="2026-03-08",
                            style=h.Style(color=h.var("--muted"), font_size=13),
                        )
                        h.H3(note.title, style=h.Style(margin=0, font_size=22, line_height=1.0))
                        h.P(note.body, style=h.Style(margin=0, color=h.var("--muted")))

        with h.Details(open=True, style=_panel_style(accent="--violet")):
            h.Summary(
                "What this page is intentionally showing",
                style=h.Style(
                    cursor="pointer",
                    font_weight=600,
                    list_style="none",
                    hover=h.Style(color=h.var("--violet")),
                    focus_visible=h.Style(
                        outline=h.border(2, "solid", h.var("--violet")), outline_offset=4
                    ),
                ),
            )
            with h.Div(
                style=h.Style(selectors={"& > * + *": h.Style(margin_top=12)}, margin_top=16)
            ):
                h.P(
                    "Use typed Style values for the common path, selectors for scoped composition, and raw dicts only when browser-specific properties fall outside the typed layer.",
                    style=h.Style(margin=0, color=h.var("--muted")),
                )
                with h.Ul(
                    style=h.Style(
                        margin=0, padding_left=18, selectors={"& > * + *": h.Style(margin_top=8)}
                    )
                ):
                    h.Li("Semantic tags drive the structure instead of generic container widgets.")
                    h.Li("Pseudo states and media rules compile into scoped classes automatically.")
                    h.Li(
                        "Custom properties keep a page-level palette reusable without introducing a theme system."
                    )
                    h.Li(
                        "The glassy metrics panel uses a raw dict for backdrop-filter, which is exactly the kind of edge the escape hatch is for."
                    )


@component
def DispatchSection() -> None:
    """Render a native HTML form with typed CSS helpers and focus states."""
    with h.Section(id="dispatch", style=_panel_style(accent="--lagoon")):
        h.P("Dispatch form", style=_eyebrow_style())
        h.H2(
            "Finish with native form controls and typed focus styling.",
            style=h.Style(
                margin=0,
                font_family='"Iowan Old Style", "Palatino Linotype", Georgia, serif',
                font_size=h.clamp(h.px(30), "3.4vw", h.px(46)),
                line_height=0.98,
                max_width="16ch",
            ),
        )
        h.P(
            "The form is static, but it demonstrates native labels, placeholders, button states, and a typed media layout inside the same HTML layer.",
            style=h.Style(margin=0, color=h.var("--muted"), max_width="34rem"),
        )
        with h.Form(
            action="#",
            style=h.Style(
                display="grid",
                gap=14,
                margin_top=8,
                media=[
                    h.media(
                        min_width=760,
                        style=h.Style(
                            grid_template_columns="minmax(0, 1fr) minmax(12rem, auto)",
                            align_items="end",
                        ),
                    )
                ],
            ),
        ):
            with h.Div(style=h.Style(selectors={"& > * + *": h.Style(margin_top=10)})):
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
                )
            h.Button("Request notes", type="submit", style=_button_style())


@component
def FooterRail() -> None:
    """Render the closing note and link rail."""
    with h.Footer(
        style=h.Style(
            display="flex",
            flex_direction="column",
            gap=12,
            padding_top=6,
            border_top=h.border(1, "solid", h.var("--line")),
            media=[
                h.media(
                    min_width=760,
                    style=h.Style(
                        flex_direction="row",
                        align_items="center",
                        justify_content="space-between",
                    ),
                )
            ],
        )
    ):
        h.P(
            "HTML Studio is intentionally small: it shows how semantic trellis.html and typed CSS feel in a real page without collapsing into a widget demo.",
            style=h.Style(margin=0, color=h.var("--muted"), max_width="44rem"),
        )
        with h.Div(style=h.Style(display="flex", gap=12, flex_wrap="wrap")):
            h.A(
                "MDN HTML",
                href="https://developer.mozilla.org/en-US/docs/Web/HTML",
                target="_blank",
                rel="noreferrer",
                style=_ghost_link_style(),
            )
            h.A(
                "MDN CSS",
                href="https://developer.mozilla.org/en-US/docs/Web/CSS",
                target="_blank",
                rel="noreferrer",
                style=_ghost_link_style(),
            )


@component
def HtmlStudio() -> None:
    """Render the standalone trellis.html example."""
    with h.Main(style=_shell_style()):
        with h.Div(style=_page_frame_style()):
            ChromeHeader()
            HeroSection()
            CapabilitiesSection()
            NotesSection()
            DispatchSection()
            FooterRail()


app = App(HtmlStudio)
