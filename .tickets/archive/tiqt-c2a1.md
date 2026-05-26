---
id: tiqt-c2a1
status: closed
type: bug
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T13:31Z
---
# Stop swallowing AmbiguousIDError for --undep/--unlink removal targets

## Description

store.py _resolve_optional (~line 644) falls back to raw partial on AmbiguousIDError so removal becomes a silent no-op. Add path errors on ambiguity; remove path should match. Document any intentional asymmetry.
