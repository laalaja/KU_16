"""Read a versioned graph from a local JSON fixture."""

import json
from pathlib import Path

from .config import TEST_ID
from .graph import Package
from .nuget import RepositoryError
from .version import normalize


def package(name, version):
    """Validate a test package identity."""
    if not TEST_ID.fullmatch(name) or not isinstance(version, str):
        raise RepositoryError("используйте имя A–Z и строку версии в JSON")
    return Package(name, normalize(version))


def mapping(value):
    """Reject non-object values in the test repository."""
    if not isinstance(value, dict):
        raise RepositoryError("ожидается объект JSON")
    return value.items()


def unique_object(pairs):
    """Reject duplicate keys before decoding a JSON object."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise RepositoryError(f"повторный ключ JSON: {key}")
        result[key] = value
    return result


def load_graph(path):
    """Load all vertices and reject edges to absent versions."""
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      object_pairs_hook=unique_object)
    graph = {}
    for name, versions in mapping(data):
        for version, dependencies in mapping(versions):
            node = package(name, version)
            if node in graph:
                raise RepositoryError(f"повторная версия: {node}")
            graph[node] = tuple(
                package(child, required)
                for child, required in mapping(dependencies)
            )
    for children in graph.values():
        for child in children:
            if child not in graph:
                raise RepositoryError(f"не описан узел {child}")
    return graph


class TestRepository:
    """Expose the adjacency list of a file without any network I/O."""

    def __init__(self, path):
        """Load and validate all declared versions."""
        self.graph = load_graph(path)

    def require(self, root):
        """Ensure the package and its exact version are defined."""
        if root not in self.graph:
            raise RepositoryError(f"не найден пакет {root} в тестовом файле")

    def neighbors(self, node):
        """Return the dependencies already specified in the JSON file."""
        return self.graph[node]
