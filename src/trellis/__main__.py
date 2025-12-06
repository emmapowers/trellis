from dataclasses import dataclass

from rich.pretty import pprint

from trellis.core import Element, Elements, RenderContext, blockComponent, component
from trellis.core.state import Stateful


@component
def A() -> Elements:
    return None


@component
def B() -> Elements:
    with Column() as col:
        A()
        A()
    return col


@component
def SomeText(text: str) -> Elements:
    print(f"SomeText: {text}")
    return None


@blockComponent
def Column(children: list[Element]) -> Elements:
    return children


@dataclass(kw_only=True)
class AppState(Stateful):
    text: str = "Hello, World!"


global_app_state = AppState(text="Hello, World!")


@component
def Top() -> Elements:
    with Column() as col:
        A()
        B()
        SomeText(text=global_app_state.text)
    return col


if __name__ == "__main__":
    context = RenderContext(Top)
    context.render(from_element=None)
    pprint(context.root_element)
    # Change state and re-render
    global_app_state.text = "Neat!"
    context.render_dirty()
    pprint(context.root_element)
