"""Tests for DirtyTracker and LifecycleTracker classes."""

from trellis.core.rendering.dirty_tracker import DirtyTracker
from trellis.core.rendering.lifecycle import LifecycleTracker

# =============================================================================
# DirtyTracker Tests
# =============================================================================


class TestDirtyTracker:
    def test_mark_and_contains(self):
        tracker = DirtyTracker()

        tracker.mark("e1")
        assert "e1" in tracker
        assert "e2" not in tracker

    def test_clear(self):
        tracker = DirtyTracker()
        tracker.mark("e1")

        tracker.clear("e1")
        assert "e1" not in tracker

    def test_clear_nonexistent_no_error(self):
        tracker = DirtyTracker()
        tracker.clear("nonexistent")  # Should not raise

    def test_discard(self):
        tracker = DirtyTracker()
        tracker.mark("e1")

        tracker.discard("e1")
        assert "e1" not in tracker

    def test_has_dirty(self):
        tracker = DirtyTracker()
        assert not tracker.has_dirty()

        tracker.mark("e1")
        assert tracker.has_dirty()

        tracker.clear("e1")
        assert not tracker.has_dirty()

    def test_pop_all(self):
        tracker = DirtyTracker()
        tracker.mark("e1")
        tracker.mark("e2")
        tracker.mark("e3")

        ids = tracker.pop_all()
        assert set(ids) == {"e1", "e2", "e3"}
        assert not tracker.has_dirty()
        assert len(tracker) == 0

    def test_len(self):
        tracker = DirtyTracker()
        assert len(tracker) == 0

        tracker.mark("e1")
        assert len(tracker) == 1

        tracker.mark("e1")  # Duplicate
        assert len(tracker) == 1

        tracker.mark("e2")
        assert len(tracker) == 2


# =============================================================================
# LifecycleTracker Tests
# =============================================================================


class TestLifecycleTracker:
    def test_track_mount(self):
        tracker = LifecycleTracker()

        tracker.track_mount("e1")
        tracker.track_mount("e2")

        mounts = tracker.pop_mounts()
        assert mounts == ["e1", "e2"]

    def test_track_unmount(self):
        tracker = LifecycleTracker()

        tracker.track_unmount("e1")
        tracker.track_unmount("e2")

        unmounts = tracker.pop_unmounts()
        assert unmounts == ["e1", "e2"]

    def test_pop_mounts_clears(self):
        tracker = LifecycleTracker()
        tracker.track_mount("e1")

        tracker.pop_mounts()
        assert tracker.pop_mounts() == []

    def test_pop_unmounts_clears(self):
        tracker = LifecycleTracker()
        tracker.track_unmount("e1")

        tracker.pop_unmounts()
        assert tracker.pop_unmounts() == []

    def test_has_pending(self):
        tracker = LifecycleTracker()
        assert not tracker.has_pending()

        tracker.track_mount("e1")
        assert tracker.has_pending()

        tracker.pop_mounts()
        assert not tracker.has_pending()

        tracker.track_unmount("e1")
        assert tracker.has_pending()

    def test_clear(self):
        tracker = LifecycleTracker()
        tracker.track_mount("e1")
        tracker.track_unmount("e2")

        tracker.clear()
        assert not tracker.has_pending()
        assert tracker.pop_mounts() == []
        assert tracker.pop_unmounts() == []
