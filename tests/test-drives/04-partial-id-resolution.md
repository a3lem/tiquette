# Partial ID Resolution

Tickets can be referenced by partial ID. This tests matching, ambiguity
handling, and edge cases.

## Setup

Empty tickets directory.

## Steps

1. Create a ticket. Note the full ID (e.g., `tiquette-a3f1`).
2. Use `show` with just the hex suffix (e.g., `a3f1`). Should resolve and display the ticket.
3. Use `show` with a longer prefix (e.g., `tiquette-a3`). Should also resolve if unique.
4. Create a second ticket. If the two IDs share a common prefix, try a partial that's ambiguous. Should fail with an error listing the matches.
5. Use the full ID for both tickets in a `dep` command. Should work.
6. Use partial IDs in a `dep` command. Should work when each partial is unambiguous.

## What to watch for

- Ambiguous partials produce a helpful error listing all matches.
- Partial IDs work in every position: subject ID, dep target, parent, link target, etc.
- A partial that matches nothing gives a clear "not found" error.
