## Context

`tq` commands that create relationships (`dep`, `nest`, `link`) validate targets at write time, but nothing detects references that become dangling after the target is deleted or archived. The new `validate` command fills that gap by scanning all non-archived tickets and checking every `deps`, `parent`, and `links` reference.

Archived tickets live in `.tickets/archive/<id>.md` -- same format, flat directory.

## Goals / Non-Goals

**Goals:**
- Detect dangling `deps`, `parent`, and `links` references.
- Distinguish "missing" (error) from "archived" (warning).
- Structured, parseable output.

**Non-Goals:**
- Fix violations automatically (future work).
- Validate field values (type, priority, status enums) -- argparse already guards those at write time.
- Validate bidirectional consistency (e.g. link symmetry, parent-child agreement) -- out of scope for this change.

## Decisions

### New module: `commands/validate.py`

One new file following the existing pattern: a `register(subparsers)` function that wires up the `validate` subcommand, and a `_handle_validate` handler. Imported and registered in `cli.py` alongside the other command groups.

No arguments or flags. The command always scans everything.

### Ticket loading

Build two ID sets up front:

1. `active_ids: set[str]` -- from `tickets_dir.glob("*.md")`, reading stems.
2. `archived_ids: set[str]` -- from `(tickets_dir / "archive").glob("*.md")`, reading stems. Empty set if the archive directory doesn't exist.

Then load each active ticket via `read_ticket()` and check its `deps`, `parent`, and `links` against both sets.

This means two `glob` calls and N `read_ticket` calls (where N = active ticket count). Archived tickets are never loaded -- only their IDs are needed.

**Alternatives considered:** Loading all tickets (active + archived) into `Ticket` objects. Rejected because we only need archived IDs, not their content.

### Problem classification

For each reference field on each active ticket, classify the target:

| Target in `active_ids` | Target in `archived_ids` | Classification |
|---|---|---|
| yes | -- | OK |
| no | yes | warning |
| no | no | error |

Collect problems as a flat list of `(ticket_id, level, message)` tuples, where `level` is `"error"` or `"warning"`.

### Output

Print each problem to stderr as `{ticket_id}: {level}: {message}`, sorted by ticket ID then by level (errors before warnings) for stable output.

After all problems, print a summary line:
- Problems found: `{n} errors, {m} warnings`
- Clean: `all tickets valid`

Exit 1 if any errors; exit 0 otherwise (warnings alone don't fail).

### CLI registration

Add `validate` to `cli.py`:
- Import `validate` module in the imports block.
- Call `validate.register(subparsers)` in `build_parser()`.
- Add `validate` line to both `HELP_SUMMARY` and `HELP_TEXT`.

Place it under a new "Maintenance:" section in the help text, after "View:".

## Risks / Trade-offs / Limitations

- **[Performance on large stores]** → Every active ticket is loaded from disk. Acceptable for the expected scale (hundreds, not millions). No index or caching needed.
- **[No partial-ID resolution]** → References are checked by exact ID match against file stems, not via `resolve_id()`. This is intentional: stored references use full IDs, and partial matching would mask real problems.
