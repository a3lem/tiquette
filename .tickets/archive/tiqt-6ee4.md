---
id: tiqt-6ee4
status: closed
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T11:25:09.223494+00:00
---
# Lift _handle_deps tree-printing closures to module level

## Description

query.py:412-474 _handle_deps still defines _subtree_depth and _print_tree as inner closures over all_tickets/seen/args.full. Tiqt-8288 and tiqt-ed8c moved the ls tree printer out of a closure; _handle_deps is the holdout. Lift to module-level functions with explicit args, or reuse the _TreePrinter dataclass pattern.
