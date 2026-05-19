---
id: tiqt-66f7
status: open
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T08:54:55.795547+00:00
---
# Replace T.Any annotations with concrete types

## Description

Style rules forbid T.Any. Occurrences: cli.py:140 (values: T.Any in a custom Action; should be 'str | T.Sequence[str] | None'), store.py:237 _format_yaml_value, store.py:265 _parse_yaml_value, store.py:281 _parse_frontmatter. Fix: replace with 'str | int | list[str] | None' (the actual frontmatter value union) and propagate. _parse_frontmatter's return type becomes dict[str, str | int | list[str] | None].
