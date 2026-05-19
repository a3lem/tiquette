---
id: tiqt-963a
status: open
type: bug
priority: 2
deps: []
links: []
tags: []
created: 2026-05-19T08:55:53.287429+00:00
---
# Make has_dep_cycle pure: accept candidate edges, don't mutate graph

## Description

store.has_dep_cycle (store.py:413) mutates the dep graph to add proposed edges, runs the cycle check, then restores the graph. A pure predicate that mutates shared state is a foot-gun -- any exception between mutate and restore leaves the graph corrupted, and concurrent callers (even just a future caller in the same process) would see inconsistent state. Fix: change signature to 'has_dep_cycle(graph: Mapping[str, list[str]], extra_edges: Mapping[str, Iterable[str]]) -> bool' and walk a virtual union without mutation.
