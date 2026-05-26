# Timestamp Format

## Why

The current timestamp format (`2026-04-29T12:48:50.906383+00:00`) carries microsecond precision and a numeric UTC offset. For a human-facing ticket file, minute precision and a `Z` suffix are easier to read, easier to type, and lose no information that matters for ticket workflows.

## What Changes

- Written timestamps use the format `YYYY-MM-DDTHH:MMZ` (minute precision, Zulu suffix). Applies to the `created` frontmatter field and every Notes-section entry.
- Reads accept both the new format and the legacy microsecond-plus-offset format indefinitely. No migration of existing ticket files.
- Any timestamp comparison (e.g. `tq prune --before`) continues to work across mixed-format ticket sets.

## Capabilities

### Modified Capabilities

- `ticket-store`: Adds a written-timestamp format requirement; readers accept both formats.
- `ticket-autofix`: Normalises legacy timestamps in active and archived tickets to the new format on `tq autofix`.

The lifecycle and edit specs already say "ISO 8601 timestamp" without constraining the precision or offset notation, so no deltas are needed there -- the format is owned by `ticket-store`.

## Impact

- New ticket files and new note entries appear in the new format.
- Existing ticket files are not rewritten; mixed formats coexist in `.tickets/` indefinitely.
- Any code that parses timestamps (lifecycle, edit, query/prune) must accept both formats.
- Existing tests that assert on timestamp shape need updates.

## Out of Scope

- Automatic migration on read (write paths still leave legacy timestamps alone; only `tq autofix` rewrites them).
- Changing the `--before` filter input format (stays `YYYY-MM-DD`).
- Sub-minute event ordering (we accept that two events in the same minute may sort by insertion order, not real time).
