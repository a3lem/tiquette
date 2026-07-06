# Proposal: Archived tickets stay consultable via lookup commands

## Why

`tq show <archived-id>` fails with `ticket '<id>' not found`, even though the ticket file exists under `.tickets/archive/`. Archiving is meant to retire terminal tickets from active views, not to make them unreadable. `info`, `path`, and `deps` share the same ID-resolution choke point and fail the same way. `tq ls --archived`/`--all` already prove archived tickets are meant to stay queryable -- single-ticket lookup just never got the same treatment.

## What Changes

- Partial and exact ID resolution for the four single-ticket lookup commands -- `show`, `info`, `path`, `deps` -- considers both active tickets and archived tickets, not just `.tickets/*.md`.
- Mutation commands (`edit`, `start`, `close`, `cancel`, `reopen`, and dep/link/parent targets passed to them) are unaffected: their ID resolution stays active-only, unchanged from today.
- WHEN an ID exists in both locations (a data-integrity edge case; no code path deliberately produces this), the active ticket takes precedence -- consistent with the existing active-wins convention in `store.py`'s `load_all_tickets`/`iter_tickets`.
- `show`, `info`, and `path` locate and read the ticket file wherever it actually lives (`.tickets/` or `.tickets/archive/`).
- `show`'s relationship sections (Blockers/Blocking/Children/Linked) and `deps`'s dependency tree resolve against the combined active+archived ticket set, so an archived ticket's own (possibly also-archived) dependencies still render instead of silently vanishing.
- No change to `tq ls` default behavior (still active-only without `--archived`/`--all`) and no change to which tickets are eligible for archiving.

## Capabilities

### Modified Capabilities

- `id-resolution`: partial/exact ID matching now searches active and archived tickets together.
- `ticket-query`: `show`, `info`, `path`, and `deps` (`Show dependency tree`) work against archived tickets.

## Impact

- `src/tiquette/store.py`: `resolve_id_in_dir` (or a new sibling) must glob `tickets_dir/archive/*.md` in addition to `tickets_dir/*.md`. `_read_ticket_and_body` builds its path from `tickets_dir` only and must locate the file in whichever directory holds it.
- `src/tiquette/commands/query.py`: `_handle_show`, `_handle_path` construct `tickets_dir / f"{ticket_id}.md"` directly and need the same directory-aware lookup. `_handle_show` and `_handle_deps` call `_load_all_tickets(tickets_dir)` with the default `source="active"`; both need `source="all"` so an archived (root or dependency) ticket is present in the loaded set.

## Out of Scope

- `tags`, `links`, `ls`, `archive`, `prune` -- unaffected; `ls` already has its own source-selection axis.
- Fixing `info`'s pre-existing mismatch with its spec (the human-readable path currently prints frontmatter only, no relationship sections, unlike what `ticket-query`'s "Info command" requirement describes) -- unrelated bug, not touched here.
- Changing which tickets are eligible for archiving, or archive/prune semantics.
