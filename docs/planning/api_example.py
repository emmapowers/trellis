"""
Trellis UI Framework API Example

This example demonstrates the key concepts of the Trellis framework.
Read from the bottom up for a top-down view of the app structure.

Key Concepts:
* Trellis serves a webapp with WebSocket updates for real-time UI changes
* State is stored in Stateful dataclasses with automatic dependency tracking
* When state changes, only components that read that specific property re-render
* The `mutable()` function enables two-way binding for form inputs
* Context API (`with state:` / `from_context()`) shares state with descendants
* Components use `with` blocks to define parent-child relationships
* Elements use `.key()` for stable identity in dynamic lists
"""

from dataclasses import dataclass

from trellis import App, Stateful, component, mutable
from trellis import html as h
from trellis import widgets as w


# ---------------------------------------------------------------------------
# Application State
# ---------------------------------------------------------------------------
@dataclass
class FormState(Stateful):
    """Form state with validation and submission logic."""

    # Form status
    submitting: bool = False
    error: str = ""

    # Form fields
    username: str = ""
    email: str = ""

    @property
    def valid(self) -> bool:
        """Form is valid when both fields are filled."""
        return bool(self.username) and bool(self.email)

    async def submit(self) -> None:
        """Handle form submission."""
        if not self.valid:
            self.error = "Please fill in all fields"
            return

        self.submitting = True
        self.error = ""
        try:
            # Simulate async operation
            import asyncio

            await asyncio.sleep(1)
            print(f"Submitted: {self.username} <{self.email}>")
        except Exception as e:
            self.error = str(e)
        finally:
            self.submitting = False


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------
@component
def TextWithLabel(label: str, value: str | None = None) -> None:
    """Labeled text input using mutable binding.

    The `value` parameter accepts a Mutable[str] for two-way binding.
    Use mutable(state.field) when calling this component.
    """
    with w.Row(gap=8, align="center"):
        w.Label(text=label, width=100)
        w.TextInput(value=value or mutable(FormState.from_context().username))


@component
def ErrorMessage(message: str) -> None:
    """Display an error message in red."""
    if message:
        with h.Div(style={"color": "red", "padding": "8px"}):
            w.Label(text=message)


@component
def UserList(users: list[dict]) -> None:
    """Display a list of users with proper key usage.

    The `.key()` method ensures stable element identity when the list
    changes. Without keys, reordering items would cause incorrect state
    preservation. Keys should be unique, stable identifiers (like IDs).
    """
    with w.Column(gap=8):
        for user in users:
            # Use .key() for stable identity - essential for dynamic lists
            with w.Row(gap=8, align="center").key(user["id"]):
                w.Label(text=user["name"])
                w.Label(text=user["email"], style={"color": "gray"})


@component
def Form() -> None:
    """Form component - accesses FormState from context."""
    state = FormState.from_context()

    with w.Column(gap=16, padding=16):
        # Error display
        ErrorMessage(message=state.error)

        # Form fields with two-way binding
        with w.Row(gap=8, align="center"):
            w.Label(text="Username:", width=100)
            w.TextInput(value=mutable(state.username), placeholder="Enter username")

        with w.Row(gap=8, align="center"):
            w.Label(text="Email:", width=100)
            w.TextInput(value=mutable(state.email), placeholder="Enter email")

        # Submit button - disabled when invalid or submitting
        with w.Row(justify="end"):
            w.Button(
                text="Submit" if not state.submitting else "Submitting...",
                on_click=state.submit,
                disabled=not state.valid or state.submitting,
            )


# ---------------------------------------------------------------------------
# App Entry Point
# ---------------------------------------------------------------------------
@component
def Root() -> None:
    """Root component providing FormState context to descendants."""
    with h.Div(style={"maxWidth": "400px", "margin": "40px auto"}):
        w.Label(text="User Registration", font_size=24, bold=True)

        # FormState provided via context - Form accesses it with from_context()
        with FormState():
            Form()


app = App(Root)
