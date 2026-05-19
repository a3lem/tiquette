---
id: tiqt-bbd8
status: closed
type: chore
priority: 2
deps: []
links: []
tags: []
created: 2026-05-19T08:55:30.307941+00:00
---
# Split apply_field_changes into validate then mutate

## Description

store.apply_field_changes (store.py:471-612, ~140 lines) interleaves resolution, cycle-check, link-target loading, and six mutation blocks. The 'validate first, then mutate' invariant is real but not enforced by structure -- a future edit could easily mutate before a later validation fails. Also: store.py:537 names a list 'new_deps_set'. store.has_dep_cycle (store.py:413) mutates the graph and restores it, which is a foot-gun. Fix: extract _validate_changes(ticket, changes, ...) -> ValidatedChanges (returns resolved IDs, cycle-safe dep set, link targets) and _apply_validated(ticket, validated) that only mutates. Make has_dep_cycle accept the candidate edges as a parameter instead of mutating the graph.
