---
id: tiqt-f586
status: closed
type: bug
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T13:31Z
---
# Make read_ticket title/section detection structural, not first-match

## Description

store.py:422-430 -- title comes from the first '# ' line anywhere, description marker is first '## Description' substring. Body containing such lines is misparsed. Anchor to a stable contract with write_ticket (e.g. first non-empty line after frontmatter).
