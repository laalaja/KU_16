"""Print validated configuration for the first stage."""

from dataclasses import asdict

from .config import parse_config


def main(argv=None):
    """Print the effective options as key-value pairs."""
    for key, value in asdict(parse_config(argv)).items():
        print(f"{key}={value}")
    return 0
