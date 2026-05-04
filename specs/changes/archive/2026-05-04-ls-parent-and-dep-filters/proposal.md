# Add `--parent` and `--dep` filters to `tq ls`

## Why

Two recurring navigation needs aren't covered by current `tq ls` filters:
- Seeing every ticket under a given parent or ancestor as a tree (useful for working an epic).
- Seeing every ticket that depends on a given ticket (useful for impact analysis before closing or changing it).

## What Changes

- Add `--parent <id>` to `tq ls`. Restricts the candidate set to the named ticket and all its transitive descendants. Output uses the existing tree rendering with the named ticket as the root.
- Add `--dep <id>` to `tq ls`. Restricts the candidate set to tickets whose `deps` directly contain `<id>`. Output is a flat list (no tree rendering).
- Both flags resolve `<id>` through the standard partial-ID resolution used elsewhere.
- Both flags stack with all existing filters (`--status`, `--ready`, `--blocked`, `--tag`, `--type`, `--assignee`, `--limit`, `--sort`, `--archived`, `--all`).
- `--parent` and `--dep` are mutually exclusive with each other.

## Capabilities

### Modified Capabilities

- `ticket-query`: Adds two source-set filters to `tq ls`.

## Impact

- Affects the `tq ls` command surface and its argument parser.
- No data model changes; both filters operate on existing `parent` and `deps` frontmatter fields.
- No changes to `--jsonl` field schema.
