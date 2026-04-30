---
id: tiqt-433c
status: closed
type: feature
priority: 2
deps: []
links: []
tags: [spexl]
resolution: completed
created: 2026-04-29T12:48:50.906383+00:00
---
# Apply spexl change: create-rename-assignee-short-flag

## Description

Implement spec change at specs/changes/create-rename-assignee-short-flag/. Renames tq create --assignee short flag from -a to -A. See design.md.

## Notes

- 2026-04-30T13:25:15.279183+00:00: Implemented. lifecycle.py:39 -a → -A. Tests updated (test_cli_lifecycle.py 3 sites, test_cli_help.py 1 site). 316/316 pass. CHANGELOG updated.
