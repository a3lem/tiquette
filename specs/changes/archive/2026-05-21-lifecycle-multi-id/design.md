# Design: Lifecycle multi-ID

## Approach

All four transition subparsers (`start`, `close`, `cancel`, `reopen`) already share `_handle_status` via `set_defaults(func=_handle_status, target_status=...)`. The change is local to `src/tiquette/commands/lifecycle.py`.

### Parser

In `register`, change the positional from single to multi:

```python
p.add_argument("id", nargs="+", help="Ticket ID(s)")
```

`args.id` becomes `list[str]`. With `nargs="+"`, argparse already enforces "at least one", so empty invocation stays a usage error.

### Handler: validate-then-mutate

`_handle_status` is restructured into three phases so the atomic guarantee holds:

1. **Resolve + load all.** Resolve every ID in `args.id` (de-duplicated, preserving first-seen order) and `read_ticket` each. On the first `TicketNotFoundError`, write the error to stderr and `sys.exit(1)` — nothing has been written yet.
2. **Pre-flight descendant check** (terminal targets only, no `--force`). Load all tickets once. For each target independently, compute open descendants. Collect targets that have any. If the collection is non-empty, write one error per offending target to stderr and `sys.exit(1)` — still no writes.
3. **Mutate + emit.** For each target in order: cascade its open descendants (force path), set the target's status, write, and print IDs as writes commit. The last-open-child notification for `close` runs per target as today.

De-duplication uses a seen-set keyed on resolved ID so a ticket named twice (directly, or as both an explicit target and a descendant of another target) is written at most once.

## Why fail-fast/atomic

The user chose atomic semantics: a batch that touches the wrong ticket should leave the store untouched so the operator can correct and re-run. This mirrors the existing single-ticket cascade comment ("partial failure leaves the parent open ... re-runnable"). Validating all IDs and all descendant checks before any write extends that property to the batch.

## Output ordering

Writes commit in argument order; within a forced target, descendants commit before the target (unchanged from current single-ID behavior). stdout therefore lists IDs in commit order, satisfying the Transition output requirement.

## Out of scope

No change to `store` helpers, `create`, `edit`, or query commands. No new flags.
