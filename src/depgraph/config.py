"""Parse and validate user-supplied options."""

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from urllib.parse import urlsplit

DEFAULT_REPOSITORY = "https://api.nuget.org/v3/index.json"
DEFAULT_DEPTH = 3
ROOT_DEPTH = 0
INVALID_PORT = 0
PACKAGE_ID = re.compile(r"[A-Za-z0-9_]+(?:[.-][A-Za-z0-9_]+)*")
TEST_ID = re.compile(r"[A-Z]+")
VERSION = re.compile(
    r"[0-9]+(?:\.[0-9]+){0,3}"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


@dataclass(frozen=True)
class Config:
    """Hold the validated options passed to the command."""

    package: str
    repository: str
    test_mode: bool
    version: str
    max_depth: int
    reverse: bool


def validate_url(value):
    """Return an HTTP(S) URL with an authority and no fragment."""
    if not value or any(char.isspace() for char in value):
        raise ValueError("укажите URL HTTP(S) без пробелов")
    parsed = urlsplit(value)
    port = parsed.port
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("укажите URL HTTP(S) с именем сервера")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("URL не должен содержать учётные данные или фрагмент")
    if port == INVALID_PORT:
        raise ValueError("порт не может быть равен нулю")
    return value


def repository(value, test_mode):
    """Validate a local test file or the repository URL."""
    if test_mode:
        if value is None or not Path(value).is_file():
            raise ValueError("в режиме тестирования укажите существующий файл")
        return value
    return validate_url(DEFAULT_REPOSITORY if value is None else value)


def make_parser():
    """Describe accepted command line options."""
    parser = argparse.ArgumentParser(description="Граф зависимостей NuGet")
    parser.add_argument("--package", required=True, help="имя пакета")
    parser.add_argument("--repository", help="URL NuGet v3 или тестовый файл")
    parser.add_argument("--test-mode", action="store_true", help="читать файл")
    parser.add_argument("--version", required=True, help="точная версия пакета")
    parser.add_argument(
        "--reverse", action="store_true",
        help="найти обратные зависимости в тестовом репозитории",
    )
    parser.add_argument(
        "--max-depth", type=int, default=DEFAULT_DEPTH,
        help="глубина: 0 — только корневой пакет (по умолчанию: %(default)s)",
    )
    return parser


def parse_config(argv=None):
    """Return validated options or produce an argparse diagnostic."""
    parser = make_parser()
    args = parser.parse_args(argv)
    pattern = TEST_ID if args.test_mode else PACKAGE_ID
    if not pattern.fullmatch(args.package):
        parser.error("--package: недопустимое имя для выбранного режима")
    if not VERSION.fullmatch(args.version):
        parser.error("--version: требуется точная версия NuGet")
    if args.max_depth < ROOT_DEPTH:
        parser.error("--max-depth: требуется неотрицательное число")
    if args.reverse and not args.test_mode:
        parser.error("--reverse: требуется --test-mode")
    try:
        args.repository = repository(args.repository, args.test_mode)
    except (ValueError, OSError) as error:
        parser.error(f"--repository: {error}")
    return Config(**vars(args))
