from dataclasses import dataclass

from rich.pretty import pprint

from trellis.core import Element, RenderContext, component
from trellis.core.state import Stateful


@component
def A() -> None:
    pass


@component
def B() -> None:
    with Column():
        A()
        A()


@component
def SomeText(text: str) -> None:
    print(f"SomeText: {text}")


@component
def Column(children: list[Element]) -> None:
    for child in children:
        child()


@dataclass
class AppState(Stateful):
    text: str = "Hello, World!"


global_app_state = AppState()


@component
def Top() -> None:
    with Column():
        A()
        B()
        SomeText(text=global_app_state.text)


if __name__ == "__main__":
    context = RenderContext(Top)
    context.render(from_element=None)
    pprint(context.root_element)
    # Change state and re-render
    global_app_state.text = "Neat!"
    context.render_dirty()
    pprint(context.root_element)
