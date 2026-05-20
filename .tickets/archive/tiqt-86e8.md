---
id: tiqt-86e8
status: closed
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T08:55:12.326785+00:00
---
# Extract resolve-or-exit helper

## Description

query.py:278-282, 364-370, 411-416, 429-434 each contain the same try/except around resolve_id that prints to stderr and sys.exit(1). Fix: add '_resolve_or_exit(partial: str, tickets_dir: Path) -> str' that wraps resolve_id and centralises the exit-code and message format. Replace the four call sites.
