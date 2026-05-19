---
id: tiqt-43f8
status: open
type: chore
priority: 2
deps: []
links: []
tags: []
created: 2026-05-19T08:55:37.913202+00:00
---
# Convert Status from string constants to StrEnum

## Description

store.Status (store.py:177) is a class of string constants and TERMINAL_STATUSES (store.py:38) is a redundant alias of Status.TERMINAL. The 'match status' at query.py:178-188 falls through to '[?]' silently because the type checker can't prove exhaustiveness over loose strings. Fix: make Status a 'class Status(enum.StrEnum)' with members OPEN, IN_PROGRESS, BLOCKED, DONE, CANCELLED (values matching current strings for backward-compat on serialization); change is_terminal to take 'status: Status' and reuse Status.TERMINAL as a frozenset of members; update the match in _checkbox to be exhaustive.
