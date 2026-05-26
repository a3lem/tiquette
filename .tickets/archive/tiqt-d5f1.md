---
id: tiqt-d5f1
status: closed
type: chore
priority: 4
deps: []
links: []
tags: []
created: 2026-05-19T08:56Z
---
# Reuse already-loaded tickets in _handle_status descendants

## Description

lifecycle._find_open_descendants (lifecycle.py:96-116) reads every ticket from disk to compute the descendant set; _handle_status then iterates the returned IDs and re-reads each one at lifecycle.py:174 to mutate it. Two full reads per descendant. Fix: have _find_open_descendants return 'dict[str, Ticket]' (or accept a preloaded dict) and reuse the loaded instances for the mutation pass.
