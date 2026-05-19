---
id: tiqt-ffc6
status: open
type: chore
priority: 4
deps: []
links: []
tags: []
created: 2026-05-19T13:31:44.059785+00:00
---
# autofix rewrites every ticket even when nothing changed

## Description

autofix.py:107-115 -- _apply_renames writes new file for every ticket in every dir. For a 500-ticket repo with one rename, that's 499 unnecessary writes. Short-circuit when original_id == updated.id and refs unchanged.
