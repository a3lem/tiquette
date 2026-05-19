---
id: tiqt-dc74
status: open
type: chore
priority: 2
deps: []
links: []
tags: []
created: 2026-05-19T11:24:37.019013+00:00
---
# Replace Status.TERMINAL monkey-patch with module-level frozenset

## Description

store.py:49-56 attaches TERMINAL_STATUSES as a class attribute on the StrEnum Status using three # type: ignore comments, and both TERMINAL_STATUSES and is_terminal() wrap the same set. Follow-up to tiqt-43f8 (StrEnum conversion) and tiqt-77ba (is_terminal signature). Done = no type:ignore on Status, single source of truth for terminal set.
