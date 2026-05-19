---
id: tiqt-4e3d
status: open
type: bug
priority: 2
deps: []
links: []
tags: []
created: 2026-05-19T08:55:45.873880+00:00
---
# Validate ticket frontmatter schema instead of trusting **fields

## Description

store.py:343-347 calls 'Ticket(title=title, description=description, **fields)' where fields is the parsed-frontmatter dict. Two problems: (1) 'id' comes from the file body, not from the filename -- file content is silently trusted over the canonical name; (2) any type mismatch (e.g. priority as string) or unknown key crashes inside the dataclass __init__ with an unhelpful TypeError. Fix: add an explicit schema-validation step that (a) cross-checks frontmatter id against the filename, (b) coerces/checks each known field, (c) raises TicketParseError(path, msg) for any mismatch.
