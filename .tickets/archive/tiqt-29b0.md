---
id: tiqt-29b0
status: closed
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T13:31Z
---
# Precompute parent->children index in _TreePrinter (O(N^2) -> O(N))

## Description

query.py:497-503 -- _get_visible_children scans visible_ids per recursive call. Tree of N nodes: O(N^2). Build {parent_id: [child_id]} once at construction.
