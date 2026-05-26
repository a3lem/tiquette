---
id: tiqt-d616
status: closed
type: bug
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T13:31Z
---
# _resolve_or_exit catches ValueError too broadly

## Description

query.py:212 -- except (TicketNotFoundError, ValueError) catches AmbiguousIDError (a ValueError) but also any other ValueError raised inside resolve_id_in_dir. Catch specific exceptions, mirror store.py:639.
