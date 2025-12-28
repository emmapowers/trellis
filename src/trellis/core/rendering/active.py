"""Render-scoped state container.

ActiveRender holds state that exists only during a render pass.
Created at start of render(), discarded at end.
"""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass, field

from trellis.core.rendering.elements import ElementStore
from trellis.core.rendering.frames import FrameStack
from trellis.core.rendering.lifecycle import LifecycleTracker
from trellis.core.rendering.patches import PatchCollector

__all__ = ["ActiveRender"]


@dataclass
class ActiveRender:
    """Render-scoped state container.

    Created at the start of each render() call and discarded at the end.
    Holds state that is only relevant during the render pass.

    Attributes:
        frames: Stack of Frames for collecting child element IDs
        patches: Collector for patches generated during this render
        lifecycle: Tracker for pending mount/unmount hooks
        old_elements: Snapshot of elements from before render (for diffing)
        current_node_id: ID of the element currently being executed
        last_property_access: Last Stateful property access (for mutable/callback capture)
    """

    frames: FrameStack = field(default_factory=FrameStack)
    patches: PatchCollector = field(default_factory=PatchCollector)
    lifecycle: LifecycleTracker = field(default_factory=LifecycleTracker)
    old_elements: ElementStore = field(default_factory=ElementStore)

    # Execution context
    current_node_id: str | None = None
    last_property_access: tuple[tp.Any, str, tp.Any] | None = None
