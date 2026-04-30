# Ticket Query

Covers commands for viewing and listing tickets: `show`, `info`, `ls`, `dep tree`, `tags`, `archive`, `path`.

## Requirement: Show ticket

The system SHALL display a ticket's full content (frontmatter + body) when `tq show <id>` is invoked.

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

### Scenario: Show hides blockers when all deps closed
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

## Requirement: Info command

The system SHALL display a ticket's frontmatter and computed relationships (without body content) when `tq info <id>` is invoked.

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

## Requirement: List tickets

The system SHALL list tickets matching filter criteria when `tq ls` is invoked. With no source-selection flag, only active (non-archived) tickets are considered. With no status/resolution filter flags, all statuses within the selected source set are shown, sorted by priority. Source selection (`--archived`, `--all`) is governed by the "List source axis" requirement.

### Scenario: List all open tickets
- Given tickets "list-0001" and "list-0002" exist (status open)
- When the user runs `tq ls`
- Then the output contains both ticket IDs

### Scenario: Default excludes archived
- Given active ticket "act-001" and archived ticket "arc-001" exist
- When the user runs `tq ls`
- Then the output contains "act-001"
- And the output does not contain "arc-001"

### Scenario: List with status filter
- Given "list-0001" is open and "list-0002" is closed
- When the user runs `tq ls --status open`
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

### Scenario: Ready includes tickets with all deps closed
- Given "ready-001" depends on "ready-002" (status closed)
- When the user runs `tq ls --ready`
- Then the output contains "ready-001"

### Scenario: Ready excludes closed tickets
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
- And the output shows only unclosed blockers

### Scenario: Blocked by open children
- Given "block-001" has open child "block-003"
- When the user runs `tq ls --blocked`
- Then the output contains "block-001"

### Scenario: Blocked excludes tickets with all deps closed and no open children
- Given "block-001" depends on "block-002" (status closed) and has no open children
- When the user runs `tq ls --blocked`
- Then the output does not contain "block-001"

### Scenario: Completed filter (active only by default)
- Given active "done-001" is closed with resolution completed
- And active "done-002" is closed with resolution canceled
- And archived "done-003" has resolution completed
- When the user runs `tq ls --completed`
- Then the output contains "done-001"
- And the output does not contain "done-002"
- And the output does not contain "done-003"

### Scenario: Canceled filter (active only by default)
- Given active "done-001" is closed with resolution completed
- And active "done-002" is closed with resolution canceled
- And archived "done-003" has resolution canceled
- When the user runs `tq ls --canceled`
- Then the output contains "done-002"
- And the output does not contain "done-001"
- And the output does not contain "done-003"

### Scenario: Limit
- Given two closed tickets exist
- When the user runs `tq ls --status closed --limit 1`
- Then the output has exactly 1 line

### Scenario: JSONL output
- Given ticket "query-001" exists
- When the user runs `tq ls --jsonl`
- Then the output is valid JSONL
- And each line has fields: id, status, deps, links, type, priority

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

### Scenario: -a is no longer short for --assignee
- When the user runs `tq ls -a Alice`
- Then `Alice` is not interpreted as an assignee filter

### Scenario: Filter by tag
- Given "t-001" has tag "ui" and "t-002" has tag "backend"
- When the user runs `tq ls --tag ui`
- Then the output contains "t-001"
- And the output does not contain "t-002"

### Scenario: -T is short for --tag
- Given "t-001" has tag "ui" and "t-002" has tag "backend"
- When the user runs `tq ls -T ui`
- Then the output contains "t-001"
- And the output does not contain "t-002"

### Scenario: Filter by type
- Given "t-001" has type "bug" and "t-002" has type "task"
- When the user runs `tq ls --type bug`
- Then the output contains "t-001"
- And the output does not contain "t-002"

### Scenario: Sort by mtime
- Given tickets exist with different modification times
- When the user runs `tq ls --sort mtime`
- Then tickets are sorted by modification time

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

- The checkbox represents status: `[ ]` for open, `[/]` for in_progress, `[x]` for closed.
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

The system SHALL display a transitive dependency tree when `tq deps <id>` is invoked.

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

## Requirement: Tags listing

The system SHALL list all tags with counts when `tq tags` is invoked. Only open/in_progress tickets are counted by default.

### Scenario: Tags sorted by count descending
- Given tickets with various tags exist
- When the user runs `tq tags`
- Then tags are listed with counts, most frequent first

### Scenario: Tags excludes closed tickets by default
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

The system SHALL move closed tickets to `.tickets/archive/` when `tq archive` is invoked.

The system SHALL NOT archive a closed ticket when any non-archived ticket references it via `deps`, `links`, or `parent`. Referenced tickets are skipped with a diagnostic on stderr naming the referrers.

When a ticket is blocked from archiving, any closed ticket it references SHALL also be blocked (cascading). The archivable set is computed iteratively until stable.

### Scenario: Archive moves closed tickets
- Given tickets "t-001" (closed) and "t-002" (open) exist
- When the user runs `tq archive`
- Then "t-001" exists in `.tickets/archive/`
- And "t-001" does not exist in `.tickets/`
- And "t-002" remains in `.tickets/`

### Scenario: No closed tickets
- Given all tickets are open
- When the user runs `tq archive`
- Then the output contains "No closed tickets to archive"

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

### Scenario: Mutually-closed group archives together
- Given closed tickets "t-001" and "t-002" linked to each other, no open tickets reference either
- When the user runs `tq archive`
- Then both "t-001" and "t-002" are moved to `.tickets/archive/`

### Scenario: Cascade blocks dependent closed tickets
- Given closed "t-b" and closed "t-a" (deps: ["t-b"]), and open "t-c" (deps: ["t-a"])
- When the user runs `tq archive`
- Then "t-a" remains (referenced by open "t-c")
- And "t-b" remains (referenced by remaining "t-a")
- And stderr contains "Skipped"

### Scenario: No eligible tickets
- Given closed ticket "t-001" and open ticket "t-002" with deps including "t-001"
- When the user runs `tq archive`
- Then the output contains "No closed tickets eligible for archiving"

## Requirement: Path command

The system SHALL print the file path of a ticket when `tq path <id>` is invoked.

### Scenario: Path prints file location
- Given ticket "test-001" exists
- When the user runs `tq path test-001`
- Then the output contains ".tickets/test-001.md"

## Requirement: List source axis

The system SHALL provide a source-selection axis on `tq ls` that controls whether active tickets, archived tickets, or both are considered. The axis has three states: default (active only), `--archived` (archived only), and `--all` (active + archived).

`--archived` and `--all` SHALL be mutually exclusive. They SHALL combine freely with status/resolution filters (`--status`, `--completed`, `--canceled`, `--ready`, `--blocked`) and with stackable filters (`--tag`, `--type`, `--assignee`).

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

### Scenario: --archived combines with --canceled
- Given archived ticket "arc-001" has resolution canceled
- And archived ticket "arc-002" has resolution completed
- When the user runs `tq ls --archived --canceled`
- Then the output contains "arc-001"
- And the output does not contain "arc-002"

### Scenario: --archived combines with --completed
- Given archived ticket "arc-001" has resolution completed
- And archived ticket "arc-002" has resolution canceled
- When the user runs `tq ls --archived --completed`
- Then the output contains "arc-001"
- And the output does not contain "arc-002"

### Scenario: --all combines with --completed
- Given active "done-001" has resolution completed
- And archived "done-002" has resolution completed
- And active "done-003" has resolution canceled
- When the user runs `tq ls --all --completed`
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
