# Split Closed Status

## Why

The `closed` status combined with a `resolution` field encodes one piece of information (terminal outcome) in two fields. Filtering, line formatting, and validation all carry the cost of consulting both. Collapsing into a single `status` axis with values `completed` and `canceled` removes the `resolution` concept entirely and makes every consumer simpler.

## What Changes

- **BREAKING:** `status` values become `{open, in_progress, completed, canceled}`. The value `closed` is no longer accepted anywhere.
- **BREAKING:** The `resolution` field is removed from the ticket schema. It is neither read nor written.
- **BREAKING:** `tq close` sets status to `completed` (no resolution side-effect).
- **BREAKING:** `tq cancel` sets status to `canceled` (no resolution side-effect).
- **BREAKING:** `tq reopen` sets status to `open`. There is no resolution to clear.
- **BREAKING:** `tq ls --completed` and `tq ls --canceled` are removed. Use `tq ls -s completed` or `tq ls --status canceled` instead.
- `tq ls -s` / `--status` accepts the new value set: `open`, `in_progress`, `completed`, `canceled`. `-s` is a new short alias for `--status`.
- The `ls` line-format checkbox mapping is restated against `status` only: `[ ]` open, `[/]` in_progress, `[x]` completed, `[~]` canceled.
- The `archive` command and its diagnostics refer to "completed and canceled tickets" rather than "closed tickets".
- `tq autofix` migrates legacy tickets: `status: closed` + `resolution: completed` → `status: completed`; `status: closed` + `resolution: canceled` → `status: canceled`; `status: closed` with no resolution → `status: completed`. The `resolution` field is removed from every ticket.

## Capabilities

### Modified Capabilities

- `ticket-lifecycle`: `close`, `cancel`, `reopen` set the new terminal/open statuses directly. Force-cascade descendants land on the same terminal status as the root.
- `ticket-query`: `ls` filters, line format, and archive wording use the new status vocabulary. `--completed` and `--canceled` removed in favour of `-s/--status`.
- `ticket-store`: File format drops `resolution` from the nullable-fields list. `status` enum updated.
- `ticket-autofix`: New rule that migrates legacy `closed` + `resolution` tickets to the split statuses.

## Impact

- All ticket files in the wild carry the old shape. `tq autofix` is the migration path; users run it once after upgrading.
- Tests across `ticket-lifecycle`, `ticket-query`, `ticket-store`, and `ticket-autofix` need updating.
- CLI help text, `--help` output, and `docs/cli-design.md` need updates.
- Downstream consumers parsing JSON/JSONL output that read `resolution` will break. Documented in CHANGELOG.

## Out of Scope

- Renaming `close`/`cancel`/`reopen` commands. The discussion that motivated this change touched on naming, but only the status decomposition is in scope here.
- Backwards-compat aliasing for `--status closed` or `--completed`/`--canceled`. Hard break, with `autofix` as the migration aid.
