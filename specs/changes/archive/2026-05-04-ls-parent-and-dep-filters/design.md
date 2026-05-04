# Design: `--parent` and `--dep` filters for `tq ls`

## Context

`tq ls` already exposes a layered filtering pipeline in `src/tiquette/commands/query.py::_handle_ls`:

1. **Source axis** (active / archived / all) loads `all_tickets`.
2. **Primary filter** (one of `--ready`, `--blocked`, `--status`, or "all") seeds the working set.
3. **Stackable filters** (`--assignee`, `--tag`, `--type`) prune the working set.
4. **Sort** by priority or mtime.
5. **Output** branches between `--jsonl` (flat) and the default tree renderer.

The default tree renderer constructs a parent/child tree from `Ticket.parent` pointers, climbs upward to add "context parent" headings when a filtered child has an unfiltered ancestor, and renders with box-drawing characters using `_format_ticket_line[_with_deps]`.

`--parent <id>` and `--dep <id>` add two new candidate-set filters in front of step 3, leaving steps 3–5 unchanged in behavior except for one rendering switch (tree off for `--dep`) and one rendering tweak (tree rooted at `<id>` for `--parent`).

## Goals / Non-Goals

**Goals**

- Add `--parent <id>` and `--dep <id>` as scoping filters that restrict the working set.
- Resolve `<id>` through the same partial-ID mechanism (`resolve_id`) used by `show`, `info`, `deps`, etc.
- Stack cleanly with every existing filter and the source axis.
- Keep `--parent` rendering consistent with the existing tree (root + nested children).
- Keep `--dep` rendering flat — dependency relationships are orthogonal to parent/child trees.
- Make the two flags mutually exclusive at argparse level.

**Non-Goals**

- No transitive `--dep` (out of scope; use `--dep` repeatedly or add a `--transitive` flag in a future change).
- No new JSONL fields or schema changes.
- No changes to other commands (`deps`, `show`, `info`).
- No reverse-dep cache or index — both filters are O(N) over loaded tickets.

## Decisions

### 1. Argparse wiring

Add a new mutually-exclusive group on the `ls` subparser:

```python
scope_group = p_ls.add_mutually_exclusive_group()
scope_group.add_argument("--parent", metavar="ID",
                        help="Show ticket <ID> and its descendants as a tree")
scope_group.add_argument("--dep", metavar="ID",
                        help="Show tickets that directly depend on <ID> (flat list)")
```

This group is independent of the existing `ready`/`blocked` group and the `all`/`archived` group. argparse enforces `--parent`/`--dep` mutual exclusion automatically; cross-group combinations remain legal.

**Alternatives considered:**

- *Single `--scope <kind>:<id>` argument* — rejected as awkward at the CLI; two flags read naturally.
- *Reuse `--ready`/`--blocked` mutually-exclusive group* — rejected; `--ready --parent epic-001` is a useful combination ("what's ready under this epic"), and we want to keep them stackable.

### 2. ID resolution

Resolve `<id>` once, immediately after the source axis is determined:

```python
if args.parent or args.dep:
    raw_id = args.parent or args.dep
    try:
        scope_id = resolve_id(raw_id, tickets_dir)
    except (TicketNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
```

`resolve_id` already resolves against the active tickets directory. For consistency with the rest of `tq ls`, the resolution scope is the same set as the loaded source: when `--archived` or `--all` is in effect, resolution must look there too.

**Implementation note:** `resolve_id` currently resolves against the active dir. To honor the source axis without forking the function, pass an explicit search set built from `all_tickets.keys()`, or extend `resolve_id` to accept a source. The simpler local fix: after loading `all_tickets`, do partial-ID resolution against `all_tickets.keys()` directly (mirror `resolve_id`'s prefix/contains logic in a small helper), and reuse `resolve_id` only when the source is "active".

Pick the second approach: add a `_resolve_in_set(raw_id, all_tickets)` helper local to `query.py` that performs the same prefix-then-contains match `resolve_id` does, raising the same exceptions. Keep `resolve_id` untouched for now.

**Alternatives considered:**

- *Always resolve against active only* — rejected; `tq ls --archived --parent <archived-id>` would never work.
- *Modify `resolve_id` signature globally* — rejected as scope creep; this change shouldn't touch unrelated commands.

### 3. `--parent`: candidate-set computation

After loading `all_tickets` and resolving `scope_id`:

1. Build a children index: `children_by_parent: dict[str, list[str]] = {}` from `all_tickets`.
2. BFS from `scope_id`, collecting `descendants: set[str]`.
3. `candidate_ids = {scope_id} | descendants`.

Then apply the existing primary filter (`--ready` / `--blocked` / `--status` / none) and stackable filters, but restrict the input to tickets whose ID is in `candidate_ids`. Concretely, wrap the existing primary-filter loop:

```python
candidates = [t for t in all_tickets.values() if t.id in candidate_ids]
# then apply ready/blocked/status as today, but iterating candidates instead of all_tickets.values()
```

`_is_blocked` continues to consult the full `all_tickets` so that out-of-scope deps still count toward blocked-ness — a child that depends on something outside the epic is still blocked.

**Alternatives considered:**

- *Restrict `all_tickets` itself to the candidate set before any filtering* — rejected; would silently change `--ready`/`--blocked` semantics by hiding out-of-scope blockers.

### 4. `--parent`: tree rendering rooted at `<id>`

The existing renderer climbs each filtered ticket's `parent` chain to add context-parent headings. Without modification, `--parent epic-001` could climb above `epic-001` if epic-001 has its own parent, which is wrong — the user asked for the tree under `epic-001`, not its broader ancestry.

Solution: pass `scope_id` into the context-parent climb and stop the walk when `pid == scope_id`. One-line change in the existing climb loop:

```python
while pid and pid not in filtered_ids:
    if pid == scope_root:
        context_parents.add(pid)
        break
    context_parents.add(pid)
    parent_ticket = all_tickets.get(pid)
    pid = parent_ticket.parent if parent_ticket else None
```

`scope_root` is `scope_id` when `--parent` is set, otherwise `None` (existing behavior).

When `scope_id` itself does not survive the stackable filters (e.g., `--parent epic-001 --status completed` with an open epic), it appears as a context heading at the root — same convention used elsewhere. When `scope_id` survives, it appears as a normal entry at the root. Either way it's the root, because its real parent is excluded from `visible_ids` by the candidate-set restriction.

The current code already suppresses context-parent climbing when `--ready` or `--blocked` is set. Under `--parent`, we want context climbing of `scope_id` itself to remain enabled even alongside `--ready`/`--blocked`, so the named root is never silently dropped. Adjust the guard:

```python
if not args.ready and not args.blocked:
    # full climb (existing behavior)
elif args.parent:
    # climb only to add scope_root if needed
```

**Alternatives considered:**

- *Mutate `all_tickets[scope_id].parent = None` in a copy* — works but mutation-via-copy is uglier than parameterizing the climb.
- *Build a separate scoped dict and re-run the whole renderer against it* — rejected as duplicative.

### 5. `--dep`: candidate-set computation and flat rendering

After loading `all_tickets` and resolving `scope_id`:

```python
candidates = [t for t in all_tickets.values() if scope_id in t.deps]
```

Then apply primary filter (`--ready`/`--blocked`/`--status`/none) and stackable filters as today.

For output, branch before the tree builder:

```python
if args.dep:
    # flat rendering
    for t in filtered[: args.limit] if args.limit else filtered:
        print(_format_ticket_line_with_deps(t))
    return
```

This skips `_build_children_map`, context-parent climbing, and `_print_ls_tree` entirely. JSONL output is unaffected (it's already flat for everyone).

**Alternatives considered:**

- *Render dependents inside their parent-tree context* — rejected per user input; mixes two relationship axes and clutters output.
- *Render an inverted dep tree rooted at `<id>`* — rejected; that's effectively what an inverse `tq deps` would be, a separate feature.

### 6. Filter pipeline ordering (final shape)

```
load (source axis)
  └─ resolve scope_id              (--parent / --dep only)
  └─ scope to candidate_ids        (--parent: descendants ∪ scope_id)
                                   (--dep:    {t | scope_id in t.deps})
  └─ primary filter                (--ready / --blocked / --status / none)
  └─ stackable filters             (--assignee / --tag / --type)
  └─ sort                          (priority | mtime)
  └─ output                        (--jsonl flat | --dep flat | tree)
```

The scope step lives between load and primary filter. Everything downstream is unchanged in semantics; only the input set narrows.

### 7. Error handling

- Unknown `<id>` (no match): print `ticket '<id>' not found` to stderr, exit 1. Matches `show`/`info`/`deps`.
- Ambiguous partial `<id>`: `resolve_id`-style `ValueError` with candidate list, exit 1.
- argparse handles `--parent` and `--dep` together (mutually exclusive group emits "not allowed with argument" and exits 2).
- Missing value (`tq ls --parent` with no arg): argparse emits "expected one argument" and exits 2.
- Empty result set (no descendants for `--parent leaf-id`, no dependents for `--dep`): print nothing, exit 0. Matches `tq ls` with empty filter results.

### 8. JSONL behavior

`--parent` / `--dep` narrow the candidate set before JSONL emission. Field schema unchanged. Order follows the `--sort` flag. `--parent` includes the named root in the JSONL output if it passes filters.

### 9. Test plan

Add unit tests in `tests/test_cli_query.py` alongside the existing `test_ls_*` and `test_ready_*` tests. Use the same `tmp_path` + CLI invocation harness already in place. One test per delta scenario, plus the edge cases listed in `tasks.md` (leaf-only `--parent`, archived-source resolution, transitive-exclusion proof for `--dep`, partial-ID resolution, unknown-ID error for both, argparse mutual exclusion).

Naming convention to match the file:

- `test_ls_parent_*` for `--parent` scenarios
- `test_ls_dep_*` for `--dep` scenarios
- `test_ls_parent_and_dep_mutually_exclusive` for the cross-flag check

Add an end-to-end manual scenario at `tests/test-drives/10-scoping-by-parent-and-dep.md` exercising both flags against a small board with a cross-cutting dependency that crosses the subtree boundary — this is the only integration-style coverage that catches the "out-of-scope blocker still counts" subtlety in step (3) of the design.

## Risks / Trade-offs / Limitations

- **Performance scales O(N) per filter on every invocation.** No reverse-dep index. → Acceptable; ticket counts in real stores are small (hundreds, not millions). Revisit only if profiling shows `tq ls` slow on large stores.
- **`--dep` is direct only.** Users wanting transitive impact analysis must rerun or wait for a future `--transitive`. → Document in `--help` text. Direct-only is the safer default and matches the user's choice.
- **Tree rooting at `<id>` hides legitimate ancestor context.** A user running `--parent task-005` (a mid-tree node) sees `task-005` as the root with no breadcrumb to the real ancestry. → Accepted; that's the contract of `--parent`. Users wanting ancestry can run `tq show <id>` which lists the parent.
- **`--parent` candidate set includes `<id>` itself.** When filtered by `--ready`, an open epic with ready children will still show the epic as a context heading. Users may expect "ready tickets under epic" to exclude the epic itself. → This is consistent with the rest of `tq ls` tree behavior (parents shown as context); document by example in `--help` if confusion arises.
- **Resolution scope coupled to source axis.** `tq ls --parent <archived-id>` (without `--archived`/`--all`) will fail to resolve. → Intentional, matches user mental model: "I'm listing active; the archived parent isn't in scope."

## Open Questions

None. Behavior decisions confirmed via AskUserQuestion in the proposal phase.
