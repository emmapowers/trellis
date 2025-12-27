"""Frame stack for collecting child nodes during rendering.

FrameStack manages the stack of Frames used during component execution
to collect child node IDs in `with` blocks.
"""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass, field

if tp.TYPE_CHECKING:
    from trellis.core.component import Component

__all__ = ["Frame", "FrameStack"]


def _escape_key(key: str) -> str:
    """URL-encode special characters in user-provided keys.

    Keys may contain characters that have special meaning in position IDs:
    - ':' separates keyed prefix from key value
    - '@' separates position from component ID
    - '/' separates path segments

    These are URL-encoded to avoid ambiguity.

    Args:
        key: The user-provided key string

    Returns:
        The key with special characters URL-encoded
    """
    return key.replace("%", "%25").replace(":", "%3A").replace("@", "%40").replace("/", "%2F")


@dataclass
class Frame:
    """Scope that collects child node IDs during rendering.

    Used during component execution to collect children created in `with` blocks.
    Each `with` block pushes a new Frame onto the stack, and children created
    within have their IDs added to that frame.

    Attributes:
        child_ids: IDs of child nodes collected in this frame
        parent_id: ID of the parent node (for computing child position IDs)
        position: Counter for the next child's position index
    """

    child_ids: list[str] = field(default_factory=list)
    parent_id: str = ""
    position: int = 0


class FrameStack:
    """Stack of Frames for collecting child nodes during rendering.

    Each `with` block on a container component pushes a new Frame.
    Child nodes created within that scope are added to the current Frame.
    When the `with` block exits, the Frame is popped and its child IDs
    are assigned to the container.
    """

    __slots__ = ("_frames",)

    def __init__(self) -> None:
        self._frames: list[Frame] = []

    def push(self, parent_id: str) -> Frame:
        """Push a new frame for collecting child nodes.

        Called when entering a `with` block on a container component.

        Args:
            parent_id: ID of the parent node (for computing child position IDs)

        Returns:
            The new Frame
        """
        frame = Frame(parent_id=parent_id)
        self._frames.append(frame)
        return frame

    def pop(self) -> list[str]:
        """Pop the current frame and return collected child IDs.

        Called when exiting a `with` block.

        Returns:
            List of child node IDs collected in the frame
        """
        frame = self._frames.pop()
        return frame.child_ids

    def current(self) -> Frame | None:
        """Get the current frame if one exists.

        Returns:
            The current Frame, or None if not in a `with` block
        """
        return self._frames[-1] if self._frames else None

    def add_child(self, node_id: str) -> None:
        """Add a child node ID to the current frame.

        Args:
            node_id: The child node's ID
        """
        if self._frames:
            self._frames[-1].child_ids.append(node_id)

    def has_active(self) -> bool:
        """Check if there's an active frame.

        Returns:
            True if inside a `with` block, False otherwise
        """
        return bool(self._frames)

    def next_child_id(self, component: Component, key: str | None) -> str:
        """Get the next position-based ID for a child node.

        Position IDs encode tree position AND component identity:
        - First child: "{parent_id}/0@{id(component)}"
        - Keyed child: "{parent_id}/:key@{id(component)}"

        Args:
            component: The component being placed (for identity in ID)
            key: Optional user-provided key (replaces position index)

        Returns:
            Position-based ID string with component identity
        """
        if not self._frames:
            raise RuntimeError("next_child_id called with no active frame")

        frame = self._frames[-1]
        parent_id = frame.parent_id
        position = frame.position
        frame.position += 1

        comp_id = id(component)
        escaped_key = _escape_key(key) if key else None

        if escaped_key:
            return f"{parent_id}/:{escaped_key}@{comp_id}"
        return f"{parent_id}/{position}@{comp_id}"

    def root_id(self, component: Component) -> str:
        """Get the root node ID (for no-frame case).

        Args:
            component: The root component

        Returns:
            Root position ID: "/@{id(component)}"
        """
        return f"/@{id(component)}"

    def __len__(self) -> int:
        """Return number of frames on the stack."""
        return len(self._frames)
