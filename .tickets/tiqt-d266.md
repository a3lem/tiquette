---
id: tiqt-d266
status: open
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T11:24:48.143493+00:00
---
# Replace args.command string dispatch with target_status default

## Description

query.py:218-229 and lifecycle.py:151 dispatch on args.command in ('start','close','cancel','reopen') with assert + if/elif chain. Each subparser already calls set_defaults(func=...); also set_defaults(target_status=Status.IN_PROGRESS) etc. Removes the string-compare chain, the assert, and a dead 'reopen' branch.
