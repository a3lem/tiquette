# Ticket Query

Covers commands for viewing and listing tickets: `show`, `info`, `ls`, `dep tree`, `tags`, `archive`, `path`.

## Requirement: Show ticket

The system SHALL display full content (frontmatter + body) for every ticket ID supplied when `tq show <id>...` is invoked, whether each ticket is active or archived. At least one ID SHALL be required. The system SHALL resolve all supplied IDs before printing anything; IF any ID is unknown or ambiguous, the system SHALL exit non-zero and print nothing to stdout. IDs that resolve to the same ticket SHALL be displayed once, in first-seen order. WHEN `--json` is supplied with a single ID, the output SHALL be one JSON object (unchanged shape). WHEN `--json` is supplied with multiple IDs, the output SHALL be one JSON array of those objects, in display order.

### Scenario: Show displays ticket content
- Given ticket "show-001" exists with title "Test ticket"
- When the user runs `tq show show-001`
- Then the command exits 0
- And the output contains "id: show-001"
- And the output contains "# Test ticket"

### Scenario: Show displays all frontmatter fields
- Given ticket "show-001" exists
- When the user runs `tq show show-001`
- Then the output contains `status:`, `deps:`, `links:`, `type:`, `priority:`

### Scenario: Show displays blockers section
- Given ticket "show-001" depends on "show-002" (status open)
- When the user runs `tq show show-001`
- Then the output contains "## Blockers"
- And the output contains "show-002 [open]"

### Scenario: Show hides blockers when all deps are in terminal status
- Given ticket "show-001" depends on "show-002" (status closed)
- When the user runs `tq show show-001`
- Then the output does not contain "## Blockers"

### Scenario: Show displays blocking section (reverse deps)
- Given ticket "show-002" depends on "show-001"
- When the user runs `tq show show-001`
- Then the output contains "## Blocking"
- And the output contains "show-002"

### Scenario: Show displays children section
- Given ticket "show-002" has parent "show-001"
- When the user runs `tq show show-001`
- Then the output contains "## Children"
- And the output contains "show-002"

### Scenario: Show displays linked section
- Given ticket "show-001" is linked to "show-002"
- When the user runs `tq show show-001`
- Then the output contains "## Linked"
- And the output contains "show-002"

### Scenario: Show non-existent ticket
- When the user runs `tq show nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

### Scenario: Show with partial ID
- Given ticket "show-001" exists
- When the user runs `tq show 001`
- Then the command exits 0
- And the output contains "id: show-001"

### Scenario: Show as JSON
- Given ticket "show-001" exists
- When the user runs `tq show show-001 --json`
- Then the command exits 0
- And the output is valid JSON
- And the JSON contains fields: id, status, type, priority, title, body

### Scenario: Show displays an archived ticket
- Given ticket "show-010" is closed and archived
- When the user runs `tq show show-010`
- Then the command exits 0
- And the output contains "id: show-010"

### Scenario: Show resolves an archived ticket by partial ID
- Given ticket "show-011" is closed and archived
- When the user runs `tq show 011`
- Then the command exits 0
- And the output contains "id: show-011"

### Scenario: Show renders an archived ticket's reverse dependency
- Given ticket "show-012" depends on "show-013"
- And "show-012" and "show-013" are closed and archived together
- When the user runs `tq show show-013`
- Then the command exits 0
- And the output contains "## Blocking"
- And the output contains "show-012"

### Scenario: Show multiple tickets
- Given tickets "show-001" and "show-002" exist
- When the user runs `tq show show-001 show-002`
- Then the command exits 0
- And the output contains "id: show-001"
- And the output contains "id: show-002"

### Scenario: Show multiple tickets with one unknown prints nothing
- Given ticket "show-001" exists
- When the user runs `tq show show-001 nonexistent`
- Then the command exits non-zero
- And stdout is empty
- And stderr contains "ticket 'nonexistent' not found"

### Scenario: Show multiple tickets as JSON emits an array
- Given tickets "show-001" and "show-002" exist
- When the user runs `tq show show-001 show-002 --json`
- Then the command exits 0
- And the output is one valid JSON array with two objects
- And the objects cover "show-001" and "show-002" in argument order

### Scenario: Show deduplicates repeated IDs
- Given ticket "show-001" exists
- When the user runs `tq show show-001 show-001`
- Then the command exits 0
- And the output contains "id: show-001" exactly once

## Requirement: Info command

The system SHALL display frontmatter and computed relationships (without body content) for every ticket ID supplied when `tq info <id>...` is invoked, whether each ticket is active or archived. At least one ID SHALL be required. The system SHALL resolve all supplied IDs before printing anything; IF any ID is unknown or ambiguous, the system SHALL exit non-zero and print nothing to stdout. IDs that resolve to the same ticket SHALL be displayed once, in first-seen order. WHEN `--json` is supplied with a single ID, the output SHALL be one JSON object (unchanged shape). WHEN `--json` is supplied with multiple IDs, the output SHALL be one JSON array of those objects, in display order.

### Scenario: Info displays frontmatter and relationships
- Given ticket "info-001" exists with title "Test ticket"
- And ticket "info-002" depends on "info-001"
- When the user runs `tq info info-001`
- Then the command exits 0
- And the output contains "id: info-001"
- And the output contains "## Blocking"
- And the output does not contain `## Description`

### Scenario: Info as JSON
- Given ticket "info-001" exists
- When the user runs `tq info info-001 --json`
- Then the command exits 0
- And the output is valid JSON
- And the JSON contains computed relationship fields

### Scenario: Info non-existent ticket
- When the user runs `tq info nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

### Scenario: Info displays an archived ticket
- Given ticket "info-010" is closed and archived
- When the user runs `tq info info-010`
- Then the command exits 0
- And the output contains "id: info-010"

### Scenario: Info multiple tickets
- Given tickets "info-001" and "info-002" exist
- When the user runs `tq info info-001 info-002`
- Then the command exits 0
- And the output contains "id: info-001"
- And the output contains "id: info-002"

### Scenario: Info multiple tickets as JSON emits an array
- Given tickets "info-001" and "info-002" exist
- When the user runs `tq info info-001 info-002 --json`
- Then the command exits 0
- And the output is one valid JSON array with two objects

## Requirement: List tickets

The system SHALL list tickets matching filter criteria when `tq ls` is invoked. With no source-selection flag, only active (non-archived) tickets are considered. With no status filter, all statuses within the selected source set are shown, sorted by priority. The `--status` filter (short: `-s`) accepts one of `open`, `in_progress`, `closed`, `canceled`. Source selection (`--archived`, `--all`) is governed by the "List source axis" requirement. The `-T` short for `--tag` SHALL NOT be accepted.

### Scenario: List all open tickets
- Given tickets "list-0001" and "list-0002" exist (status open)
- When the user runs `tq ls`
- Then the output contains both ticket IDs

### Scenario: Default excludes archived
- Given active ticket "act-001" and archived ticket "arc-001" exist
- When the user runs `tq ls`
- Then the output contains "act-001"
- And the output does not contain "arc-001"

### Scenario: List with --status open
- Given "list-0001" is open and "list-0002" is closed
- When the user runs `tq ls --status open`
- Then the output contains "list-0001"
- And the output does not contain "list-0002"

### Scenario: List with -s closed
- Given "list-0001" is open and "list-0002" is closed
- When the user runs `tq ls -s closed`
- Then the output contains "list-0002"
- And the output does not contain "list-0001"

### Scenario: List with --status canceled
- Given "list-0001" is canceled and "list-0002" is closed
- When the user runs `tq ls --status canceled`
- Then the output contains "list-0001"
- And the output does not contain "list-0002"

### Scenario: List shows dependencies
- Given ticket "list-0001" depends on "list-0002"
- When the user runs `tq ls`
- Then the output contains "<- [list-0002]"

### Scenario: List with no tickets
- Given the tickets directory is empty
- When the user runs `tq ls`
- Then the output is empty

### Scenario: Ready filter (no deps)
- Given "ready-001" has no deps and no open children, and "ready-002" depends on open "ready-003"
- When the user runs `tq ls --ready`
- Then the output contains "ready-001"
- And the output does not contain "ready-002"

### Scenario: Ready includes tickets with all deps in terminal status
- Given "ready-001" depends on "ready-002" (status closed)
- When the user runs `tq ls --ready`
- Then the output contains "ready-001"

### Scenario: Ready excludes terminal tickets
- Given "ready-001" has status closed
- When the user runs `tq ls --ready`
- Then the output does not contain "ready-001"

### Scenario: Ready excludes parent with open children
- Given "ready-001" has open child "ready-002"
- When the user runs `tq ls --ready`
- Then the output does not contain "ready-001"

### Scenario: Ready sorts by priority then ID
- Given tickets with varying priorities exist
- When the user runs `tq ls --ready`
- Then tickets are sorted by priority ascending, then by ID

### Scenario: Blocked by open dependency
- Given "block-001" depends on open "block-002"
- When the user runs `tq ls --blocked`
- Then the output contains "block-001"
- And the output shows only non-terminal blockers

### Scenario: Blocked by open children
- Given "block-001" has open child "block-003"
- When the user runs `tq ls --blocked`
- Then the output contains "block-001"

### Scenario: Blocked excludes tickets with all deps terminal and no open children
- Given "block-001" depends on "block-002" (status closed) and has no open children
- When the user runs `tq ls --blocked`
- Then the output does not contain "block-001"

### Scenario: Limit
- Given two closed tickets exist
- When the user runs `tq ls --status closed --limit 1`
- Then the output has exactly 1 line

### Scenario: JSONL output
- Given ticket "query-001" exists
- When the user runs `tq ls --jsonl`
- Then the output is valid JSONL
- And each line has fields: id, status, deps, links, type, priority
- And no line contains a `resolution` field

### Scenario: Filter by assignee
- Given "t-001" has assignee "Alice" and "t-002" has assignee "Bob"
- When the user runs `tq ls --assignee Alice`
- Then the output contains "t-001"
- And the output does not contain "t-002"

### Scenario: -A is short for --assignee
- Given "t-001" has assignee "Alice" and "t-002" has assignee "Bob"
- When the user runs `tq ls -A Alice`
- Then the output contains "t-001"
- And the output does not contain "t-002"

### Scenario: Filter by tag
- Given "t-001" has tag "ui" and "t-002" has tag "backend"
- When the user runs `tq ls --tag ui`
- Then the output contains "t-001"
- And the output does not contain "t-002"

### Scenario: -T is not accepted as a short for --tag
- When the user runs `tq ls -T ui`
- Then the command exits non-zero

### Scenario: Filter by type
- Given "t-001" has type "bug" and "t-002" has type "task"
- When the user runs `tq ls --type bug`
- Then the output contains "t-001"
- And the output does not contain "t-002"

### Scenario: Sort by mtime
- Given tickets exist with different modification times
- When the user runs `tq ls --sort mtime`
- Then tickets are sorted by modification time

### Scenario: --status completed is rejected
- When the user runs `tq ls --status completed`
- Then the command exits non-zero
- And stderr indicates `closed` is the accepted spelling

### Scenario: --completed flag is rejected
- When the user runs `tq ls --completed`
- Then the command exits non-zero

### Scenario: --canceled flag is rejected
- When the user runs `tq ls --canceled`
- Then the command exits non-zero

### Scenario: Invalid status rejected
- When the user runs `tq ls --status invalid`
- Then the command exits non-zero

### Scenario: Invalid sort rejected
- When the user runs `tq ls --sort invalid`
- Then the command exits non-zero

### Scenario: Ready and blocked are mutually exclusive
- When the user runs `tq ls --ready --blocked`
- Then the command exits non-zero

### Scenario: Limit must be positive
- When the user runs `tq ls --limit 0`
- Then the command exits non-zero

## Requirement: List ticket line format

The system SHALL format each ticket line in `ls` output as: `<id> <tags> - <checkbox> <title>` where:

- The checkbox represents lifecycle state derived from `status` alone: `[ ]` for `open`, `[/]` for `in_progress`, `[x]` for `closed`, and `[~]` for `canceled`.
- Zero or more tag tokens may appear after the ID, each individually bracketed:
  - The priority tag `[P<n>]` SHALL be shown only when priority is not 2 (the default).
  - The type tag (e.g. `[epic]`, `[feature]`) SHALL be shown only when the type is not "task" (the default).
  - When both are present, priority comes first: `[P1][epic]` (no space between tags).
- When no tags are present, the format collapses to `<id> - <checkbox> <title>`.
- Dependencies are appended after the title as a comma-separated list: `<- [dep-id1, dep-id2]`.

### Scenario: Default priority and type hidden
- Given ticket "fmt-001" exists with priority 2, type "task", status open, title "Fix login"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 - [ ] Fix login`

### Scenario: Non-default priority shown
- Given ticket "fmt-001" exists with priority 1, type "task", status open, title "Fix login"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 [P1] - [ ] Fix login`

### Scenario: Non-default type shown
- Given ticket "fmt-001" exists with priority 2, type "feature", status open, title "Add export"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 [feature] - [ ] Add export`

### Scenario: Both non-default priority and type shown
- Given ticket "fmt-001" exists with priority 3, type "epic", status open, title "Refactor"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 [P3][epic] - [ ] Refactor`

### Scenario: In-progress renders half checkbox
- Given ticket "fmt-001" exists with priority 2, type "task", status in_progress, title "Working"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 - [/] Working`

### Scenario: Closed renders checked checkbox
- Given ticket "fmt-001" exists with status closed
- When the user runs `tq ls --status closed`
- Then the line contains `[x]`

### Scenario: Canceled renders tilde checkbox
- Given ticket "fmt-001" exists with status canceled
- When the user runs `tq ls --status canceled`
- Then the line contains `[~]`
- And the line does not contain `[x]`

### Scenario: Single dependency appended after title
- Given ticket "fmt-001" depends on "fmt-002"
- When the user runs `tq ls`
- Then the line for "fmt-001" ends with `<- [fmt-002]`

### Scenario: Multiple dependencies appended after title
- Given ticket "fmt-001" depends on "fmt-002" and "fmt-003"
- When the user runs `tq ls`
- Then the line for "fmt-001" ends with `<- [fmt-002, fmt-003]`

## Requirement: List with tree rendering

The system SHALL render parent-child relationships as indented trees in `ls` output by default. Each node in the tree uses the line format from "List ticket line format", with box-drawing characters prepended for child nodes.

### Scenario: Parent with children indented
- Given ticket "tree-0001" has children "tree-0002" and "tree-0003"
- When the user runs `tq ls`
- Then "tree-0001" appears at root level
- And "tree-0002" and "tree-0003" appear indented with box-drawing characters

### Scenario: Nested children with deeper indentation
- Given "tree-0001" → "tree-0002" → "tree-0003" (parent chain)
- When the user runs `tq ls`
- Then each level is indented deeper with box-drawing characters

### Scenario: Orphan tickets at root level
- Given ticket "tree-0001" has no parent
- When the user runs `tq ls`
- Then "tree-0001" appears at root level without indentation

### Scenario: Parent shown as context heading in filtered views
- Given "tree-0001" has child "tree-0002" (ready) and child "tree-0003" (blocked)
- When the user runs `tq ls --ready`
- Then "tree-0001" appears as context heading
- And "tree-0002" appears indented
- And "tree-0003" does not appear

### Scenario: Parent hidden when all children filtered out
- Given "tree-0001" has child "tree-0002" (ready, no deps)
- When the user runs `tq ls --blocked`
- Then neither "tree-0001" nor "tree-0002" appears

## Requirement: Show dependency tree

The system SHALL display a transitive dependency tree when `tq deps <id>` is invoked. The root and any transitive dependency may be active or archived.

### Scenario: Dependency tree shows transitive deps
- Given "task-0001" depends on "task-0002", which depends on "task-0003"
- When the user runs `tq deps task-0001`
- Then the output contains all three IDs with status and title
- And the output uses box-drawing characters

### Scenario: Dependency tree with multiple children
- Given "task-0001" depends on both "task-0002" and "task-0003"
- When the user runs `tq deps task-0001`
- Then the output contains both dependencies

### Scenario: Full tree disables deduplication
- Given a diamond dependency pattern
- When the user runs `tq deps --full task-0001`
- Then shared dependencies appear multiple times

### Scenario: Children sorted by subtree depth then ID
- Given dependencies with varying subtree depths
- When the user runs `tq deps task-0001`
- Then children are sorted by subtree depth ascending, then by ID

### Scenario: Dependency tree rooted at an archived ticket
- Given "task-0010" depends on "task-0011"
- And "task-0010" and "task-0011" are closed and archived
- When the user runs `tq deps task-0010`
- Then the output contains both "task-0010" and "task-0011" with status and title

## Requirement: Tags listing

The system SHALL list all tags with counts when `tq tags` is invoked. Only open/in_progress tickets are counted by default.

### Scenario: Tags sorted by count descending
- Given tickets with various tags exist
- When the user runs `tq tags`
- Then tags are listed with counts, most frequent first

### Scenario: Tags excludes terminal tickets by default
- Given a tag appears on both open and closed tickets
- When the user runs `tq tags`
- Then the count reflects only open/in_progress tickets

## Requirement: Links listing

The system SHALL list all linked pairs across tickets when `tq links` is invoked.

### Scenario: Links lists all pairs
- Given tickets with various links exist
- When the user runs `tq links`
- Then the output shows all linked pairs

## Requirement: Archive

The system SHALL move tickets in a terminal status (`closed` or `canceled`) to `.tickets/archive/` when `tq archive` is invoked.

The system SHALL NOT archive a terminal ticket when any non-archived ticket references it via `deps`, `links`, or `parent`. Referenced tickets are skipped with a diagnostic on stderr naming the referrers.

When a ticket is blocked from archiving, any terminal ticket it references SHALL also be blocked (cascading). The archivable set is computed iteratively until stable.

### Scenario: Archive moves terminal tickets
- Given tickets "t-001" (closed) and "t-002" (open) exist
- When the user runs `tq archive`
- Then "t-001" exists in `.tickets/archive/`
- And "t-001" does not exist in `.tickets/`
- And "t-002" remains in `.tickets/`

### Scenario: Archive moves canceled tickets
- Given tickets "t-001" (canceled) and "t-002" (open) exist
- When the user runs `tq archive`
- Then "t-001" exists in `.tickets/archive/`
- And "t-002" remains in `.tickets/`

### Scenario: No terminal tickets
- Given all tickets are open or in_progress
- When the user runs `tq archive`
- Then the output contains "No closed or canceled tickets to archive"

### Scenario: Archive creates directory on first use
- Given a closed ticket exists and no archive directory
- When the user runs `tq archive`
- Then `.tickets/archive/` is created

### Scenario: Archive is idempotent
- Given a closed ticket exists
- When the user runs `tq archive` twice
- Then the second run reports no tickets to archive

### Scenario: Archived ticket file is intact
- Given ticket "t-001" is closed and archived
- Then the archived file contains the original frontmatter and content

### Scenario: Skips ticket referenced as dependency
- Given closed ticket "t-001" and open ticket "t-002" with deps including "t-001"
- When the user runs `tq archive`
- Then "t-001" remains in `.tickets/`
- And stderr contains "Skipped t-001: referenced by t-002"

### Scenario: Skips ticket referenced as link
- Given closed ticket "t-001" and open ticket "t-002" with links including "t-001"
- When the user runs `tq archive`
- Then "t-001" remains in `.tickets/`
- And stderr contains "Skipped t-001"

### Scenario: Skips ticket that is a parent
- Given closed ticket "t-001" and open ticket "t-002" with parent "t-001"
- When the user runs `tq archive`
- Then "t-001" remains in `.tickets/`
- And stderr contains "Skipped t-001"

### Scenario: Mutually-terminal group archives together
- Given closed tickets "t-001" and "t-002" linked to each other, no open tickets reference either
- When the user runs `tq archive`
- Then both "t-001" and "t-002" are moved to `.tickets/archive/`

### Scenario: Cascade blocks dependent terminal tickets
- Given closed "t-b" and closed "t-a" (deps: ["t-b"]), and open "t-c" (deps: ["t-a"])
- When the user runs `tq archive`
- Then "t-a" remains (referenced by open "t-c")
- And "t-b" remains (referenced by remaining "t-a")
- And stderr contains "Skipped"

### Scenario: No eligible tickets
- Given closed ticket "t-001" and open ticket "t-002" with deps including "t-001"
- When the user runs `tq archive`
- Then the output contains "No closed or canceled tickets eligible for archiving"

## Requirement: Path command

The system SHALL print the file path of every ticket ID supplied, one per line in argument order, when `tq path <id>...` is invoked, whether each ticket is active or archived. At least one ID SHALL be required. The system SHALL resolve all supplied IDs before printing anything; IF any ID is unknown or ambiguous, the system SHALL exit non-zero and print nothing to stdout. IDs that resolve to the same ticket SHALL be printed once, in first-seen order.

### Scenario: Path prints file location
- Given ticket "test-001" exists
- When the user runs `tq path test-001`
- Then the output contains ".tickets/test-001.md"

### Scenario: Path prints archive file location
- Given ticket "test-010" is closed and archived
- When the user runs `tq path test-010`
- Then the output contains ".tickets/archive/test-010.md"

### Scenario: Path prints multiple locations
- Given tickets "test-001" and "test-002" exist
- When the user runs `tq path test-001 test-002`
- Then the output has one path per line
- And the output contains ".tickets/test-001.md"
- And the output contains ".tickets/test-002.md"

### Scenario: Path with one unknown ID prints nothing
- Given ticket "test-001" exists
- When the user runs `tq path test-001 nonexistent`
- Then the command exits non-zero
- And stdout is empty

## Requirement: List source axis

The system SHALL provide a source-selection axis on `tq ls` that controls whether active tickets, archived tickets, or both are considered. The axis has three states: default (active only), `--archived` (archived only), and `--all` (active + archived).

`--archived` and `--all` SHALL be mutually exclusive. They SHALL combine freely with the status filter (`--status` / `-s`) and with stackable filters (`--tag`, `--type`, `--assignee`).

### Scenario: --archived shows only archived tickets
- Given active ticket "act-001" and archived ticket "arc-001" exist
- When the user runs `tq ls --archived`
- Then the output contains "arc-001"
- And the output does not contain "act-001"

### Scenario: --all shows active and archived
- Given active ticket "act-001" and archived ticket "arc-001" exist
- When the user runs `tq ls --all`
- Then the output contains "act-001"
- And the output contains "arc-001"

### Scenario: -a is short for --all
- Given active ticket "act-001" and archived ticket "arc-001" exist
- When the user runs `tq ls -a`
- Then the output contains "act-001"
- And the output contains "arc-001"

### Scenario: --archived combines with --status canceled
- Given archived ticket "arc-001" has status canceled
- And archived ticket "arc-002" has status closed
- When the user runs `tq ls --archived --status canceled`
- Then the output contains "arc-001"
- And the output does not contain "arc-002"

### Scenario: --archived combines with -s closed
- Given archived ticket "arc-001" has status closed
- And archived ticket "arc-002" has status canceled
- When the user runs `tq ls --archived -s closed`
- Then the output contains "arc-001"
- And the output does not contain "arc-002"

### Scenario: --all combines with --status closed
- Given active "done-001" has status closed
- And archived "done-002" has status closed
- And active "done-003" has status canceled
- When the user runs `tq ls --all --status closed`
- Then the output contains "done-001"
- And the output contains "done-002"
- And the output does not contain "done-003"

### Scenario: --archived combines with --tag
- Given archived ticket "arc-001" has tag "ui"
- And archived ticket "arc-002" has tag "backend"
- When the user runs `tq ls --archived --tag ui`
- Then the output contains "arc-001"
- And the output does not contain "arc-002"

### Scenario: --archived with no archived tickets
- Given no archived tickets exist
- When the user runs `tq ls --archived`
- Then the output is empty

### Scenario: --all and --archived mutually exclusive
- When the user runs `tq ls --all --archived`
- Then the command exits non-zero

## Requirement: List filtered by parent

The system SHALL restrict `tq ls` to a named ticket and its transitive descendants when `--parent <id>` is supplied. The named ticket appears as the root of the tree; its descendants appear nested beneath it via the existing tree rendering. `<id>` SHALL be resolved using the standard partial-ID resolution against the ticket set selected by the source axis (default active; `--archived` resolves against archived; `--all` resolves against both). `--parent` SHALL stack with all other filters; rows that survive the descendant restriction are then subject to `--status`, `--ready`, `--blocked`, `--tag`, `--type`, `--assignee`, `--limit`, `--sort`, `--archived`, and `--all`. WHEN the named root itself does not satisfy a stacked filter (e.g. `--status`, `--ready`, `--blocked`, `--tag`), the system SHALL still display the root as a context heading (line format from "List ticket line format", with no dependency suffix), so the subtree never appears unrooted. `--parent` and `--dep` SHALL be mutually exclusive.

### Scenario: Parent shows itself and descendants
- Given "epic-001" has child "task-001" which has child "task-002"
- And unrelated ticket "other-001" exists
- When the user runs `tq ls --parent epic-001`
- Then the output contains "epic-001"
- And the output contains "task-001"
- And the output contains "task-002"
- And the output does not contain "other-001"

### Scenario: Parent renders as tree with root
- Given "epic-001" has child "task-001"
- When the user runs `tq ls --parent epic-001`
- Then "epic-001" appears at root level without indentation
- And "task-001" appears indented beneath "epic-001" with box-drawing characters

### Scenario: Parent accepts partial ID
- Given "epic-001" has child "task-001"
- When the user runs `tq ls --parent 001`
- Then the output contains "epic-001"
- And the output contains "task-001"

### Scenario: Parent with non-existent ID
- When the user runs `tq ls --parent nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

### Scenario: Parent with leaf ticket (no descendants)
- Given "leaf-001" has no children
- When the user runs `tq ls --parent leaf-001`
- Then the output contains "leaf-001"
- And no indented child rows appear

### Scenario: Parent stacks with --ready
- Given "epic-001" has children "task-001" (ready, no deps) and "task-002" (blocked by open "task-003")
- When the user runs `tq ls --parent epic-001 --ready`
- Then the output contains "task-001"
- And the output does not contain "task-002"

### Scenario: Parent stacks with --status
- Given "epic-001" has children "task-001" (open) and "task-002" (closed)
- When the user runs `tq ls --parent epic-001 --status closed`
- Then the output contains "task-002"
- And the output does not contain "task-001"

### Scenario: Parent stacks with --tag
- Given "epic-001" has children "task-001" (tag "ui") and "task-002" (tag "backend")
- When the user runs `tq ls --parent epic-001 --tag ui`
- Then the output contains "task-001"
- And the output does not contain "task-002"

### Scenario: Parent root is shown as context when filtered out
- Given "epic-001" (status open) has child "task-001" (status closed)
- When the user runs `tq ls --parent epic-001 --status closed`
- Then the output contains "epic-001" rendered as a context heading at the root
- And the output contains "task-001" indented beneath it

### Scenario: Parent does not climb above the named root
- Given "grand-epic-000" has child "epic-001" which has child "task-001"
- When the user runs `tq ls --parent epic-001`
- Then the output contains "epic-001" at root level
- And the output contains "task-001"
- And the output does not contain "grand-epic-000"

## Requirement: List filtered by dependent

The system SHALL restrict `tq ls` to tickets whose `deps` field directly contains `<id>` when `--dep <id>` is supplied. Only direct dependents are included; transitive dependents (tickets that reach `<id>` through a chain of deps) are not. The output SHALL be a flat list using the standard line format from "List ticket line format"; tree rendering from "List with tree rendering" is suppressed under `--dep`. `<id>` SHALL be resolved using the standard partial-ID resolution against the ticket set selected by the source axis (default active; `--archived` resolves against archived; `--all` resolves against both). `--dep` SHALL stack with all other filters. Ambiguous partial `<id>` matches SHALL be rejected per the id-resolution capability (exit non-zero, list candidates on stderr). `--dep` and `--parent` SHALL be mutually exclusive.

### Scenario: Dep shows direct dependents
- Given "task-002" has deps containing "task-001"
- And "task-003" has deps containing "task-001"
- And unrelated "other-001" exists
- When the user runs `tq ls --dep task-001`
- Then the output contains "task-002"
- And the output contains "task-003"
- And the output does not contain "other-001"

### Scenario: Dep excludes transitive dependents
- Given "task-002" has deps containing "task-001"
- And "task-003" has deps containing "task-002" (but not "task-001")
- When the user runs `tq ls --dep task-001`
- Then the output contains "task-002"
- And the output does not contain "task-003"

### Scenario: Dep excludes the target ticket itself
- Given "task-002" has deps containing "task-001"
- When the user runs `tq ls --dep task-001`
- Then the output does not contain "task-001"

### Scenario: Dep with no dependents
- Given no ticket has "leaf-001" in its deps
- When the user runs `tq ls --dep leaf-001`
- Then the output is empty

### Scenario: Dep accepts partial ID
- Given "task-002" has deps containing "task-001"
- When the user runs `tq ls --dep 001`
- Then the output contains "task-002"

### Scenario: Dep with non-existent ID
- When the user runs `tq ls --dep nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

### Scenario: Dep output is flat (no tree)
- Given "parent-001" has child "task-002"
- And "task-002" has deps containing "task-001"
- When the user runs `tq ls --dep task-001`
- Then "task-002" appears at root level without indentation
- And "parent-001" does not appear as a context heading

### Scenario: Dep stacks with --status
- Given "task-002" (open) and "task-003" (closed) both have deps containing "task-001"
- When the user runs `tq ls --dep task-001 --status open`
- Then the output contains "task-002"
- And the output does not contain "task-003"

### Scenario: Dep stacks with --tag
- Given "task-002" (tag "ui") and "task-003" (tag "backend") both have deps containing "task-001"
- When the user runs `tq ls --dep task-001 --tag ui`
- Then the output contains "task-002"
- And the output does not contain "task-003"

### Scenario: --parent and --dep mutually exclusive
- When the user runs `tq ls --parent epic-001 --dep task-001`
- Then the command exits non-zero

## Requirement: Prune command

The system SHALL permanently delete archived tickets matching the supplied filters when `tq prune` is invoked. Prune SHALL operate only on `.tickets/archive/`; it SHALL NOT consider or modify active tickets.

At least one filter SHALL be supplied. IF no filter (`--status`, `--type`, `--before`) is given, the system SHALL exit non-zero with a usage error and delete nothing.

Filters combine with logical AND. The available filters are:
- `--status` (short: `-s`) accepts one of `closed` or `canceled`.
- `--type` (short: `-t`) accepts one of `bug`, `feature`, `task`, `epic`, `chore`.
- `--before` accepts a `YYYY-MM-DD` date and matches archived tickets whose `created` timestamp is strictly before midnight (00:00) of that date. IF the value is not a valid `YYYY-MM-DD` date, the system SHALL exit non-zero with a usage error and delete nothing.

By default the command performs a dry run: it SHALL print every archived ticket that matches the filters, SHALL print a summary line stating the count of tickets that would be deleted and that `-y` is required to delete them, and SHALL delete nothing. WHEN `-y` / `--yes` is supplied, the system SHALL delete the matching ticket files from `.tickets/archive/`.

Prune SHALL NOT perform referential-integrity checks. Deleting an archived ticket still referenced by an active ticket's `deps`, `links`, or `parent` is permitted and leaves a dangling reference; detecting and repairing such references is the responsibility of `tq validate` / `tq autofix`.

### Scenario: Prune deletes matching canceled tickets with confirmation
- Given archived tickets "arc-001" (status `canceled`) and "arc-002" (status `closed`)
- When the user runs `tq prune --status canceled -y`
- Then the command exits 0
- And "arc-001" no longer exists in `.tickets/archive/`
- And "arc-002" still exists in `.tickets/archive/`

### Scenario: Dry run by default deletes nothing
- Given an archived ticket "arc-001" with status `canceled`
- When the user runs `tq prune --status canceled`
- Then the command exits 0
- And stdout contains "arc-001"
- And stdout contains a summary line reporting "1" ticket would be deleted
- And stdout indicates `-y` is required to delete
- And "arc-001" still exists in `.tickets/archive/`

### Scenario: Bare prune is rejected
- Given an archived ticket "arc-001" exists
- When the user runs `tq prune`
- Then the command exits non-zero
- And stderr indicates at least one filter is required
- And "arc-001" still exists in `.tickets/archive/`

### Scenario: Filters combine with AND
- Given archived ticket "arc-001" (status `canceled`, type `bug`)
- And archived ticket "arc-002" (status `canceled`, type `task`)
- When the user runs `tq prune --status canceled --type bug -y`
- Then the command exits 0
- And "arc-001" no longer exists in `.tickets/archive/`
- And "arc-002" still exists in `.tickets/archive/`

### Scenario: Before filters on created date
- Given archived ticket "arc-001" created "2025-06-01T10:00:00"
- And archived ticket "arc-002" created "2026-03-01T10:00:00"
- When the user runs `tq prune --before 2026-01-01 -y`
- Then the command exits 0
- And "arc-001" no longer exists in `.tickets/archive/`
- And "arc-002" still exists in `.tickets/archive/`

### Scenario: Prune ignores active tickets
- Given an active ticket "act-001" with status `canceled`
- And no archive directory exists
- When the user runs `tq prune --status canceled -y`
- Then the command exits 0
- And "act-001" still exists as an active ticket

### Scenario: No matches reports nothing pruned
- Given an archived ticket "arc-001" with status `closed`
- When the user runs `tq prune --status canceled -y`
- Then the command exits 0
- And stdout indicates no tickets matched

### Scenario: Prune rejects invalid status
- When the user runs `tq prune --status open`
- Then the command exits non-zero

### Scenario: Prune rejects invalid type
- When the user runs `tq prune --type invalid`
- Then the command exits non-zero

### Scenario: Prune rejects invalid before date
- When the user runs `tq prune --before not-a-date`
- Then the command exits non-zero

### Scenario: Prune accepts short flags
- Given archived ticket "arc-001" (status `canceled`, type `bug`)
- And archived ticket "arc-002" (status `closed`, type `task`)
- When the user runs `tq prune -s canceled -t bug -y`
- Then the command exits 0
- And "arc-001" no longer exists in `.tickets/archive/`
- And "arc-002" still exists in `.tickets/archive/`

### Scenario: Prune allows deleting a ticket still referenced by an active ticket
- Given an active ticket "act-001" with a dep on "arc-001"
- And an archived ticket "arc-001" with status `closed`
- When the user runs `tq prune --status closed -y`
- Then the command exits 0
- And "arc-001" no longer exists in `.tickets/archive/`

## Requirement: Recursive listing across stores

The system SHALL accept `-r` / `--recursive` on `tq ls`. WHEN supplied, `ls` SHALL operate over every store discovered per the "Recursive store discovery" requirement (ticket-store), rooted at the `--dir <path>` if given, otherwise the current working directory.

For human-readable output, the system SHALL render each store as a section: a heading line containing the store's directory path relative to the root (the root store's heading SHALL be `.`), followed by that store's ticket listing in the standard format from "List ticket line format" and "List with tree rendering". Stackable filters (`--status`, `--ready`, `--blocked`, `--tag`, `--type`, `--assignee`), the source axis (`--all`, `--archived`), and `--sort` SHALL apply independently within each store. `--limit` SHALL apply within each store. Stores with no tickets matching the active filters SHALL be omitted. Sections SHALL appear in lexicographic order of the store's relative path.

WHEN `--jsonl` is combined with `-r`, the system SHALL instead emit a single flat stream of one JSON object per ticket across all stores, each object carrying a `store` field holding the emitting store's path relative to the root, and SHALL NOT print section headings.

`-r` SHALL be mutually exclusive with `--parent` and `--dep`, which name a single ticket and therefore have no store-independent meaning across an aggregate.

### Scenario: Recursive listing groups output by store
- Given `packages/api/.tickets/` contains "api-1a2b" titled "API work"
- And `packages/web/.tickets/` contains "web-3c4d" titled "Web work"
- And the current working directory is the monorepo root
- When the user runs `tq ls -r`
- Then a heading "packages/api" appears before the line for "api-1a2b"
- And a heading "packages/web" appears before the line for "web-3c4d"

### Scenario: Recursive listing orders stores lexicographically
- Given `packages/web/.tickets/` contains "web-3c4d"
- And `packages/api/.tickets/` contains "api-1a2b"
- When the user runs `tq ls -r`
- Then the "packages/api" section appears before the "packages/web" section

### Scenario: Recursive listing omits stores with no matching tickets
- Given `packages/api/.tickets/` contains open "api-1a2b"
- And `packages/web/.tickets/` contains only closed "web-3c4d"
- When the user runs `tq ls -r --status open`
- Then the output contains "api-1a2b"
- And the output does not contain a "packages/web" heading

### Scenario: Filters apply within each store
- Given `packages/api/.tickets/` contains "api-1a2b" (tag "urgent") and "api-2b3c" (tag "later")
- And `packages/web/.tickets/` contains "web-3c4d" (tag "urgent")
- When the user runs `tq ls -r --tag urgent`
- Then the output contains "api-1a2b"
- And the output contains "web-3c4d"
- And the output does not contain "api-2b3c"

### Scenario: Source axis applies within each store
- Given `packages/api/.tickets/` has an archived ticket "api-arch"
- And `packages/web/.tickets/` has an active ticket "web-act"
- When the user runs `tq ls -r --archived`
- Then the output contains "api-arch"
- And the output does not contain "web-act"

### Scenario: Recursive JSONL emits a flat stream tagged with store
- Given `packages/api/.tickets/` contains "api-1a2b"
- And `packages/web/.tickets/` contains "web-3c4d"
- When the user runs `tq ls -r --jsonl`
- Then one JSON object is printed per line with no section headings
- And the object for "api-1a2b" has a "store" field equal to "packages/api"
- And the object for "web-3c4d" has a "store" field equal to "packages/web"

### Scenario: Recursive listing includes the root store as "."
- Given `.tickets/` at the root contains "root-0001"
- And `packages/api/.tickets/` contains "api-1a2b"
- When the user runs `tq ls -r`
- Then a heading "." appears before the line for "root-0001"

### Scenario: -r and --parent are mutually exclusive
- When the user runs `tq ls -r --parent epic-001`
- Then the command exits non-zero

### Scenario: -r and --dep are mutually exclusive
- When the user runs `tq ls -r --dep task-001`
- Then the command exits non-zero
