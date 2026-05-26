---
id: tiqt-77ba
status: closed
type: chore
priority: 4
deps: [tiqt-43f8]
links: []
tags: []
created: 2026-05-19T08:55Z
---
# Make is_terminal accept a status, not a Ticket

## Description

store.is_terminal (store.py:41) takes a full Ticket but only reads t.status. Callers that already have the status string (or want to test a hypothetical status) have to fabricate a Ticket or duplicate the membership check. Fix: change signature to 'is_terminal(status: Status) -> bool' (after the Status StrEnum ticket lands) and update the few callers.
