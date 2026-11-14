"""Represent normalized NuGet version strings."""

from .config import VERSION

STANDARD_PARTS = 3


def normalize(value):
    """Drop build metadata and canonicalize numeric components."""
    if not VERSION.fullmatch(value):
        raise ValueError(f"некорректная версия NuGet: {value!r}")
    core, _, label = value.split("+", maxsplit=1)[0].partition("-")
    parts = [int(part) for part in core.split(".")]
    parts.extend([0] * (STANDARD_PARTS - len(parts)))
    if len(parts) > STANDARD_PARTS and not parts[-1]:
        parts.pop()
    canonical = ".".join(map(str, parts))
    return f"{canonical}-{label.lower()}" if label else canonical
