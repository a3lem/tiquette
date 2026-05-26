---
id: tiqt-5d5e
status: closed
type: chore
priority: 2
deps: []
links: []
tags: []
created: 2026-05-19T11:24Z
---
# Extract _merge_unique helper for tags/deps/links in _apply_validated

## Description

store.py:701-778 reinvents dedup-append-then-filter-removals three times (tags, deps, links). Follow-up to tiqt-bbd8 (split validate/mutate). Done = single helper used by all three sections.
