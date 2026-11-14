"""Exercise the final command with a cyclic local repository."""

from pathlib import Path
import subprocess
import sys
from unittest import TestCase

PROJECT = Path(__file__).resolve().parents[1]


def command(depth):
    """Run the actual script with a depth and a relative fixture path."""
    return subprocess.run(
        [sys.executable, "src", "--test-mode", "--repository",
         "examples/repository.json", "--package", "A", "--version", "1",
         "--max-depth", str(depth)],
        cwd=PROJECT, capture_output=True, encoding="utf-8", check=True,
    )


class D2Tests(TestCase):
    """Check graph shape and that CLI stdout is valid diagram input."""

    def test_depth_two_includes_back_edge(self):
        """Preserve the cycle and transitive dependency in the D2 text."""
        result = command(2)
        self.assertEqual("", result.stderr)
        self.assertIn('n0: "A@1.0.0"', result.stdout)
        self.assertEqual(
            {"n0 -> n1", "n0 -> n2", "n1 -> n3", "n2 -> n0"},
            {line for line in result.stdout.splitlines() if " -> " in line},
        )

    def test_depth_zero_draws_only_root(self):
        """A root without edges is still rendered."""
        lines = command(0).stdout.splitlines()
        self.assertNotIn('n1: "B@1.0.0"', lines)
        self.assertIn('n0: "A@1.0.0"', lines)
        self.assertFalse(any(" -> " in line for line in lines))
