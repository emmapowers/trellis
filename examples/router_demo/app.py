"""Router demo application."""

from trellis import Link, Padding, Route, RouterState, Routes, component, router
from trellis import html as h
from trellis import widgets as w


@component
def App() -> None:
    """Main application with routing setup."""
    with RouterState():
        with w.Column(padding=Padding(x=20, y=20)):
            # Navigation header
            NavHeader()

            # Route content - Routes ensures only first match renders
            with w.Card(padding=20, style={"marginTop": "20px"}):
                with Routes():
                    Route(pattern="/", content=HomePage)
                    Route(pattern="/about", content=AboutPage)
                    Route(pattern="/users", content=UsersPage)
                    Route(pattern="/users/:id", content=UserDetailPage)
                    Route(pattern="*", content=NotFoundPage)


@component
def NavHeader() -> None:
    """Navigation header with links and history controls."""
    state = router()

    with w.Row(gap=20, align="center"):
        # Navigation links
        with h.Nav():
            with w.Row(gap=15):
                Link(to="/", text="Home")
                Link(to="/about", text="About")
                Link(to="/users", text="Users")

        # Spacer
        h.Div(style={"flex": "1"})

        # History controls
        with w.Row(gap=8):
            w.Button(
                text="Back",
                on_click=lambda: state.go_back(),
                disabled=not state.can_go_back,
                small=True,
            )
            w.Button(
                text="Forward",
                on_click=lambda: state.go_forward(),
                disabled=not state.can_go_forward,
                small=True,
            )

        # Current path display
        w.Label(text=f"Path: {state.path}", color="#666", font_size=12)


@component
def HomePage() -> None:
    """Home page content."""
    with w.Column(gap=12):
        w.Label(text="Welcome Home", font_size=24, font_weight=600)
        w.Label(
            text="This is a demo of client-side routing in Trellis.",
            color="#666",
        )
        w.Label(
            text="Use the navigation links above, or click a user below:",
            color="#666",
        )

        # Quick user links
        with w.Row(gap=10, style={"marginTop": "10px"}):
            Link(to="/users/1", text="User 1")
            Link(to="/users/2", text="User 2")
            Link(to="/users/3", text="User 3")
            Link(to="/nonexistent", text="404 Test")


@component
def AboutPage() -> None:
    """About page content."""
    with w.Column(gap=12):
        w.Label(text="About", font_size=24, font_weight=600)
        w.Label(
            text="Trellis Router provides client-side navigation without page reloads.",
            color="#666",
        )
        with w.Column(gap=4, style={"marginTop": "10px"}):
            w.Label(text="Features:", font_weight=500)
            w.Label(text="- Path-based routing with pattern matching", color="#666")
            w.Label(text="- URL parameters (/users/:id)", color="#666")
            w.Label(text="- Browser history integration", color="#666")
            w.Label(text="- Reactive state updates", color="#666")


# Sample user data
USERS = {
    "1": {"name": "Alice Johnson", "email": "alice@example.com", "role": "Admin"},
    "2": {"name": "Bob Smith", "email": "bob@example.com", "role": "Developer"},
    "3": {"name": "Carol Williams", "email": "carol@example.com", "role": "Designer"},
}


@component
def UsersPage() -> None:
    """Users list page."""
    state = router()

    with w.Column(gap=12):
        w.Label(text="Users", font_size=24, font_weight=600)

        # User list
        for user_id, user in USERS.items():
            with w.Card(
                padding=12,
                style={"cursor": "pointer"},
                on_click=lambda uid=user_id: state.navigate(f"/users/{uid}"),
            ):
                with w.Row(gap=12, align="center"):
                    w.Label(text=user["name"], font_weight=500)
                    w.Label(text=user["role"], color="#666", font_size=12)


@component
def UserDetailPage() -> None:
    """User detail page with URL parameter."""
    state = router()
    user_id = state.params.get("id", "")
    user = USERS.get(user_id)

    with w.Column(gap=12):
        if user:
            w.Label(text=user["name"], font_size=24, font_weight=600)

            with w.Column(gap=8, style={"marginTop": "10px"}):
                with w.Row(gap=8):
                    w.Label(text="Email:", font_weight=500)
                    w.Label(text=user["email"], color="#666")
                with w.Row(gap=8):
                    w.Label(text="Role:", font_weight=500)
                    w.Label(text=user["role"], color="#666")
                with w.Row(gap=8):
                    w.Label(text="ID:", font_weight=500)
                    w.Label(text=user_id, color="#666")

            with w.Row(style={"marginTop": "20px"}):
                Link(to="/users", text="Back to Users")
        else:
            w.Label(text="User Not Found", font_size=24, font_weight=600, color="#e53e3e")
            w.Label(text=f"No user with ID: {user_id}", color="#666")
            Link(to="/users", text="Back to Users")


@component
def NotFoundPage() -> None:
    """404 page for unmatched routes."""
    state = router()

    with w.Column(gap=12, align="center"):
        w.Label(text="404", font_size=48, font_weight=700, color="#e53e3e")
        w.Label(text="Page Not Found", font_size=24, font_weight=600)
        w.Label(text=f'The path "{state.path}" does not exist.', color="#666")

        with w.Row(style={"marginTop": "20px"}):
            w.Button(text="Go Home", on_click=lambda: state.navigate("/"))
