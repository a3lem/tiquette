# Cascade close/cancel and canceled checkbox

## Why

`tq cancel` silently closes a parent without checking its open children, leaving a graph with a closed parent and active children. `tq close` already errors on open descendants but offers no way to force the closure when the user genuinely wants to abandon a whole subtree. Canceled tickets render as `[x]`, indistinguishable from completed work in `tq ls`.

## What Changes

- `tq cancel` rejects a ticket with open descendants (same check as `tq close`).
- `tq cancel` accepts `-f` / `--force` to override the rejection. With `--force`, all open descendants are auto-cancelled (status `closed`, resolution `canceled`).
- `tq close` accepts `-f` / `--force` to force-close a ticket with open descendants. With `--force`, all open descendants are auto-closed as `completed`.
- `tq ls` renders canceled tickets with `[~]` instead of `[x]`. Completed tickets keep `[x]`.
- **BREAKING**: `tq cancel` of a parent with open descendants now exits non-zero (was: silently succeeded).
- **BREAKING**: `tq ls` line format for canceled tickets changes from `[x]` to `[~]`.

## Capabilities

### Modified Capabilities

- `ticket-lifecycle`: `cancel` gains descendant rejection and cascade; `close` gains cascade. Both grow a `--force` flag.
- `ticket-query`: list line format distinguishes canceled (`[~]`) from completed (`[x]`).

## Impact

- Code: `src/tiquette/commands/lifecycle.py` (cancel/close handlers, parser flags), `src/tiquette/commands/query.py` (`_STATUS_CHECKBOX` -> resolution-aware formatter).
- Tests: `tests/test_cli_lifecycle.py`, `tests/test_cli_query.py`.
- Docs: `docs/cli-design.md` if it documents the flags; CHANGELOG.
- User-visible: `tq cancel parent` without `-f` is a new error path. Scripts that relied on cancel being unconditional must add `-f`. `tq ls` parsers that match `[x]` for "closed" should also match `[~]`.
