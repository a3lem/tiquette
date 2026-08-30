# Variadic Read Commands + Canonical-Form Hints + Instruction-Layer Split

Ticket: tiqt-aa0e (supersedes the reverted tiqt-8e5c implementation)

## Why

A usage analysis of 237 real `tq` invocations (2026-08-17 → 2026-08-30) found 16 command-surface failures. A first implementation answered with new verbs and aliases (`note`, `tree`, `-m`) and was reverted in design review: it duplicated existing surfaces and broke the one-canonical-surface ethos from cli-redesign-v1.2. The evidence actually points at the instruction layer — the session-priming snippet never mentioned `--note`, and agents that read `--help` recovered — plus two genuine surface gaps that do NOT add second ways: read commands are inconsistently single-ID, and a wrong guess costs three round trips to recover from.

## What Changes

- `show`, `info`, and `path` accept multiple IDs, validated up front like the transition commands (an unknown or ambiguous ID exits non-zero and prints nothing). `deps` stays single-ID: one dependency tree per invocation.
- `--json` on `show`/`info`: a single ID keeps the current single-object shape; multiple IDs emit one JSON array of those objects. (`--jsonl` remains an `ls`-only, explicitly named flag; there is no jsonl precedent under `--json`.)
- Unknown subcommands print a hint that teaches the canonical form: `tq note ...` → `use: tq edit <id> --note TEXT`; `tq tree ...` → `use: tq ls --parent <id>`; the v1.2-removed verbs map to their `edit` equivalents; other typos get a closest-match suggestion. Hints are error text — no verb becomes valid. (Error UX; deliberately not a reference-spec requirement.)
- Instruction layer: the session-priming snippet becomes policy-only and mandates a `tiquette`-skill load before the first `tq` call; all command-surface teaching (including "there is no `note`/`tree`/`-m`" tips) lives in the skill alone. The skill drops the plugin-system section (inherited from another project; never implemented here).
- Help text documents `prune -t` (the short flag exists; the help omitted it).

## Explicitly Rejected (recorded for the next reader)

- `tq note`, `tq tree`, `-m`: aliases/duplicate verbs. One way to do things.
- Lenient (warn-and-skip) bulk loads for `show`/`deps`: reads stay fail-fast on any malformed ticket file; the diagnostic names the file and the existing `tq autofix` hint is the remedy.

## Capabilities

### Modified Capabilities

- `ticket-query`: variadic `show`/`info`/`path`; `--json` array shape for multiple IDs.

## Impact

- `commands/query.py`: `nargs="+"` on show/info/path; resolve-all-first helper; JSON array branch.
- `cli.py`: help text (variadic signatures, `--json` shape note, `prune -t`); root-parser error override for hints.
- Templates: `.shablon/templates/_includes/prime.md` (policy-only + skill mandate), `.shablon/templates/skills/tiquette/SKILL.md` (surface tips; plugin section removed); regenerate via `shablon generate`.

## Out of Scope

- Variadic `deps`.
- Any change to note/tag/link mechanics.
- Intercepting `-m` inside subcommand errors (the skill and prime now teach `--note`; re-measure before more machinery).
