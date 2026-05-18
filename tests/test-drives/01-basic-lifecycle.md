# Basic Lifecycle

A single ticket moves through every status transition.

## Setup

Empty tickets directory.

## Steps

1. Create a bug ticket titled "Login page 500s on empty password" with priority 1 and type bug.
2. Verify `ls` shows it as open with priority 1.
3. Start the ticket. Verify `show` displays status as in_progress.
4. Close the ticket. Verify status is `closed` (not `completed`). No `resolution` field should be present.
5. Reopen it. Verify status is back to `open` and no `resolution` field is written.
6. Cancel it. Verify status is `canceled`. No `resolution` field.
7. Reopen again, then close. Should work cleanly both ways.

## What to watch for

- Each transition prints the ticket ID on success.
- `show` output reflects the new status immediately after each command.
- The terminal status is `closed`, not `completed` — `tq ls --status closed` is the correct filter.
- No `resolution` field is ever written or read.
