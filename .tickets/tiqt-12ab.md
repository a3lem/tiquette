---
id: tiqt-12ab
status: open
type: chore
priority: 4
deps: []
links: []
tags: []
created: 2026-05-19T13:31:31.503864+00:00
---
# Cache file mtime per ID in _render_tree sort keys

## Description

query.py:515,636,717 -- sort callbacks call (tickets_dir / f'{id}.md').stat() repeatedly during recursion. Tree of N nodes does O(N log N) syscalls. Build an mtime map once per render.
