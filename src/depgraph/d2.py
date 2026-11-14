"""Serialize a directed package graph in D2 syntax."""

import json

ROOT_FILL = "#E0EEFF"


def render(graph, root):
    """Emit stable IDs, one node per version and all DFS edges."""
    nodes = [root, *sorted(node for node in graph if node != root)]
    identifiers = {node: f"n{index}" for index, node in enumerate(nodes)}
    lines = ["direction: right", ""]
    for node in nodes:
        label = json.dumps(str(node))
        identifier = identifiers[node]
        lines.append(f"{identifier}: {label}")
    lines.extend([f'n0.style.fill: "{ROOT_FILL}"', ""])
    for node in nodes:
        for child in sorted(graph[node]):
            lines.append(f"{identifiers[node]} -> {identifiers[child]}")
    return "\n".join(lines).rstrip() + "\n"
