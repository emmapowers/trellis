"""Tests for deeply nested and wide component trees.

These tests verify that the framework correctly handles:
- Deep trees (50+ levels)
- Wide trees (50+ siblings)
- Combined deep and wide structures
- Correct parent/child relationships
"""

from dataclasses import dataclass

from trellis.core.components.composition import component
from trellis.core.rendering.element import ElementNode
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful


class TestDeepTrees:
    """Tests for deeply nested component trees."""

    def test_50_level_deep_tree(self) -> None:
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

        ctx = RenderSession(Root)
        render(ctx)

        # Verify tree structure by counting levels
        def count_depth(node: ElementNode) -> int:
            if not node.child_ids:
                return 1
            return 1 + max(count_depth(ctx.elements.get(cid)) for cid in node.child_ids if ctx.elements.get(cid))

        max_depth = count_depth(ctx.root_element)
        assert max_depth == DEPTH + 1  # +1 for Root

    def test_parent_child_relationships_deep_tree(self) -> None:
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

        ctx = RenderSession(Root)
        render(ctx)

        def verify_relationships(node: ElementNode, expected_parent_id: str | None) -> None:
            state = ctx._element_state.get(node.id)
            if state is None:
                relationship_errors.append(f"No state for node {node.id}")
                return
            if state.parent_id != expected_parent_id:
                relationship_errors.append(
                    f"Node {node.id} has parent_id {state.parent_id}, expected {expected_parent_id}"
                )
            for child_id in node.child_ids:
                child = ctx.elements.get(child_id)
                if child:
                    verify_relationships(child, node.id)

        verify_relationships(ctx.root_element, None)
        assert len(relationship_errors) == 0, f"Relationship errors: {relationship_errors}"

    def test_deep_tree_rerender_preserves_structure(self) -> None:
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

        ctx = RenderSession(Root)
        render(ctx)

        def collect_ids(node: ElementNode, ids: list[str]) -> None:
            ids.append(node.id)
            for child_id in node.child_ids:
                child = ctx.elements.get(child_id)
                if child:
                    collect_ids(child, ids)

        collect_ids(ctx.root_element, node_ids_before)

        # Re-render
        ctx.mark_dirty_id(ctx.root_element.id)
        render(ctx)

        collect_ids(ctx.root_element, node_ids_after)

        # Node IDs should be preserved
        assert node_ids_before == node_ids_after

    def test_deep_tree_with_state(self) -> None:
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

        ctx = RenderSession(Root)
        render(ctx)

        # One state per level (not including root)
        assert mount_count[0] == DEPTH

        # Re-render should not create new states
        ctx.mark_dirty_id(ctx.root_element.id)
        render(ctx)
        assert mount_count[0] == DEPTH  # Still same


class TestWideTrees:
    """Tests for wide component trees (many siblings)."""

    def test_50_siblings(self) -> None:
        """Tree with 50 siblings should render correctly."""
        WIDTH = 50

        @component
        def Child(n: int = 0) -> None:
            pass

        @component
        def Parent() -> None:
            for i in range(WIDTH):
                Child(n=i)

        ctx = RenderSession(Parent)
        render(ctx)

        assert len(ctx.root_element.child_ids) == WIDTH

    def test_wide_tree_rerender(self) -> None:
        """Re-rendering wide tree should preserve children."""
        WIDTH = 50

        @component
        def Child(n: int = 0) -> None:
            pass

        @component
        def Parent() -> None:
            for i in range(WIDTH):
                Child(n=i)

        ctx = RenderSession(Parent)
        render(ctx)

        original_ids = list(ctx.root_element.child_ids)

        ctx.mark_dirty_id(ctx.root_element.id)
        render(ctx)

        new_ids = list(ctx.root_element.child_ids)
        assert original_ids == new_ids

    def test_add_siblings(self) -> None:
        """Adding siblings should mount new elements."""
        count_ref = [3]

        @component
        def Child(n: int = 0) -> None:
            pass

        @component
        def Parent() -> None:
            for i in range(count_ref[0]):
                Child(n=i)

        ctx = RenderSession(Parent)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 3

        # Add more siblings
        count_ref[0] = 50
        ctx.mark_dirty_id(ctx.root_element.id)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 50

    def test_remove_siblings(self) -> None:
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

        ctx = RenderSession(Parent)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 50

        # Remove siblings
        count_ref[0] = 10
        ctx.mark_dirty_id(ctx.root_element.id)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 10
        # 40 elements should have been unmounted (indices 10-49)
        assert len(unmount_log) == 40
        assert all(n >= 10 for n in unmount_log)


class TestCombinedDeepAndWide:
    """Tests for trees that are both deep and wide."""

    def test_branching_tree(self) -> None:
        """Tree with branching factor at each level."""
        DEPTH = 5
        BRANCH_FACTOR = 3

        @component
        def Level(depth: int = 0) -> None:
            if depth < DEPTH:
                for i in range(BRANCH_FACTOR):
                    Level(depth=depth + 1)

        @component
        def Root() -> None:
            Level(depth=1)

        ctx = RenderSession(Root)
        render(ctx)

        # Count total nodes
        def count_nodes(node: ElementNode) -> int:
            return 1 + sum(count_nodes(ctx.elements.get(cid)) for cid in node.child_ids if ctx.elements.get(cid))

        total = count_nodes(ctx.root_element)

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

    def test_deep_tree_with_wide_leaf_level(self) -> None:
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

        ctx = RenderSession(Root)
        render(ctx)

        # Navigate to leaf level and check
        node = ctx.root_element
        for _ in range(DEPTH):
            node = ctx.elements.get(node.child_ids[0])

        assert len(node.child_ids) == LEAF_COUNT


class TestMountingOrder:
    """Tests for correct mounting order in deep/wide trees."""

    def test_deep_tree_mount_order(self) -> None:
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

        ctx = RenderSession(Root)
        render(ctx)

        # Should be in order 0, 1, 2, ..., DEPTH
        assert mount_order == list(range(DEPTH + 1))

    def test_wide_tree_unmount_order(self) -> None:
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

        ctx = RenderSession(Root)
        render(ctx)

        # Remove container
        show_ref[0] = False
        ctx.mark_dirty_id(ctx.root_element.id)
        render(ctx)

        # All children should have unmounted
        assert len(unmount_order) == 10


class TestTreeTraversal:
    """Tests for tree traversal edge cases."""

    def test_empty_tree(self) -> None:
        """Tree with no children should work."""
        @component
        def Empty() -> None:
            pass

        ctx = RenderSession(Empty)
        render(ctx)

        assert ctx.root_element is not None
        assert len(ctx.root_element.child_ids) == 0

    def test_single_child_chain(self) -> None:
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

        ctx = RenderSession(Root)
        render(ctx)

        # Traverse and verify single-child chain
        node = ctx.root_element
        count = 0
        while node.child_ids:
            assert len(node.child_ids) == 1
            node = ctx.elements.get(node.child_ids[0])
            count += 1

        # Should have traversed DEPTH levels (from Root's child to deepest)
        assert count == DEPTH

    def test_asymmetric_tree(self) -> None:
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
            ShallowBranch()       # Shallow right branch

        ctx = RenderSession(Root)
        render(ctx)

        # Root has 2 children
        assert len(ctx.root_element.child_ids) == 2

        # Count depth of deep branch
        def count_depth(node: ElementNode) -> int:
            if not node.child_ids:
                return 1
            return 1 + max(count_depth(ctx.elements.get(cid)) for cid in node.child_ids if ctx.elements.get(cid))

        deep_branch = ctx.elements.get(ctx.root_element.child_ids[0])
        shallow_branch = ctx.elements.get(ctx.root_element.child_ids[1])

        deep_depth = count_depth(deep_branch)
        shallow_depth = count_depth(shallow_branch)

        # Deep branch: DeepBranch(10) -> DeepBranch(9) -> ... -> DeepBranch(0) -> Leaf = 12 levels
        assert deep_depth == 12
        # Shallow branch: ShallowBranch -> Leaf = 2 levels
        assert shallow_depth == 2
        # Deep branch should be much deeper
        assert deep_depth > shallow_depth
