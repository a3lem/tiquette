# Design: Status-Transition Notes

## Context

`_handle_status` in `src/tiquette/commands/lifecycle.py` is the single entry point for `start`, `close`, `cancel`, `reopen`. It runs three phases: resolve+load, descendant pre-flight (terminal targets), mutate+emit. Mutations call `write_ticket` directly -- they do **not** route through `apply_field_changes`, so the existing `--note` plumbing (`FieldChanges.notes` → `_append_note`) is currently bypassed by transition commands.

Note-writing primitives already exist:

- `store._append_note(ticket, text, timestamp)` at `store.py:629` -- appends `- <timestamp>: <text>` to the `## Notes` section.
- `apply_field_changes` shares a single timestamp across all notes in one invocation (see `store.py:815`).

The `tq create` and `tq edit` paths share one timestamp per invocation by computing `datetime.now(timezone.utc).isoformat()` once at the top and passing it down.

## Goals / Non-Goals

**Goals**
- `--note TEXT` (repeatable) accepted on `start`, `close`, `cancel`, `reopen`.
- Auto-prefix each note with `[started|closed|canceled|reopened]:`.
- Cascades propagate the same notes to every descendant whose status actually changed.
- Atomic with the transition: failed transitions write zero notes.

**Non-Goals**
- A `-m` short flag.
- A general status changelog (every transition recorded regardless of `--note`).
- Pretty-rendering tagged notes in `show`/`info` (they remain plain text).

## Decisions

### Extend `_append_note` with an optional tag

Change `_append_note`'s signature to:

```python
def _append_note(ticket: Ticket, text: str, timestamp: str, tag: str | None = None) -> None
```

When `tag` is set, the written line is `- <timestamp> [<tag>]: <text>`; otherwise it stays `- <timestamp>: <text>` (existing behaviour, no churn at the `create`/`edit` call sites).

**Alternatives considered:** have callers pre-format `text` as `[closed]: ...` -- rejected; pushes formatting concern out of the store and makes it easy to introduce inconsistency.

### Verb tag table

```python
_TRANSITION_TAG: dict[Status, str] = {
    Status.IN_PROGRESS: "started",
    Status.CLOSED: "closed",
    Status.CANCELED: "canceled",
    Status.OPEN: "reopened",
}
```

Keyed by target status because that's what `_handle_status` already has in hand (`args.target_status`). The mapping lives in `lifecycle.py` -- it is a CLI/UX concern, not a store concern.

### Argparse surface

Add `--note TEXT` (repeatable) to the `start`, `close`, `cancel`, `reopen` subparsers. Reuse the same `action="append", default=[]` shape used by `create`/`edit`. No short flag.

### Wiring into `_handle_status`

One change: after Phase 1 resolves IDs and before Phase 3 mutates, compute:

```python
tag = _TRANSITION_TAG[target]
notes: list[str] = args.note or []
ts = now_iso() if notes else None
```

(`now_iso` comes from the timestamp-format change; if that change has not landed yet, `datetime.now(timezone.utc).isoformat()`.)

In Phase 3, immediately before each `write_ticket(ticket, ...)` call (both the descendant cascade write and the target write), do:

```python
for note in notes:
    _append_note(ticket, note, ts, tag=tag)
```

This works for both the explicit-target write and the cascade-descendant write -- they all go through `write_ticket`, so a single insertion point per write site covers every scenario in the spec.

The non-terminal branch (`start`, `reopen`) has its own write loop earlier in `_handle_status`; apply the same insertion there.

**Alternatives considered:** route everything through `apply_field_changes` -- rejected. That function carries a lot of behaviour we don't need on a status flip (field merges, dep symmetry, etc.); the insertion is two lines and clearer to read.

### Already-terminal descendants are skipped

`_find_open_descendants` returns only non-terminal descendants, and Phase 3 only writes to those. So the spec scenario "already-terminal descendants left untouched" is satisfied automatically -- no extra guard needed.

### Failure semantics

The existing Phase 1 / Phase 2 abort-before-write structure already guarantees zero writes on failure. Notes are produced **inside** Phase 3, after pre-flight passes, so they inherit this guarantee for free.

### Tests

- New: `tq close T --note "X"` produces `[closed]: X` entry; same shape for cancel/start/reopen.
- New: `tq close T` (no `--note`) writes no Notes section.
- New: multi-note shares timestamp, both tagged.
- New: multi-ID transition writes the note on every affected ticket.
- New: `tq close -f par --note "X"` writes `[closed]: X` on parent + every cascaded descendant.
- New: `tq close -f par` (no `--note`) writes no notes on cascade.
- New: rejected force-less cascade with `--note` writes nothing.
- New: failed multi-ID (one unknown) with `--note` writes nothing.

## Risks / Trade-offs / Limitations

- **Note grammar drift** → only `_append_note` writes; tag format is centralised there.
- **Reopen-then-close-again produces two `[closed]:` entries in Notes** → intentional; matches the user-confirmed model that this is a note log, not a status snapshot.
- **`--note` semantics now differ slightly across commands**: on `create`/`edit` notes are untagged; on `start`/`close`/`cancel`/`reopen` they are auto-tagged. Documented in the spec; consistent with "the tag describes what happened".

## Open Questions

None.
