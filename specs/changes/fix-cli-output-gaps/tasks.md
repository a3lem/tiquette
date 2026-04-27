# Tasks

## Implementation

- [x] `src/tiquette/store.py`: skip nullable fields when value is `None` in `_serialize_frontmatter`
- [x] `src/tiquette/commands/lifecycle.py`: print ticket ID to stdout after each successful transition
- [x] `src/tiquette/commands/query.py`: add `-a` alias for `--assignee` and `-T` alias for `--tag` on `ls`

## Verification

- [x] Tests for requirement: Transition output (lifecycle)
- [x] Tests for requirement: Ticket file format — nullable fields omitted when null (store)
- [x] Tests for requirement: List tickets — `-a` / `-T` short aliases (query)
