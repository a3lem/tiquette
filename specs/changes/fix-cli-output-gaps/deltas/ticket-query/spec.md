# Ticket Query

## MODIFIED Requirements

### Requirement: List tickets

The system SHALL list tickets matching filter criteria when `tq ls` is invoked. The default
filter shows `open` and `in_progress` tickets, sorted by priority. The `--assignee` filter
SHALL accept `-a` as a short alias. The `--tag` filter SHALL accept `-T` as a short alias.

#### Scenario: List all open tickets
- Given tickets "list-0001" and "list-0002" exist (status open)
- When the user runs `tq ls`
- Then the output contains both ticket IDs

#### Scenario: List with status filter
- Given "list-0001" is open and "list-0002" is closed
- When the user runs `tq ls --status open`
- Then the output contains "list-0001"
- And the output does not contain "list-0002"

#### Scenario: List shows dependencies
- Given ticket "list-0001" depends on "list-0002"
- When the user runs `tq ls`
- Then the output contains "<- [list-0002]"

#### Scenario: List with no tickets
- Given the tickets directory is empty
- When the user runs `tq ls`
- Then the output is empty

#### Scenario: Ready filter (no deps)
- Given "ready-001" has no deps and no open children, and "ready-002" depends on open "ready-003"
- When the user runs `tq ls --ready`
- Then the output contains "ready-001"
- And the output does not contain "ready-002"

#### Scenario: Ready includes tickets with all deps closed
- Given "ready-001" depends on "ready-002" (status closed)
- When the user runs `tq ls --ready`
- Then the output contains "ready-001"

#### Scenario: Ready excludes closed tickets
- Given "ready-001" has status closed
- When the user runs `tq ls --ready`
- Then the output does not contain "ready-001"

#### Scenario: Ready excludes parent with open children
- Given "ready-001" has open child "ready-002"
- When the user runs `tq ls --ready`
- Then the output does not contain "ready-001"

#### Scenario: Ready sorts by priority then ID
- Given tickets with varying priorities exist
- When the user runs `tq ls --ready`
- Then tickets are sorted by priority ascending, then by ID

#### Scenario: Blocked by open dependency
- Given "block-001" depends on open "block-002"
- When the user runs `tq ls --blocked`
- Then the output contains "block-001"
- And the output shows only unclosed blockers

#### Scenario: Blocked by open children
- Given "block-001" has open child "block-003"
- When the user runs `tq ls --blocked`
- Then the output contains "block-001"

#### Scenario: Blocked excludes tickets with all deps closed and no open children
- Given "block-001" depends on "block-002" (status closed) and has no open children
- When the user runs `tq ls --blocked`
- Then the output does not contain "block-001"

#### Scenario: Completed filter
- Given "done-001" is closed with resolution completed
- And "done-002" is closed with resolution canceled
- When the user runs `tq ls --completed`
- Then the output contains "done-001"
- And the output does not contain "done-002"

#### Scenario: Canceled filter
- Given "done-001" is closed with resolution completed
- And "done-002" is closed with resolution canceled
- When the user runs `tq ls --canceled`
- Then the output contains "done-002"
- And the output does not contain "done-001"

#### Scenario: Limit
- Given two closed tickets exist
- When the user runs `tq ls --status closed --limit 1`
- Then the output has exactly 1 line

#### Scenario: JSONL output
- Given ticket "query-001" exists
- When the user runs `tq ls --jsonl`
- Then the output is valid JSONL
- And each line has fields: id, status, deps, links, type, priority

#### Scenario: Filter by assignee (long form)
- Given "t-001" has assignee "Alice" and "t-002" has assignee "Bob"
- When the user runs `tq ls --assignee Alice`
- Then the output contains "t-001"
- And the output does not contain "t-002"

#### Scenario: Filter by assignee (short form)
- Given "t-001" has assignee "Alice" and "t-002" has assignee "Bob"
- When the user runs `tq ls -a Alice`
- Then the output contains "t-001"
- And the output does not contain "t-002"

#### Scenario: Filter by tag (long form)
- Given "t-001" has tag "ui" and "t-002" has tag "backend"
- When the user runs `tq ls --tag ui`
- Then the output contains "t-001"
- And the output does not contain "t-002"

#### Scenario: Filter by tag (short form)
- Given "t-001" has tag "ui" and "t-002" has tag "backend"
- When the user runs `tq ls -T ui`
- Then the output contains "t-001"
- And the output does not contain "t-002"

#### Scenario: Filter by type
- Given "t-001" has type "bug" and "t-002" has type "task"
- When the user runs `tq ls --type bug`
- Then the output contains "t-001"
- And the output does not contain "t-002"

#### Scenario: Sort by mtime
- Given tickets exist with different modification times
- When the user runs `tq ls --sort mtime`
- Then tickets are sorted by modification time

#### Scenario: Invalid status rejected
- When the user runs `tq ls --status invalid`
- Then the command exits non-zero

#### Scenario: Invalid sort rejected
- When the user runs `tq ls --sort invalid`
- Then the command exits non-zero

#### Scenario: Ready and blocked are mutually exclusive
- When the user runs `tq ls --ready --blocked`
- Then the command exits non-zero

#### Scenario: Limit must be positive
- When the user runs `tq ls --limit 0`
- Then the command exits non-zero
