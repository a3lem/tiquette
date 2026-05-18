# Listing and Filtering

Exercise `ls` with its various filters and the ready/blocked views.

## Setup

Create a small project board:

- Epic "Backend overhaul" (priority 0, tag: backend)
- Task "Migrate DB" (priority 1, tag: backend, assigned to alice, parent: epic)
- Bug "Fix auth crash" (priority 0, tag: auth, assigned to bob)
- Task "Write docs" (priority 3, tag: docs, assigned to alice)

Add dep: "Migrate DB" depends on "Fix auth crash".

## Steps

1. `ls` with no filters. All four should appear, sorted by priority.
2. `ls --status open`. All four (all are open).
3. `ls -A alice`. Should show "Migrate DB" and "Write docs".
4. `ls --tag backend`. Should show "Backend overhaul" and "Migrate DB".
5. `ls --ready`. Should show "Fix auth crash" and "Write docs" (the epic is blocked by its open child, "Migrate DB" is blocked by its dep).
6. `ls --blocked`. Should show the epic and "Migrate DB".
7. Close "Fix auth crash". Now `ls --ready` should include "Migrate DB" (dep resolved).
8. Close "Migrate DB". Now the epic should move from blocked to ready (last child closed).
9. `ls --status closed`. Should show "Fix auth crash" and "Migrate DB".

## What to watch for

- Ready/blocked correctly accounts for BOTH deps and open children.
- A parent with open children is implicitly blocked even without explicit deps.
- Closing a dep or child cascades the ready/blocked status of dependents/parents.
- Filters can combine (e.g., `-A alice --status open`).
