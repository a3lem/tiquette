---
id: tiqt-280e
status: closed
type: bug
priority: 2
deps: []
links: []
tags: []
created: 2026-05-19T12:28:24.758859+00:00
---
# validate crashes with raw ValueError on legacy 'completed' status

## Description

Discovered during second-pass test drive. _parse_yaml_value (store.py:301) calls Status(raw) directly and lets the ValueError bubble up as a Python traceback. read_ticket has its own status-coercion path that wraps in TicketParseError (store.py:392-396) but _parse_yaml_value runs first. Repro: set status: completed in a ticket and run 'tq validate'. Expected: clean diagnostic pointing user at 'tq autofix'. Fix: _parse_yaml_value should return the raw string for status and let read_ticket's coercion path handle validation -- or wrap the ValueError in TicketParseError here.
