"""Build a dependency graph and print it in D2 format."""

import sys

from .config import parse_config
from .d2 import render
from .graph import Package, walk
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
    """Print D2 to stdout and errors to stderr."""
    config = parse_config(argv)
    try:
        root, source = prepare(config)
        graph = walk(root, config.max_depth, source.neighbors)
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    print(render(graph, root), end="")
    return 0
