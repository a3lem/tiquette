# Archive

Closed tickets can be archived out of the active directory.

## Setup

Create three tickets. Close two of them, leave one open.

## Steps

1. Run `archive`. The two closed tickets should move to `.tickets/archive/`.
2. Verify `ls` only shows the remaining open ticket.
3. Verify the archived ticket files exist under `.tickets/archive/`.
4. Run `archive` again with nothing to archive. Should succeed silently (no error).

## What to watch for

- Only closed tickets get archived, not open or in_progress ones.
- Archived files retain their original content.
- `ls` no longer shows archived tickets.
- Idempotent: running archive with nothing to do is a no-op.
