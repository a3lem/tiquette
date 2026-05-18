# Ticket Query

## MODIFIED Requirements

### Requirement: List tickets

The system SHALL list tickets matching filter criteria when `tq ls` is invoked. With no source-selection flag, only active (non-archived) tickets are considered. With no status filter, all statuses within the selected source set are shown, sorted by priority. The `--status` filter (short: `-s`) accepts one of `open`, `in_progress`, `closed`, `canceled`. Source selection (`--archived`, `--all`) is governed by the "List source axis" requirement. The `-T` short for `--tag` SHALL NOT be accepted.

#### Scenario: List all open tickets
- Given tickets "list-0001" and "list-0002" exist (status open)
- When the user runs `tq ls`
- Then the output contains both ticket IDs

#### Scenario: Default excludes archived
- Given active ticket "act-001" and archived ticket "arc-001" exist
- When the user runs `tq ls`
- Then the output contains "act-001"
- And the output does not contain "arc-001"

#### Scenario: List with --status open
- Given "list-0001" is open and "list-0002" is closed
- When the user runs `tq ls --status open`
- Then the output contains "list-0001"
- And the output does not contain "list-0002"

#### Scenario: List with -s closed
- Given "list-0001" is open and "list-0002" is closed
- When the user runs `tq ls -s closed`
- Then the output contains "list-0002"
- And the output does not contain "list-0001"

#### Scenario: List with --status canceled
- Given "list-0001" is canceled and "list-0002" is closed
- When the user runs `tq ls --status canceled`
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

#### Scenario: Ready includes tickets with all deps in terminal status
- Given "ready-001" depends on "ready-002" (status closed)
- When the user runs `tq ls --ready`
- Then the output contains "ready-001"

#### Scenario: Ready excludes terminal tickets
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
- And the output shows only non-terminal blockers

#### Scenario: Blocked by open children
- Given "block-001" has open child "block-003"
- When the user runs `tq ls --blocked`
- Then the output contains "block-001"

#### Scenario: Blocked excludes tickets with all deps terminal and no open children
- Given "block-001" depends on "block-002" (status closed) and has no open children
- When the user runs `tq ls --blocked`
- Then the output does not contain "block-001"

#### Scenario: Limit
- Given two closed tickets exist
- When the user runs `tq ls --status closed --limit 1`
- Then the output has exactly 1 line

#### Scenario: JSONL output
- Given ticket "query-001" exists
- When the user runs `tq ls --jsonl`
- Then the output is valid JSONL
- And each line has fields: id, status, deps, links, type, priority
- And no line contains a `resolution` field

#### Scenario: Filter by assignee
- Given "t-001" has assignee "Alice" and "t-002" has assignee "Bob"
- When the user runs `tq ls --assignee Alice`
- Then the output contains "t-001"
- And the output does not contain "t-002"

#### Scenario: -A is short for --assignee
- Given "t-001" has assignee "Alice" and "t-002" has assignee "Bob"
- When the user runs `tq ls -A Alice`
- Then the output contains "t-001"
- And the output does not contain "t-002"

#### Scenario: Filter by tag
- Given "t-001" has tag "ui" and "t-002" has tag "backend"
- When the user runs `tq ls --tag ui`
- Then the output contains "t-001"
- And the output does not contain "t-002"

#### Scenario: -T is not accepted as a short for --tag
- When the user runs `tq ls -T ui`
- Then the command exits non-zero

#### Scenario: Filter by type
- Given "t-001" has type "bug" and "t-002" has type "task"
- When the user runs `tq ls --type bug`
- Then the output contains "t-001"
- And the output does not contain "t-002"

#### Scenario: Sort by mtime
- Given tickets exist with different modification times
- When the user runs `tq ls --sort mtime`
- Then tickets are sorted by modification time

#### Scenario: --status completed is rejected
- When the user runs `tq ls --status completed`
- Then the command exits non-zero
- And stderr indicates `closed` is the accepted spelling

#### Scenario: --completed flag is rejected
- When the user runs `tq ls --completed`
- Then the command exits non-zero

#### Scenario: --canceled flag is rejected
- When the user runs `tq ls --canceled`
- Then the command exits non-zero

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

### Requirement: List ticket line format

The system SHALL format each ticket line in `ls` output as: `<id> <tags> - <checkbox> <title>` where:

- The checkbox represents lifecycle state derived from `status` alone: `[ ]` for `open`, `[/]` for `in_progress`, `[x]` for `closed`, and `[~]` for `canceled`.
- Zero or more tag tokens may appear after the ID, each individually bracketed:
  - The priority tag `[P<n>]` SHALL be shown only when priority is not 2 (the default).
  - The type tag (e.g. `[epic]`, `[feature]`) SHALL be shown only when the type is not "task" (the default).
  - When both are present, priority comes first: `[P1][epic]` (no space between tags).
- When no tags are present, the format collapses to `<id> - <checkbox> <title>`.
- Dependencies are appended after the title as a comma-separated list: `<- [dep-id1, dep-id2]`.

#### Scenario: Default priority and type hidden
- Given ticket "fmt-001" exists with priority 2, type "task", status open, title "Fix login"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 - [ ] Fix login`

#### Scenario: Non-default priority shown
- Given ticket "fmt-001" exists with priority 1, type "task", status open, title "Fix login"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 [P1] - [ ] Fix login`

#### Scenario: Non-default type shown
- Given ticket "fmt-001" exists with priority 2, type "feature", status open, title "Add export"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 [feature] - [ ] Add export`

#### Scenario: Both non-default priority and type shown
- Given ticket "fmt-001" exists with priority 3, type "epic", status open, title "Refactor"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 [P3][epic] - [ ] Refactor`

#### Scenario: In-progress renders half checkbox
- Given ticket "fmt-001" exists with priority 2, type "task", status in_progress, title "Working"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 - [/] Working`

#### Scenario: Closed renders checked checkbox
- Given ticket "fmt-001" exists with status closed
- When the user runs `tq ls --status closed`
- Then the line contains `[x]`

#### Scenario: Canceled renders tilde checkbox
- Given ticket "fmt-001" exists with status canceled
- When the user runs `tq ls --status canceled`
- Then the line contains `[~]`
- And the line does not contain `[x]`

#### Scenario: Single dependency appended after title
- Given ticket "fmt-001" depends on "fmt-002"
- When the user runs `tq ls`
- Then the line for "fmt-001" ends with `<- [fmt-002]`

#### Scenario: Multiple dependencies appended after title
- Given ticket "fmt-001" depends on "fmt-002" and "fmt-003"
- When the user runs `tq ls`
- Then the line for "fmt-001" ends with `<- [fmt-002, fmt-003]`

### Requirement: Tags listing

The system SHALL list all tags with counts when `tq tags` is invoked. Only open/in_progress tickets are counted by default.

#### Scenario: Tags sorted by count descending
- Given tickets with various tags exist
- When the user runs `tq tags`
- Then tags are listed with counts, most frequent first

#### Scenario: Tags excludes terminal tickets by default
- Given a tag appears on both open and closed tickets
- When the user runs `tq tags`
- Then the count reflects only open/in_progress tickets

### Requirement: Archive

The system SHALL move tickets in a terminal status (`closed` or `canceled`) to `.tickets/archive/` when `tq archive` is invoked.

The system SHALL NOT archive a terminal ticket when any non-archived ticket references it via `deps`, `links`, or `parent`. Referenced tickets are skipped with a diagnostic on stderr naming the referrers.

When a ticket is blocked from archiving, any terminal ticket it references SHALL also be blocked (cascading). The archivable set is computed iteratively until stable.

#### Scenario: Archive moves terminal tickets
- Given tickets "t-001" (closed) and "t-002" (open) exist
- When the user runs `tq archive`
- Then "t-001" exists in `.tickets/archive/`
- And "t-001" does not exist in `.tickets/`
- And "t-002" remains in `.tickets/`

#### Scenario: Archive moves canceled tickets
- Given tickets "t-001" (canceled) and "t-002" (open) exist
- When the user runs `tq archive`
- Then "t-001" exists in `.tickets/archive/`
- And "t-002" remains in `.tickets/`

#### Scenario: No terminal tickets
- Given all tickets are open or in_progress
- When the user runs `tq archive`
- Then the output contains "No closed or canceled tickets to archive"

#### Scenario: Archive creates directory on first use
- Given a closed ticket exists and no archive directory
- When the user runs `tq archive`
- Then `.tickets/archive/` is created

#### Scenario: Archive is idempotent
- Given a closed ticket exists
- When the user runs `tq archive` twice
- Then the second run reports no tickets to archive

#### Scenario: Archived ticket file is intact
- Given ticket "t-001" is closed and archived
- Then the archived file contains the original frontmatter and content

#### Scenario: Skips ticket referenced as dependency
- Given closed ticket "t-001" and open ticket "t-002" with deps including "t-001"
- When the user runs `tq archive`
- Then "t-001" remains in `.tickets/`
- And stderr contains "Skipped t-001: referenced by t-002"

#### Scenario: Skips ticket referenced as link
- Given closed ticket "t-001" and open ticket "t-002" with links including "t-001"
- When the user runs `tq archive`
- Then "t-001" remains in `.tickets/`
- And stderr contains "Skipped t-001"

#### Scenario: Skips ticket that is a parent
- Given closed ticket "t-001" and open ticket "t-002" with parent "t-001"
- When the user runs `tq archive`
- Then "t-001" remains in `.tickets/`
- And stderr contains "Skipped t-001"

#### Scenario: Mutually-terminal group archives together
- Given closed tickets "t-001" and "t-002" linked to each other, no open tickets reference either
- When the user runs `tq archive`
- Then both "t-001" and "t-002" are moved to `.tickets/archive/`

#### Scenario: Cascade blocks dependent terminal tickets
- Given closed "t-b" and closed "t-a" (deps: ["t-b"]), and open "t-c" (deps: ["t-a"])
- When the user runs `tq archive`
- Then "t-a" remains (referenced by open "t-c")
- And "t-b" remains (referenced by remaining "t-a")
- And stderr contains "Skipped"

#### Scenario: No eligible tickets
- Given closed ticket "t-001" and open ticket "t-002" with deps including "t-001"
- When the user runs `tq archive`
- Then the output contains "No closed or canceled tickets eligible for archiving"
