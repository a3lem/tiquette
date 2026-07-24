# Ticket Query

## ADDED Requirements

### Requirement: Recursive listing across stores

The system SHALL accept `-r` / `--recursive` on `tq ls`. WHEN supplied, `ls` SHALL operate over every store discovered per the "Recursive store discovery" requirement (ticket-store), rooted at the `--dir <path>` if given, otherwise the current working directory.

For human-readable output, the system SHALL render each store as a section: a heading line containing the store's directory path relative to the root (the root store's heading SHALL be `.`), followed by that store's ticket listing in the standard format from "List ticket line format" and "List with tree rendering". Stackable filters (`--status`, `--ready`, `--blocked`, `--tag`, `--type`, `--assignee`), the source axis (`--all`, `--archived`), and `--sort` SHALL apply independently within each store. `--limit` SHALL apply within each store. Stores with no tickets matching the active filters SHALL be omitted. Sections SHALL appear in lexicographic order of the store's relative path.

WHEN `--jsonl` is combined with `-r`, the system SHALL instead emit a single flat stream of one JSON object per ticket across all stores, each object carrying a `store` field holding the emitting store's path relative to the root, and SHALL NOT print section headings.

`-r` SHALL be mutually exclusive with `--parent` and `--dep`, which name a single ticket and therefore have no store-independent meaning across an aggregate.

#### Scenario: Recursive listing groups output by store
- Given `packages/api/.tickets/` contains "api-1a2b" titled "API work"
- And `packages/web/.tickets/` contains "web-3c4d" titled "Web work"
- And the current working directory is the monorepo root
- When the user runs `tq ls -r`
- Then a heading "packages/api" appears before the line for "api-1a2b"
- And a heading "packages/web" appears before the line for "web-3c4d"

#### Scenario: Recursive listing orders stores lexicographically
- Given `packages/web/.tickets/` contains "web-3c4d"
- And `packages/api/.tickets/` contains "api-1a2b"
- When the user runs `tq ls -r`
- Then the "packages/api" section appears before the "packages/web" section

#### Scenario: Recursive listing omits stores with no matching tickets
- Given `packages/api/.tickets/` contains open "api-1a2b"
- And `packages/web/.tickets/` contains only closed "web-3c4d"
- When the user runs `tq ls -r --status open`
- Then the output contains "api-1a2b"
- And the output does not contain a "packages/web" heading

#### Scenario: Filters apply within each store
- Given `packages/api/.tickets/` contains "api-1a2b" (tag "urgent") and "api-2b3c" (tag "later")
- And `packages/web/.tickets/` contains "web-3c4d" (tag "urgent")
- When the user runs `tq ls -r --tag urgent`
- Then the output contains "api-1a2b"
- And the output contains "web-3c4d"
- And the output does not contain "api-2b3c"

#### Scenario: Source axis applies within each store
- Given `packages/api/.tickets/` has an archived ticket "api-arch"
- And `packages/web/.tickets/` has an active ticket "web-act"
- When the user runs `tq ls -r --archived`
- Then the output contains "api-arch"
- And the output does not contain "web-act"

#### Scenario: Recursive JSONL emits a flat stream tagged with store
- Given `packages/api/.tickets/` contains "api-1a2b"
- And `packages/web/.tickets/` contains "web-3c4d"
- When the user runs `tq ls -r --jsonl`
- Then one JSON object is printed per line with no section headings
- And the object for "api-1a2b" has a "store" field equal to "packages/api"
- And the object for "web-3c4d" has a "store" field equal to "packages/web"

#### Scenario: Recursive listing includes the root store as "."
- Given `.tickets/` at the root contains "root-0001"
- And `packages/api/.tickets/` contains "api-1a2b"
- When the user runs `tq ls -r`
- Then a heading "." appears before the line for "root-0001"

#### Scenario: -r and --parent are mutually exclusive
- When the user runs `tq ls -r --parent epic-001`
- Then the command exits non-zero

#### Scenario: -r and --dep are mutually exclusive
- When the user runs `tq ls -r --dep task-001`
- Then the command exits non-zero
