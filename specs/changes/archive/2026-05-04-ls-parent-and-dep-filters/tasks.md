# Tasks: `--parent` and `--dep` filters for `tq ls`

## Argparse

- [x] Add `--parent ID` / `--dep ID` mutually-exclusive group on the `ls` subparser in `src/tiquette/commands/query.py::register`
- [x] Help text describes scoping behavior and direct-only semantics for `--dep`

## Resolution

- [x] Add `_resolve_in_set(raw_id, all_tickets)` helper in `query.py` that mirrors `resolve_id`'s prefix-then-contains logic against the loaded source set
- [x] Wire resolution into `_handle_ls` immediately after `_load_all_tickets`, gated on `args.parent or args.dep`
- [x] On `TicketNotFoundError` / `ValueError`, print to stderr and exit 1 (match `show`/`info`/`deps`)

## `--parent` scoping

- [x] Build `children_by_parent` index from `all_tickets`
- [x] BFS from `scope_id` to collect descendants; candidate set is `{scope_id} | descendants`
- [x] Apply candidate set as input to the existing primary-filter loop (do not narrow `all_tickets`; `_is_blocked` must still see out-of-scope deps)
- [x] Parameterize the context-parent climb with `scope_root` so it stops at `scope_id`
- [x] Allow `scope_id` itself to appear as a context heading even under `--ready` / `--blocked`

## `--dep` scoping

- [x] Filter candidate set: `[t for t in all_tickets.values() if scope_id in t.deps]`
- [x] Branch before tree builder: render flat using `_format_ticket_line_with_deps`, honoring `--limit`
- [x] JSONL path needs no special-case (already flat)

## Validation

- [x] argparse handles `--parent` + `--dep` mutual exclusion (no manual check needed)
- [x] Empty result set prints nothing and exits 0

## Tests (`tests/test_cli_query.py`)

- [x] `--parent` happy path: shows root + descendants, hides unrelated tickets
- [x] `--parent` renders root unindented and children indented with box-drawing chars
- [x] `--parent` accepts partial ID
- [x] `--parent` with unknown ID exits non-zero with "not found"
- [x] `--parent` on a leaf shows only the leaf, no indented rows
- [x] `--parent` stacks with `--ready` (scopes ready set to subtree)
- [x] `--parent` stacks with `--status` (status filter applied within subtree)
- [x] `--parent` stacks with `--tag` (tag filter applied within subtree)
- [x] `--parent` honors `--archived` / `--all` source axis (resolves and lists archived subtree)
- [x] `--parent` does not climb above `scope_id` when `scope_id` itself has a parent
- [x] `--dep` happy path: lists direct dependents only
- [x] `--dep` excludes transitive chain (depth-2 dependent not shown)
- [x] `--dep` excludes the target ticket itself
- [x] `--dep` returns empty when no direct dependents exist
- [x] `--dep` accepts partial ID
- [x] `--dep` with unknown ID exits non-zero with "not found"
- [x] `--dep` renders flat (parent of a dependent does not appear as context heading)
- [x] `--dep` stacks with `--status`
- [x] `--dep` stacks with `--tag`
- [x] `--parent` and `--dep` together exit non-zero (argparse mutual exclusion)

## Test drive

- [x] Add `tests/test-drives/10-scoping-by-parent-and-dep.md` exercising both flags end-to-end against a small board

## Docs

- [x] Update `docs/cli-design.md` `ls` section with the two new flags
- [x] Add CHANGELOG.md entry under `## [Unreleased]`

## Verification

- [x] Tests for requirement: List filtered by parent
- [x] Tests for requirement: List filtered by dependent

## Notes

- `_is_blocked` must continue consulting the unrestricted `all_tickets`; otherwise `--parent` would silently make subtree tickets look "ready" when they actually depend on out-of-scope work.
- `resolve_id` is left untouched. The local `_resolve_in_set` helper avoids cross-command churn.
