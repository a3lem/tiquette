---
id: tiqt-fd18
status: closed
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T13:31:14.633467+00:00
---
# Express load_all_tickets via iter_tickets to dedupe glob/sort/merge

## Description

store.py:469-506 -- iter_tickets and load_all_tickets walk the same *.md corpus with divergent archive-merge semantics. load_all_tickets could be {t.id: t for t in iter_tickets(..., source=...)} with explicit merge, eliminating the implicit 'active wins' rule scattered across callers.
