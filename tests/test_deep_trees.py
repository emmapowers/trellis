"""Tests for deeply nested and wide component trees.

These tests verify that the framework correctly handles:
- Deep trees (50+ levels)
- Wide trees (50+ siblings)
- Combined deep and wide structures
- Correct depth tracking and parent/child relationships
"""

from dataclasses import dataclass

from trellis.core.rendering import RenderContext, Element
from trellis.core.functional_component import component
from trellis.core.state import Stateful


class TestDeepTrees:
    """Tests for deeply nested component trees."""

    def test_50_level_deep_tree(self) -> None:
        """Tree with 50 levels should render correctly."""
        DEPTH = 50
        depths_seen: list[int] = []

        def make_level(n: int):
            @component
            def Level() -> None:
                if n < DEPTH:
                    make_level(n + 1)()
            return Level

        @component
        def Root() -> None:
            make_level(1)()

        ctx = RenderContext(Root)
        ctx.render(from_element=None)

        # Verify tree structure
        def count_depth(element: Element) -> int:
            if not element.children:
                return element.depth
            return max(count_depth(c) for c in element.children)

        max_depth = count_depth(ctx.root_element)
        assert max_depth == DEPTH

    def test_depth_values_correct(self) -> None:
        """All elements should have correct depth values."""
        DEPTH = 50
        depth_errors: list[str] = []

        def make_level(n: int):
            @component
            def Level() -> None:
                if n < DEPTH:
                    make_level(n + 1)()
            return Level

        @component
        def Root() -> None:
            make_level(1)()

        ctx = RenderContext(Root)
        ctx.render(from_element=None)

        def verify_depths(element: Element, expected_depth: int) -> None:
            if element.depth != expected_depth:
                depth_errors.append(
                    f"Element at expected depth {expected_depth} has depth {element.depth}"
                )
            for child in element.children:
                verify_depths(child, expected_depth + 1)

        verify_depths(ctx.root_element, 0)
        assert len(depth_errors) == 0, f"Depth errors: {depth_errors}"

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

        ctx = RenderContext(Root)
        ctx.render(from_element=None)

        def verify_relationships(element: Element) -> None:
            for child in element.children:
                if child.parent is not element:
                    relationship_errors.append(
                        f"Child's parent is not the expected parent at depth {element.depth}"
                    )
                verify_relationships(child)

        verify_relationships(ctx.root_element)
        assert len(relationship_errors) == 0, f"Relationship errors: {relationship_errors}"

    def test_deep_tree_rerender_preserves_structure(self) -> None:
        """Re-rendering deep tree should preserve element identity."""
        DEPTH = 20
        element_ids_before: list[int] = []
        element_ids_after: list[int] = []

        @component
        def Level(n: int = 0) -> None:
            if n < DEPTH:
                Level(n=n + 1)

        @component
        def Root() -> None:
            Level(n=1)

        ctx = RenderContext(Root)
        ctx.render(from_element=None)

        def collect_ids(element: Element, ids: list[int]) -> None:
            ids.append(id(element))
            for child in element.children:
                collect_ids(child, ids)

        collect_ids(ctx.root_element, element_ids_before)

        # Re-render
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        collect_ids(ctx.root_element, element_ids_after)

        # Element identities should be preserved
        assert element_ids_before == element_ids_after

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
            state = LevelState()
            state.level = n
            if n < DEPTH:
                Level(n=n + 1)

        @component
        def Root() -> None:
            Level(n=1)

        ctx = RenderContext(Root)
        ctx.render(from_element=None)

        # One state per level (not including root)
        assert mount_count[0] == DEPTH

        # Re-render should not create new states
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()
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

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert len(ctx.root_element.children) == WIDTH

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

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        original_ids = [id(c) for c in ctx.root_element.children]

        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        new_ids = [id(c) for c in ctx.root_element.children]
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

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert len(ctx.root_element.children) == 3

        # Add more siblings
        count_ref[0] = 50
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert len(ctx.root_element.children) == 50

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
            state = TrackedState()
            state.n = n

        @component
        def Parent() -> None:
            for i in range(count_ref[0]):
                Child(key=str(i), n=i)

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert len(ctx.root_element.children) == 50

        # Remove siblings
        count_ref[0] = 10
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert len(ctx.root_element.children) == 10
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

        ctx = RenderContext(Root)
        ctx.render(from_element=None)

        # Count total elements
        def count_elements(element: Element) -> int:
            return 1 + sum(count_elements(c) for c in element.children)

        total = count_elements(ctx.root_element)

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

        ctx = RenderContext(Root)
        ctx.render(from_element=None)

        # Navigate to leaf level and check
        element = ctx.root_element
        for _ in range(DEPTH):
            element = element.children[0]

        assert len(element.children) == LEAF_COUNT


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
                state = TrackedState()
                state.level = n
                if n < DEPTH:
                    make_level(n + 1)()
            return Level

        @component
        def Root() -> None:
            state = TrackedState()
            state.level = 0
            make_level(1)()

        ctx = RenderContext(Root)
        ctx.render(from_element=None)

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
            state = TrackedState()
            state.n = n

        @component
        def Container() -> None:
            for i in range(10):
                Child(n=i)

        @component
        def Root() -> None:
            if show_ref[0]:
                Container()

        ctx = RenderContext(Root)
        ctx.render(from_element=None)

        # Remove container
        show_ref[0] = False
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # All children should have unmounted
        assert len(unmount_order) == 10


class TestTreeTraversal:
    """Tests for tree traversal edge cases."""

    def test_empty_tree(self) -> None:
        """Tree with no children should work."""
        @component
        def Empty() -> None:
            pass

        ctx = RenderContext(Empty)
        ctx.render(from_element=None)

        assert ctx.root_element is not None
        assert len(ctx.root_element.children) == 0

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

        ctx = RenderContext(Root)
        ctx.render(from_element=None)

        # Traverse and verify single-child chain
        element = ctx.root_element
        for expected_depth in range(DEPTH):
            assert element.depth == expected_depth
            if expected_depth < DEPTH:
                assert len(element.children) == 1
                element = element.children[0]

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

        ctx = RenderContext(Root)
        ctx.render(from_element=None)

        # Root has 2 children
        assert len(ctx.root_element.children) == 2

        # Verify deep branch depth
        deep_branch = ctx.root_element.children[0]
        element = deep_branch
        max_deep_depth = 0
        while element.children:
            element = element.children[0]
            max_deep_depth = max(max_deep_depth, element.depth)

        # Verify shallow branch depth
        shallow_branch = ctx.root_element.children[1]
        assert len(shallow_branch.children) == 1
        assert shallow_branch.children[0].depth == 2  # Root -> ShallowBranch -> Leaf

        # Deep branch should be much deeper
        assert max_deep_depth > 5
