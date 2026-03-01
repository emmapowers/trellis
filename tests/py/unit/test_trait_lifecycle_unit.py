"""Unit tests for trait state management and hook discovery."""

from __future__ import annotations

from dataclasses import dataclass

from trellis.core.rendering.element_state import ElementState
from trellis.core.rendering.traits import get_trait_hooks

# =============================================================================
# ElementState.trait() accessor
# =============================================================================


class TestElementStateTrait:
    def test_trait_creates_state_on_first_access(self) -> None:
        """trait() instantiates the state type on first call."""

        @dataclass
        class FooState:
            value: int = 0

        state = ElementState()
        foo = state.trait(FooState)
        assert isinstance(foo, FooState)
        assert foo.value == 0

    def test_trait_returns_cached_on_subsequent_access(self) -> None:
        """trait() returns the same instance on repeated calls."""

        @dataclass
        class FooState:
            value: int = 0

        state = ElementState()
        first = state.trait(FooState)
        first.value = 42
        second = state.trait(FooState)
        assert second is first
        assert second.value == 42

    def test_different_state_types_are_independent(self) -> None:
        """Different state types get independent instances."""

        @dataclass
        class AlphaState:
            x: int = 1

        @dataclass
        class BetaState:
            y: str = "hello"

        state = ElementState()
        alpha = state.trait(AlphaState)
        beta = state.trait(BetaState)
        assert isinstance(alpha, AlphaState)
        assert isinstance(beta, BetaState)
        assert alpha is not beta

    def test_trait_state_starts_empty(self) -> None:
        """_trait_state dict is empty on a fresh ElementState."""
        state = ElementState()
        assert state._trait_state == {}


# =============================================================================
# TraitHooks and get_trait_hooks()
# =============================================================================


class _BaseTrait:
    """A trait with all four hooks defined."""

    def _before_execute(self, element: object, state: object, session: object) -> None:
        pass

    def _after_execute(self, element: object, state: object, session: object) -> None:
        pass

    def _on_trait_mount(self, element: object, state: object, session: object) -> None:
        pass

    def _on_trait_unmount(self, element: object, state: object, session: object) -> None:
        pass


class _PartialTrait:
    """A trait with only some hooks."""

    def _before_execute(self, element: object, state: object, session: object) -> None:
        pass


class _NoHooksTrait:
    """A trait with no lifecycle hooks (like KeyTrait)."""

    def some_method(self) -> None:
        pass


class TestTraitHooks:
    def test_discovers_traits_with_all_hooks(self) -> None:
        """get_trait_hooks finds traits with all four hooks."""

        class MyElement(_BaseTrait):
            pass

        hooks = get_trait_hooks(MyElement)
        assert len(hooks) == 1
        th = hooks[0]
        assert th.trait_class is _BaseTrait
        assert th.before_execute is not None
        assert th.after_execute is not None
        assert th.on_mount is not None
        assert th.on_unmount is not None

    def test_skips_traits_without_hooks(self) -> None:
        """Traits without any of the four hooks are skipped."""

        class MyElement(_NoHooksTrait):
            pass

        hooks = get_trait_hooks(MyElement)
        assert len(hooks) == 0

    def test_handles_partial_hooks(self) -> None:
        """Traits with only some hooks are discovered with correct fields."""

        class MyElement(_PartialTrait):
            pass

        hooks = get_trait_hooks(MyElement)
        assert len(hooks) == 1
        th = hooks[0]
        assert th.before_execute is not None
        assert th.after_execute is None
        assert th.on_mount is None
        assert th.on_unmount is None

    def test_caches_results_per_class(self) -> None:
        """Repeated calls return the same list object (cached)."""

        class MyElement(_BaseTrait):
            pass

        first = get_trait_hooks(MyElement)
        second = get_trait_hooks(MyElement)
        assert first is second

    def test_multiple_traits(self) -> None:
        """Element with multiple trait bases discovers all of them."""

        class MyElement(_BaseTrait, _PartialTrait):
            pass

        hooks = get_trait_hooks(MyElement)
        trait_classes = {th.trait_class for th in hooks}
        # _BaseTrait has all hooks; _PartialTrait has _before_execute
        # Both should be discovered
        assert _BaseTrait in trait_classes
        assert _PartialTrait in trait_classes

    def test_does_not_discover_hooks_from_element_class_itself(self) -> None:
        """Hooks defined directly on the element class (not in a trait) are not discovered."""

        class MyElement:
            def _before_execute(self, element: object, state: object, session: object) -> None:
                pass

        hooks = get_trait_hooks(MyElement)
        # MyElement itself defines hooks but is the element class, not a trait base
        assert len(hooks) == 0
