---
id: tiqt-07e1
status: closed
type: chore
priority: 2
deps: []
links: []
tags: []
created: 2026-05-19T08:55:09.740369+00:00
---
# Extract _ticket_to_dict helper for JSON serialization

## Description

Near-identical ticket-to-dict literals appear three times in query.py: lines 292-306 (_handle_show --json), 375-388 (_handle_info --json), 594-605 (ls --jsonl). They drift independently and have already started to. Fix: add '_ticket_to_dict(t: Ticket, include_body: bool = False) -> dict[str, str | int | list[str] | None]' in query.py (or store.py) and use it in all three call sites.
