---
id: tiqt-6a09
status: closed
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T13:31Z
---
# Narrow has_dep_cycle signature to (graph, source, new_deps)

## Description

store.py:516-548 -- extra_edges Mapping accepts multiple sources but the sole caller passes one. Unused generality. Narrow to one source or actually exercise multi-source path.
