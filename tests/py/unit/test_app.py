"""Unit tests for user-facing App class."""

from __future__ import annotations

from trellis.app.app import App
from trellis.core.components.base import Component
from trellis.core.components.composition import CompositionComponent, component


class TestApp:
    """Tests for App class constructor and top attribute."""

    def test_constructor_stores_top(self) -> None:
        """App constructor stores the top component."""

        @component
        def MyRoot() -> None:
            pass

        app = App(MyRoot)

        assert app.top is MyRoot

    def test_top_returns_component(self) -> None:
        """App.top returns the component passed to constructor."""

        @component
        def AnotherRoot() -> None:
            pass

        app = App(AnotherRoot)

        assert app.top is AnotherRoot

    def test_top_accepts_callable(self) -> None:
        """App accepts any callable that returns Element."""

        def plain_function() -> None:
            pass

        app = App(plain_function)

        assert app.top is plain_function


class TestAppGetWrappedTop:
    """Tests for App.get_wrapped_top method."""

    def test_returns_composition_component(self) -> None:
        """get_wrapped_top returns a CompositionComponent."""

        @component
        def Root() -> None:
            pass

        app = App(Root)

        wrapped = app.get_wrapped_top(system_theme="light", theme_mode="system")

        assert isinstance(wrapped, CompositionComponent)

    def test_wrapped_component_name_is_trellis_root(self) -> None:
        """Wrapped component has name 'TrellisRoot'."""

        @component
        def Root() -> None:
            pass

        app = App(Root)

        wrapped = app.get_wrapped_top(system_theme="light", theme_mode="system")

        assert wrapped.name == "TrellisRoot"

    def test_with_system_theme_light(self) -> None:
        """get_wrapped_top handles system_theme='light'."""

        @component
        def Root() -> None:
            pass

        app = App(Root)

        # Should not raise
        wrapped = app.get_wrapped_top(system_theme="light", theme_mode="system")

        assert isinstance(wrapped, Component)

    def test_with_system_theme_dark(self) -> None:
        """get_wrapped_top handles system_theme='dark'."""

        @component
        def Root() -> None:
            pass

        app = App(Root)

        # Should not raise
        wrapped = app.get_wrapped_top(system_theme="dark", theme_mode="dark")

        assert isinstance(wrapped, Component)

    def test_with_theme_mode_none_defaults_to_system(self) -> None:
        """get_wrapped_top uses 'system' when theme_mode is None."""

        @component
        def Root() -> None:
            pass

        app = App(Root)

        # Should not raise - defaults to system theme mode
        wrapped = app.get_wrapped_top(system_theme="light", theme_mode=None)

        assert isinstance(wrapped, Component)

    def test_with_theme_mode_light(self) -> None:
        """get_wrapped_top handles theme_mode='light'."""

        @component
        def Root() -> None:
            pass

        app = App(Root)

        wrapped = app.get_wrapped_top(system_theme="dark", theme_mode="light")

        assert isinstance(wrapped, Component)

    def test_with_theme_mode_dark(self) -> None:
        """get_wrapped_top handles theme_mode='dark'."""

        @component
        def Root() -> None:
            pass

        app = App(Root)

        wrapped = app.get_wrapped_top(system_theme="light", theme_mode="dark")

        assert isinstance(wrapped, Component)

    def test_with_theme_mode_system(self) -> None:
        """get_wrapped_top handles theme_mode='system'."""

        @component
        def Root() -> None:
            pass

        app = App(Root)

        wrapped = app.get_wrapped_top(system_theme="dark", theme_mode="system")

        assert isinstance(wrapped, Component)


class TestAppExport:
    """Tests for App being exported from trellis.app package."""

    def test_app_exported_from_package(self) -> None:
        """App is exported from trellis.app."""
        from trellis.app import App as AppFromPackage  # noqa: PLC0415

        @component
        def Root() -> None:
            pass

        # Should be usable
        app = AppFromPackage(Root)
        assert app.top is Root
