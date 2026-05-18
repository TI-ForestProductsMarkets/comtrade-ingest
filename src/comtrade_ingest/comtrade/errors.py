import textwrap
import sys


class ComtradeIngestError(Exception):
    """Base error for user-facing comtrade-ingest failures."""


class ConfigValidationError(ComtradeIngestError):
    """Raised when the user config or reference config is invalid."""

def print_cli_error(title: str, reason: str) -> None:
    line = "=" * 72

    print("", file=sys.stderr)
    print(line, file=sys.stderr)
    print(f"ERROR: {title}", file=sys.stderr)
    print(line, file=sys.stderr)
    print("Reason:", file=sys.stderr)

    wrapped = textwrap.wrap(
        str(reason),
        width=68,
        initial_indent="  ",
        subsequent_indent="  ",
    )

    for part in wrapped:
        print(part, file=sys.stderr)

    print(line, file=sys.stderr)