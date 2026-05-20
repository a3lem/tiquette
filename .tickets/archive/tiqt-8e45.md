---
id: tiqt-8e45
status: closed
type: chore
priority: 4
deps: []
links: []
tags: []
created: 2026-05-19T11:25:06.535886+00:00
---
# Drop type:ignore on link-pair tuple in _handle_links

## Description

query.py:782-788 builds a sorted pair with tuple(sorted([a,b])) which widens to tuple[str, ...], requiring # type: ignore[arg-type]. Replace with: pair = (a, b) if a < b else (b, a). Removes the ignore and the runtime length assert.
