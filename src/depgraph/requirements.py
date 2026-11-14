"""Resolve simple NuGet dependency constraints against feed versions."""

from dataclasses import dataclass

from .version import version_key


@dataclass(frozen=True)
class Requirement:
    """Express an inclusive or exclusive interval of NuGet versions."""

    lower: str = ""
    upper: str = ""
    include_lower: bool = True
    include_upper: bool = True

    def accepts(self, version):
        """Check both version bounds."""
        key = version_key(version)
        if self.lower:
            low = version_key(self.lower)
            if key < low or (key == low and not self.include_lower):
                return False
        if self.upper:
            high = version_key(self.upper)
            if key > high or (key == high and not self.include_upper):
                return False
        return True


def parse_requirement(value):
    """Accept bare minima, exact pins and NuGet interval notation."""
    value = value.strip()
    if not value:
        return Requirement()
    if value[0] not in "[(":
        version_key(value)
        return Requirement(lower=value)
    if value[-1] not in "])":
        raise ValueError(f"некорректный диапазон версий: {value}")
    lower, comma, upper = map(str.strip, value[1:-1].partition(","))
    if not comma:
        if not lower or value[0] != "[" or value[-1] != "]":
            raise ValueError(f"некорректная точная версия: {value}")
        version_key(lower)
        return Requirement(lower, lower)
    for bound in (lower, upper):
        if bound:
            version_key(bound)
    return Requirement(lower, upper, value[0] == "[", value[-1] == "]")


def select_version(versions, value, allow_prerelease=False):
    """Find the lowest eligible version satisfying a declaration."""
    requirement = parse_requirement(value)
    allow_prerelease |= "-" in (requirement.lower + requirement.upper)
    return min(
        (item for item in versions
         if (allow_prerelease or "-" not in item)
         and requirement.accepts(item)),
        key=version_key, default=None,
    )
