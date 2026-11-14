"""Exercise NuGet metadata ingestion without a public network."""

from unittest import TestCase
from unittest.mock import patch

from src.depgraph.nuget import Dependency, NuGetRepository, RepositoryError

INDEX = "https://example.test/v3/index.json"
BASE = "https://example.test/packages"
MANIFEST = b"""<package xmlns="http://schemas.microsoft.com/nuspec.xsd">
<metadata><dependencies>
  <dependency id="Flat" version="[1.0]" />
  <group targetFramework="net8.0">
    <dependency id="Child" version="[2.0,3.0)" />
  </group>
  <group targetFramework="net9.0" />
</dependencies></metadata></package>"""


class NuGetTests(TestCase):
    """Validate request paths, manifest shape and source errors."""

    @patch("src.depgraph.nuget.fetch")
    def test_requested_version(self, fetch):
        """Discover the base URL and read exactly the requested version."""
        fetch.side_effect = [
            b'{"resources":[{"@type":"PackageBaseAddress/3.0.0",'
            b'"@id":"https://example.test/packages/"}]}',
            MANIFEST,
        ]
        repository = NuGetRepository(INDEX)
        expected = (
            Dependency("Flat", "[1.0]"),
            Dependency("Child", "[2.0,3.0)", "net8.0"),
        )
        self.assertEqual(expected, repository.declarations("Example", "01.2"))
        self.assertEqual(expected, repository.declarations("EXAMPLE", "1.2"))
        self.assertEqual(
            [INDEX, f"{BASE}/example/1.2.0/example.nuspec"],
            [call.args[0] for call in fetch.call_args_list],
        )

    @patch("src.depgraph.nuget.fetch", return_value=b'{"resources":[]}')
    def test_missing_base_address(self, _fetch):
        """Reject a service index without flat-container metadata."""
        with self.assertRaisesRegex(RepositoryError, "PackageBaseAddress"):
            NuGetRepository(INDEX)
