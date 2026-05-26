---
id: tiqt-0d9b
status: closed
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T11:24Z
---
# Fix lying return type of _ticket_to_dict

## Description

query.py:289 _ticket_to_dict is annotated dict[str, str | int | list[str] | None], but status is a Status enum (works in json.dumps only because StrEnum subclasses str) and include_body adds a body: str | None. Coerce status to str(t.status) at the boundary, or switch to TypedDict. Follow-up to tiqt-07e1 (extracted the helper).
