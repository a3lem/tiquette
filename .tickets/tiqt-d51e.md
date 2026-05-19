---
id: tiqt-d51e
status: closed
type: chore
priority: 4
deps: []
links: []
tags: []
created: 2026-05-19T13:31:35.717838+00:00
---
# _handle_show reads ticket file twice; reuse read_ticket output

## Description

query.py:309 then 314 or 324 -- read_ticket reads it, then file_path.read_text() reruns split-on-'---' parsing inline. Pass body/raw text out of read_ticket once.
