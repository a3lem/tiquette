# Design: Split Closed Status

## Context

Today the lifecycle has three observable statuses (`open`, `in_progress`, `closed`) and a separate `resolution` field that is meaningful only when status is `closed`. The pair `(status=closed, resolution=completed|canceled)` encodes terminal outcome in two fields.

Two-field encoding leaks across the codebase:

- `commands/lifecycle.py` writes both fields on close/cancel and clears both on reopen.
- `commands/query.py` consults both fields for the checkbox glyph, the `--completed` / `--canceled` filters, and the `archive` eligibility check.
- `store.py` lists `resolution` in `_NULLABLE_FIELDS` and `Ticket.resolution`.
- The CLI help and `docs/cli-design.md` describe the pair.

Tickets in the wild already have the old shape, so any rollout requires a one-shot migration. `tq autofix` already exists for exactly this purpose.

## Goals / Non-Goals

**Goals:**

- Single source of truth for terminal outcome: `status` ∈ `{open, in_progress, completed, canceled}`.
- Hard removal of the `resolution` concept from code, schema, frontmatter, JSON output, and CLI help.
- One-step migration via `tq autofix` so users can upgrade in place.
- Update tests in lockstep with code so the suite stays green every commit.

**Non-Goals:**

- Renaming `close` / `cancel` / `reopen` commands (separate change).
- Aliasing `--status closed`, `--completed`, or `--canceled` for backwards compatibility. Hard break with a clear migration tool.
- Touching capabilities that don't reference status terminality (`ticket-fields`, `ticket-relationships`, `id-resolution`, `ticket-validate`).

## Decisions

### Terminology: "terminal" replaces "closed"

Internally and in user-facing diagnostics, replace "closed" with "completed or canceled" or "terminal". A small helper makes the intent obvious and removes string-comparison drift.

```python
TERMINAL_STATUSES: frozenset[str] = frozenset({"completed", "canceled"})

def is_terminal(t: Ticket) -> bool:
    return t.status in TERMINAL_STATUSES
```

Place this constant + helper in `store.py` next to the existing schema constants. Every site that currently does `t.status == "closed"` or `t.status != "closed"` rewrites to call the helper. There are roughly a dozen such sites — they were inventoried in the spec deltas.

**Alternatives considered:** Inline `t.status in {"completed", "canceled"}` everywhere. Rejected — the predicate gets used 10+ times; one named function reads better and is easier to grep for than a bare set.

### Schema: drop `resolution`, expand `status` enum

In `store.py`:

- Remove `resolution` from `Ticket` (the dataclass field, the YAML round-trip, `_NULLABLE_FIELDS`, the JSON dump).
- Update the `status` enum constants to `{"open", "in_progress", "completed", "canceled"}`.
- Frontmatter writer drops the field unconditionally; reader silently ignores any stray `resolution` key it encounters (defensive — autofix handles permanent removal).

The reader's silent-ignore is the only place backwards-compatibility code lives. It exists so a user who has not yet run `tq autofix` can still `tq show` their tickets without a parse error. The writer never re-emits the field, so on the next mutation the ticket is implicitly migrated; `autofix` makes the migration explicit and bulk.

**Alternatives considered:** Hard-fail on `resolution: ...` in the reader. Rejected — that punishes users for the order in which they upgrade, and a defensive ignore costs one line.

### Lifecycle commands: direct status assignment

`close`/`cancel` set `status` directly and never touch a `resolution` field. `reopen` sets `status = "open"` and is done. The branching helper that selected `"completed"` vs `"canceled"` becomes a constant per command.

The descendants check (`if child.status != "closed"`) becomes `if not is_terminal(child)`. The cascade write under `--force` assigns the parent's terminal status to each non-terminal descendant.

The diagnostic strings (`"has open descendants"`) stay verbatim — the spec keeps that wording for backward-compat with users grepping output. "Open" here is shorthand for "not terminal", which matches user expectation.

**Alternatives considered:** Reword the diagnostic to "has non-terminal descendants". Rejected — needlessly noisy and the existing wording is unambiguous in context.

### `ls --status` accepts the new four-value enum; legacy filter flags removed

In `commands/query.py`:

- `VALID_STATUSES` becomes `("open", "in_progress", "completed", "canceled")`.
- Add `-s` as a short alias for `--status` (argparse: `add_argument("-s", "--status", ...)`).
- Drop the `--completed` and `--canceled` argparse entries entirely. Argparse will raise `unrecognized arguments` and exit non-zero — that satisfies the "rejected" scenarios without custom code.
- The dispatch block that filtered on `(status=closed, resolution=X)` collapses to a single `--status` filter on the new enum.

The legacy `--status closed` value lands in argparse's `choices=` list, so passing it produces the standard argparse error with exit 2 — matches the "rejected" scenario.

**Alternatives considered:** Custom error messages pointing users at the new flags. Rejected for now — scope creep; the CHANGELOG entry is the right place to teach the migration. If users complain, we add it later.

### Checkbox derivation: status alone

`_checkbox(t)` becomes a four-way `match` on `t.status` with no resolution lookup. The `[AI]` block above the function is rewritten to reflect the simplification.

### Archive eligibility: terminal set, not closed set

`archive` computes `terminal_ids = {t.id for t in all_tickets.values() if is_terminal(t)}`. Diagnostic strings update from "No closed tickets to archive" → "No completed or canceled tickets to archive" (and the eligible-for-archiving variant likewise).

### `autofix` migration

A new top-level rule in `commands/autofix.py`. Order of operations:

1. Load every ticket (active and archived).
2. For each ticket: classify into one of three buckets — *migrated* (status was `closed`), *stripped* (status was not `closed` but a stray `resolution` field is present), or *unchanged*.
3. For migrated tickets, derive new status: `resolution == "canceled"` → `canceled`; everything else → `completed` (this folds the "missing resolution" case into the same branch).
4. Emit one summary line. If any tickets were migrated, print `- Migrated N ticket(s) from closed status`. Else if any had stray resolution, print `- Stripped resolution from N ticket(s)`. Else print nothing for this rule (the existing "No fixes needed" branch handles the empty case).
5. Pluralize manually (`ticket` vs `tickets`) — same convention used by the existing prefix-rename rule.

The dataclass loses its `resolution` field; the migration reads the raw frontmatter dict before it is parsed into a `Ticket`, classifies, then writes back through the normal `save_ticket` path. This avoids polluting the dataclass with a transition-only field.

**Alternatives considered:** Keep `Ticket.resolution` as a transition-only `T.Optional[str]` for one release. Rejected — `autofix` runs at the YAML layer anyway, so the dataclass never needs to know.

### CLI help text

The two-tier help (`tq` short help in `cli.py:23-26` and the long help block at `:91-127`) both mention closed/resolution. Rewrite line by line:

- `close`: "Close as completed" → "Set status to completed"
- `cancel`: "Close as canceled" → "Set status to canceled"
- `reopen`: "Reopen (clears resolution)" → "Reopen (set status to open)"
- `archive`: "Move closed tickets ..." → "Move completed and canceled tickets ..."
- `--status`: enum updated, add `-s` short form
- Drop the two `--completed` / `--canceled` lines.

`docs/cli-design.md` gets the same edits.

### Order of work

Schema first, then commands, then tests. Doing it this way keeps `pytest` green at each commit:

1. Update `store.py` (schema + helper). Tests that explicitly read `resolution` will fail — that's fine for one commit.
2. Update lifecycle commands. Update lifecycle tests in the same commit.
3. Update query commands (filters, checkbox, archive). Update query tests in the same commit.
4. Update CLI help (`cli.py`, help test). Same commit.
5. Implement `autofix` migration + tests.
6. Update `docs/cli-design.md` and `CHANGELOG.md`.

## Risks / Trade-offs / Limitations

- **Migration failure leaves mixed state** → autofix is idempotent and prints what it did; users can re-run safely. Reader's silent-ignore of stray `resolution` means partial migration doesn't break reads.
- **External consumers reading `resolution` from JSON output** → documented breaking change in CHANGELOG; no programmatic mitigation.
- **`tq ls --status closed` is now a hard error** → user instruction was explicit ("hard break"); CHANGELOG covers it.

## Open Questions

None.
