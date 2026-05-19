---
id: tiqt-e9d6
status: open
type: chore
priority: 4
deps: []
links: []
tags: []
created: 2026-05-19T11:25:02.292048+00:00
---
# Drive conflicting_set_and_unset from UNSET_TARGETS

## Description

store.py:135-145 conflicting_set_and_unset hard-codes parent/xref/assignee in an if/elif chain; commands/_fields.py:14 already has UNSET_TARGETS = ('parent','xref','assignee'). Iterate with getattr(self, field). Adding a fourth unsettable field currently requires edits in three places (FieldChanges, this method, _apply_validated unset block).
