---
id: tiqt-cbe2
status: closed
type: bug
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T13:31Z
---
# ls --type accepts arbitrary strings; constrain to VALID_TYPES

## Description

query.py:124 -- p_ls.add_argument('--type', ...) has no choices=, so 'tq ls --type buggg' matches zero tickets silently while create/edit reject the same value. Use choices=VALID_TYPES from _fields.py.
