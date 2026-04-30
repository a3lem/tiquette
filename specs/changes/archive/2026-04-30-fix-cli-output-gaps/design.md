# Design: Fix CLI Output Gaps

## Context

Three targeted fixes across two modules and one command registration:

- `src/tiquette/store.py` — serialization of nullable fields
- `src/tiquette/commands/lifecycle.py` — stdout output for transition commands
- `src/tiquette/commands/query.py` — short flag aliases on `ls`

All changes are surgical. No new abstractions, no new dependencies, no data model changes.

## Goals / Non-Goals

**Goals:**
- Print ticket ID to stdout on every successful transition (`start`, `close`, `cancel`, `reopen`)
- Omit nullable fields from frontmatter when their value is `None`
- Add `-a` / `-T` as short aliases for `--assignee` / `--tag` on `ls`

**Non-goals:**
- Changing the behavior of `tq create` (already prints ID correctly)
- Migrating existing ticket files with `null` lines (the parser already handles missing fields gracefully)
- Adding short aliases for other `ls` flags (not in scope)

## Decisions

### 1. Nullable field omission in `_serialize_frontmatter`

**Change:** In `_serialize_frontmatter` (store.py:126), skip the field entirely when
`key in _NULLABLE_FIELDS and value is None`. Currently the loop unconditionally appends every
field; the fix adds a guard:

```python
for key in _FIELD_ORDER:
    value = getattr(ticket, key)
    if key in _NULLABLE_FIELDS and value is None:
        continue
    lines.append(f"{key}: {_format_yaml_value(key, value)}")
```

`_format_yaml_value` does not need to change; its `null` branch becomes dead code for new
writes (but can stay for clarity).

**Parser compatibility:** `_parse_frontmatter` (store.py:151) only adds a key to `result` when
the line is present. The `Ticket` dataclass defaults all four nullable fields to `None`. Missing
lines round-trip correctly: omitted on write → absent on read → default `None` applied by
dataclass → correct in-memory state.

**Existing files:** Files that already have `assignee: null` etc. continue to parse correctly
(`_parse_yaml_value` handles `"null"` → `None`). No migration needed.

**Alternatives considered:** Keeping `null` in the file for "always-present" fields and only
omitting `resolution`. Rejected: the spec says every cleared nullable field should leave no
trace, and a uniform rule (omit-all-when-None) is simpler and more consistent than a per-field
allowlist.

### 2. Transition output in `_handle_status`

**Change:** Add `sys.stdout.write(ticket.id + "\n")` at the end of `_handle_status`
(lifecycle.py:139), after `write_ticket`. This is the single shared exit point for all four
commands.

Output ordering for `close` (the only command with a conditional side-effect):

1. `_check_last_open_child` runs (may print `note: <parent> has no remaining open children`)
2. `write_ticket` persists the state change
3. Ticket ID is printed

The note comes first because it is context for the operation. The ID confirms the operation
completed. This ordering means the ID is always the last line, making it easy to capture in
scripts (`ID=$(tq close foo | tail -1)`).

Failed transitions already `sys.exit(1)` before reaching the new print, so the spec's
"failed transition does not print ID" constraint is satisfied without additional guards.

**Alternatives considered:** Printing ID before `write_ticket`. Rejected: printing before the
write would be misleading if `write_ticket` raises (unlikely but possible on I/O error).

### 3. Short flag aliases on `ls`

**Change:** Two one-line edits in `query.py`:

```python
# before
p_ls.add_argument("--assignee", help="Filter by assignee")
p_ls.add_argument("--tag", help="Filter by tag")

# after
p_ls.add_argument("-a", "--assignee", help="Filter by assignee")
p_ls.add_argument("-T", "--tag", help="Filter by tag")
```

`-a` matches the existing short form on `create --assignee`. `-T` is uppercase to avoid
collision with any future `-t` alias for `--type` on `ls` (the `create` command already uses
`-t` for `--type`, so the convention is established). No other `ls` flags use `-a` or `-T`.

**Alternatives considered:** `-t` for `--tag` on `ls`. Rejected: `-t` means `--type` on
`create`; using it for `--tag` on `ls` would be inconsistent. `-T` is the next-best mnemonic.

## Risks / Trade-offs

- **Existing files with `null` lines:** Will continue to parse correctly. Old-format and
  new-format files can coexist in the same `.tickets/` directory.
- **Output ordering (note then ID):** Scripts that grep stdout for the ID will still find it.
  Scripts that assume the ID is the only stdout line will need updating -- but no such scripts
  are known to exist today.

## Open Questions

None. All decisions are resolved.
