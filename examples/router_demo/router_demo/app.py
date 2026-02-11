"""Router demo application."""

from typing import Literal

from trellis import Margin, Padding, Route, Routes, component, router
from trellis import html as h
from trellis import widgets as w
from trellis.app import App, theme
from trellis.widgets import IconName, ThemeSwitcher


@component
def RouterDemo() -> None:
    """Main application with routing setup."""
    with w.Column(gap=0, style={"height": "100vh"}):
        # Header
        Header()

        # Main content
        with w.Column(flex=1, padding=Padding(x=24, y=20), style={"overflow": "auto"}):
            with w.Row(gap=0):
                w.Button(
                    text="",
                    icon=IconName.CHEVRON_LEFT,
                    on_click=router().go_back,
                    disabled=not router().can_go_back,
                    variant="ghost",
                    size="sm",
                    style={"width": "16px", "padding": "0px"},
                )
                w.Button(
                    text="",
                    icon=IconName.CHEVRON_RIGHT,
                    on_click=router().go_forward,
                    disabled=not router().can_go_forward,
                    variant="ghost",
                    size="sm",
                    style={"width": "16px", "padding": "0px", "marginRight": "4px"},
                )
                # Breadcrumb navigation
                BreadcrumbNav()

            # Route content
            with w.Card(padding=24, margin=Margin(top=16)):
                with Routes():
                    with Route(pattern="/"):
                        HomePage()
                    with Route(pattern="/about"):
                        AboutPage()
                    with Route(pattern="/users"):
                        UsersPage()
                    with Route(pattern="/users/:id"):
                        UserDetailPage()
                    with Route(pattern="*"):
                        NotFoundPage()


@component
def Header() -> None:
    """Application header with navigation and controls."""
    with w.Row(
        align="center",
        gap=16,
        padding=Padding(x=24, y=12),
        style={
            "borderBottom": f"1px solid {theme.border_default}",
            "backgroundColor": theme.bg_surface,
            "flexShrink": "0",
        },
    ):
        # Logo/title
        with w.Row(align="center", gap=8):
            w.Icon(name=IconName.COMPASS, size=24, color=theme.accent_primary)
            w.Heading(text="Router Demo", level=3)

        # Navigation links
        with w.Row(gap=4):
            NavLink(to="/", text="Home", icon=IconName.HOME)
            NavLink(to="/about", text="About", icon=IconName.INFO)
            NavLink(to="/users", text="Users", icon=IconName.USERS)

        # Spacer
        w.Row(flex=1)

        # Theme switcher
        ThemeSwitcher()


@component
def NavLink(to: str, text: str, icon: IconName) -> None:
    """Navigation link button."""
    state = router()
    is_active = state.path == to or (to != "/" and state.path.startswith(to))

    w.Button(
        text=text,
        icon=icon,
        href=to,
        variant="primary" if is_active else "ghost",
        size="sm",
    )


@component
def BreadcrumbNav() -> None:
    """Breadcrumb showing current navigation path.

    Uses native Trellis anchor elements that integrate with the router
    for client-side navigation without page reloads.
    """
    state = router()

    # Build breadcrumb items from path
    # Items with href use html.A which auto-routes for relative URLs
    items: list[dict[str, str]] = [{"label": "Home", "href": "/"}]
    if state.path != "/":
        parts = state.path.strip("/").split("/")
        for i, part in enumerate(parts):
            # Build href by joining all parts up to current index
            href = "/" + "/".join(parts[: i + 1])
            # Capitalize and handle numeric IDs (like user IDs)
            if part.isdigit():
                items.append({"label": f"User {part}", "href": href})
            else:
                items.append({"label": part.capitalize(), "href": href})

    # Last item has no href (current page) - rendered as Label not link
    if items:
        items[-1] = {"label": items[-1]["label"]}  # Remove href from last item

    w.Breadcrumb(items=items)


@component
def HomePage() -> None:
    """Home page content."""
    with w.Column(gap=16):
        with w.Row(align="center", gap=12):
            w.Icon(name=IconName.HOME, size=28, color=theme.accent_primary)
            w.Heading(text="Welcome Home", level=2)

        w.Label(
            text="This demo showcases client-side routing in Trellis with URL parameters, "
            "browser history integration, and reactive navigation.",
            color=theme.text_secondary,
        )

        w.Divider()

        w.Label(text="Quick Links", bold=True)
        with w.Row(gap=8, margin=Margin(top=4)):
            w.Button(
                text="Alice", icon=IconName.USER, variant="outline", size="sm", href="/users/1"
            )
            w.Button(text="Bob", icon=IconName.USER, variant="outline", size="sm", href="/users/2")
            w.Button(
                text="Carol", icon=IconName.USER, variant="outline", size="sm", href="/users/3"
            )
            w.Button(
                text="404 Test",
                icon=IconName.ALERT_TRIANGLE,
                variant="ghost",
                size="sm",
                href="/nonexistent",
            )


@component
def AboutPage() -> None:
    """About page content."""
    with w.Column(gap=16):
        with w.Row(align="center", gap=12):
            w.Icon(name=IconName.INFO, size=28, color=theme.accent_primary)
            w.Heading(text="About", level=2)

        w.Label(
            text="Trellis Router provides seamless client-side navigation without page reloads.",
            color=theme.text_secondary,
        )

        w.Divider()

        w.Label(text="Features", bold=True)
        with w.Column(gap=8, margin=Margin(top=8)):
            FeatureItem(icon=IconName.COMPASS, text="Path-based routing with pattern matching")
            FeatureItem(icon=IconName.CODE, text="URL parameters (/users/:id)")
            FeatureItem(icon=IconName.CLOCK, text="Browser history integration")
            FeatureItem(icon=IconName.REFRESH_CW, text="Reactive state updates")


@component
def FeatureItem(icon: IconName, text: str) -> None:
    """Single feature list item."""
    with w.Row(gap=8, align="center"):
        w.Icon(name=icon, size=16, color=theme.text_secondary)
        w.Label(text=text, color=theme.text_secondary)


# Sample user data
USERS: dict[str, dict[str, str]] = {
    "1": {"name": "Alice Johnson", "email": "alice@example.com", "role": "Admin"},
    "2": {"name": "Bob Smith", "email": "bob@example.com", "role": "Developer"},
    "3": {"name": "Carol Williams", "email": "carol@example.com", "role": "Designer"},
}

ROLE_VARIANTS: dict[str, Literal["default", "success", "error", "warning", "info"]] = {
    "Admin": "error",
    "Developer": "info",
    "Designer": "success",
}


@component
def UsersPage() -> None:
    """Users list page."""
    with w.Column(gap=16):
        with w.Row(align="center", gap=12):
            w.Icon(name=IconName.USERS, size=28, color=theme.accent_primary)
            w.Heading(text="Users", level=2)

        with w.Column(gap=8):
            for user_id, user in USERS.items():
                UserCard(user_id=user_id, user=user)


@component
def UserCard(user_id: str, user: dict[str, str]) -> None:
    """Clickable user card."""
    with h.A(href=f"/users/{user_id}"):
        with w.Card(
            padding=16,
            style={"cursor": "pointer", "transition": "box-shadow 0.15s ease"},
        ):
            with w.Row(gap=12, align="center"):
                w.Icon(name=IconName.USER, size=20, color=theme.text_secondary)
                w.Label(text=user["name"], bold=True, flex=1)
                w.Badge(text=user["role"], variant=ROLE_VARIANTS.get(user["role"], "default"))
                w.Icon(name=IconName.CHEVRON_RIGHT, size=16, color=theme.text_secondary)


@component
def UserDetailPage() -> None:
    """User detail page with URL parameter."""
    state = router()
    user_id = state.params.get("id", "")
    user = USERS.get(user_id)

    with w.Column(gap=16):
        if user:
            with w.Row(align="center", gap=12):
                w.Icon(name=IconName.USER, size=28, color=theme.accent_primary)
                w.Heading(text=user["name"], level=2)
                w.Badge(text=user["role"], variant=ROLE_VARIANTS.get(user["role"], "default"))

            w.Divider()

            with w.Column(gap=12):
                DetailRow(label="Email", value=user["email"], icon=IconName.MAIL)
                DetailRow(label="Role", value=user["role"], icon=IconName.TAG)
                DetailRow(label="ID", value=user_id, icon=IconName.HASH)

            with w.Row(margin=Margin(top=8)):
                w.Button(
                    text="Back to Users",
                    icon=IconName.ARROW_LEFT,
                    variant="outline",
                    href="/users",
                )
        else:
            with w.Column(gap=12, align="center"):
                w.Icon(name=IconName.USER_X, size=48, color=theme.error)
                w.Heading(text="User Not Found", level=3, color=theme.error)
                w.Label(text=f"No user with ID: {user_id}", color=theme.text_secondary)

                w.Button(
                    text="Back to Users",
                    icon=IconName.ARROW_LEFT,
                    variant="outline",
                    href="/users",
                )


@component
def DetailRow(label: str, value: str, icon: IconName) -> None:
    """User detail row with icon."""
    with w.Row(gap=12, align="center"):
        w.Icon(name=icon, size=16, color=theme.text_secondary)
        w.Label(text=label, bold=True, style={"width": "80px"})
        w.Label(text=value, color=theme.text_secondary)


@component
def NotFoundPage() -> None:
    """404 page for unmatched routes."""
    state = router()

    with w.Column(gap=16, align="center"):
        w.Icon(name=IconName.ALERT_CIRCLE, size=64, color=theme.error)
        w.Heading(text="404", level=1, color=theme.error)
        w.Heading(text="Page Not Found", level=3)
        w.Label(text=f'The path "{state.path}" does not exist.', color=theme.text_secondary)

        with w.Row(margin=Margin(top=8)):
            w.Button(
                text="Go Home",
                icon=IconName.HOME,
                href="/",
            )


app = App(RouterDemo)
