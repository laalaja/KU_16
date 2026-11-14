"""Check transposed DFS with cycles, isolated nodes and versions."""

from unittest import TestCase

from src.depgraph.graph import Package, reverse_dependencies


class ReverseTests(TestCase):
    """Exercise version-specific incoming edges and depth."""

    def test_cycle_depth_and_isolation(self):
        """Find incoming paths without listing the root via a cycle."""
        graph = {"A": ("C",), "C": ("A",), "E": ("A",), "F": ("E",), "G": ()}
        self.assertEqual((), reverse_dependencies(graph, "A", 0))
        self.assertEqual(("C", "E"), reverse_dependencies(graph, "A", 1))
        self.assertEqual(("C", "E", "F"), reverse_dependencies(graph, "A", 5))
        self.assertEqual((), reverse_dependencies(graph, "G", 5))

    def test_other_version_is_not_a_match(self):
        """Resolve reverse edges to the precise package version."""
        first = Package("A", "1.0.0")
        second = Package("A", "2.0.0")
        dependent = Package("B", "1.0.0")
        graph = {first: (), second: (), dependent: (second,)}
        self.assertEqual((), reverse_dependencies(graph, first, 3))
        self.assertEqual(
            (dependent,), reverse_dependencies(graph, second, 3),
        )
