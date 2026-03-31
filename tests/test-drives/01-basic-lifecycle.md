# Basic Lifecycle

A single ticket moves through every status transition.

## Setup

Empty tickets directory.

## Steps

1. Create a bug ticket titled "Login page 500s on empty password" with priority 1 and type bug.
2. Verify `ls` shows it as open with priority 1.
3. Start the ticket. Verify `show` displays status as in_progress.
4. Close the ticket. Verify status is closed and resolution is completed.
5. Reopen it. Verify status is back to open and resolution is cleared.
6. Cancel it. Verify status is closed and resolution is canceled.
7. Reopen again, then close. Should work cleanly both ways.

## What to watch for

- Each transition prints the ticket ID on success.
- `show` output reflects the new status immediately after each command.
- Reopening clears the resolution field entirely (not just blanking it).
