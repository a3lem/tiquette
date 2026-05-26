---
id: tiqt-ea43
status: closed
type: chore
priority: 4
deps: []
links: []
tags: []
created: 2026-05-19T08:56Z
---
# Tighten _handle_archive convergence loop

## Description

query._handle_archive (query.py:799-837) shrinks the archivable set with 'while changed: for tid in archivable: ... _find_referrers(...)'. _find_referrers is O(n) and called inside the loop, and the loop may need multiple full passes to converge because it doesn't propagate within a single pass. Fix: build a reverse-reference index once (O(n)) outside the loop and remove items from archivable in a single pass driven by that index. Even if N is small today this is the kind of code that traps the next reader.
