---
id: tiqt-cac3
status: closed
type: bug
priority: 2
deps: []
links: []
tags: []
created: 2026-05-19T11:24:53.384996+00:00
---
# Stop swallowing TicketsNotFoundError silently in _handle_status

## Description

lifecycle.py:137-141 has 'except TicketsNotFoundError: return' -- violates the no-silent-errors style rule. cli.py:192 already handles the bare-tq case. Let it propagate. Follow-up to tiqt-5781 (dict.get silent defaults) and tiqt-8d9f (real errors over asserts).
