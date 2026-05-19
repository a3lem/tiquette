---
id: tiqt-ed8c
status: open
type: chore
priority: 1
deps: [tiqt-8288]
links: []
tags: []
created: 2026-05-19T08:55:25.258443+00:00
---
# Decompose _handle_ls into scope/filter/output stages

## Description

query._handle_ls (query.py:496-736, ~240 lines) is the worst function in the codebase. It mixes (a) source selection (active vs archive), (b) scope resolution (parent/dep tree), (c) three filter modes (ready/blocked/all), (d) sorting, (e) three output modes (flat-with-deps / jsonl / tree), plus the nested recursive closure with nonlocal state. Sort logic is repeated three times within the function (574-580, 704-709, 728-731). Fix: split into _select_source(args) -> dict[str, Ticket], _apply_scope(args, source), _apply_filter(args, scoped), _sort(args, filtered), and _render_flat / _render_jsonl / _render_tree. _handle_ls becomes a small driver. Do this AFTER the _print_ls_tree closure-removal ticket lands.
