---
id: tiqt-757b
status: open
type: chore
priority: 4
deps: []
links: []
tags: []
created: 2026-05-19T11:25:04.483443+00:00
---
# Delete unused list_ticket_ids

## Description

store.py:455-471 list_ticket_ids appears to have no callers under commands/. Verify with grep, then delete. All commands route through load_all_tickets / iter_tickets.
