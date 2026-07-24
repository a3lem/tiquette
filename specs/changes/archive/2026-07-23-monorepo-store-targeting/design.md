# Design: monorepo store targeting

## Context

`tq` resolves one store per invocation via `store.find_tickets_dir()` (zero-arg): `TICKETS_DIR` env, else walk up from cwd for `.tickets/`. Every handler calls the zero-arg resolver, then reads/writes that single directory. `read_ticket`, `write_ticket`, `resolve_id_in_dir`, and cycle detection all operate on one flat `.tickets/`; the only recognized subdirectory is `archive/`, handled through the active/archived/all source axis.

The ID prefix already derives from `tickets_dir.parent.name` (`generate_id` → `abbreviate`). So a `.tickets/` placed at `packages/api/` already mints `api-...` IDs. The monorepo model is latent in the ID scheme; this change makes it a first-class targeting story without touching the file format or per-store semantics.

## Goals

- `--dir <path>` targets a single store, for every command.
- `ls -r` aggregates all stores under a root into one read-only overview.
- Draw the cross-store reference boundary explicitly: stores are isolated.
- Zero behavior change when neither flag is present.

## Non-Goals

- Cross-store deps/links/parent (see Out of Scope in the proposal).
- `-r` on commands other than `ls`.
- A moved-ticket / re-home command, or changing `archive`.

## Two orthogonal axes

Store selection separates into two independent concerns:

| Axis | Question | Set by |
|------|----------|--------|
| Location | which store? | `--dir <path>` · `TICKETS_DIR` (full path) · walk-up |
| Recursion | one store or many? | `-r` |

`--dir` and `TICKETS_DIR` both fully name a store, so they *compete* on the location axis — `--dir` wins. `-r` supersedes the single-store location inputs, rooting at `--dir` (else cwd) and ignoring `TICKETS_DIR`. The store's basename stays fixed at `.tickets` (a configurable name was considered and dropped — see Alternatives).

## Decisions

### Store resolution and `--dir` threading

`--dir` is a **global** option on the top-level parser, declared before `add_subparsers`, so it lands on the parsed namespace (`args.dir`) regardless of subcommand. Replace direct `find_tickets_dir()` calls in handlers with a single resolver that reads `args`:

```python
def resolve_store(args) -> Path:
    if args.dir is not None:
        return Path(args.dir) / ".tickets"   # explicit: no walk-up, ignore TICKETS_DIR
    return find_tickets_dir()                 # TICKETS_DIR (exact path), else walk-up
```

Single-store precedence, most-explicit first:

1. `--dir <path>` → `<path>/.tickets/`. No walk-up; `TICKETS_DIR` ignored. **A typed flag beats ambient env** — the universal flags > env > default order. `--dir` always prevails. This is the answer to "which wins if both are set."
2. `TICKETS_DIR` → that exact path.
3. walk up from cwd for a `.tickets/` directory.

- For read commands, a missing target raises `TicketsNotFoundError` (existing "no .tickets directory found" path).
- For `create`, the init target becomes the resolved store instead of hardcoded `cwd/.tickets/`. The existing catch-`TicketsNotFoundError`-then-`mkdir` logic (`lifecycle.py:90-93`) generalizes to `resolve_store(args)`, so `--dir` flows through create.

`--dir` names a **project/tree directory**, not a store directory. This is what makes `-r` compose (recursing "from" a project dir means "find stores under it"; recursing from inside a store dir would be nonsense). It also keeps a clean split from `TICKETS_DIR`, which points *at* a store.

### Recursive discovery and pruning

`-r` walks the tree from the root (the `--dir` path, else cwd) with `os.walk`, pruning `dirnames` in place:

- Skip a static denylist of VCS/dependency/build dirs: `.git`, `node_modules`, `.venv`, `__pycache__`, `.tox`, `dist`, `build`, `.mypy_cache`, `.ruff_cache`.
- When a directory contains a `.tickets/` child, register that directory as a store and remove `.tickets` from `dirnames` so the walk does not descend into the store (its `archive/` is not a separate store). Keep descending into the directory's *other* children, so a project that has tickets can still contain sub-projects that have their own tickets.
- `TICKETS_DIR` is ignored under `-r` — it pins one store, incompatible with discovery.

Stores are ordered by `os.path.relpath(store_parent, root)`, lexicographically. The root's own store relpaths to `.`.

The denylist is pragmatic, not `.gitignore`-aware. Respecting `.gitignore` (skip anything git ignores when inside a repo) is a reasonable later enhancement; the spec scenario only pins `.git` and `node_modules`, which the denylist covers.

### `ls -r` rendering

Reuse the existing single-store pipeline per discovered store. For each store: load via `_load_all_tickets(store_dir, source)`, run the existing filter/sort/tree render, but capture output under a heading line (the store's relpath). Omit a store whose filtered result is empty. `--limit` applies within each store (each section renders its own capped listing) — simplest, and matches "each store renders its normal `ls`". A global cap across the aggregate would need cross-section bookkeeping for little gain.

`-r` is mutually exclusive with `--parent`/`--dep`, validated in `_handle_ls` (argparse's existing `scope_group` already makes `--parent`/`--dep` exclusive with each other; adding `-r` to that group is not possible since `-r` is otherwise independent, so a handler guard raises the error).

`--jsonl` + `-r`: emit a flat stream, one object per ticket across all stores, each object extended with `"store": <relpath>`. This is the agent-facing overview format — machine-parseable without headings. The base `_ticket_to_dict` is unchanged; the `store` key is added only on this path, so non-recursive `--jsonl` output is byte-for-byte unchanged.

### Cross-store isolation is (mostly) free

Mutations already resolve targets against the single mutated store (`resolve_id_in_dir`) and detect cycles within it. `--dir` only changes *which* store that is. So isolation is the existing default; the ticket-relationships and id-resolution deltas document and test the boundary rather than adding enforcement code. The one guarantee to preserve: never let `-r` machinery feed a multi-store candidate set into a mutation or a single-ticket resolve.

## Alternatives Considered

- **`--dir` walks up from its path** (like the default does from cwd). Rejected: reintroduces implicit magic under a flag whose whole point is explicitness, and collides with `-r`'s "recurse down from here". `--dir` is a precise pointer; plain invocation keeps the walk-up.
- **`--dir` points at a `.tickets/` directory** (mirroring `TICKETS_DIR`). Rejected: breaks `-r` composition and duplicates `TICKETS_DIR`. Two distinct tools: `TICKETS_DIR` = the store; `--dir` = the tree location.
- **`-r` as a global flag on all read commands.** Deferred: `ls` is the overview the use case asks for. A global `-r` would also force a read-only guard on every mutation. Scoping `-r` to `ls` sidesteps that entirely for v1.
- **Cross-store references now.** Rejected for this change — see proposal Out of Scope. The isolation boundary here is drawn so a later change can widen it (qualified IDs) without contradicting archived reference specs.
- **Configurable store name (`TICKETS_DIR_NAME`).** Considered — a monorepo standardizing on `tickets/` or `my-tickets/` — and dropped. It adds a second env var that shadows and interacts with `TICKETS_DIR` (a path vs a basename), widening the config surface for a convenience the fixed `.tickets` name already serves. `--dir` + `.tickets` covers the monorepo need; the name stays fixed.
- **`.gitignore`-aware discovery.** Deferred in favor of a static denylist; revisit if real trees put stores behind non-standard ignore patterns.

## Verification

Automated scenario tests cover each requirement (see tasks.md). For an end-to-end human walkthrough, `tests/test-drives/11-monorepo-stores.md` builds a throwaway monorepo (`packages/api`, `packages/web`, a root store) and exercises: `--dir` create + prefix, `ls -r` grouping and ordering, `-r --jsonl` `store` tagging, the cross-store `--dep` rejection, and `--dir` vs `TICKETS_DIR` precedence. The existing test-drive harness points `TICKETS_DIR` at a temp dir; this drive instead `cd`s into a temp tree and drives `--dir`/`-r`, using `TICKETS_DIR` only in the precedence step.

## Impact

- `store.py`: add explicit-root resolution and a `discover_stores(root)` walker. `find_tickets_dir()` stays as the no-`--dir` path.
- `cli.py`: add global `--dir` to the top-level parser.
- `query.py`: add `-r`/`--recursive` to the `ls` subparser; branch `_handle_ls` into a recursive path (loop stores → per-store render / store-tagged jsonl); add the `-r` × `--parent`/`--dep` guard.
- `lifecycle.py` (create): route the init target through the resolved root.
- Every handler that calls `find_tickets_dir()` switches to the shared resolver so `--dir` works uniformly.
- Docs: `docs/cli-design.md` (flag reference), `HELP_TEXT`, `CHANGELOG.md`.
