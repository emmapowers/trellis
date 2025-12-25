"""Tests for the pure reconcile_children function.

These tests verify the reconciliation algorithm directly without going through
the full render cycle. If reconcile_children outputs the correct added/removed/
matched/child_order for any input, the renderer behavior follows.
"""

import random

from trellis.core.reconcile import ReconcileResult, reconcile_children


class TestReconcileChildrenBasic:
    """Basic tests for reconcile_children."""

    def test_empty_to_empty(self) -> None:
        """Empty lists produce empty result."""
        result = reconcile_children([], [])
        assert result == ReconcileResult(added=[], removed=[], matched=[], child_order=[])

    def test_empty_to_many(self) -> None:
        """All new IDs are added."""
        result = reconcile_children([], ["a", "b", "c"])
        assert result.added == ["a", "b", "c"]
        assert result.removed == []
        assert result.matched == []
        assert result.child_order == ["a", "b", "c"]

    def test_many_to_empty(self) -> None:
        """All old IDs are removed."""
        result = reconcile_children(["a", "b", "c"], [])
        assert result.added == []
        assert result.removed == ["a", "b", "c"]
        assert result.matched == []
        assert result.child_order == []

    def test_all_match(self) -> None:
        """Identical lists produce all matched."""
        result = reconcile_children(["a", "b", "c"], ["a", "b", "c"])
        assert result.added == []
        assert result.removed == []
        assert result.matched == ["a", "b", "c"]
        assert result.child_order == ["a", "b", "c"]

    def test_partial_overlap(self) -> None:
        """Some matched, some added, some removed."""
        result = reconcile_children(["a", "b", "c"], ["b", "c", "d"])
        assert result.added == ["d"]
        assert result.removed == ["a"]
        assert set(result.matched) == {"b", "c"}
        assert result.child_order == ["b", "c", "d"]


class TestReconcileChildrenHeadTail:
    """Tests for head/tail optimization."""

    def test_head_match_append(self) -> None:
        """Head matching with append at end."""
        result = reconcile_children(["a", "b"], ["a", "b", "c", "d"])
        assert result.added == ["c", "d"]
        assert result.removed == []
        assert result.matched == ["a", "b"]
        assert result.child_order == ["a", "b", "c", "d"]

    def test_tail_match_prepend(self) -> None:
        """Tail matching with prepend at start."""
        result = reconcile_children(["c", "d"], ["a", "b", "c", "d"])
        assert result.added == ["a", "b"]
        assert result.removed == []
        assert set(result.matched) == {"c", "d"}
        assert result.child_order == ["a", "b", "c", "d"]

    def test_middle_removal(self) -> None:
        """Remove from middle (exercises head + tail scan)."""
        result = reconcile_children(["a", "b", "c", "d", "e"], ["a", "b", "d", "e"])
        assert result.added == []
        assert result.removed == ["c"]
        assert set(result.matched) == {"a", "b", "d", "e"}
        assert result.child_order == ["a", "b", "d", "e"]

    def test_middle_insertion(self) -> None:
        """Insert in middle."""
        result = reconcile_children(["a", "d"], ["a", "b", "c", "d"])
        assert set(result.added) == {"b", "c"}
        assert result.removed == []
        assert set(result.matched) == {"a", "d"}
        assert result.child_order == ["a", "b", "c", "d"]

    def test_head_tail_no_middle(self) -> None:
        """Head and tail match with nothing in middle."""
        result = reconcile_children(["a", "b", "c"], ["a", "c"])
        assert result.added == []
        assert result.removed == ["b"]
        assert set(result.matched) == {"a", "c"}
        assert result.child_order == ["a", "c"]


class TestReconcileChildrenEdgeCases:
    """Edge case tests for reconcile_children."""

    def test_reverse_list(self) -> None:
        """Reversing a list should match all, just reordered."""
        old = ["a", "b", "c", "d", "e"]
        new = list(reversed(old))
        result = reconcile_children(old, new)
        assert result.added == []
        assert result.removed == []
        assert set(result.matched) == set(old)
        assert result.child_order == new

    def test_shuffle_list(self) -> None:
        """Shuffling a list should match all, just reordered."""
        random.seed(42)
        old = [f"item_{i}" for i in range(20)]
        new = old.copy()
        random.shuffle(new)
        result = reconcile_children(old, new)
        assert result.added == []
        assert result.removed == []
        assert set(result.matched) == set(old)
        assert result.child_order == new

    def test_remove_from_start(self) -> None:
        """Remove items from the start of a list."""
        old = [f"item_{i}" for i in range(50)]
        new = [f"item_{i}" for i in range(25, 50)]
        result = reconcile_children(old, new)
        assert set(result.removed) == {f"item_{i}" for i in range(25)}
        assert result.added == []
        assert set(result.matched) == set(new)
        assert result.child_order == new

    def test_remove_from_middle(self) -> None:
        """Remove items from the middle of a list."""
        old = [f"item_{i}" for i in range(50)]
        new = [f"item_{i}" for i in range(10)] + [f"item_{i}" for i in range(40, 50)]
        result = reconcile_children(old, new)
        assert set(result.removed) == {f"item_{i}" for i in range(10, 40)}
        assert result.added == []
        assert set(result.matched) == set(new)
        assert result.child_order == new

    def test_remove_from_end(self) -> None:
        """Remove items from the end of a list."""
        old = [f"item_{i}" for i in range(50)]
        new = [f"item_{i}" for i in range(25)]
        result = reconcile_children(old, new)
        assert set(result.removed) == {f"item_{i}" for i in range(25, 50)}
        assert result.added == []
        assert set(result.matched) == set(new)
        assert result.child_order == new

    def test_insert_at_start(self) -> None:
        """Insert items at the start of a list."""
        old = [f"item_{i}" for i in range(25, 50)]
        new = [f"item_{i}" for i in range(50)]
        result = reconcile_children(old, new)
        assert set(result.added) == {f"item_{i}" for i in range(25)}
        assert result.removed == []
        assert set(result.matched) == set(old)
        assert result.child_order == new

    def test_insert_at_end(self) -> None:
        """Insert items at the end of a list."""
        old = [f"item_{i}" for i in range(25)]
        new = [f"item_{i}" for i in range(50)]
        result = reconcile_children(old, new)
        assert set(result.added) == {f"item_{i}" for i in range(25, 50)}
        assert result.removed == []
        assert set(result.matched) == set(old)
        assert result.child_order == new

    def test_complete_replacement(self) -> None:
        """All old removed, all new added."""
        result = reconcile_children(["a", "b", "c"], ["x", "y", "z"])
        assert set(result.added) == {"x", "y", "z"}
        assert set(result.removed) == {"a", "b", "c"}
        assert result.matched == []
        assert result.child_order == ["x", "y", "z"]

    def test_single_item_added(self) -> None:
        """Add a single item."""
        result = reconcile_children([], ["a"])
        assert result.added == ["a"]
        assert result.removed == []
        assert result.matched == []

    def test_single_item_removed(self) -> None:
        """Remove a single item."""
        result = reconcile_children(["a"], [])
        assert result.added == []
        assert result.removed == ["a"]
        assert result.matched == []

    def test_single_item_unchanged(self) -> None:
        """Single item unchanged."""
        result = reconcile_children(["a"], ["a"])
        assert result.added == []
        assert result.removed == []
        assert result.matched == ["a"]


class TestReconcileChildrenLargeScale:
    """Scale tests for reconcile_children."""

    def test_large_list_append(self) -> None:
        """Append to large list (should be fast via head scan)."""
        old = [f"item_{i}" for i in range(1000)]
        new = old + [f"item_{i}" for i in range(1000, 1100)]
        result = reconcile_children(old, new)
        assert len(result.added) == 100
        assert result.removed == []
        assert len(result.matched) == 1000

    def test_large_list_prepend(self) -> None:
        """Prepend to large list (should be fast via tail scan)."""
        old = [f"item_{i}" for i in range(100, 1100)]
        new = [f"item_{i}" for i in range(1100)]
        result = reconcile_children(old, new)
        assert len(result.added) == 100
        assert result.removed == []
        assert len(result.matched) == 1000

    def test_large_list_reverse(self) -> None:
        """Reverse large list (all matched, none added/removed)."""
        old = [f"item_{i}" for i in range(500)]
        new = list(reversed(old))
        result = reconcile_children(old, new)
        assert result.added == []
        assert result.removed == []
        assert len(result.matched) == 500

    def test_large_list_shuffle(self) -> None:
        """Shuffle large list (all matched, none added/removed)."""
        random.seed(123)
        old = [f"item_{i}" for i in range(500)]
        new = old.copy()
        random.shuffle(new)
        result = reconcile_children(old, new)
        assert result.added == []
        assert result.removed == []
        assert len(result.matched) == 500


class TestReconcileChildrenDuplicates:
    """Tests for duplicate ID handling."""

    def test_duplicate_ids_in_new(self) -> None:
        """Duplicate IDs in new list - first match wins."""
        # Note: This is an edge case that shouldn't happen in practice
        # (IDs should be unique), but we test the behavior
        result = reconcile_children(["a"], ["a", "a"])
        # First "a" matches old "a", second "a" is also in old_id_set
        # but already matched, so it's not added again
        assert "a" in result.matched
        assert result.removed == []

    def test_duplicate_ids_in_old(self) -> None:
        """Duplicate IDs in old list - uses set-based matching."""
        result = reconcile_children(["a", "a"], ["a"])
        # The algorithm uses sets, so duplicates in old list are deduplicated
        # Only one "a" is counted as matched (via matched_old_ids set)
        assert "a" in result.matched
        # Both old "a"s are in old_child_ids, but since we use a set for matching,
        # neither duplicate is seen as "unmatched" by the phase 4 loop
        # because "a" is in matched_old_ids
        assert result.removed == []
