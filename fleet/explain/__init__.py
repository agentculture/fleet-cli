"""Explain catalog — markdown keyed by command-path tuples (stable-contract).

Every noun/verb registered in the CLI should have a catalog entry.
"""

from __future__ import annotations

from fleet.cli._errors import EXIT_USER_ERROR, CliError
from fleet.explain.catalog import ENTRIES


def resolve(path: tuple[str, ...]) -> str:
    if path in ENTRIES:
        return ENTRIES[path]
    display = " ".join(path) if path else "<root>"
    raise CliError(
        code=EXIT_USER_ERROR,
        message=f"no explain entry for: {display}",
        # Name the console script, not the distribution: `fleet-cli` is not a
        # runnable command, so a hint spelling it that way sends the reader to
        # a "command not found".
        remediation="list entries with: fleet explain fleet",
    )


def known_paths() -> list[tuple[str, ...]]:
    return list(ENTRIES.keys())
