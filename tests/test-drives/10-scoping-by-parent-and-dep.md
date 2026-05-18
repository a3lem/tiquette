# Scoping by Parent and Dependent

Exercise `ls --parent <id>` (subtree view) and `ls --dep <id>` (direct dependents view).

## Setup

Create a board with a small epic and a cross-cutting dependency:

- Epic "Auth rewrite" (priority 1, tag: auth)
- Task "Design tokens" (priority 1, tag: auth, parent: epic)
- Task "Implement login" (priority 2, tag: auth, parent: epic)
- Task "Implement signup" (priority 2, tag: auth, parent: epic)
- Sub-task "Write JWT helper" (priority 2, parent: "Design tokens")
- Bug "Fix legacy session leak" (priority 0, tag: legacy) — outside the epic
- Doc task "Update auth README" (priority 3, tag: docs) — outside the epic, depends on "Implement login"

Add deps:
- "Implement login" depends on "Design tokens"
- "Implement signup" depends on "Design tokens"
- "Update auth README" depends on "Implement login"

## Steps

### `--parent`

1. `ls --parent <epic-id>`. Should show the epic at root with all four descendants nested ("Design tokens" → "Write JWT helper", plus "Implement login", "Implement signup"). "Fix legacy session leak" and "Update auth README" should NOT appear.
2. `ls --parent <epic-id> --ready`. Should show "Design tokens" only (the only descendant with no open deps and no open children). The epic appears as a context heading; "Implement login" and "Implement signup" are blocked by "Design tokens".
3. `ls --parent <epic-id> --tag auth`. Should show the epic and all three direct task children (all tagged auth). "Write JWT helper" (no auth tag) should be excluded — but its parent "Design tokens" still appears.
4. `ls --parent <design-tokens-id>`. Should show "Design tokens" at root with only "Write JWT helper" nested.
5. `ls --parent <leaf-id>` (try a ticket with no children, e.g. "Write JWT helper"). Should show just that ticket at root, no nested rows.
6. Close "Write JWT helper" (the only child of "Design tokens"), then close "Design tokens" itself, then run `ls --parent <epic-id> --ready`. "Implement login" and "Implement signup" should now appear under the epic (their dep is now `closed`, a terminal state). Note: closing "Design tokens" directly without first closing its child would fail with "has open descendants" -- use `tq close <design-tokens-id> -f` if you want to cascade.
7. `ls --parent nonexistent`. Should exit non-zero with `ticket 'nonexistent' not found` on stderr.
8. Try a partial ID, e.g. `ls --parent <first 3 chars of epic-id>`. Should resolve and behave the same as step 1.

### `--dep`

9. `ls --dep <design-tokens-id>`. Should show "Implement login" and "Implement signup" as a flat list (no tree, no indentation). The epic should NOT appear as a context heading.
10. `ls --dep <implement-login-id>`. Should show "Update auth README" only.
11. `ls --dep <design-tokens-id>` should NOT include "Update auth README" — it depends on "Implement login", not directly on "Design tokens" (transitive dependents are excluded).
12. `ls --dep <write-jwt-helper-id>`. Nothing depends on it directly — output should be empty, exit 0.
13. `ls --dep <design-tokens-id> --status open`. Should show both implementations (assuming they're still open).
14. Run `tq close <implement-login-id>`, then `ls --dep <design-tokens-id> --status open`. Should show only "Implement signup".
15. `ls --dep nonexistent`. Should exit non-zero with `ticket 'nonexistent' not found`.

### Mutual exclusion

16. `ls --parent <epic-id> --dep <design-tokens-id>`. Should exit non-zero with an argparse "not allowed" message.

## What to watch for

- `--parent` always roots at the named ticket; ancestors above it never appear, even if they exist.
- `--parent` keeps tree rendering and parent context-heading semantics within the subtree.
- `--parent` stacked with `--ready` / `--blocked` correctly accounts for blockers that live outside the subtree.
- `--dep` is direct only — transitive chains never appear.
- `--dep` output is flat; parent/child relationships of dependents are ignored in rendering.
- Both flags accept partial IDs and emit consistent error messages on miss.
- Empty result sets exit 0 silently rather than erroring.
