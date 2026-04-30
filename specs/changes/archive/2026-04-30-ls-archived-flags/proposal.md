# Proposal: `ls` flags for archived tickets

## Why

`tq ls` currently has no way to view archived tickets. Users can browse the filesystem but the CLI offers no built-in path to historical work, and resolution filters (`--completed`, `--canceled`) silently exclude archived rows.

## What Changes

- Add `--archived` flag to `tq ls`: lists only archived tickets.
- Add `--all` (short: `-a`) flag to `tq ls`: lists active + archived tickets. Mirrors `ls -a`.
- Treat source selection as a separate axis from status/resolution filtering. Source flags (`--archived`, `--all`) combine freely with status/resolution filters (`--status`, `--completed`, `--canceled`, `--ready`, `--blocked`, `--tag`, `--type`, `--assignee`).
- `--archived` and `--all` are mutually exclusive with each other (they each name a different source set).
- **BREAKING:** Rename the short flag for `tq ls --assignee` from `-a` to `-A`, freeing `-a` for `--all`.

Default behavior is preserved: bare `tq ls` and bare `tq ls --completed` still show active tickets only.

## Capabilities

### Modified Capabilities

- `ticket-query`: `ls` gains a source-selection axis with `--archived` and `--all`.

## Impact

- `src/tiquette/commands/query.py`: argparse for `ls`, `_handle_ls`, ticket loading helper.
- `src/tiquette/store.py`: `list_ticket_ids` currently globs only the top level; needs an option (or a sibling helper) to include `archive/`.
- Scripts using `tq ls -a <name>` (assignee) will break; they must switch to `-A <name>` or `--assignee <name>`.

## Out of Scope

- A `--closed` shortcut flag (`--status closed` already covers active closed tickets).
- Restructuring how archived tickets are stored.
- Changing the default `tq ls` source set.
