## Why

Today `tq` operates on exactly one `.tickets/` store, found by walking up from the cwd (or via `TICKETS_DIR`). In a monorepo that forces one catch-all top-level store, or an awkward `cd`/`TICKETS_DIR` dance to work per-project. Tickets should be scoped to project directories, and an agent standing at the monorepo root should still be able to (a) target a specific project's store and (b) get one overview across every project.

This change adds two composable primitives: `--dir` to target a store, and `ls -r` to aggregate many. It also settles the conceptual question that comes with "one CLI, many stores": whether tickets in different stores can reference one another.

## What Changes

- Add a global `--dir <path>` option: `tq --dir packages/api <command>`. It sets the root the command operates from, overriding walk-up and `TICKETS_DIR`. The target store is `<path>/.tickets/`.
- Add `-r` / `--recursive` to `tq ls`: discover every store at or below the root (the `--dir` path, or cwd) and print a read-only overview grouped by store. Under `--jsonl`, emit a flat stream where each object carries a `store` field.
- Settle cross-store references: **stores are isolated**. `deps`, `links`, and `parent` reference tickets **within the same store only**; ID resolution and cycle detection stay store-local; `-r` neither creates nor traverses edges between stores. (See Out of Scope for the forward path.)
- Settle store-selection precedence: `--dir` (explicit flag) always prevails over `TICKETS_DIR` (ambient env), which beats walk-up. `-r` roots at `--dir` (else cwd) and ignores `TICKETS_DIR`. The store basename stays fixed at `.tickets`. Absent every new input, current behavior is unchanged.

No **BREAKING** changes: `--dir` and `-r` are opt-in; default behavior is untouched.

## Capabilities

### Modified Capabilities

- `ticket-store`: `--dir` targeting and recursive multi-store discovery join walk-up and `TICKETS_DIR` as ways to locate stores; the location-selection precedence is defined (`--dir` prevails).
- `ticket-query`: `tq ls` gains `-r` for a store-grouped (or `--jsonl`-flat-with-`store`-field) overview across a subtree.
- `ticket-relationships`: relationships are declared store-local; cross-store deps/links/parent are rejected.
- `id-resolution`: partial-ID resolution is scoped to a single store; `-r` performs no cross-store resolution.

## Impact

- `store.find_tickets_dir()` gains an explicit-root path; handlers thread `args.dir` instead of always calling the zero-arg resolver. A new discovery walk backs `-r`.
- `query.py` `ls` pipeline gains a recursive branch that loops the existing single-store renderer over discovered stores, plus a `store`-tagged JSONL path.
- No change to the on-disk file format, ID-generation rule, or any relationship semantics *within* a store. The ID prefix already derives from the store's parent directory name, so per-project stores are already ID-namespaced.

## Out of Scope

- **Cross-store references.** Letting `web-3c4d` depend on `api-1a2b` in another store would need qualified IDs, cross-store cycle detection, cross-store archive-safety, and symmetric link back-writes that reach into a second store — which breaks the "a mutation targets exactly one store" invariant. Deliberately deferred. This change draws the isolation boundary cleanly so a later change can widen it without contradicting reference specs.
- `-r` on commands other than `ls` (`tags`, `links`, `show`, `info`, `path`, `deps`). `--dir` covers single-store targeting for all of them; recursive aggregation for those is future work.
- Any `.gitignore`-parsing beyond a pragmatic denylist for discovery (see design).
