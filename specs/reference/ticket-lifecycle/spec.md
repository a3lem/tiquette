# Ticket Lifecycle

Covers ticket creation and status transitions: `create`, `start`, `close`, `cancel`, `reopen`.

## Requirement: Create ticket

The system SHALL create a ticket file in `.tickets/` when `tq create` is invoked, and print the generated ID to stdout.

### Scenario: Create with title
- Given a clean tickets directory
- When the user runs `tq create "My first ticket"`
- Then the command exits 0
- And stdout matches the ticket ID pattern `<prefix>-<4hex>`
- And a ticket file exists with `# My first ticket` as the heading

### Scenario: Create with default title
- Given a clean tickets directory
- When the user runs `tq create`
- Then the command exits 0
- And the created ticket has title "Untitled"

### Scenario: Create with description
- Given a clean tickets directory
- When the user runs `tq create "Test ticket" -d "This is the description"`
- Then the command exits 0
- And the created ticket contains a `## Description` section with "This is the description"

### Scenario: Create with type
- Given a clean tickets directory
- When the user runs `tq create "Bug ticket" -t bug`
- Then the created ticket has field `type` with value `bug`

### Scenario: Create with priority
- Given a clean tickets directory
- When the user runs `tq create "High priority" -p 0`
- Then the created ticket has field `priority` with value `0`

### Scenario: Create with assignee (short flag)
- Given a clean tickets directory
- When the user runs `tq create "Assigned ticket" -A "John Doe"`
- Then the created ticket has field `assignee` with value `John Doe`

### Scenario: Create with assignee (long flag)
- Given a clean tickets directory
- When the user runs `tq create "Assigned ticket" --assignee "John Doe"`
- Then the created ticket has field `assignee` with value `John Doe`

### Scenario: -a is no longer accepted for --assignee
- When the user runs `tq create "X" -a "John Doe"`
- Then the command exits non-zero

### Scenario: Create with external reference
- Given a clean tickets directory
- When the user runs `tq create "External ticket" --xref "JIRA-123"`
- Then the created ticket has field `xref` with value `JIRA-123`

### Scenario: Create with parent
- Given a ticket exists with ID "parent-001"
- When the user runs `tq create "Child ticket" --parent parent-001`
- Then the created ticket has field `parent` with value `parent-001`

### Scenario: Create with tags
- Given a clean tickets directory
- When the user runs `tq create "Tagged ticket" --tag ui --tag backend`
- Then the created ticket has tags `[ui, backend]`

### Scenario: Create with deps
- Given tickets "dep-001" and "dep-002" exist
- When the user runs `tq create "Blocked ticket" --dep dep-001 --dep dep-002`
- Then the created ticket has deps `[dep-001, dep-002]`

### Scenario: Create rejects invalid type
- When the user runs `tq create "Test" -t invalid`
- Then the command exits non-zero

### Scenario: Create rejects invalid priority
- When the user runs `tq create "Test" -p 5`
- Then the command exits non-zero

### Scenario: Create rejects negative priority
- When the user runs `tq create "Test" -p -1`
- Then the command exits non-zero

## Requirement: Default field values

The system SHALL set sensible defaults for all fields when creating a ticket.

### Scenario: Default status is open
- When the user runs `tq create "New ticket"`
- Then the created ticket has field `status` with value `open`

### Scenario: Default priority is 2
- When the user runs `tq create "Normal priority"`
- Then the created ticket has field `priority` with value `2`

### Scenario: Default type is task
- When the user runs `tq create "Default type"`
- Then the created ticket has field `type` with value `task`

### Scenario: Default deps is empty
- When the user runs `tq create "No deps"`
- Then the created ticket has field `deps` with value `[]`

### Scenario: Default links is empty
- When the user runs `tq create "No links"`
- Then the created ticket has field `links` with value `[]`

### Scenario: Default tags is empty
- When the user runs `tq create "No tags"`
- Then the created ticket has field `tags` with value `[]`

### Scenario: Default assignee is null
- When the user runs `tq create "Unassigned"`
- Then the created ticket has no `assignee` value

### Scenario: Created timestamp is set
- When the user runs `tq create "Timestamped"`
- Then the created ticket has a valid ISO 8601 `created` timestamp

## Requirement: Tickets directory auto-creation

The system SHALL create the `.tickets/` directory on demand when creating the first ticket.

### Scenario: Directory created on first ticket
- Given the tickets directory does not exist
- When the user runs `tq create "First ticket"`
- Then the command exits 0
- And the `.tickets/` directory exists

## Requirement: Start command

The system SHALL set a ticket's status to `in_progress` when `tq start` is invoked.

### Scenario: Start sets in_progress
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq start test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `in_progress`

## Requirement: Close command

The system SHALL set a ticket's status to `completed` when `tq close` is invoked. The system SHALL NOT write a `resolution` field. The system SHALL reject closing a ticket that has descendants whose status is not a terminal state (`completed` or `canceled`) unless `-f` / `--force` is supplied. WHEN `--force` is supplied, the system SHALL set every non-terminal descendant's status to `completed`.

### Scenario: Close sets completed
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq close test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `completed`
- And ticket "test-0001" has no `resolution` field

### Scenario: Close rejects parent with non-terminal children
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0002"
- And ticket "par-0001" has field `status` with value `open`

### Scenario: Close succeeds when all children are terminal
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `completed`
- When the user runs `tq close par-0001`
- Then the command exits 0

### Scenario: Close rejects grandparent with non-terminal grandchild
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `canceled`
- And ticket "par-0003" exists with parent "par-0002" and status `open`
- When the user runs `tq close par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0003"

### Scenario: Close ticket with no children
- Given a ticket "test-0001" exists with no children
- When the user runs `tq close test-0001`
- Then the command exits 0

### Scenario: Close notifies when closing last non-terminal child
- Given ticket "par-0001" has one open child "par-0002"
- When the user runs `tq close par-0002`
- Then the command exits 0
- And stdout contains the ticket ID "par-0002"
- And stdout contains a notification that "par-0001" has no remaining open children

### Scenario: Force-close cascades to non-terminal descendants
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- And ticket "par-0003" exists with parent "par-0002" and status `in_progress`
- When the user runs `tq close -f par-0001`
- Then the command exits 0
- And ticket "par-0001" has field `status` with value `completed`
- And ticket "par-0002" has field `status` with value `completed`
- And ticket "par-0003" has field `status` with value `completed`

### Scenario: Force-close leaves already-terminal descendants untouched
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `canceled`
- When the user runs `tq close --force par-0001`
- Then the command exits 0
- And ticket "par-0002" has field `status` with value `canceled`

## Requirement: Cancel command

The system SHALL set a ticket's status to `canceled` when `tq cancel` is invoked. The system SHALL NOT write a `resolution` field. The system SHALL reject cancelling a ticket that has descendants whose status is not a terminal state (`completed` or `canceled`) unless `-f` / `--force` is supplied. WHEN `--force` is supplied, the system SHALL set every non-terminal descendant's status to `canceled`.

### Scenario: Cancel sets canceled
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq cancel test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `canceled`
- And ticket "test-0001" has no `resolution` field

### Scenario: Cancel rejects parent with non-terminal children
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq cancel par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0002"
- And ticket "par-0001" has field `status` with value `open`

### Scenario: Cancel succeeds when all descendants are terminal
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `completed`
- When the user runs `tq cancel par-0001`
- Then the command exits 0
- And ticket "par-0001" has field `status` with value `canceled`

### Scenario: Force-cancel cascades to non-terminal descendants
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- And ticket "par-0003" exists with parent "par-0002" and status `in_progress`
- When the user runs `tq cancel -f par-0001`
- Then the command exits 0
- And ticket "par-0001" has field `status` with value `canceled`
- And ticket "par-0002" has field `status` with value `canceled`
- And ticket "par-0003" has field `status` with value `canceled`

### Scenario: Force-cancel leaves already-terminal descendants untouched
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `completed`
- When the user runs `tq cancel --force par-0001`
- Then the command exits 0
- And ticket "par-0002" has field `status` with value `completed`

## Requirement: Reopen command

The system SHALL set a ticket's status to `open` when `tq reopen` is invoked. The system SHALL NOT write or read a `resolution` field.

### Scenario: Reopen from completed
- Given a ticket "test-0001" exists with status `completed`
- When the user runs `tq reopen test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `open`
- And ticket "test-0001" has no `resolution` field

### Scenario: Reopen from canceled
- Given a ticket "test-0001" exists with status `canceled`
- When the user runs `tq reopen test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `open`

## Requirement: Invalid operations

The system SHALL reject invalid status values and non-existent ticket IDs with non-zero exit codes.

### Scenario: Non-existent ticket
- When the user runs `tq close nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

## Requirement: Transition output

WHEN a transition command (`start`, `close`, `cancel`, `reopen`) succeeds, the system SHALL print the affected ticket ID to stdout. WHEN `close --force` or `cancel --force` cascades to descendants, the system SHALL print one ID per line for every ticket whose status was changed, in the order the writes were committed.

### Scenario: Start prints ticket ID
- Given ticket "test-0001" exists with status `open`
- When the user runs `tq start test-0001`
- Then the command exits 0
- And stdout contains "test-0001"

### Scenario: Close prints ticket ID
- Given ticket "test-0001" exists with status `open`
- When the user runs `tq close test-0001`
- Then the command exits 0
- And stdout contains "test-0001"

### Scenario: Cancel prints ticket ID
- Given ticket "test-0001" exists with status `open`
- When the user runs `tq cancel test-0001`
- Then the command exits 0
- And stdout contains "test-0001"

### Scenario: Reopen prints ticket ID
- Given ticket "test-0001" exists with status `completed`
- When the user runs `tq reopen test-0001`
- Then the command exits 0
- And stdout contains "test-0001"

### Scenario: Failed transition does not print ID
- When the user runs `tq close nonexistent`
- Then the command exits non-zero
- And stdout is empty

### Scenario: Force-close prints all affected IDs
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close -f par-0001`
- Then the command exits 0
- And stdout contains "par-0001"
- And stdout contains "par-0002"

### Scenario: Force-cancel prints all affected IDs
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq cancel -f par-0001`
- Then the command exits 0
- And stdout contains "par-0001"
- And stdout contains "par-0002"
