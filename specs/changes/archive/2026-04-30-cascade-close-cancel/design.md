## Context

Lifecycle commands live in `src/tiquette/commands/lifecycle.py`. The current `_handle_status` dispatcher branches on `args.command` for `start`/`close`/`cancel`/`reopen`. Only `close` consults `_find_open_descendants`; `cancel` writes through unconditionally. Listing renders status with a flat dict `_STATUS_CHECKBOX` in `src/tiquette/commands/query.py`, keyed by status only -- it cannot distinguish completed from canceled because both share `status="closed"`.

Tests covering the affected behavior live in `tests/test_cli_lifecycle.py` (cancel, close, descendant rejection) and `tests/test_cli_query.py` (line format scenarios).

## Goals / Non-Goals

**Goals:**

- Unify descendant handling between `close` and `cancel`.
- Add `-f` / `--force` to both, cascading to *open* descendants only.
- Differentiate canceled (`[~]`) from completed (`[x]`) in `tq ls`.

**Non-Goals:**

- No new flag on `start` or `reopen`.
- No re-cancel of already-closed tickets even when force-cascading. Already-closed descendants are skipped, regardless of their resolution.
- No change to JSON output or to `tq show`.

## Decisions

### Argparse: shared flag for close and cancel

Add `-f` / `--force` to both `close` and `cancel` subparsers in the existing `for name, helptext in [...]` loop. Branch on `name in ("close", "cancel")` to attach the flag, keeping `start` and `reopen` flagless.

```python
for name, helptext in [...]:
    p = subparsers.add_parser(name, help=helptext)
    p.add_argument("id", help="Ticket ID")
    if name in ("close", "cancel"):
        p.add_argument("-f", "--force",
                       action="store_true",
                       help="Force closure; cascade to open descendants")
    p.set_defaults(func=_handle_status)
```

`args.force` is `False` for `start`/`reopen`, but those branches never read it.

**Alternatives considered:** Two separate handler functions per command. Rejected -- the dispatch is tiny and the cascade logic is identical.

### Cascade: reuse `_find_open_descendants`, write each one

Both `close` and `cancel` call `_find_open_descendants(ticket.id, tickets_dir)`. Behavior:

- If the list is empty, proceed as today.
- If non-empty and `--force` is not set, error to stderr and exit 1 (current `close` behavior, now also for `cancel`).
- If non-empty and `--force` is set, read each descendant, apply the same status/resolution as the parent (`closed`/`completed` for close, `closed`/`canceled` for cancel), and `write_ticket` it.

Cascade applies the parent's resolution uniformly. We do not preserve a descendant's prior open state distinction (e.g., an `in_progress` child becomes `closed`, same as an `open` one). Already-closed descendants are not in the list returned by `_find_open_descendants`, so they are untouched -- that satisfies the "leaves already-closed descendants untouched" scenarios.

Order of writes: cascade descendants first, then the parent. This means a partial failure leaves the parent open (resumable) rather than closed-with-orphans. No transaction layer exists; this is the best we can do with file writes.

**Alternatives considered:** Recursive cascade calling `_handle_status` per descendant. Rejected -- adds spurious stdout lines per child and re-reads files we already loaded.

### Cancel error message: match close

Cancel's rejection uses the same message format as close: `error: <id> has open descendants: <id1>, <id2>`. Tests assert `"has open descendants"` so reusing the string keeps test parity.

### Notification suppression on cascade

`_check_last_open_child` runs only on `close` of a leaf-or-explicitly-closed ticket. When force-closing a parent, the parent's parent (if any) might newly become childless. Run the check on the *root* of the cascade (the user-named ticket), not on each cascaded descendant -- the descendants' parent is being closed in the same operation, so notifying about them would be noise.

### Stdout output

Emit one ID per line for every ticket whose status changed: each cascaded descendant immediately after its successful write, then the primary ticket last. Order matches write order so that if a later write fails, stdout reflects exactly what landed on disk. The "Transition output" requirement gains scenarios for the cascade case.

### Query: resolution-aware checkbox

Replace the `_STATUS_CHECKBOX` dict with a small function:

```python
def _checkbox(t: Ticket) -> str:
    if t.status == "open":
        return "[ ]"
    if t.status == "in_progress":
        return "[/]"
    if t.status == "closed":
        return "[~]" if t.resolution == "canceled" else "[x]"
    return "[?]"
```

`completed` and any unset/unknown resolution map to `[x]`. Only the explicit string `"canceled"` flips to `[~]`. This is a deliberate default -- legacy tickets without `resolution` set still render as `[x]`.

`_format_ticket_line` calls `_checkbox(t)` instead of dict lookup.

**Alternatives considered:** Two-key dict `(status, resolution)`. Rejected -- the `None`/`"completed"` collapse is simpler as an `if`.

## Risks / Trade-offs / Limitations

- [BREAKING: `tq cancel parent` now errors when descendants are open] → Document in CHANGELOG. Users who relied on cancel being unconditional add `-f`.
- [BREAKING: `[x]` no longer means "closed, any resolution" in `ls`] → Document in CHANGELOG. Downstream parsers that match on the checkbox need to accept both `[x]` and `[~]` for closed.
- [Partial failure during cascade leaves a half-closed subtree] → Acceptable: re-running the same command picks up where it left off, since cascade-eligible descendants are still open. No rollback needed.
- [`_find_open_descendants` reads every ticket file in `.tickets/` per call] → Already the case for `close`; not a regression. Out of scope for this change.

## Open Questions

None.
