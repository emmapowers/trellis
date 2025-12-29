"""Tests for indicator widgets: ProgressBar, StatusIndicator, Badge, Tooltip."""

from trellis.core.components.composition import component
from trellis.widgets import Badge, Button, Label, ProgressBar, StatusIndicator, Tooltip


class TestProgressBarWidget:
    """Tests for ProgressBar widget."""

    def test_progress_bar_with_value(self, rendered) -> None:
        """ProgressBar stores value, min, max props."""

        @component
        def App() -> None:
            ProgressBar(value=50, min=0, max=100)

        result = rendered(App)

        progress = result.session.elements.get(result.root_element.child_ids[0])
        assert progress.component.name == "ProgressBar"
        assert progress.properties["value"] == 50
        assert progress.properties["min"] == 0
        assert progress.properties["max"] == 100

    def test_progress_bar_loading(self, rendered) -> None:
        """ProgressBar accepts loading prop."""

        @component
        def App() -> None:
            ProgressBar(loading=True)

        result = rendered(App)

        progress = result.session.elements.get(result.root_element.child_ids[0])
        assert progress.properties["loading"] is True

    def test_progress_bar_disabled(self, rendered) -> None:
        """ProgressBar accepts disabled prop."""

        @component
        def App() -> None:
            ProgressBar(disabled=True)

        result = rendered(App)

        progress = result.session.elements.get(result.root_element.child_ids[0])
        assert progress.properties["disabled"] is True

    def test_progress_bar_with_color(self, rendered) -> None:
        """ProgressBar accepts color prop."""

        @component
        def App() -> None:
            ProgressBar(value=75, color="#22c55e")

        result = rendered(App)

        progress = result.session.elements.get(result.root_element.child_ids[0])
        assert progress.properties["color"] == "#22c55e"

    def test_progress_bar_with_height(self, rendered) -> None:
        """ProgressBar accepts height prop."""

        @component
        def App() -> None:
            ProgressBar(value=25, height=12)

        result = rendered(App)

        progress = result.session.elements.get(result.root_element.child_ids[0])
        assert progress.properties["height"] == 12

    def test_progress_bar_with_style(self, rendered) -> None:
        """ProgressBar accepts style dict."""

        @component
        def App() -> None:
            ProgressBar(value=50, style={"marginBottom": "24px"})

        result = rendered(App)

        progress = result.session.elements.get(result.root_element.child_ids[0])
        assert progress.properties["style"] == {"marginBottom": "24px"}


class TestStatusIndicatorWidget:
    """Tests for StatusIndicator widget."""

    def test_status_indicator_with_status(self, rendered) -> None:
        """StatusIndicator stores status prop."""

        @component
        def App() -> None:
            StatusIndicator(status="success")

        result = rendered(App)

        indicator = result.session.elements.get(result.root_element.child_ids[0])
        assert indicator.component.name == "StatusIndicator"
        assert indicator.properties["status"] == "success"

    def test_status_indicator_with_label(self, rendered) -> None:
        """StatusIndicator stores label prop."""

        @component
        def App() -> None:
            StatusIndicator(status="error", label="Failed")

        result = rendered(App)

        indicator = result.session.elements.get(result.root_element.child_ids[0])
        assert indicator.properties["status"] == "error"
        assert indicator.properties["label"] == "Failed"

    def test_status_indicator_hide_icon(self, rendered) -> None:
        """StatusIndicator accepts show_icon prop."""

        @component
        def App() -> None:
            StatusIndicator(status="warning", show_icon=False)

        result = rendered(App)

        indicator = result.session.elements.get(result.root_element.child_ids[0])
        assert indicator.properties["show_icon"] is False


class TestBadgeWidget:
    """Tests for Badge widget."""

    def test_badge_with_text(self, rendered) -> None:
        """Badge stores text prop."""

        @component
        def App() -> None:
            Badge(text="New")

        result = rendered(App)

        badge = result.session.elements.get(result.root_element.child_ids[0])
        assert badge.component.name == "Badge"
        assert badge.properties["text"] == "New"

    def test_badge_with_variant(self, rendered) -> None:
        """Badge accepts variant prop."""

        @component
        def App() -> None:
            Badge(text="Error", variant="error")

        result = rendered(App)

        badge = result.session.elements.get(result.root_element.child_ids[0])
        assert badge.properties["variant"] == "error"

    def test_badge_with_size(self, rendered) -> None:
        """Badge accepts size prop."""

        @component
        def App() -> None:
            Badge(text="Large", size="md")

        result = rendered(App)

        badge = result.session.elements.get(result.root_element.child_ids[0])
        assert badge.properties["size"] == "md"


class TestTooltipWidget:
    """Tests for Tooltip widget."""

    def test_tooltip_with_content(self, rendered) -> None:
        """Tooltip stores content prop."""

        @component
        def App() -> None:
            with Tooltip(content="Helpful hint"):
                Label(text="Hover me")

        result = rendered(App)

        tooltip = result.session.elements.get(result.root_element.child_ids[0])
        assert tooltip.component.name == "Tooltip"
        assert tooltip.properties["content"] == "Helpful hint"
        assert len(tooltip.child_ids) == 1

    def test_tooltip_with_position(self, rendered) -> None:
        """Tooltip accepts position prop."""

        @component
        def App() -> None:
            with Tooltip(content="Below", position="bottom"):
                Button(text="Click")

        result = rendered(App)

        tooltip = result.session.elements.get(result.root_element.child_ids[0])
        assert tooltip.properties["position"] == "bottom"

    def test_tooltip_with_delay(self, rendered) -> None:
        """Tooltip accepts delay prop."""

        @component
        def App() -> None:
            with Tooltip(content="Slow", delay=500):
                Label(text="Wait")

        result = rendered(App)

        tooltip = result.session.elements.get(result.root_element.child_ids[0])
        assert tooltip.properties["delay"] == 500
