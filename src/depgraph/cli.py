"""Build a graph from CLI options and report user-facing errors."""

import sys

from .config import parse_config
from .graph import Package, format_graph, reverse_dependencies, walk
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
    """Print the forward graph or the list of reverse dependencies."""
    config = parse_config(argv)
    try:
        root, source = prepare(config)
        if config.reverse:
            dependents = reverse_dependencies(
                source.graph, root, config.max_depth,
            )
            for node in dependents:
                print(node)
            if not dependents:
                print("Обратных зависимостей нет.")
        else:
            graph = walk(root, config.max_depth, source.neighbors)
            for line in format_graph(graph):
                print(line)
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0
