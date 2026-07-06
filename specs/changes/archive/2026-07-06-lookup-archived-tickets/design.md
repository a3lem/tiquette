## Context

`show`, `info`, `path`, and `deps` all resolve their `<id>` argument via `_resolve_or_exit` (`query.py:236`), which calls `resolve_id_in_dir` (`store.py:897`) -- a glob over `tickets_dir/*.md` only. Archived tickets live in `tickets_dir/archive/*.md` and are invisible to that glob, so resolution fails first with `ticket '<id>' not found`, before any handler gets a chance to look in the archive.

`resolve_id_in_dir` is also used by `edit.py` and `lifecycle.py` (start/close/cancel/reopen) -- those are mutation commands and stay active-only; this change does not touch them or `resolve_id_in_dir` itself.

Even with resolution fixed, three more spots build a path or load a ticket set assuming everything lives directly under `tickets_dir`:
- `_handle_show` and `_handle_path` construct `tickets_dir / f"{ticket_id}.md"` directly.
- `_handle_show` and `_handle_deps` call `_load_all_tickets(tickets_dir)`, which defaults to `source="active"` -- an archived ticket's own dependencies (which may themselves be archived) wouldn't resolve in the relationship/tree output even once the root ticket is found.

## Goals / Non-Goals

**Goals:**
- `show`, `info`, `path`, `deps` work identically whether the target ticket is active or archived.
- Preserve the existing active-wins precedence convention (`store.py`'s `load_all_tickets`/`iter_tickets`) for the edge case of a duplicate ID across both directories.
- No behavior change to `ls` (already has its own `--archived`/`--all` axis), `archive`, `prune`, or any mutation command (`edit`, `start`, `close`, `cancel`, `reopen`).

**Non-Goals:**
- Fixing `info`'s pre-existing spec/code mismatch (human-readable `info` prints frontmatter only, no relationship sections, despite the reference spec describing relationships) -- unrelated, out of scope.
- Any change to archive eligibility rules or `resolve_id_in_dir`'s active-only scope.

## Decisions

### Add `resolve_id_including_archive`, not a new mode on `resolve_id_in_dir`

Add a sibling function next to `resolve_id_in_dir` in `store.py`:

```python
def resolve_id_including_archive(partial: str, tickets_dir: Path) -> str:
    """Resolve a partial ID against active + archived ticket files."""
    archive_dir = tickets_dir / "archive"
    ids = {p.stem for p in tickets_dir.glob("*.md")}
    if archive_dir.is_dir():
        ids |= {p.stem for p in archive_dir.glob("*.md")}
    return resolve_id(partial, ids)
```

`resolve_id_in_dir` keeps its current active-only behavior for `edit`/`lifecycle` and the internal caller in `store.py` (`apply_field_changes`'s dep/link/parent validation, around line 703/711). Using a `set` union means a duplicate ID across active+archive collapses to one candidate -- no spurious ambiguity error, and `resolve_id`'s exact-match-first rule still applies for genuine ambiguity between two distinct IDs.

**Alternatives considered:** Route through `load_all_tickets(tickets_dir, source="all").keys()` instead. Rejected -- it fully parses every ticket file (frontmatter + body) just to extract IDs, where `resolve_id_in_dir`'s sibling only needs filenames. Keeping the new function glob-based matches the cost profile of the function it sits next to.

### Add `ticket_home_dir` to locate the containing directory

```python
def ticket_home_dir(ticket_id: str, tickets_dir: Path) -> Path:
    """Return the directory holding `ticket_id`'s file: `tickets_dir` if active,
    otherwise `tickets_dir / "archive"`. Caller must have already resolved
    `ticket_id` to a full ID known to exist in one of the two."""
    if (tickets_dir / f"{ticket_id}.md").exists():
        return tickets_dir
    return tickets_dir / "archive"
```

Checking the active directory first makes this consistent with `resolve_id_including_archive`'s implicit active-wins precedence for the duplicate-ID edge case. `read_ticket`/`read_ticket_with_body` already accept an arbitrary directory (see `iter_tickets`, which calls `read_ticket(path.stem, archive_dir)` for archived entries) -- no change needed there.

### Update the four call sites

- `_resolve_or_exit` (`query.py:236`, used by `show`/`info`/`path`/`deps`): call `resolve_id_including_archive` instead of `resolve_id_in_dir`.
- `_handle_show`: resolve `ticket_dir = ticket_home_dir(ticket_id, tickets_dir)`; pass it to `read_ticket_with_body` and use it to build `file_path`; change the relationship-section load from `_load_all_tickets(tickets_dir)` to `_load_all_tickets(tickets_dir, source="all")`.
- `_handle_info`: resolve `ticket_dir` the same way and pass it to `read_ticket`.
- `_handle_path`: resolve `ticket_dir` the same way and build `file_path` from it.
- `_handle_deps`: change `_load_all_tickets(tickets_dir)` to `_load_all_tickets(tickets_dir, source="all")`.

## Risks / Trade-offs / Limitations

- [`_load_all_tickets(source="all")` parses every active and archived ticket file for `show`/`deps`, where before `show`/`deps` only parsed active ones] → Acceptable: `tq ls --all` already pays this cost, and ticket counts in this system are small (file-based store, no pagination anywhere).
- [Duplicate ID across active+archive is not deliberately produced by any code path, but isn't provably unreachable either: `generate_id` (`store.py:248-255`) only checks `tickets_dir / f"{ticket_id}.md"` for collisions, never `tickets_dir/archive/`, so a freshly created ticket could in principle collide with an already-archived ID] → Behavior is still defined (active wins) for robustness, but no migration or validation is added to detect/prevent it; out of scope.

## Open Questions

None.
