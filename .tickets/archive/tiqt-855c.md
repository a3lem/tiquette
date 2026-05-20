---
id: tiqt-855c
status: closed
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T11:24:59.675062+00:00
---
# Promote _abbreviate to public API or move it to autofix

## Description

commands/autofix.py:9 imports a leading-underscore helper from store.py. Either rename to abbreviate (declare it part of the store's public API) or relocate the prefix-planning code into store.py. The underscore convention is being violated across module boundaries.
