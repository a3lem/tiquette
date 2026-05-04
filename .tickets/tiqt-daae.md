---
id: tiqt-daae
status: completed
type: feature
priority: 2
deps: []
links: []
tags: [spexl]
created: 2026-04-29T12:48:48.155913+00:00
---
# Apply spexl change: ls-archived-flags

## Description

Implement spec change at specs/changes/ls-archived-flags/. Adds --archived and --all (-a) flags to tq ls; renames ls --assignee short flag from -a to -A. See design.md for implementation plan.

## Notes

- 2026-04-30T11:45:38.141231+00:00: Implemented. All 314 tests pass. Smoke-tested ls / ls -a / ls --archived / ls --archived --completed in /tmp/tq-smoke. CHANGELOG updated under [Unreleased]. Ready to archive spec change.
