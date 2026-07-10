# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo actually is

`fleet-cli` is an **AgentCulture mesh agent**, scaffolded from the
`culture-agent-template`. Two things are true at once, and you must hold both:

- **Stated domain (the goal):** "Agent and CLI to control a fleet of drones
  (multiple UAVs), built on `drone-cli` — coordinate, command, and monitor many
  drones at once." This is the agent's identity and the direction of future work.
- **Actual code today (the reality):** a generic **agent-first CLI scaffold** —
  identity/introspection verbs (`whoami`, `learn`, `explain`, `overview`,
  `doctor`, `cli`) plus the vendored AgentCulture skill kit. **No drone / UAV /
  `drone-cli` functionality exists yet.** The CLI's own self-description still
  reads "a clonable template for AgentCulture mesh agents" (see `learn.py`,
  `explain/catalog.py`, `README.md`).

When you add the drone-fleet functionality, you are *specializing the scaffold*:
add new noun groups under `fleet/cli/_commands/`, give them catalog entries, and
update the self-description strings — all while preserving the contracts below.
Do not invent drone behavior that isn't asked for, and don't assume any drone
plumbing is present.

## Commands

```bash
uv sync                                   # install deps into .venv (uses uv.lock)

# Run the CLI — the console script is `fleet`, NOT `fleet-cli` (see gotcha below)
uv run fleet whoami
uv run python -m fleet whoami             # equivalent
uv run fleet learn --json                 # every verb supports --json

# Tests
uv run pytest -n auto                     # full suite, parallel (xdist)
uv run pytest tests/test_cli.py::test_whoami_text   # a single test
uv run pytest -n auto --cov=fleet --cov-report=term # with coverage (CI gate: fail_under=60)

# Lint / format (exactly what the CI `lint` job runs)
uv run black --check fleet tests          # line length 100
uv run isort --check-only fleet tests     # black profile
uv run flake8 fleet tests                 # max-line-length 100, ignores E203/W503
uv run bandit -c pyproject.toml -r fleet
markdownlint-cli2 "**/*.md" "#node_modules" "#.local" "#.claude/skills" "#.teken"
uv run teken cli doctor . --strict        # the agent-first rubric gate (see below)
```

Black/isort: drop `--check`/`--check-only` to auto-format.

Two toolchain wrinkles: `markdownlint-cli2` is an **npm** tool, not a `dev`
dependency — CI does `npm install -g markdownlint-cli2@0.21.0`, so `uv run` will
not find it. And **flake8 is configured in `.flake8`, not `pyproject.toml`**
(black/isort/bandit/pytest/coverage all live in `pyproject.toml`).

## Critical gotcha: `fleet` vs `fleet-cli`

These names are split, and the docs are inconsistent about it:

- **`fleet-cli`** = the distribution / PyPI name (`pyproject.toml [project].name`),
  the `prog=` display name in `--help`, and the string used throughout doc text,
  the `explain` catalog, and `learn` output.
- **`fleet`** = the **actual runnable command** — the only `[project.scripts]`
  entry (`fleet = "fleet.cli:main"`) — and the Python package directory.

So `uv run fleet-cli whoami` (as `README.md`'s quickstart and several SKILL docs
claim) **fails** — use `uv run fleet …` or `uv run python -m fleet …`.

The split is *reconciled where it is load-bearing*, not eliminated. `explain`
accepts both spellings (`("fleet",)` and `("fleet-cli",)` both key the root
entry), so the rubric's `explain_self` bundle passes. But `prog=` is still
`fleet-cli`, `--help` and `learn` still say `fleet-cli`, and `README.md:22-23`
still prints commands that don't run. Fully collapsing the two names would mean
changing `prog=`, which several tests pin (`usage: fleet-cli`, `subject ==
"fleet-cli"`, `"# fleet-cli"`); that is a deliberate, separate change.

## The agent-first CLI architecture

The whole CLI is a small, deliberate set of contracts spread across a few files.
Read these together before changing dispatch, errors, or output:

- **`fleet/cli/__init__.py` — entry + dispatch.** `main(argv)` builds the
  argparse tree and dispatches. Two non-obvious mechanisms live here:
  - `_CliArgumentParser` overrides argparse's `.error()` so *parse-time* errors
    (unknown verb, bad flag) route through the same structured `error:` / `hint:`
    contract as runtime errors and exit `1` — not argparse's default stderr/exit-2.
    The subparsers are built with `parser_class=_CliArgumentParser` so this
    propagates to every noun.
  - Parse-time errors happen before `args.json` exists, so JSON-mode rendering of
    them relies on a class-level `_json_hint` that `main()` pre-populates by
    scanning raw `argv` for `--json`.
  - `_dispatch` wraps *any* unexpected exception into a `CliError` so **no Python
    traceback ever leaks to stderr**.
- **`fleet/cli/_errors.py` — error + exit-code policy (stable contract).** Every
  failure raises `CliError(code, message, remediation)`. Exit codes: `0` success,
  `1` user-input error, `2` environment/setup error, `3+` reserved. Centralised
  here; don't invent ad-hoc exits.
- **`fleet/cli/_output.py` — stream split (stable contract).** Results → stdout,
  errors/diagnostics → stderr, **never mixed**. JSON mode routes structured
  payloads to the same streams. Text-mode errors render as `error: <msg>` +
  `hint: <remediation>` (the `hint:` prefix is required by the rubric).
- **`fleet/cli/_commands/` — one module per verb/noun.** Each exposes
  `register(sub)` and is wired in `_build_parser`. Add a new noun group the same
  way (there's a commented template in `_build_parser`). A noun that has
  action-verbs **must** also expose an `overview` verb (rubric requirement — see
  `cli.py`, which exists only to satisfy `overview_cli_noun_exists`).
- **`fleet/explain/` — the `explain` catalog.** `catalog.py` holds `ENTRIES`, a
  dict keyed by command-path tuples (`()` and `("fleet-cli",)` both map to root).
  `resolve()` raises `CliError` for unknown paths. **Every registered noun/verb
  should have a catalog entry**, and `tests/test_cli.py::test_every_catalog_path_resolves`
  enforces that every key resolves.
- **`whoami.py` / `doctor.py` — identity, parsed without a YAML library.**
  `find_culture_yaml()` walks up from `__file__` (the agent's *own* identity, not
  the caller's CWD) and `read_agent_fields()` hand-parses the first agent block.
  This is deliberate: see the empty-runtime-deps invariant below. `doctor.py`
  reuses both and checks the mesh invariants.

The two test modules split along the same seam, and both call `main(argv)`
in-process (no subprocess), asserting on `capsys`:

- **`tests/test_cli.py`** — the core contracts: `whoami`/`learn`/`explain`, and
  `test_every_catalog_path_resolves`, which iterates `ENTRIES` and resolves each
  key.
- **`tests/test_cli_introspection.py`** — mirrors the `teken` rubric in pytest, so
  the rubric bundles fail fast locally: `overview` graceful on a bogus target,
  `cli overview` JSON shape, the bare `cli` noun printing something, `doctor`'s
  `{id, passed, severity, message, remediation}` per-check keys, and — the one
  that catches most regressions — `test_cli_overview_unknown_flag_structured_error`,
  which asserts a parse error exits `1` with `error:` + `hint:` on stderr rather
  than argparse's default exit `2`.

Practical consequence: **changing dispatch, `_output.py`, or `_errors.py` breaks
`test_cli_introspection.py` before it breaks the rubric gate.** Run pytest first;
it is far faster than `teken cli doctor`.

## Adding a noun group (the specialization path)

This is the shape of essentially all future work here — e.g. a `drone` or
`mission` noun. Five places, in order:

> **`fleet` is a reserved noun name.** `("fleet",)` keys the *root* `explain`
> entry, because the rubric's `explain_self` bundle probes `explain <console
> script>` and the console script is `fleet`. A `fleet` noun group would have to
> overwrite that key to document itself, which re-breaks the gate. The conflict
> is inherent to the rubric, not to the catalog's lookup scheme — no aliasing
> mechanism can make `explain fleet` render both the root docs and a noun's docs.
> Name the drone-fleet noun something else (`drone`, `swarm`, `mission`).

1. **Create `fleet/cli/_commands/<noun>.py`** exposing `register(sub) -> None`.
   Copy `cli.py`; it is the smallest complete example.
2. **Wire it in `_build_parser`** (`fleet/cli/__init__.py`) — import it and call
   `_<noun>_group.register(sub)`. There is a commented template at the call site.
   Always build the noun's parser from the passed-in `sub.add_parser(...)`: that
   makes it a `_CliArgumentParser`, and `add_subparsers` then does
   `kwargs.setdefault('parser_class', type(self))`, so the structured-error
   contract propagates to nested verbs automatically. (`cli.py:40` passes
   `parser_class=type(p)` explicitly — that is belt-and-braces, not required.)
   What *would* break the contract is constructing a parser with a bare
   `argparse.ArgumentParser`. `test_cli_overview_unknown_flag_structured_error`
   is the guard.
3. **Give the noun an `overview` verb** if it carries action verbs. `overview.py`
   exports `emit_overview()` / `render_text()` for exactly this reuse, and the
   rubric's `overview_cli_noun_exists` bundle is what `cli.py` exists to satisfy.
4. **Add `explain` catalog entries** in `fleet/explain/catalog.py` — one for
   `("<noun>",)` and one per `("<noun>", "<verb>")`.
5. **Handlers return `int | None` and raise `CliError` on failure.** Never
   `sys.exit()`, never print to stdout directly — use `emit_result`.

**Trap:** `test_every_catalog_path_resolves` walks the catalog **keys → commands**,
not the reverse. A new noun with *no* catalog entry therefore passes the whole
pytest suite silently; nothing fails until a human runs `explain <noun>`. Adding
the catalog entry is on you, not on the test.

## Invariants you must not break

These are enforced by tests and/or the CI rubric gate — breaking one fails CI:

1. **Runtime dependencies stay empty.** `pyproject.toml` has `dependencies = []`
   and the README sells "no third-party dependencies." `teken` is **dev-only**.
   The hand-rolled `culture.yaml` parser exists precisely to avoid a YAML runtime
   dep — don't add `pyyaml` (or anything) to runtime deps without a deliberate
   decision.
2. **No traceback leaks.** All failures go through `CliError` → `emit_error`.
3. **stdout/stderr never mix**, and **every command supports `--json`**.
4. **Every `explain` catalog path resolves** (test) and every CLI surface has an
   entry.
5. **The agent-first rubric passes:** `teken cli doctor . --strict`. It checks
   seven bundles (learn ≥200 chars mentioning purpose/command-map/exit-codes/
   `--json`/`explain`; `explain` resolves self + root and fails-with-hint on
   bogus; global + per-noun `overview`; descriptive verbs never hard-fail on a
   bad target; `doctor` shape; structured errors carry hints).

## The rubric gate (green — keep it that way)

`uv run teken cli doctor . --strict` passes **26/26** bundles. It regressed
historically on `explain_self`: the rubric derives the CLI's self-name from the
console-script entry point (`fleet`) and probes `explain fleet`, while the
catalog only keyed `("fleet-cli",)`. Fixed by registering both spellings, and
pinned in pytest by `test_explain_self_name_matches_console_script` so the gap
surfaces in the fast suite rather than only in the slow gate.

If you rename the console script in `[project.scripts]`, add the matching catalog
key in the same commit — nothing derives it automatically.

## Mesh identity (`culture.yaml`)

`culture.yaml` declares this agent: `suffix: fleet-cli`, **`backend: colleague`**
(a served Qwen model), so the resident prompt file is **`AGENTS.colleague.md`**,
not `CLAUDE.md`. `doctor.py`'s backend → prompt-file map is the source of truth:
`claude → CLAUDE.md`, `colleague → AGENTS.colleague.md`, `acp → AGENTS.md`,
`gemini → GEMINI.md`. (Note: the seed text and a few stray strings have
historically claimed `backend: claude` — that is stale; the declared backend is
`colleague`.)

What the tests actually pin here is narrower than "the backend is `colleague`":
`test_doctor_recognizes_declared_backend` asserts the declared backend is a
*known* key of `_PROMPT_FILE` and that `doctor` exits healthy. So **deleting
`AGENTS.colleague.md` fails the suite**, but flipping `culture.yaml` to
`backend: claude` would still pass (because `CLAUDE.md` exists). If you change
the backend, update `_PROMPT_FILE` and the prompt file together — the suite will
not catch a half-done rename.

## Version-bump-every-PR

CI's `version-check` job fails any PR whose `pyproject.toml` version equals
`main` — **including docs/config/CI-only PRs**. Bump `version` in `pyproject.toml`
and prepend a `CHANGELOG.md` entry (Keep a Changelog format) before opening a PR;
use the `/version-bump` skill. PyPI Trusted Publishing fires on push to `main`
(`.github/workflows/publish.yml`); PRs publish a `.devN` build to TestPyPI.

## Skills are vendored cite-don't-import

`.claude/skills/` holds skills copied verbatim from upstream, not installed as
deps. `docs/skill-sources.md` is the authoritative provenance ledger (upstream,
origin, last-synced, and tracked local divergences).

**The ledger is currently incomplete:** 14 skill directories exist on disk but
only 12 have ledger rows — `recall` and `remember` are vendored and unrecorded.
Don't read the ledger as exhaustive until that's reconciled. (The README's
"canonical guildmaster skill kit (11 skills)" is a *different* count and is
correct: exactly 11 rows have a `guildmaster` upstream; `ask-colleague` comes
from `colleague`, and three devague skills are re-broadcast through guildmaster.)

Rules:

- Most skills come from **guildmaster**; `ask-colleague` is vendored **directly
  from `colleague`** (guildmaster hasn't re-broadcast the rename) as a tracked
  divergence.
- **Do not reformat or edit vendored script bodies** — they're cited, not owned.
  markdownlint and Sonar both exclude `.claude/skills/**` for this reason. The
  only sanctioned edits are the one consumer-identifying prose clause in each
  `SKILL.md` and adding `type: command` to frontmatter (load-bearing for the
  culture skill loader). Re-sync via the procedure in `docs/skill-sources.md`.
- Reach for `ask-colleague` reflexively for a diverse second opinion: `review` a
  committed diff before a PR, `explore` an unfamiliar area — both are read-only
  (isolated worktree, no side effects). Side-effecting `write --apply`/`--pr`
  needs the user's go-ahead.

## Quality gate

SonarCloud (`agentculture_fleet-cli`) gates the `test` job when `SONAR_TOKEN` is
set (`sonar.qualitygate.wait=true`); token-less repos and fork PRs skip it and
stay green. `coverage.xml` uses `relative_files = true` so paths map to
`sonar.sources=fleet`. The `cicd` skill (`status`/`await`) queries this gate.
