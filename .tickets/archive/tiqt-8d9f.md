---
id: tiqt-8d9f
status: closed
type: bug
priority: 2
deps: []
links: []
tags: []
created: 2026-05-19T08:55Z
---
# Replace asserts used for file-format validation with real errors

## Description

store.py:322 uses 'assert len(parts) >= 3, ...' to validate the structure of a parsed ticket markdown file. Asserts are stripped under python -O, so a malformed file would then raise a confusing IndexError instead of a clear schema error. Style rule allows aggressive asserts for *programming* errors but file content is external input. Fix: raise a dedicated exception (e.g. TicketParseError) with the file path and a clear message; reserve asserts for invariants the code itself controls.
