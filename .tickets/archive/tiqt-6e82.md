---
id: tiqt-6e82
status: closed
type: bug
priority: 1
deps: []
links: []
tags: []
created: 2026-05-19T11:24:45.562315+00:00
---
# Fix link-referrer asymmetry in _handle_archive propagation

## Description

query.py:802-874 builds a referrer index that tracks deps, parent, AND links, but the propagation loop at 838-853 only walks deps + parent referrers. A ticket referenced only via 'link' may not get its archivability re-evaluated when a linked ticket becomes terminal. Also: function is 70+ lines mixing concerns -- split into _build_referrer_index / _compute_archivable / _move_to_archive. Follow-up to tiqt-ea43 (tightened convergence loop).
