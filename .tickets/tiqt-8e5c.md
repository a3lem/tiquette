---
id: tiqt-8e5c
status: canceled
type: feature
priority: 2
assignee: claude
deps: []
links: []
tags: []
created: 2026-08-30T12:12Z
---
# CLI ergonomics: note verb, -m alias, variadic reads, tree alias, scoped validation, command hints

## Description

Usage analysis of 237 tq invocations (2026-08-17..08-30) found 16 command-surface failures; 81% trace to the missing note verb. Changes: (1) tq note <id> TEXT as first-class verb; (2) -m short alias for --note on create/edit/start/close/cancel/reopen; (3) show/info/path accept multiple IDs; (4) tq tree <id> alias for ls --parent; (5) show/deps no longer hard-fail when an unrelated ticket file is malformed (warn+skip); (6) unknown-command hint suggests nearest verb; (7) prime.md + help text doc fixes (--link/--note in create options, prune -t short flag). Done = tests pass, spec deltas applied, skill regenerated via shablon.

## Notes

- 2026-08-30T12:28Z: Implemented all 7 recommendations + skill discrepancy fixes. 554 tests pass (34 new), basedpyright 0 errors. Spec deltas applied to ticket-edit/-lifecycle/-query and change archived as specs/changes/archive/2026-08-30-cli-ergonomics. Skill+README+prime.md regenerated via shablon. Also removed the skill's nonexistent-plugin-system section and fixed edit/note traceback on ambiguous subject ID.
- 2026-08-30T12:28Z [closed]: not committed yet; working tree holds the change
- 2026-08-30T13:47Z [canceled]: Implementation reverted after design review: the note/tree verbs and -m alias duplicate existing surfaces (edit --note, ls --parent) and break the one-canonical-surface ethos from cli-redesign-v1.2. A redesign assessment replaces this ticket.

