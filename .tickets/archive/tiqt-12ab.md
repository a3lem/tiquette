---
id: tiqt-12ab
status: closed
type: chore
priority: 4
deps: []
links: []
tags: []
created: 2026-05-19T13:31Z
---
# Cache file mtime per ID in _render_tree sort keys

## Description

query.py:515,636,717 -- sort callbacks call (tickets_dir / f'{id}.md').stat() repeatedly during recursion. Tree of N nodes does O(N log N) syscalls. Build an mtime map once per render.
