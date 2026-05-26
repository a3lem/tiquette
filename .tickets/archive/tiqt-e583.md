---
id: tiqt-e583
status: closed
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T13:31Z
---
# has_parent_cycle does disk I/O per ancestor; accept preloaded map

## Description

store.py:556-576 -- read_ticket call per ancestor. _validate_changes already builds dep graphs from iter_tickets and could pass that map. Triples I/O on a deep tree per edit.
