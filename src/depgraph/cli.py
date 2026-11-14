"""Report direct dependencies of an exact NuGet package version."""

import sys

from .config import parse_config
from .nuget import NuGetRepository


def main(argv=None):
    """Print each dependency declaration with its framework and range."""
    config = parse_config(argv)
    try:
        if config.test_mode:
            raise ValueError("анализ тестового файла появится на этапе 3")
        repo = NuGetRepository(config.repository)
        declarations = repo.declarations(config.package, config.version)
    except ValueError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    for item in declarations:
        print(f"{item.package}\t{item.requirement or '*'}\t"
              f"{item.framework or 'any'}")
    if not declarations:
        print("Прямых зависимостей нет.")
    return 0
