"""Render-scoped state container.

ActiveRender holds state that exists only during a render pass.
Created at start of render(), discarded at end.
"""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass, field

from trellis.core.frame_stack import FrameStack
from trellis.core.lifecycle_tracker import LifecycleTracker
from trellis.core.node_store import NodeStore
from trellis.core.patch_collector import PatchCollector

__all__ = ["ActiveRender"]


@dataclass
class ActiveRender:
    """Render-scoped state container.

    Created at the start of each render() call and discarded at the end.
    Holds state that is only relevant during the render pass.

    Attributes:
        frames: Stack of Frames for collecting child node IDs
        patches: Collector for patches generated during this render
        lifecycle: Tracker for pending mount/unmount hooks
        old_nodes: Snapshot of nodes from before render (for diffing)
        current_node_id: ID of the node currently being executed
        last_property_access: Last Stateful property access (for mutable/callback capture)
    """

    frames: FrameStack = field(default_factory=FrameStack)
    patches: PatchCollector = field(default_factory=PatchCollector)
    lifecycle: LifecycleTracker = field(default_factory=LifecycleTracker)
    old_nodes: NodeStore = field(default_factory=NodeStore)

    # Execution context
    current_node_id: str | None = None
    last_property_access: tuple[tp.Any, str, tp.Any] | None = None
