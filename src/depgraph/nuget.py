"""Read NuGet v3 service indexes, versions and .nuspec manifests."""

from dataclasses import dataclass
import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from xml.etree import ElementTree

from .config import PACKAGE_ID, validate_url
from .version import normalize

TIMEOUT = 15
BYTE_LIMIT = 8 * 1024 * 1024
BASE_ADDRESS = "PackageBaseAddress/3.0.0"


class RepositoryError(ValueError):
    """Describe a missing or invalid repository resource."""


@dataclass(frozen=True)
class Dependency:
    """Record a dependency declaration and its framework group."""

    package: str
    requirement: str
    framework: str = ""


def fetch(url):
    """Read a public HTTP resource with time and size limits."""
    try:
        with urlopen(url, timeout=TIMEOUT) as response:
            data = response.read(BYTE_LIMIT + 1)
    except HTTPError as error:
        raise RepositoryError(f"HTTP {error.code}: {url}") from error
    except (URLError, OSError) as error:
        raise RepositoryError(f"не удалось прочитать {url}: {error}") from error
    if len(data) > BYTE_LIMIT:
        raise RepositoryError(f"слишком большой ответ: {url}")
    return data


def read_json(url):
    """Decode a NuGet JSON response."""
    try:
        return json.loads(fetch(url))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise RepositoryError(f"некорректный JSON: {url}") from error


def discover_base(url):
    """Resolve the NuGet PackageBaseAddress from its service index."""
    try:
        resources = read_json(url)["resources"]
        for resource in resources:
            if resource.get("@type") == BASE_ADDRESS:
                return validate_url(resource["@id"]).rstrip("/")
    except (AttributeError, KeyError, TypeError) as error:
        raise RepositoryError(f"некорректный индекс NuGet: {url}") from error
    raise RepositoryError(f"в индексе нет {BASE_ADDRESS}: {url}")


def read_declaration(element, framework=""):
    """Convert a dependency element to a typed declaration."""
    package = element.get("id") or ""
    if not PACKAGE_ID.fullmatch(package):
        raise RepositoryError(f"некорректное имя зависимости: {package!r}")
    return Dependency(package, element.get("version", ""), framework)


def parse_manifest(data):
    """Return flat and framework-specific dependencies from a .nuspec."""
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as error:
        raise RepositoryError("некорректный XML манифеста .nuspec") from error
    metadata = root.find("{*}metadata")
    if metadata is None or root.tag.rsplit("}", 1)[-1] != "package":
        raise RepositoryError("манифест .nuspec не содержит package/metadata")
    dependencies = metadata.find("{*}dependencies")
    if dependencies is None:
        return ()
    result = [read_declaration(item) for item in dependencies.findall(
        "{*}dependency"
    )]
    for group in dependencies.findall("{*}group"):
        framework = group.get("targetFramework", "")
        result.extend(
            read_declaration(item, framework)
            for item in group.findall("{*}dependency")
        )
    return tuple(result)


class NuGetRepository:
    """Access and cache metadata for a single NuGet source."""

    def __init__(self, url):
        """Discover flat-container endpoints for the given index."""
        self.base = discover_base(url)
        self.manifests = {}

    def declarations(self, package, version):
        """Find dependency declarations for the requested exact version."""
        name, version = package.lower(), normalize(version)
        key = name, version
        if key not in self.manifests:
            url = f"{self.base}/{name}/{version}/{name}.nuspec"
            try:
                self.manifests[key] = parse_manifest(fetch(url))
            except RepositoryError as error:
                raise RepositoryError(f"{name}@{version}: {error}") from error
        return self.manifests[key]
