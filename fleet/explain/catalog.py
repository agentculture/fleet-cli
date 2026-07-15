"""Markdown catalog for ``fleet-cli explain <path>``.

Each entry is verbatim markdown. Keys are command-path tuples. The empty tuple
resolves to the root entry, as do both spellings of this CLI's name: the
distribution name ``("fleet-cli",)`` and the console-script name ``("fleet",)``.
Both are registered because the agent-first rubric derives the CLI's self-name
from the ``[project.scripts]`` entry point (``fleet``) and probes
``explain fleet``, while the doc text throughout addresses it as ``fleet-cli``.

Keep bodies self-contained: an agent reading one entry should get enough
context without chaining reads.
"""

from __future__ import annotations

_ROOT = """\
# fleet-cli

A clonable template for AgentCulture mesh agents. It carries an agent-first CLI
(cited from the teken `python-cli` reference), a mesh identity (`culture.yaml` +
`CLAUDE.md`), the canonical guildmaster skill kit under `.claude/skills/`, and a
buildable/deployable package baseline. Clone it, rename the package, edit
`culture.yaml`, and you have a new agent.

## Verbs

- `fleet-cli whoami` — identity probe from `culture.yaml`.
- `fleet-cli learn` — structured self-teaching prompt.
- `fleet-cli explain <path>` — markdown docs for any noun/verb.
- `fleet-cli overview` — descriptive snapshot of the agent.
- `fleet-cli doctor` — check the agent-identity invariants.
- `fleet-cli cli overview` — describe the CLI surface.

## Exit-code policy

- `0` success
- `1` user-input error
- `2` environment / setup error
- `3+` reserved

## See also

- `fleet-cli explain whoami`
- `fleet-cli explain doctor`
"""

_WHOAMI = """\
# fleet-cli whoami

Reports the agent's identity from `culture.yaml`: nick (`suffix`), backend,
served model, and the package version. Read-only.

## Usage

    fleet-cli whoami
    fleet-cli whoami --json
"""

_LEARN = """\
# fleet-cli learn

Prints a structured self-teaching prompt covering purpose, command map,
exit-code policy, `--json` support, and the `explain` pointer.

## Usage

    fleet-cli learn
    fleet-cli learn --json
"""

_EXPLAIN = """\
# fleet-cli explain <path>

Prints markdown documentation for any noun/verb path. Unlike `--help` (terse,
positional), `explain` is global and addressable by path.

## Usage

    fleet-cli explain fleet-cli
    fleet-cli explain whoami
    fleet-cli explain --json <path>
"""

_OVERVIEW = """\
# fleet-cli overview

Read-only descriptive snapshot of the agent: identity (from `culture.yaml`), the
verb surface, and the sibling-pattern artifacts the template carries. Accepts an
ignored `target` so a stray path never hard-fails.

## Usage

    fleet-cli overview
    fleet-cli overview --json
"""

_DOCTOR = """\
# fleet-cli doctor

Checks the agent-identity invariants `steward doctor` verifies:
prompt-file-present and backend-consistency (`colleague` → `AGENTS.colleague.md`), plus a
skills-present check. Exits 1 when unhealthy.

## Usage

    fleet-cli doctor
    fleet-cli doctor --json
"""

_CLI = """\
# fleet-cli cli

Noun group for CLI-surface introspection. `cli overview` describes the CLI
itself (distinct from the global `overview`, which describes the agent).

## Usage

    fleet-cli cli overview
    fleet-cli cli overview --json
"""


ENTRIES: dict[tuple[str, ...], str] = {
    (): _ROOT,
    ("fleet-cli",): _ROOT,  # distribution name (prog=, doc text)
    # Console-script name. RESERVED: `resolve()` does exact-tuple lookup, so this
    # key cannot also document a noun group named `fleet` — and the rubric's
    # `explain_self` bundle requires it to render the root entry. Name any future
    # noun `drone`/`swarm`/`mission`, never `fleet`. See CLAUDE.md.
    ("fleet",): _ROOT,
    ("whoami",): _WHOAMI,
    ("learn",): _LEARN,
    ("explain",): _EXPLAIN,
    ("overview",): _OVERVIEW,
    ("doctor",): _DOCTOR,
    ("cli",): _CLI,
    ("cli", "overview"): _CLI,
}
