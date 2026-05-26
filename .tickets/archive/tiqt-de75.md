---
id: tiqt-de75
status: closed
type: bug
priority: 2
deps: []
links: []
tags: []
created: 2026-05-19T13:31Z
---
# Reject unknown/malformed frontmatter keys instead of silent drop

## Description

store.py:308-317 -- _parse_frontmatter drops lines missing ': ' separator and ignores unknown keys. A field typo (e.g. 'statu: closed' or 'severity: high') silently reverts to default on next write. Strict mode or warning required.
