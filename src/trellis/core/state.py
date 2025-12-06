import typing as tp
from dataclasses import dataclass, field, fields

from trellis.core.block_component import BlockElement
from trellis.core.rendering import Element, RenderContext, get_active_render_context

DEFAULT_MARKER = object()


@dataclass(kw_only=True)
class StatePropertyInfo:
    name: str
    value: tp.Any = DEFAULT_MARKER
    default: tp.Any = DEFAULT_MARKER
    elements: set[tuple[RenderContext, Element]] = field(default_factory=set)


@dataclass(kw_only=True)
class Stateful:
    _state_properties: tp.ClassVar[dict[str, StatePropertyInfo]]

    def __init__(self):
        # Copy the state properties from the class to the instance so they can be modified per-instance
        self._state_properties = type(self)._state_properties.copy()
        print(f"Initialized state properties for {self} {fields(self)}")

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls._state_properties = {}

        # For all annotated fields, convert them to StatefulProperty if they are not already
        for field_name in tp.get_type_hints(cls):
            if field_name != "_state_properties":
                # default_value = field_def.default if field_def.default is not field_def.default_factory else DEFAULT_MARKER
                prop = StatefulProperty(default=DEFAULT_MARKER)
                prop.__set_name__(cls, field_name)
                setattr(cls, field_name, prop)
                print(
                    f"Converted field '{field_name}' to StatefulProperty with default '{DEFAULT_MARKER}'"
                )


class StatefulProperty:
    name: str

    def __init__(self, default: tp.Any = DEFAULT_MARKER) -> None:
        self.default = default

    def __set_name__(self, owner: type[Stateful], name: str) -> None:
        if not issubclass(owner, Stateful):
            raise TypeError("StatefulProperty can only be used in subclasses of Stateful")
        owner._state_properties[name] = StatePropertyInfo(name=name, default=self.default)
        self.name = name

    # overloads for class and instance access
    @tp.overload
    def __get__(self, instance: Stateful, owner: type[Stateful]) -> tp.Any: ...

    @tp.overload
    def __get__(self, instance: None, owner: type[Stateful]) -> "StatefulProperty": ...

    def __get__(self, instance: Stateful, owner: type[Stateful]) -> tp.Any:
        print(f"Getting state property '{self.name}' for instance '{instance}' of owner '{owner}'")
        if instance is None:
            return self
        state_info = instance._state_properties[self.name]
        if state_info.value is DEFAULT_MARKER:
            if state_info.default is not DEFAULT_MARKER:
                state_info.value = state_info.default
            else:
                raise AttributeError(
                    f"State property '{self.name}' has not been set and has no default value."
                )

        context = get_active_render_context()
        print(
            f"Accessing state property '{self.name}' with value '{state_info.value}' in context '{context}'"
        )
        if context is not None and context.rendering:
            # Register the current element as dependent on this state property
            if (current_element := context.current_element) is not None:
                print(
                    f"Registering element {current_element.component.name} for state property '{self.name}'"
                )
                if isinstance(current_element, BlockElement):
                    state_info.elements.add((context, current_element.parent))
                else:
                    state_info.elements.add((context, current_element))
        return state_info.value

    def __set__(self, instance: Stateful, value: tp.Any) -> None:
        state_info = instance._state_properties[self.name]
        state_info.value = value
        print(
            f"Setting state property '{self.name}' to value '{value}' for instance '{instance}' number of dependent elements: {len(state_info.elements)}"
        )
        # Mark all associated elements as dirty
        for context, element in state_info.elements:
            print(
                f"Marking element {element.component.name} in context {context} as dirty due to state change of '{self.name}'"
            )
            context.mark_dirty(element)
