"""Tests for indicator widgets: ProgressBar, StatusIndicator, Badge, Tooltip."""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.widgets import Badge, Button, Label, ProgressBar, StatusIndicator, Tooltip


class TestProgressBarWidget:
    """Tests for ProgressBar widget."""

    def test_progress_bar_with_value(self) -> None:
        """ProgressBar stores value, min, max props."""

        @component
        def App() -> None:
            """
            Renders a ProgressBar set to value 50 with minimum 0 and maximum 100.
            
            This component provides a simple wrapper that mounts a ProgressBar with predefined value and bounds for use in tests.
            """
            ProgressBar(value=50, min=0, max=100)

        ctx = RenderSession(App)
        render(ctx)

        progress = ctx.elements.get(ctx.root_element.child_ids[0])
        assert progress.component.name == "ProgressBar"
        assert progress.properties["value"] == 50
        assert progress.properties["min"] == 0
        assert progress.properties["max"] == 100

    def test_progress_bar_loading(self) -> None:
        """ProgressBar accepts loading prop."""

        @component
        def App() -> None:
            """
            Defines a test component that renders a ProgressBar configured in the loading state.
            
            This component produces a single ProgressBar with loading=True for use in rendering tests.
            """
            ProgressBar(loading=True)

        ctx = RenderSession(App)
        render(ctx)

        progress = ctx.elements.get(ctx.root_element.child_ids[0])
        assert progress.properties["loading"] is True

    def test_progress_bar_disabled(self) -> None:
        """ProgressBar accepts disabled prop."""

        @component
        def App() -> None:
            """
            Render a disabled ProgressBar component used by tests.
            """
            ProgressBar(disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        progress = ctx.elements.get(ctx.root_element.child_ids[0])
        assert progress.properties["disabled"] is True

    def test_progress_bar_with_color(self) -> None:
        """ProgressBar accepts color prop."""

        @component
        def App() -> None:
            """
            Render a ProgressBar with a value of 75 and color "#22c55e".
            
            This component creates a ProgressBar configured to 75% progress and styled with the hex color #22c55e.
            """
            ProgressBar(value=75, color="#22c55e")

        ctx = RenderSession(App)
        render(ctx)

        progress = ctx.elements.get(ctx.root_element.child_ids[0])
        assert progress.properties["color"] == "#22c55e"

    def test_progress_bar_with_height(self) -> None:
        """ProgressBar accepts height prop."""

        @component
        def App() -> None:
            """
            Render a ProgressBar configured with a value of 25 and a height of 12.
            
            This component function is used by tests to produce a ProgressBar element with those props.
            """
            ProgressBar(value=25, height=12)

        ctx = RenderSession(App)
        render(ctx)

        progress = ctx.elements.get(ctx.root_element.child_ids[0])
        assert progress.properties["height"] == 12

    def test_progress_bar_with_style(self) -> None:
        """ProgressBar accepts style dict."""

        @component
        def App() -> None:
            """
            Render a minimal App component containing a ProgressBar configured with a value of 50 and a bottom margin.
            
            The component instantiates a single ProgressBar with `value=50` and `style={"marginBottom": "24px"}`.
            """
            ProgressBar(value=50, style={"marginBottom": "24px"})

        ctx = RenderSession(App)
        render(ctx)

        progress = ctx.elements.get(ctx.root_element.child_ids[0])
        assert progress.properties["style"] == {"marginBottom": "24px"}


class TestStatusIndicatorWidget:
    """Tests for StatusIndicator widget."""

    def test_status_indicator_with_status(self) -> None:
        """
        Verifies that StatusIndicator receives and exposes the provided status property.
        
        Renders a component containing a StatusIndicator with status "success" and asserts the rendered element's component name is "StatusIndicator" and its "status" property equals "success".
        """

        @component
        def App() -> None:
            """
            Component that renders a StatusIndicator with status "success".
            """
            StatusIndicator(status="success")

        ctx = RenderSession(App)
        render(ctx)

        indicator = ctx.elements.get(ctx.root_element.child_ids[0])
        assert indicator.component.name == "StatusIndicator"
        assert indicator.properties["status"] == "success"

    def test_status_indicator_with_label(self) -> None:
        """StatusIndicator stores label prop."""

        @component
        def App() -> None:
            """
            Render a StatusIndicator component with status "error" and label "Failed".
            """
            StatusIndicator(status="error", label="Failed")

        ctx = RenderSession(App)
        render(ctx)

        indicator = ctx.elements.get(ctx.root_element.child_ids[0])
        assert indicator.properties["status"] == "error"
        assert indicator.properties["label"] == "Failed"

    def test_status_indicator_hide_icon(self) -> None:
        """StatusIndicator accepts show_icon prop."""

        @component
        def App() -> None:
            """
            Create an application component that renders a StatusIndicator with a "warning" status and its icon hidden.
            
            This App component instantiates a single StatusIndicator configured with status="warning" and show_icon=False.
            """
            StatusIndicator(status="warning", show_icon=False)

        ctx = RenderSession(App)
        render(ctx)

        indicator = ctx.elements.get(ctx.root_element.child_ids[0])
        assert indicator.properties["show_icon"] is False


class TestBadgeWidget:
    """Tests for Badge widget."""

    def test_badge_with_text(self) -> None:
        """Badge stores text prop."""

        @component
        def App() -> None:
            """
            Render a test application containing a single Badge with text "New".
            
            Used by unit tests to instantiate and render a single Badge component for inspection.
            """
            Badge(text="New")

        ctx = RenderSession(App)
        render(ctx)

        badge = ctx.elements.get(ctx.root_element.child_ids[0])
        assert badge.component.name == "Badge"
        assert badge.properties["text"] == "New"

    def test_badge_with_variant(self) -> None:
        """Badge accepts variant prop."""

        @component
        def App() -> None:
            """
            Renders a Badge component with text "Error" and variant "error" for use in tests.
            """
            Badge(text="Error", variant="error")

        ctx = RenderSession(App)
        render(ctx)

        badge = ctx.elements.get(ctx.root_element.child_ids[0])
        assert badge.properties["variant"] == "error"

    def test_badge_with_size(self) -> None:
        """Badge accepts size prop."""

        @component
        def App() -> None:
            """
            Test component that renders a medium-sized Badge with the text "Large".
            
            Used by tests to produce a Badge widget configured with size "md" and text "Large".
            """
            Badge(text="Large", size="md")

        ctx = RenderSession(App)
        render(ctx)

        badge = ctx.elements.get(ctx.root_element.child_ids[0])
        assert badge.properties["size"] == "md"


class TestTooltipWidget:
    """Tests for Tooltip widget."""

    def test_tooltip_with_content(self) -> None:
        """Tooltip stores content prop."""

        @component
        def App() -> None:
            """
            Renders a Tooltip with the text "Helpful hint" that wraps a Label displaying "Hover me".
            
            Used by tests to produce a widget tree containing a Tooltip element with a single Label child.
            """
            with Tooltip(content="Helpful hint"):
                Label(text="Hover me")

        ctx = RenderSession(App)
        render(ctx)

        tooltip = ctx.elements.get(ctx.root_element.child_ids[0])
        assert tooltip.component.name == "Tooltip"
        assert tooltip.properties["content"] == "Helpful hint"
        assert len(tooltip.child_ids) == 1

    def test_tooltip_with_position(self) -> None:
        """Tooltip accepts position prop."""

        @component
        def App() -> None:
            """
            Create a component that renders a Tooltip positioned at the bottom with content "Below" wrapping a Button labeled "Click".
            """
            with Tooltip(content="Below", position="bottom"):
                Button(text="Click")

        ctx = RenderSession(App)
        render(ctx)

        tooltip = ctx.elements.get(ctx.root_element.child_ids[0])
        assert tooltip.properties["position"] == "bottom"

    def test_tooltip_with_delay(self) -> None:
        """Tooltip accepts delay prop."""

        @component
        def App() -> None:
            """
            Render a Tooltip with content "Slow" and a 500ms delay around a Label displaying "Wait".
            """
            with Tooltip(content="Slow", delay=500):
                Label(text="Wait")

        ctx = RenderSession(App)
        render(ctx)

        tooltip = ctx.elements.get(ctx.root_element.child_ids[0])
        assert tooltip.properties["delay"] == 500