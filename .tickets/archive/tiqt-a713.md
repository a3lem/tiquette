---
id: tiqt-a713
status: closed
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T08:55:15.741295+00:00
---
# Unify partial-ID resolution: store.resolve_id and query._resolve_in_set

## Description

store.resolve_id (store.py:621-639) and query._resolve_in_set (query.py:229-240) implement the same partial-ID-to-full-ID lookup; the only real difference is the candidate set (filesystem vs. pre-filtered dict). Fix: change resolve_id to accept the candidate iterable: 'resolve_id(partial: str, candidates: Iterable[str]) -> str' and provide a thin 'resolve_id_in_dir(partial, tickets_dir)' wrapper. Delete _resolve_in_set.
