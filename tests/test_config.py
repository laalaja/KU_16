"""Check valid CLI options and diagnostics for invalid input."""

from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from src.depgraph.config import DEFAULT_REPOSITORY, parse_config

VALID = ["--package", "A", "--version", "1.0.0"]
ARGUMENT_ERROR = 2


class ConfigTests(unittest.TestCase):
    """Exercise both modes and every stage-one parameter."""

    def test_defaults(self):
        """Use the public NuGet index unless overridden."""
        config = parse_config(VALID)
        self.assertEqual(DEFAULT_REPOSITORY, config.repository)
        self.assertFalse(config.test_mode)

    def test_local_repository(self):
        """Accept a test file with depth zero."""
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory, "repo with spaces.json")
            file.write_text("{}", encoding="utf-8")
            options = ["--test-mode", "--repository", str(file)]
            config = parse_config(VALID + options + ["--max-depth", "0"])
        self.assertEqual(str(file), config.repository)
        self.assertEqual(0, config.max_depth)

    def test_invalid_options(self):
        """Show a diagnostic and exit 2 for each invalid option."""
        cases = {
            ("--package", "bad/name"): "--package",
            ("--version", "[1,)"): "--version",
            ("--max-depth", "-1"): "--max-depth",
            ("--max-depth", "a"): "--max-depth",
            ("--repository", "ftp://example.org"): "--repository",
            ("--repository", "https://bad:port"): "--repository",
            ("--test-mode",): "--repository",
            ("--test-mode", "false"): "false",
            ("--test-mode", "--package", "abc"): "--package",
        }
        for options, expected in cases.items():
            with self.subTest(options=options):
                self.assert_invalid(options, expected)

    def assert_invalid(self, options, expected):
        """Assert the parser points to the erroneous option."""
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as exit_:
            parse_config(VALID + list(options))
        self.assertEqual(ARGUMENT_ERROR, exit_.exception.code)
        self.assertIn(expected, stderr.getvalue().splitlines()[-1])
