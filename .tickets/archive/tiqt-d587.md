---
id: tiqt-d587
status: closed
type: chore
priority: 4
deps: []
links: []
tags: []
created: 2026-05-19T13:31Z
---
# Delete unused all_tickets merge in validate._collect_problems

## Description

validate.py:27 -- all_tickets = {**archived, **active} is computed but only active[ticket_id] is read via the merged dict downstream. Dead computation.
