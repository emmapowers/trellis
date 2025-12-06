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


import asyncio
from dataclasses import dataclass
from typing import Callable
from framework import widgets as w
from framework import html as h
from framework import navigation as nav
import framework as fw

routerState = nav.RouterState()

# Stateful Component
@dataclass
class FormState(fw.Stateful):
    # Form state
    submitting: bool
    error: str

    @fw.composite
    def valid(self):
        return self.text != "" and self.enabled

    # Form Data
    text: str
    enabled: str

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
            raise # This is safe, by default exceptoin from callbacks are logged, but there's a hook so you can show an error message

@fw.component
def Form(state: FormState):
    with w.Column() as out:
        if state.error:
            Notification(message=state.error)

        TextWithlabel(
            label="text",
            text=mutable(state.text)
        )
        with ButtonBar():
            Button(label="Cancel")
            Button(label="Submit", disabled=not state.valid, onClicked=state.submit)



# Component with local state
@dataclass
class NotificationState(fw.Stateful):
    shownTime: float | None = None

@fw.component
def Notification(message: str, duration: float) -> fw.Component:
    state = NotificationState(showTime=time.time())

    if (time.time() - state.shownTime) < duration:
        with h.Div() as out:
            ErrorText(message=message)
        return out
    
    return w.Empty()

    


# ---------------------------------------------------
# Stateless Component, state variable used for bi-directional sync to state held outside the component
# ---------------------------------------------------
@fw.component
def TextWithlabel(label: str, text: Mutable[str], placeholderText=None):
    with w.Row() as out:
        w.Label(label=label, width=150) # pixels assumed
        w.TextInput(text=text, placeholderText=placeholderText)

    return out

# ---------------------------------------------------
# Simple stateless Component, component functions must be sync
# ---------------------------------------------------
@fw.component
def ErrorText(message: str) -> fw.Component:
    return w.Label(text=message, textColor='red')

# ---------------------------------------------------
# Top, app has a router for navigation
# ---------------------------------------------------
@fw.component
def top():
    formState = FormState() # State can go here, or in a global like routerState below

    with nav.Router(state=routerState) as out:
        nav.Route(path="/", target=Form(state=formState))
        with nav.Route(path="/done"):
            w.Column(hAlign=w.Align.Center)
            w.Label("Hurray, you submited the form!")
            w.Button(label="Try Again!", onClick=lambda: routerState.navigate("/"))

async def main():
    app = fw.App()

    await app.serve(top)


if __name__ == "__main__":
    asyncio.run(main())