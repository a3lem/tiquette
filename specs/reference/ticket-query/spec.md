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

The system SHALL list tickets matching filter criteria when `tq ls` is invoked. The default filter shows `open` and `in_progress` tickets, sorted by priority.

### Scenario: List all open tickets
- Given tickets "list-0001" and "list-0002" exist (status open)
- When the user runs `tq ls`
- Then the output contains both ticket IDs

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

### Scenario: Ready filter
- Given "ready-001" has no deps and "ready-002" depends on open "ready-003"
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

### Scenario: Ready sorts by priority then ID
- Given tickets with varying priorities exist
- When the user runs `tq ls --ready`
- Then tickets are sorted by priority ascending, then by ID

### Scenario: Blocked filter
- Given "block-001" depends on open "block-002"
- When the user runs `tq ls --blocked`
- Then the output contains "block-001"
- And the output shows only unclosed blockers

### Scenario: Blocked excludes tickets with all deps closed
- Given "block-001" depends on "block-002" (status closed)
- When the user runs `tq ls --blocked`
- Then the output does not contain "block-001"

### Scenario: Completed filter
- Given "done-001" is closed with resolution completed
- And "done-002" is closed with resolution canceled
- When the user runs `tq ls --completed`
- Then the output contains "done-001"
- And the output does not contain "done-002"

### Scenario: Canceled filter
- Given "done-001" is closed with resolution completed
- And "done-002" is closed with resolution canceled
- When the user runs `tq ls --canceled`
- Then the output contains "done-002"
- And the output does not contain "done-001"

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

### Scenario: Filter by tag
- Given "t-001" has tag "ui" and "t-002" has tag "backend"
- When the user runs `tq ls --tag ui`
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

## Requirement: List with tree rendering

The system SHALL render parent-child relationships as indented trees in `ls` output by default.

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

The system SHALL display a transitive dependency tree when `tq show-deps <id>` is invoked.

### Scenario: Dependency tree shows transitive deps
- Given "task-0001" depends on "task-0002", which depends on "task-0003"
- When the user runs `tq show-deps task-0001`
- Then the output contains all three IDs with status and title
- And the output uses box-drawing characters

### Scenario: Dependency tree with multiple children
- Given "task-0001" depends on both "task-0002" and "task-0003"
- When the user runs `tq show-deps task-0001`
- Then the output contains both dependencies

### Scenario: Full tree disables deduplication
- Given a diamond dependency pattern
- When the user runs `tq show-deps --full task-0001`
- Then shared dependencies appear multiple times

### Scenario: Children sorted by subtree depth then ID
- Given dependencies with varying subtree depths
- When the user runs `tq show-deps task-0001`
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

## Requirement: Archive

The system SHALL move closed tickets to `.tickets/archive/` when `tq archive` is invoked.

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

## Requirement: Path command

The system SHALL print the file path of a ticket when `tq path <id>` is invoked.

### Scenario: Path prints file location
- Given ticket "test-001" exists
- When the user runs `tq path test-001`
- Then the output contains ".tickets/test-001.md"
