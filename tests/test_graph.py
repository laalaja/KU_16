"""Verify DFS, depth limits, cycles, and local repository input."""

from pathlib import Path
import tempfile
from unittest import TestCase

from src.depgraph.graph import Package, walk
from src.depgraph.local import TestRepository
from src.depgraph.nuget import RepositoryError

FIXTURE = Path(__file__).resolve().parents[1] / "examples/repository.json"


class GraphTests(TestCase):
    """Check visible nodes and depth-limited edges."""

    def test_shorter_path_after_first_visit(self):
        """Reopen a node reached first at a larger depth by DFS."""
        source = {"A": ("B", "C"), "B": ("C",), "C": ("D",), "D": ()}
        graph = walk("A", 2, source.__getitem__)
        self.assertEqual(("D",), graph["C"])
        self.assertEqual((), graph["D"])

    def test_cycle_and_depth(self):
        """Keep a back edge only when the source can be expanded."""
        repository = TestRepository(FIXTURE)
        root = Package("A", "1.0.0")
        b = Package("B", "1.0.0")
        c = Package("C", "1.0.0")
        d = Package("D", "1.0.0")
        search = repository.neighbors
        self.assertEqual({root: ()}, walk(root, 0, search))
        self.assertEqual({root: (b, c), b: (), c: ()}, walk(root, 1, search))
        self.assertEqual({root: (b, c), b: (d,), d: (), c: (root,)},
                         walk(root, 2, search))

    def test_self_loop(self):
        """Return a self-loop without visiting the vertex indefinitely."""
        self.assertEqual({"A": ("A",)}, walk("A", 500, lambda _: ("A",)))

    def test_no_python_recursion_limit(self):
        """Process a chain longer than Python's normal recursion limit."""
        length = 1500
        graph = walk(0, length, lambda node: (node + 1,))
        self.assertEqual(length + 1, len(graph))
        self.assertEqual((), graph[length])

    def test_dangling_edge(self):
        """Reject a fixture that references a missing package version."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "repo.json")
            path.write_text('{"A":{"1.0":{"B":"1.0"}}}', encoding="utf-8")
            with self.assertRaisesRegex(RepositoryError, "B@1.0.0"):
                TestRepository(path)
