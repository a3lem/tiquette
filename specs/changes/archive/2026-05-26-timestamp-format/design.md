# Design: Timestamp Format

## Context

Timestamps are written in three places today, all using `datetime.now(timezone.utc).isoformat()`:

- `src/tiquette/store.py:163` -- `Ticket.created` default factory
- `src/tiquette/store.py:816` -- note-append fallback timestamp
- `src/tiquette/commands/lifecycle.py:73` -- `_handle_create` computes the shared create-time timestamp
- `src/tiquette/commands/edit.py:49` -- `_handle_edit` computes the shared per-invocation note timestamp

Reads happen in:

- `src/tiquette/commands/query.py:963` -- `datetime.fromisoformat(t.created).date()` for `--before` filtering
- `src/tiquette/commands/query.py:417` -- `tq show` prints `created` as raw string (no parse)
- YAML loader for frontmatter `created` (raw string, no parse at load)

Python 3.11+'s `datetime.fromisoformat` already accepts both `2026-04-29T12:48:50.906383+00:00` and `2026-05-26T10:00Z`, so no custom parser is required for legacy reads.

## Goals / Non-Goals

**Goals**
- Every newly-written timestamp uses `YYYY-MM-DDTHH:MMZ`.
- Reads transparently accept both old and new formats.
- A single helper owns the format so it cannot drift across call sites.

**Non-Goals**
- Migrating existing files.
- Sub-minute ordering guarantees (`tq` sorts by file mtime / insertion order when needed; this change does not address that).
- Changing the `--before` CLI input format (stays `YYYY-MM-DD`).

## Decisions

### Single helper module for timestamps

Add `src/tiquette/timestamps.py` exposing exactly two functions:

```python
def now_iso() -> str: ...        # returns "2026-05-26T10:00Z"
def parse_iso(s: str) -> datetime: ...  # accepts both old and new
```

`now_iso` implementation: `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")`.

`parse_iso` normalises a trailing `Z` to `+00:00` before delegating to `datetime.fromisoformat`. (Python 3.11+ accepts `Z` natively, but normalising keeps us compatible with the 3.10 minimum stated in CLAUDE.md.)

Every existing call site is rewritten to import from this module. No raw `datetime.now(...).isoformat()` survives in the codebase.

**Alternatives considered:** inline `strftime` at each site -- rejected, drift risk and exactly the issue the helper exists to prevent.

### Read path: parse only where parsed today

The only existing parse site is `query.py:963` (`--before` filter). It switches from `datetime.fromisoformat(t.created)` to `parse_iso(t.created)`. Everywhere else timestamps are passed around as strings; no new parsing introduced.

**Alternatives considered:** parse on load into `Ticket.created: datetime` -- rejected, larger blast radius and the string round-trips fine.

### No migration, no rewrite-on-read

Loading a legacy-format ticket does not rewrite it. The `created` field is preserved verbatim through `read_ticket` → `write_ticket`. Only fields the user mutates change; `created` is never re-stamped.

A user who wants to normalise can edit-and-no-op the file themselves; we do not provide a `tq migrate` command.

### Tests

- Add unit tests for `timestamps.now_iso` (regex match) and `parse_iso` (both formats produce equal `datetime`).
- Existing tests that assert on timestamp shape (`test_cli_lifecycle.py`, `test_cli_edit.py`) update their regex from `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+00:00` to `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z`.
- Add at least one round-trip test that loads a fixture ticket with a legacy timestamp, edits a field, and asserts `created` is byte-identical on disk afterward.

## Risks / Trade-offs / Limitations

- **Mixed formats in `.tickets/` forever** → acceptable; the read path handles both, and `tq show` displays whatever the file holds.
- **Minute precision loses ordering for events in the same minute** → `tq` already orders notes by file position, not timestamp, so this is observably a no-op. Documented in the proposal's Out of Scope.
- **Python 3.10 `fromisoformat` does not accept `Z`** → handled by the `parse_iso` wrapper normalising `Z` to `+00:00`.

## Open Questions

None.
