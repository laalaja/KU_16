"""Construct a depth-limited graph using iterative DFS."""

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Package:
    """Identify a node by package name and normalized version."""

    name: str
    version: str

    def __str__(self):
        """Show the exact package identity."""
        return f"{self.name}@{self.version}"


def walk(root, max_depth, neighbors):
    """Return adjacency lists for the graph reachable within max_depth."""
    graph = {}
    best_depth = {}
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if node in best_depth and best_depth[node] <= depth:
            continue
        best_depth[node] = depth
        graph.setdefault(node, ())
        if depth == max_depth:
            continue
        children = graph[node] or tuple(dict.fromkeys(neighbors(node)))
        graph[node] = children
        stack.extend((child, depth + 1) for child in reversed(children))
    return graph


def format_graph(graph):
    """Show roots, leaves and edges without hiding cycles."""
    for node, children in graph.items():
        if children:
            for child in children:
                yield f"{node} -> {child}"
        else:
            yield str(node)
