## store.py

- [x] Add `resolve_id_including_archive(partial, tickets_dir)` next to `resolve_id_in_dir`
- [x] Add `ticket_home_dir(ticket_id, tickets_dir)` returning the active or archive directory

## commands/query.py

- [x] `_resolve_or_exit` calls `resolve_id_including_archive` instead of `resolve_id_in_dir`
- [x] `_handle_show`: resolve `ticket_dir` via `ticket_home_dir`; use it for `read_ticket_with_body` and the raw-content `file_path`; load relationships with `_load_all_tickets(tickets_dir, source="all")`
- [x] `_handle_info`: resolve `ticket_dir` via `ticket_home_dir`; use it for `read_ticket`
- [x] `_handle_path`: resolve `ticket_dir` via `ticket_home_dir`; build `file_path` from it
- [x] `_handle_deps`: load with `_load_all_tickets(tickets_dir, source="all")`

## Verification

- [x] Tests for requirement: id-resolution / Partial ID matching (archived scenarios)
- [x] Tests for requirement: id-resolution / ID resolution across commands (edit --dep archive-only boundary scenario)
- [x] Tests for requirement: ticket-query / Show ticket (archived scenarios)
- [x] Tests for requirement: ticket-query / Info command (archived scenario)
- [x] Tests for requirement: ticket-query / Path command (archived scenario)
- [x] Tests for requirement: ticket-query / Show dependency tree (archived scenario)

## Notes

- `resolve_id_in_dir` itself, and its callers in `edit.py`/`lifecycle.py`, stay active-only -- not part of this change.
