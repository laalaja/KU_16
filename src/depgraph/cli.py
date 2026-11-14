"""Build a graph from CLI options and report user-facing errors."""

import sys

from .config import parse_config
from .graph import Package, format_graph, walk
from .local import TestRepository
from .nuget import NuGetRepository
from .version import normalize


def prepare(config):
    """Create the selected source and validate the requested root."""
    version = normalize(config.version)
    if config.test_mode:
        root = Package(config.package, version)
        source = TestRepository(config.repository)
    else:
        root = Package(config.package.lower(), version)
        source = NuGetRepository(config.repository, "-" in version)
    source.require(root)
    return root, source


def main(argv=None):
    """Print the depth-limited dependency graph as an adjacency list."""
    config = parse_config(argv)
    try:
        root, source = prepare(config)
        graph = walk(root, config.max_depth, source.neighbors)
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    for line in format_graph(graph):
        print(line)
    return 0
