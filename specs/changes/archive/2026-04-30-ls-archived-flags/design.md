# Design: `ls` flags for archived tickets

## Context

Today, `tq ls` reads tickets via `_load_all_tickets()` in `src/tiquette/commands/query.py`, which calls `store.list_ticket_ids()`. That helper globs `tickets_dir/*.md` only -- archived tickets in `tickets_dir/archive/` are invisible to `ls` regardless of flags.

Argparse for `ls` already uses one `add_mutually_exclusive_group()` (for `--ready` / `--blocked`). Status/resolution filters (`--status`, `--completed`, `--canceled`) are independent flags whose mutual exclusion is implicit through the if/elif chain in `_handle_ls`.

The new flags introduce a second, orthogonal axis: source. `--archived` and `--all` change which tickets are loaded; the existing filters then operate on whatever was loaded.

## Goals

- `--archived` and `--all` available as source selectors on `ls`.
- `-a` is short for `--all`; `-A` is short for `--assignee` (was `-a`).
- Source axis composes cleanly with existing status/resolution and stackable filters.
- Archived ticket files are loaded from `.tickets/archive/` without altering active-ticket code paths.

## Non-Goals

- Changing how tickets are archived or moved (`tq archive` is untouched).
- Letting `--ready` / `--blocked` show archived tickets (archived = closed, so the result would always be empty -- not worth special-casing).
- Inventing a new ticket-source abstraction beyond what `ls` needs.

## Decisions

### Source enumeration: extend `list_ticket_ids` with a `source` parameter

Add an enum-typed parameter to `store.list_ticket_ids`:

```python
TicketSource = T.Literal["active", "archived", "all"]

def list_ticket_ids(tickets_dir: Path, source: TicketSource = "active") -> list[str]:
    ...
```

- `"active"` (default): glob `tickets_dir/*.md` (current behavior, unchanged).
- `"archived"`: glob `tickets_dir/archive/*.md`.
- `"all"`: union of both.

`_load_all_tickets()` in `query.py` gains the same parameter and forwards it. For `"all"`, it calls `read_ticket` against the correct directory per ID (active vs archive). The simplest implementation: build two dicts (one per source) and merge, since `read_ticket` takes a `tickets_dir` argument.

ID collisions between active and archive shouldn't occur (archive is a one-way move), but if they do, active wins. Document this as an invariant rather than a runtime check -- it would indicate corruption, which the existing autofix path already covers.

**Alternatives considered:**

- *Two separate functions (`list_archived_ticket_ids` etc.)*. Rejected: callers would still need a switch on the source flag; same complexity, more surface.
- *Glob recursively in `list_ticket_ids`*. Rejected: would silently include any future subdirectories. Explicit beats implicit.

### Argparse: source group + short-flag rename

In `query.py` parser setup:

```python
source_group = p_ls.add_mutually_exclusive_group()
source_group.add_argument("-a", "--all", action="store_true",
                          help="Include archived tickets")
source_group.add_argument("--archived", action="store_true",
                          help="Show only archived tickets")

p_ls.add_argument("-A", "--assignee", help="Filter by assignee")
```

Mutual exclusion between `--all` and `--archived` is enforced by argparse and produces a non-zero exit with a standard error message.

The status/resolution flags (`--status`, `--completed`, `--canceled`) remain a separate concern. They are not currently in a mutually exclusive group, and the spec does not require enforcing exclusion between them in this change -- their mutual exclusion is implicit (the `if/elif` chain picks the first that matches). Keep that as-is.

**Alternatives considered:**

- *Put `--all`, `--archived`, `--status`, `--completed`, `--canceled` all in one group*. Rejected: would force a behavior change for users relying on combinations that currently silently work, and the spec explicitly says source and status/resolution are independent axes.
- *Use `nargs='?'` so `-a` could optionally take an assignee value*. Rejected: contradicts mirroring `ls -a`; ambiguous parsing.

### `_handle_ls` dispatch

At the top of `_handle_ls`, resolve the source:

```python
if args.archived:
    source: TicketSource = "archived"
elif args.all:
    source = "all"
else:
    source = "active"

all_tickets = _load_all_tickets(tickets_dir, source=source)
```

The remainder of the function (status filtering, ready/blocked, stackable filters, sorting, tree rendering, output) is unchanged. `_is_blocked` and tree rendering operate on whatever dict they receive.

One implication: with `--all`, archived tickets become candidates for tree rendering. A closed-and-archived parent of an active child would render as a context heading. This is intentional and matches the cross-axis composition spec.

### Tests

Add tests under the existing `tests/` layout (mirror the structure used by current `ls` tests). Cover:

- Default excludes archived (regression guard).
- `--archived`, `-a`/`--all`, combinations with `--completed`/`--canceled`/`--tag`.
- `--all --archived` rejected.
- `-A "Alice"` works for assignee; `-a "Alice"` no longer interpreted as assignee filter (will be parsed as `--all` followed by a positional, which ls does not accept -- argparse exits non-zero).

## Risks / Trade-offs / Limitations

- *[Risk] Existing scripts using `tq ls -a <name>` break silently if `<name>` happens to be omitted (e.g., `tq ls -a | grep ...` previously errored on missing assignee value, now succeeds with a different output set).* → Mitigation: announce in CHANGELOG under the version bump; the breaking nature is called out in the proposal.
- *[Trade-off] `--all` loads twice as many ticket files as default `ls`.* → Acceptable: archive is small relative to active set in practice, and lazy-loading would complicate the dispatch for negligible gain.
- *[Limitation] `--ready --archived` returns empty (archived tickets are closed by definition).* → Acceptable: composition is uniform; no special error message needed.

## Open Questions

None.
