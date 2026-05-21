# Proposal: Lifecycle commands accept multiple ticket IDs

## Why

Closing, cancelling, reopening, or starting several tickets currently means one `tq` invocation each. Batch operations are common (closing a sprint's worth of tickets, reopening a mistaken cancel set), so the lifecycle commands should take more than one ID at a time.

## What Changes

- `tq start`, `tq close`, `tq cancel`, and `tq reopen` accept one or more ticket IDs as positional arguments.
- IDs are resolved and validated up front. **If any ID is unknown, the command exits non-zero and writes nothing** (atomic, fail-fast). No partial mutation.
- For `close`/`cancel` without `--force`, the open-descendant check runs **independently per target**. If any target has open descendants, the whole run aborts before any write.
- `--force` on `close`/`cancel` still cascades to each target's open descendants.
- Transition output prints one affected ID per line, in the order writes are committed.
- Duplicate IDs in a single invocation are de-duplicated (each resolved ticket is written at most once).
- Single-ID usage is unchanged; this is a strict superset of current behavior.

## Capabilities

### Modified Capabilities

- `ticket-lifecycle`: `start`, `close`, `cancel`, `reopen` accept multiple IDs with atomic validation and per-target descendant checks.

## Impact

- `src/tiquette/commands/lifecycle.py`: `id` positional becomes `nargs="+"` for the four transition subparsers; `_handle_status` loops over resolved IDs with up-front validation.
- No storage format change. No change to `create`, `edit`, or query commands.
- `docs/cli-design.md` usage lines for the four commands need updating.

## Out of Scope

- Multi-ID support for non-lifecycle commands (`show`, `edit`, `deps`, etc.).
- Glob/range/`--all` style ID selection — only explicit IDs.
