# Prune archived tickets

## Why

`tq archive` moves terminal tickets into `.tickets/archive/` but nothing ever removes them, so the archive grows without bound. Users need a way to permanently delete archived tickets by filter.

## What Changes

- Add a `tq prune` command that permanently deletes tickets from `.tickets/archive/`, scoped by filter.
- Filters combine with AND (mirroring `tq ls`): `--status {closed,canceled}`, `--type {bug,feature,task,epic,chore}`, `--before YYYY-MM-DD` (matches tickets whose `created` is strictly before that date).
- At least one filter is required; bare `tq prune` exits non-zero with a usage error.
- Dry-run by default: prints the archived tickets that would be deleted and removes nothing. `-y`/`--yes` performs the deletion.
- Operates only on `.tickets/archive/`. Active tickets are never touched.

## Capabilities

### Modified Capabilities

- `ticket-query`: Adds the `prune` command alongside the existing `archive` command.

## Impact

- New subcommand wired in `src/tiquette/commands/query.py` (sibling to `archive`), plus help text in `src/tiquette/cli.py`.
- No schema change: `--before` compares against the existing `created` timestamp.
- CHANGELOG.md entry.

## Out of Scope

- Age tracking beyond `created` (no `closed-at` / `archived-at` timestamp). `--before` prunes by ticket birth date, not resolution date.
- Dangling-reference detection after deletion. Reference integrity is owned by `validate`/`autofix`; `prune` is a blunt instrument.
- Pruning active (non-archived) tickets.
- Relative durations (e.g. `--older-than 30d`). Only absolute `--before YYYY-MM-DD`.
