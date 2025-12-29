"""Tests for deeply nested and wide component trees.

These tests verify that the framework correctly handles:
- Deep trees (50+ levels)
- Wide trees (50+ siblings)
- Combined deep and wide structures
- Correct parent/child relationships
"""

from dataclasses import dataclass

from tests.conftest import PatchCapture
from trellis.core.components.composition import component
from trellis.core.rendering.element import Element
from trellis.core.state.stateful import Stateful


class TestDeepTrees:
    """Tests for deeply nested component trees."""

    def test_50_level_deep_tree(self, capture_patches: "type[PatchCapture]") -> None:
        """Tree with 50 levels should render correctly."""
        DEPTH = 50

        def make_level(n: int):
            @component
            def Level() -> None:
                if n < DEPTH:
                    make_level(n + 1)()

            return Level

        @component
        def Root() -> None:
            make_level(1)()

        capture = capture_patches(Root)
        capture.render()

        # Verify tree structure by counting levels
        def count_depth(node: Element) -> int:
            if not node.child_ids:
                return 1
            return 1 + max(
                count_depth(capture.session.elements.get(cid))
                for cid in node.child_ids
                if capture.session.elements.get(cid)
            )

        max_depth = count_depth(capture.session.root_element)
        assert max_depth == DEPTH + 1  # +1 for Root

    def test_parent_child_relationships_deep_tree(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Parent/child relationships should be correct in deep tree."""
        DEPTH = 50
        relationship_errors: list[str] = []

        def make_level(n: int):
            @component
            def Level() -> None:
                if n < DEPTH:
                    make_level(n + 1)()

            return Level

        @component
        def Root() -> None:
            make_level(1)()

        capture = capture_patches(Root)
        capture.render()

        def verify_relationships(node: Element, expected_parent_id: str | None) -> None:
            state = capture.session.states.get(node.id)
            if state is None:
                relationship_errors.append(f"No state for node {node.id}")
                return
            if state.parent_id != expected_parent_id:
                relationship_errors.append(
                    f"Node {node.id} has parent_id {state.parent_id}, expected {expected_parent_id}"
                )
            for child_id in node.child_ids:
                child = capture.session.elements.get(child_id)
                if child:
                    verify_relationships(child, node.id)

        verify_relationships(capture.session.root_element, None)
        assert len(relationship_errors) == 0, f"Relationship errors: {relationship_errors}"

    def test_deep_tree_rerender_preserves_structure(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Re-rendering deep tree should preserve node identity."""
        DEPTH = 20
        node_ids_before: list[str] = []
        node_ids_after: list[str] = []

        @component
        def Level(n: int = 0) -> None:
            if n < DEPTH:
                Level(n=n + 1)

        @component
        def Root() -> None:
            Level(n=1)

        capture = capture_patches(Root)
        capture.render()

        def collect_ids(node: Element, ids: list[str]) -> None:
            ids.append(node.id)
            for child_id in node.child_ids:
                child = capture.session.elements.get(child_id)
                if child:
                    collect_ids(child, ids)

        collect_ids(capture.session.root_element, node_ids_before)

        # Re-render
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        collect_ids(capture.session.root_element, node_ids_after)

        # Node IDs should be preserved
        assert node_ids_before == node_ids_after

    def test_deep_tree_with_state(self, capture_patches: "type[PatchCapture]") -> None:
        """Deep tree with state at various levels should work correctly."""
        DEPTH = 30
        mount_count = [0]
        unmount_count = [0]

        @dataclass
        class LevelState(Stateful):
            level: int = 0

            def on_mount(self) -> None:
                mount_count[0] += 1

            def on_unmount(self) -> None:
                unmount_count[0] += 1

        @component
        def Level(n: int = 0) -> None:
            LevelState(level=n)
            if n < DEPTH:
                Level(n=n + 1)

        @component
        def Root() -> None:
            Level(n=1)

        capture = capture_patches(Root)
        capture.render()

        # One state per level (not including root)
        assert mount_count[0] == DEPTH

        # Re-render should not create new states
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()
        assert mount_count[0] == DEPTH  # Still same


class TestWideTrees:
    """Tests for wide component trees (many siblings)."""

    def test_50_siblings(self, capture_patches: "type[PatchCapture]") -> None:
        """Tree with 50 siblings should render correctly."""
        WIDTH = 50

        @component
        def Child(n: int = 0) -> None:
            pass

        @component
        def Parent() -> None:
            for i in range(WIDTH):
                Child(n=i)

        capture = capture_patches(Parent)
        capture.render()

        assert len(capture.session.root_element.child_ids) == WIDTH

    def test_wide_tree_rerender(self, capture_patches: "type[PatchCapture]") -> None:
        """Re-rendering wide tree should preserve children."""
        WIDTH = 50

        @component
        def Child(n: int = 0) -> None:
            pass

        @component
        def Parent() -> None:
            for i in range(WIDTH):
                Child(n=i)

        capture = capture_patches(Parent)
        capture.render()

        original_ids = list(capture.session.root_element.child_ids)

        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        new_ids = list(capture.session.root_element.child_ids)
        assert original_ids == new_ids

    def test_add_siblings(self, capture_patches: "type[PatchCapture]") -> None:
        """Adding siblings should mount new elements."""
        count_ref = [3]

        @component
        def Child(n: int = 0) -> None:
            pass

        @component
        def Parent() -> None:
            for i in range(count_ref[0]):
                Child(n=i)

        capture = capture_patches(Parent)
        capture.render()

        assert len(capture.session.root_element.child_ids) == 3

        # Add more siblings
        count_ref[0] = 50
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert len(capture.session.root_element.child_ids) == 50

    def test_remove_siblings(self, capture_patches: "type[PatchCapture]") -> None:
        """Removing siblings should unmount old elements."""
        count_ref = [50]
        unmount_log: list[int] = []

        @dataclass
        class TrackedState(Stateful):
            n: int = 0

            def on_unmount(self) -> None:
                unmount_log.append(self.n)

        @component
        def Child(n: int = 0) -> None:
            TrackedState(n=n)

        @component
        def Parent() -> None:
            for i in range(count_ref[0]):
                Child(key=str(i), n=i)

        capture = capture_patches(Parent)
        capture.render()

        assert len(capture.session.root_element.child_ids) == 50

        # Remove siblings
        count_ref[0] = 10
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert len(capture.session.root_element.child_ids) == 10
        # 40 elements should have been unmounted (indices 10-49)
        assert len(unmount_log) == 40
        assert all(n >= 10 for n in unmount_log)


class TestCombinedDeepAndWide:
    """Tests for trees that are both deep and wide."""

    def test_branching_tree(self, capture_patches: "type[PatchCapture]") -> None:
        """Tree with branching factor at each level."""
        DEPTH = 5
        BRANCH_FACTOR = 3

        @component
        def Level(depth: int = 0) -> None:
            if depth < DEPTH:
                for _ in range(BRANCH_FACTOR):
                    Level(depth=depth + 1)

        @component
        def Root() -> None:
            Level(depth=1)

        capture = capture_patches(Root)
        capture.render()

        # Count total nodes
        def count_nodes(node: Element) -> int:
            return 1 + sum(
                count_nodes(capture.session.elements.get(cid))
                for cid in node.child_ids
                if capture.session.elements.get(cid)
            )

        total = count_nodes(capture.session.root_element)

        # Expected: Root + Level(1) + 3*Level(2) + 9*Level(3) + 27*Level(4) + 81*Level(5)
        # Level(depth) creates no children when depth >= DEPTH, so:
        # - Root: 1
        # - Level(1): 1 (creates 3 children)
        # - Level(2): 3
        # - Level(3): 9
        # - Level(4): 27
        # - Level(5): 81 (no children, depth=5 is not < 5)
        # Total: 1 + 1 + 3 + 9 + 27 + 81 = 122
        expected = 1 + 1 + 3 + 9 + 27 + 81
        assert total == expected

    def test_deep_tree_with_wide_leaf_level(self, capture_patches: "type[PatchCapture]") -> None:
        """Deep tree with many children at the leaf level."""
        DEPTH = 20
        LEAF_COUNT = 50

        def make_level(n: int):
            @component
            def Level() -> None:
                if n < DEPTH:
                    make_level(n + 1)()
                else:
                    # Leaf level - add many children
                    for i in range(LEAF_COUNT):
                        Leaf(n=i)

            return Level

        @component
        def Leaf(n: int = 0) -> None:
            pass

        @component
        def Root() -> None:
            make_level(1)()

        capture = capture_patches(Root)
        capture.render()

        # Navigate to leaf level and check
        node = capture.session.root_element
        for _ in range(DEPTH):
            node = capture.session.elements.get(node.child_ids[0])

        assert len(node.child_ids) == LEAF_COUNT


class TestMountingOrder:
    """Tests for correct mounting order in deep/wide trees."""

    def test_deep_tree_mount_order(self, capture_patches: "type[PatchCapture]") -> None:
        """Mount order should be parent-first in deep tree."""
        DEPTH = 20
        mount_order: list[int] = []

        @dataclass
        class TrackedState(Stateful):
            level: int = 0

            def on_mount(self) -> None:
                mount_order.append(self.level)

        def make_level(n: int):
            @component
            def Level() -> None:
                TrackedState(level=n)
                if n < DEPTH:
                    make_level(n + 1)()

            return Level

        @component
        def Root() -> None:
            TrackedState(level=0)
            make_level(1)()

        capture = capture_patches(Root)
        capture.render()

        # Should be in order 0, 1, 2, ..., DEPTH
        assert mount_order == list(range(DEPTH + 1))

    def test_wide_tree_unmount_order(self, capture_patches: "type[PatchCapture]") -> None:
        """Unmount order for siblings when parent unmounts."""
        show_ref = [True]
        unmount_order: list[int] = []

        @dataclass
        class TrackedState(Stateful):
            n: int = 0

            def on_unmount(self) -> None:
                unmount_order.append(self.n)

        @component
        def Child(n: int = 0) -> None:
            TrackedState(n=n)

        @component
        def Container() -> None:
            for i in range(10):
                Child(n=i)

        @component
        def Root() -> None:
            if show_ref[0]:
                Container()

        capture = capture_patches(Root)
        capture.render()

        # Remove container
        show_ref[0] = False
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        # All children should have unmounted
        assert len(unmount_order) == 10


class TestTreeTraversal:
    """Tests for tree traversal edge cases."""

    def test_empty_tree(self, capture_patches: "type[PatchCapture]") -> None:
        """Tree with no children should work."""

        @component
        def Empty() -> None:
            pass

        capture = capture_patches(Empty)
        capture.render()

        assert capture.session.root_element is not None
        assert len(capture.session.root_element.child_ids) == 0

    def test_single_child_chain(self, capture_patches: "type[PatchCapture]") -> None:
        """Tree where each node has exactly one child."""
        DEPTH = 50

        def make_level(n: int):
            @component
            def Level() -> None:
                if n < DEPTH:
                    make_level(n + 1)()

            return Level

        @component
        def Root() -> None:
            make_level(1)()

        capture = capture_patches(Root)
        capture.render()

        # Traverse and verify single-child chain
        node = capture.session.root_element
        count = 0
        while node.child_ids:
            assert len(node.child_ids) == 1
            node = capture.session.elements.get(node.child_ids[0])
            count += 1

        # Should have traversed DEPTH levels (from Root's child to deepest)
        assert count == DEPTH

    def test_asymmetric_tree(self, capture_patches: "type[PatchCapture]") -> None:
        """Tree with different depths in different branches."""

        @component
        def Leaf() -> None:
            pass

        @component
        def DeepBranch(depth: int = 5) -> None:
            if depth > 0:
                DeepBranch(depth=depth - 1)
            else:
                Leaf()

        @component
        def ShallowBranch() -> None:
            Leaf()

        @component
        def Root() -> None:
            DeepBranch(depth=10)  # Deep left branch
            ShallowBranch()  # Shallow right branch

        capture = capture_patches(Root)
        capture.render()

        # Root has 2 children
        assert len(capture.session.root_element.child_ids) == 2

        # Count depth of deep branch
        def count_depth(node: Element) -> int:
            if not node.child_ids:
                return 1
            return 1 + max(
                count_depth(capture.session.elements.get(cid))
                for cid in node.child_ids
                if capture.session.elements.get(cid)
            )

        deep_branch = capture.session.elements.get(capture.session.root_element.child_ids[0])
        shallow_branch = capture.session.elements.get(capture.session.root_element.child_ids[1])

        deep_depth = count_depth(deep_branch)
        shallow_depth = count_depth(shallow_branch)

        # Deep branch: DeepBranch(10) -> DeepBranch(9) -> ... -> DeepBranch(0) -> Leaf = 12 levels
        assert deep_depth == 12
        # Shallow branch: ShallowBranch -> Leaf = 2 levels
        assert shallow_depth == 2
        # Deep branch should be much deeper
        assert deep_depth > shallow_depth
