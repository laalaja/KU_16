"""Check NuGet range and version ordering behavior."""

from unittest import TestCase

from src.depgraph.requirements import select_version
from src.depgraph.version import normalize, version_key


class VersionTests(TestCase):
    """Verify normalized versions, prerelease and interval endpoints."""

    def test_normalize_and_sort(self):
        """Use numeric components and numeric prerelease identifiers."""
        self.assertEqual("1.2.0-beta", normalize("01.02.0.0-Beta+meta"))
        versions = ["1.0.1", "1.0.0-rc.11", "1.0.0", "1.0.0-rc.2"]
        self.assertEqual(
            ["1.0.0-rc.2", "1.0.0-rc.11", "1.0.0", "1.0.1"],
            sorted(versions, key=version_key),
        )

    def test_ranges(self):
        """Select the lowest applicable exact, open or closed version."""
        versions = ["3.0.0", "1.5.0", "1.0.0", "2.0.0"]
        for spec, expected in {
            "[2]": "2.0.0",
            "1.1": "1.5.0",
            "(1,2]": "1.5.0",
            "(,1.5)": "1.0.0",
            "(2,)": "3.0.0",
            "(2,3)": None,
            "[1,2)": "1.0.0",
        }.items():
            with self.subTest(spec=spec):
                self.assertEqual(expected, select_version(versions, spec))

    def test_prerelease(self):
        """Use prereleases when activated by a bound or the root."""
        versions = ["1.0.0", "1.0.0-beta.2", "1.0.0-beta.1"]
        self.assertEqual("1.0.0", select_version(versions, ""))
        self.assertEqual("1.0.0-beta.1", select_version(versions, "1.0-beta.1"))
        self.assertEqual("1.0.0-beta.1", select_version(versions, "", True))
