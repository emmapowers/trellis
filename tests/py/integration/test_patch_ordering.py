"""Tests for patch ordering during incremental renders.

When a new subtree is added during re-render, AddPatches must be emitted
in parent-before-child order. The frontend needs parent nodes to exist
before children can be added to them.
"""

from tests.conftest import PatchCapture
from trellis.core.components.composition import component
from trellis.core.rendering.patches import RenderAddPatch, RenderRemovePatch, RenderUpdatePatch


class TestPatchOrdering:
    """Tests for correct ordering of AddPatches during incremental renders."""

    def test_add_patches_emitted_parent_before_children(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """When a subtree is added, parent AddPatch must come before child AddPatch.

        The frontend processes patches in order. If a child AddPatch arrives
        before its parent AddPatch, the frontend cannot add the child because
        the parent doesn't exist yet.
        """
        # Control whether we show the subtree
        show_subtree = [False]

        @component
        def Grandchild() -> None:
            pass

        @component
        def Child() -> None:
            Grandchild()

        @component
        def Root() -> None:
            if show_subtree[0]:
                Child()

        capture = capture_patches(Root)

        # Initial render - no children
        initial_patches = capture.render()
        assert len(initial_patches) == 1
        assert isinstance(initial_patches[0], RenderAddPatch)
        assert len(capture.session.root_element.child_ids) == 0

        # Toggle to show subtree
        show_subtree[0] = True
        capture.session.dirty.mark(capture.session.root_element.id)

        # Incremental render - should add Child and Grandchild
        patches = capture.render()

        # Should have at least one AddPatch for the new Child
        add_patches = [p for p in patches if isinstance(p, RenderAddPatch)]
        assert len(add_patches) >= 1, f"Expected at least 1 AddPatch, got {len(add_patches)}"

        # Extract node IDs from AddPatches in order
        add_patch_node_ids = [p.node.id for p in add_patches]

        # Find Child and Grandchild IDs
        child_id = capture.session.root_element.child_ids[0]
        child_node = capture.session.elements.get(child_id)
        grandchild_id = child_node.child_ids[0] if child_node.child_ids else None

        # If both Child and Grandchild have separate AddPatches,
        # Child's AddPatch must come BEFORE Grandchild's AddPatch
        if child_id in add_patch_node_ids and grandchild_id in add_patch_node_ids:
            child_index = add_patch_node_ids.index(child_id)
            grandchild_index = add_patch_node_ids.index(grandchild_id)
            assert child_index < grandchild_index, (
                f"Parent AddPatch must come before child AddPatch. "
                f"Got Child at index {child_index}, Grandchild at index {grandchild_index}"
            )

    def test_new_subtree_emits_single_add_patch(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """When a subtree is added, only the root of the subtree gets an AddPatch.

        AddPatch serialization is recursive - it includes the node and all its
        descendants. Therefore, descendants of a newly added node should NOT
        get their own separate AddPatch. Otherwise, they would be added twice:
        once as part of the parent's serialized subtree, and once via their own
        AddPatch.
        """
        # Control whether we show the subtree
        show_subtree = [False]

        @component
        def Grandchild() -> None:
            pass

        @component
        def Child() -> None:
            Grandchild()

        @component
        def Root() -> None:
            if show_subtree[0]:
                Child()

        capture = capture_patches(Root)

        # Initial render - no children
        capture.render()
        assert len(capture.session.root_element.child_ids) == 0

        # Toggle to show subtree
        show_subtree[0] = True
        capture.session.dirty.mark(capture.session.root_element.id)

        # Incremental render - should add Child (with Grandchild nested inside)
        patches = capture.render()

        # Collect all AddPatches
        add_patches = [p for p in patches if isinstance(p, RenderAddPatch)]

        # Get the IDs of nodes that received AddPatches
        add_patch_node_ids = {p.node.id for p in add_patches}

        # Find Child and Grandchild IDs
        child_id = capture.session.root_element.child_ids[0]
        child_node = capture.session.elements.get(child_id)
        grandchild_id = child_node.child_ids[0]

        # Child should have an AddPatch (it's a new subtree root)
        assert child_id in add_patch_node_ids, "Child should have an AddPatch"

        # Grandchild should NOT have its own AddPatch (it's included in Child's)
        assert grandchild_id not in add_patch_node_ids, (
            f"Grandchild should not have its own AddPatch. "
            f"It's already included in Child's AddPatch via recursive serialization. "
            f"Got AddPatches for: {add_patch_node_ids}"
        )

    def test_new_subtree_emits_single_complete_add_patch(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """A new subtree should emit exactly one AddPatch containing the full tree.

        When a new subtree is added:
        1. Only one AddPatch should be emitted (for the subtree root)
        2. That patch must contain the fully populated subtree (all descendants)

        This requires executing the subtree BEFORE emitting the patch, so that
        child_ids are populated for recursive serialization.
        """
        show_subtree = [False]

        @component
        def Grandchild() -> None:
            pass

        @component
        def Child() -> None:
            Grandchild()

        @component
        def Root() -> None:
            if show_subtree[0]:
                Child()

        capture = capture_patches(Root)
        capture.render()

        # Toggle to show subtree
        show_subtree[0] = True
        capture.session.dirty.mark(capture.session.root_element.id)
        patches = capture.render()

        # Should have exactly one AddPatch (for Child, the subtree root)
        add_patches = [p for p in patches if isinstance(p, RenderAddPatch)]
        assert len(add_patches) == 1, (
            f"Expected exactly 1 AddPatch for the new subtree, got {len(add_patches)}. "
            f"Patches for: {[p.node.id for p in add_patches]}"
        )

        # The single AddPatch must have child_ids populated (contains Grandchild)
        child_add_patch = add_patches[0]
        child_id = capture.session.root_element.child_ids[0]
        assert child_add_patch.node.id == child_id, "AddPatch should be for Child"

        assert len(child_add_patch.node.child_ids) > 0, (
            "AddPatch's node.child_ids is empty - subtree not fully populated. "
            "This happens when AddPatch is emitted BEFORE executing the subtree."
        )

        # Verify Grandchild is in Child's child_ids
        grandchild_id = capture.session.elements.get(child_id).child_ids[0]
        assert grandchild_id in child_add_patch.node.child_ids, (
            f"Child's AddPatch should include Grandchild. "
            f"Expected {grandchild_id} in {child_add_patch.node.child_ids}"
        )


class TestInitialRenderInvariants:
    """Tests for initial render behavior.

    Initial render MUST emit exactly one AddPatch containing the entire tree.
    This is a core invariant - the frontend expects to receive the full tree
    in a single patch on first render.
    """

    def test_initial_render_emits_single_add_patch(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Initial render returns exactly one AddPatch, regardless of tree depth."""

        @component
        def Leaf() -> None:
            pass

        @component
        def Branch() -> None:
            Leaf()
            Leaf()

        @component
        def Root() -> None:
            Branch()
            Branch()

        capture = capture_patches(Root)
        patches = capture.render()

        # Must be exactly one patch
        assert len(patches) == 1, (
            f"Initial render must emit exactly 1 patch, got {len(patches)}: "
            f"{[type(p).__name__ for p in patches]}"
        )

        # Must be an AddPatch
        assert isinstance(
            patches[0], RenderAddPatch
        ), f"Initial render patch must be RenderAddPatch, got {type(patches[0]).__name__}"

    def test_initial_render_add_patch_contains_full_tree(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """The single AddPatch must contain the entire tree structure."""

        @component
        def GrandChild() -> None:
            pass

        @component
        def Child() -> None:
            GrandChild()

        @component
        def Root() -> None:
            Child()

        capture = capture_patches(Root)
        patches = capture.render()

        add_patch = patches[0]
        assert isinstance(add_patch, RenderAddPatch)

        # Root node should have child_ids populated
        root_node = add_patch.node
        assert len(root_node.child_ids) == 1, "Root should have Child in child_ids"

        # Child should have GrandChild in child_ids
        child_id = root_node.child_ids[0]
        child_node = capture.session.elements.get(child_id)
        assert child_node is not None
        assert len(child_node.child_ids) == 1, "Child should have GrandChild in child_ids"

    def test_initial_render_add_patch_has_no_parent(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Initial render AddPatch has parent_id=None (it's the root)."""

        @component
        def Root() -> None:
            pass

        capture = capture_patches(Root)
        patches = capture.render()

        add_patch = patches[0]
        assert isinstance(add_patch, RenderAddPatch)
        assert add_patch.parent_id is None, "Root AddPatch should have parent_id=None"


class TestIncrementalAddInvariants:
    """Tests for adding subtrees to an existing tree.

    When a new subtree is added during incremental render:
    1. Parent gets an UpdatePatch (child_ids changed)
    2. New subtree root gets exactly one AddPatch (containing all descendants)
    3. Descendants do NOT get their own AddPatch
    """

    def test_adding_subtree_emits_update_and_add_patches(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Adding a subtree emits UpdatePatch for parent and AddPatch for subtree root."""
        show_child = [False]

        @component
        def Child() -> None:
            pass

        @component
        def Root() -> None:
            if show_child[0]:
                Child()

        capture = capture_patches(Root)
        capture.render()  # Initial render

        # Toggle to show child
        show_child[0] = True
        capture.session.dirty.mark(capture.session.root_element.id)
        patches = capture.render()

        # Categorize patches by type
        update_patches = [p for p in patches if isinstance(p, RenderUpdatePatch)]
        add_patches = [p for p in patches if isinstance(p, RenderAddPatch)]
        remove_patches = [p for p in patches if isinstance(p, RenderRemovePatch)]

        # Should have exactly: 1 UpdatePatch (Root) + 1 AddPatch (Child)
        assert len(remove_patches) == 0, f"No removes expected, got {len(remove_patches)}"
        assert (
            len(update_patches) == 1
        ), f"Expected 1 UpdatePatch for parent, got {len(update_patches)}"
        assert len(add_patches) == 1, f"Expected 1 AddPatch for new subtree, got {len(add_patches)}"

        # UpdatePatch should be for Root (its child_ids changed)
        assert update_patches[0].node_id == capture.session.root_element.id
        assert update_patches[0].children is not None, "UpdatePatch should include new children"

        # AddPatch should be for Child
        child_id = capture.session.root_element.child_ids[0]
        assert add_patches[0].node.id == child_id

    def test_adding_deep_subtree_emits_single_add_patch(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Adding a deep subtree emits only one AddPatch for the subtree root."""
        show_subtree = [False]

        @component
        def Level3() -> None:
            pass

        @component
        def Level2() -> None:
            Level3()

        @component
        def Level1() -> None:
            Level2()

        @component
        def Root() -> None:
            if show_subtree[0]:
                Level1()

        capture = capture_patches(Root)
        capture.render()

        show_subtree[0] = True
        capture.session.dirty.mark(capture.session.root_element.id)
        patches = capture.render()

        add_patches = [p for p in patches if isinstance(p, RenderAddPatch)]

        # Only Level1 should get an AddPatch - Level2 and Level3 are included
        # in Level1's patch via recursive serialization
        assert len(add_patches) == 1, (
            f"Expected exactly 1 AddPatch for subtree root, got {len(add_patches)}. "
            f"Descendants should be included via recursive serialization, not separate patches."
        )

    def test_adding_multiple_siblings_emits_add_patch_per_sibling(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Adding multiple siblings at once emits one AddPatch per sibling."""
        show_children = [False]

        @component
        def ChildA() -> None:
            pass

        @component
        def ChildB() -> None:
            pass

        @component
        def Root() -> None:
            if show_children[0]:
                ChildA()
                ChildB()

        capture = capture_patches(Root)
        capture.render()

        show_children[0] = True
        capture.session.dirty.mark(capture.session.root_element.id)
        patches = capture.render()

        add_patches = [p for p in patches if isinstance(p, RenderAddPatch)]
        update_patches = [p for p in patches if isinstance(p, RenderUpdatePatch)]

        # 1 UpdatePatch for Root + 2 AddPatches for ChildA and ChildB
        assert len(update_patches) == 1
        assert (
            len(add_patches) == 2
        ), f"Expected 2 AddPatches (one per sibling), got {len(add_patches)}"
