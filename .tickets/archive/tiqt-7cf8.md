---
id: tiqt-7cf8
status: closed
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T11:24Z
---
# Stop calling sys.exit from inside _apply_scope pipeline stage

## Description

query.py:551-587 _apply_scope prints argparse errors and sys.exits mid-pipeline, defeating the point of the scope/filter/output decomposition done in tiqt-ed8c. Raise a local LsArgError (or similar) and handle in _handle_ls. Same leak pattern in _resolve_or_exit (query.py:205) introduced by tiqt-86e8.
