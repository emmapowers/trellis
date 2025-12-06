

from dataclasses import dataclass
from typing import NewType

NodeId = NewType[int]

class Component:
    pass

@dataclass
class Node:
    id: NodeId
    type: type[Component]
    parent: "Node" | None
    children: set["Node"]

    properties: set[str]
    events: set[str]

@dataclass
class ComponentTree:
    root: Node
    _nodes: dict[NodeId, Node]

    def getNode(nodeId: NodeId) -> Node:
        """Returns a node from the tree"""
        pass

    def replaceNode(nodeId: NodeId, node: Node) -> Node:
        """Replaces a node and it's children, return the old node"""
        pass
