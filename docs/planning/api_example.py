"""
UI Framework API example

It's probably best to read this file from the bottom up.

Notes:
* This would serve a webapp on some default port
* On startup, the top() function is called, all children are called and a Component Tree is created
* State is stored in Stateful classes. When the app does the initial render, it notices which stateful
  elements were used, and automatically watches those values for changes.
* When a stete value changes, only the components that use that particular state varible are re-rendered.
  This is fine grained, so if a component uses FormState.valid, and nothing else, it only re-renders if that
  value changed, even if the whole FormState object is passed to the component.
* Once the components that have changed are re-rendered, the Component Tree is updated.
* Once every so often (20ms perhaps?) the Component Tree is diffed with the version from the last "tick" and the
  differences sent to the client.
* Changes to the Component Tree can be made from anywhere at any time. Locking is handled automatically.
* To avoid lots of onChange callbacks, you can pass state variables (State[Type]) to a component.
  You'd use them like statefulVar.value, or statefulVar.value = "new value". w.Text.text expects a stateful var, for example.
* Stateful Vars make it all the way to the Component Tree, so links between component can be auto-detected and
  javascript side links can be created for the user.
* It should be able to support hot-reload, I think.
"""


from dataclasses import dataclass

from trellis.core.state import Stateful
from trellis.core.functional_component import component
from trellis.core.rendering import Element
from trellis import widgets as w
from trellis import html as h
from trellis import navigation as nav
from trellis import Trellis, Mutable, mutable
from trellis.utils import async_main

routerState = nav.RouterState()


@dataclass
class FormState(Stateful):
    # Form state
    submitting: bool
    error: str

    # Form Data
    text: str
    enabled: str

    @property
    def valid(self):
        return self.text != "" and self.enabled

    async def submit(self):
        try:
            self.error = ""
            if not self.valid:
                raise RuntimeError("Form submitted while not valid")

            result = await doSomethingNetworky(self.text)
            routerState.navigate("/done")
        except RuntimeError as e:
            self.error = e.msg
        except Exception:
            raise  # This is safe, by default exception from callbacks are logged, but there's a hook so you can show an error message


@component
def Form() -> None:
    """Form component - gets FormState from context."""
    state = FormState.from_context()

    with w.Column():
        if state.error:
            Notification(message=state.error)

        TextWithLabel(label="text", text=mutable(state.text))
        with ButtonBar():
            Button(label="Cancel")
            Button(label="Submit", disabled=not state.valid, onClicked=state.submit)


# Component with local state
@dataclass
class NotificationState(Stateful):
    shownTime: float | None = None


@component
def Notification(message: str, duration: float) -> None:
    state = NotificationState(showTime=time.time())

    if (time.time() - state.shownTime) < duration:
        with h.Div():
            ErrorText(message=message)
    else:
        w.Empty()


# ---------------------------------------------------
# Stateless Component, state variable used for bi-directional sync to state held outside the component
# ---------------------------------------------------
@component
def TextWithLabel(
    label: str, text: Mutable[str], placeholderText: str | None = None
) -> None:
    with w.Row():
        w.Label(label=label, width=150)  # pixels assumed
        w.TextInput(text=text, placeholderText=placeholderText)


# ---------------------------------------------------
# Simple stateless Component, component functions must be sync
# ---------------------------------------------------
@component
def ErrorText(message: str) -> None:
    w.Label(text=message, textColor="red")


# ---------------------------------------------------
# Top, app has a router for navigation
# ---------------------------------------------------
@component
def top() -> None:
    with nav.Router(state=routerState):
        # FormState provided via context - children access it with FormState.from_context()
        with FormState():
            nav.Route(path="/", target=Form())  # No props needed!
        with nav.Route(path="/done"):
            with w.Column(hAlign=w.Align.Center):
                w.Label("Hurray, you submited the form!")
                w.Button(label="Try Again!", onClick=lambda: routerState.navigate("/"))


@async_main
async def main() -> None:
    app = Trellis(top=top)
    await app.serve()
