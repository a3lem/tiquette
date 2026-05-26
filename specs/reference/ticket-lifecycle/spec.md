# Ticket Lifecycle

Covers ticket creation and status transitions: `create`, `start`, `close`, `cancel`, `reopen`.

## Requirement: Create ticket

The system SHALL create a ticket file in `.tickets/` when `tq create <title>` is invoked, and print the generated ID to stdout. The `<title>` positional SHALL be required; invoking `tq create` with no title SHALL exit non-zero with an argparse usage error. The system SHALL accept the field-options defined by `ticket-edit` plus `--link ID` (repeatable, symmetric) and `--note TEXT` (repeatable, timestamped) on the create surface.

### Scenario: Create with title
- Given a clean tickets directory
- When the user runs `tq create "My first ticket"`
- Then the command exits 0
- And stdout matches the ticket ID pattern `<prefix>-<4hex>`
- And a ticket file exists with `# My first ticket` as the heading

### Scenario: Create without title is rejected
- When the user runs `tq create`
- Then the command exits non-zero
- And stderr indicates the title argument is required

### Scenario: Create with description
- Given a clean tickets directory
- When the user runs `tq create "Test ticket" -d "This is the description"`
- Then the command exits 0
- And the created ticket contains a `## Description` section with "This is the description"

### Scenario: Create with type
- When the user runs `tq create "Bug ticket" -t bug`
- Then the created ticket has field `type` with value `bug`

### Scenario: Create with priority
- When the user runs `tq create "High priority" -p 0`
- Then the created ticket has field `priority` with value `0`

### Scenario: Create with assignee (short flag)
- When the user runs `tq create "Assigned ticket" -A "John Doe"`
- Then the created ticket has field `assignee` with value `John Doe`

### Scenario: Create with assignee (long flag)
- When the user runs `tq create "Assigned ticket" --assignee "John Doe"`
- Then the created ticket has field `assignee` with value `John Doe`

### Scenario: -a is not accepted for --assignee
- When the user runs `tq create "X" -a "John Doe"`
- Then the command exits non-zero

### Scenario: Create with external reference
- When the user runs `tq create "External ticket" --xref "JIRA-123"`
- Then the created ticket has field `xref` with value `JIRA-123`

### Scenario: Create with parent
- Given a ticket exists with ID "parent-001"
- When the user runs `tq create "Child ticket" --parent parent-001`
- Then the created ticket has field `parent` with value `parent-001`

### Scenario: Create with tags
- When the user runs `tq create "Tagged ticket" --tag ui --tag backend`
- Then the created ticket has tags `[ui, backend]`

### Scenario: Create with deps
- Given tickets "dep-001" and "dep-002" exist
- When the user runs `tq create "Blocked ticket" --dep dep-001 --dep dep-002`
- Then the created ticket has deps `[dep-001, dep-002]`

### Scenario: Create with links is symmetric
- Given a ticket "rel-001" exists with no links
- When the user runs `tq create "Related ticket" --link rel-001`
- Then the created ticket lists "rel-001" in links
- And ticket "rel-001" lists the new ticket's id in links

### Scenario: Create with note
- When the user runs `tq create "Kickoff ticket" --note "initial context"`
- Then the created ticket contains a `## Notes` section
- And the note "initial context" appears with a timestamp in the format defined by `ticket-store` matching the ticket's `created` timestamp

### Scenario: Create with multiple notes shares one timestamp
- When the user runs `tq create "Multi-note" --note "first" --note "second"`
- Then both notes appear in `## Notes` in order
- And both notes carry the same timestamp in the format defined by `ticket-store`

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
- Then the created ticket has a `created` field in the format defined by `ticket-store`

## Requirement: Tickets directory auto-creation

The system SHALL create the `.tickets/` directory on demand when creating the first ticket.

### Scenario: Directory created on first ticket
- Given the tickets directory does not exist
- When the user runs `tq create "First ticket"`
- Then the command exits 0
- And the `.tickets/` directory exists

## Requirement: Start command

The system SHALL set the status to `in_progress` for every ticket ID supplied when `tq start <id>...` is invoked. At least one ID SHALL be required. The system SHALL resolve and validate all supplied IDs before mutating any ticket; IF any ID is unknown, the system SHALL exit non-zero and write nothing.

### Scenario: Start sets in_progress
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq start test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `in_progress`

### Scenario: Start multiple tickets
- Given tickets "test-0001" and "test-0002" exist with status `open`
- When the user runs `tq start test-0001 test-0002`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `in_progress`
- And ticket "test-0002" has field `status` with value `in_progress`

### Scenario: Start with one unknown ID writes nothing
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq start test-0001 nonexistent`
- Then the command exits non-zero
- And ticket "test-0001" has field `status` with value `open`

## Requirement: Close command

The system SHALL set the status to `closed` for every ticket ID supplied when `tq close <id>...` is invoked. At least one ID SHALL be required. The system SHALL resolve and validate all supplied IDs before mutating any ticket; IF any ID is unknown, the system SHALL exit non-zero and write nothing. The system SHALL NOT write a `resolution` field. For each supplied ticket independently, the system SHALL reject closing it when it has descendants whose status is not a terminal state (`closed` or `canceled`) unless `-f` / `--force` is supplied; IF any supplied ticket is rejected, the system SHALL exit non-zero and write nothing. WHEN `--force` is supplied, the system SHALL set every non-terminal descendant of every supplied ticket to `closed`.

### Scenario: Close sets closed
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq close test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `closed`
- And ticket "test-0001" has no `resolution` field

### Scenario: Close multiple tickets
- Given tickets "test-0001" and "test-0002" exist with status `open` and no children
- When the user runs `tq close test-0001 test-0002`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `closed`
- And ticket "test-0002" has field `status` with value `closed`

### Scenario: Close with one unknown ID writes nothing
- Given a ticket "test-0001" exists with status `open` and no children
- When the user runs `tq close test-0001 nonexistent`
- Then the command exits non-zero
- And ticket "test-0001" has field `status` with value `open`

### Scenario: Close rejects parent with non-terminal children
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0002"
- And ticket "par-0001" has field `status` with value `open`

### Scenario: Close batch aborts when one target has non-terminal children
- Given ticket "test-0001" exists with status `open` and no children
- And ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close test-0001 par-0001`
- Then the command exits non-zero
- And stderr contains "par-0001"
- And ticket "test-0001" has field `status` with value `open`
- And ticket "par-0001" has field `status` with value `open`

### Scenario: Close succeeds when all children are terminal
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `closed`
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
- And ticket "par-0001" has field `status` with value `closed`
- And ticket "par-0002" has field `status` with value `closed`
- And ticket "par-0003" has field `status` with value `closed`

### Scenario: Force-close leaves already-terminal descendants untouched
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `canceled`
- When the user runs `tq close --force par-0001`
- Then the command exits 0
- And ticket "par-0002" has field `status` with value `canceled`

## Requirement: Cancel command

The system SHALL set the status to `canceled` for every ticket ID supplied when `tq cancel <id>...` is invoked. At least one ID SHALL be required. The system SHALL resolve and validate all supplied IDs before mutating any ticket; IF any ID is unknown, the system SHALL exit non-zero and write nothing. The system SHALL NOT write a `resolution` field. For each supplied ticket independently, the system SHALL reject cancelling it when it has descendants whose status is not a terminal state (`closed` or `canceled`) unless `-f` / `--force` is supplied; IF any supplied ticket is rejected, the system SHALL exit non-zero and write nothing. WHEN `--force` is supplied, the system SHALL set every non-terminal descendant of every supplied ticket to `canceled`.

### Scenario: Cancel sets canceled
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq cancel test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `canceled`
- And ticket "test-0001" has no `resolution` field

### Scenario: Cancel multiple tickets
- Given tickets "test-0001" and "test-0002" exist with status `open` and no children
- When the user runs `tq cancel test-0001 test-0002`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `canceled`
- And ticket "test-0002" has field `status` with value `canceled`

### Scenario: Cancel with one unknown ID writes nothing
- Given a ticket "test-0001" exists with status `open` and no children
- When the user runs `tq cancel test-0001 nonexistent`
- Then the command exits non-zero
- And ticket "test-0001" has field `status` with value `open`

### Scenario: Cancel rejects parent with non-terminal children
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq cancel par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0002"
- And ticket "par-0001" has field `status` with value `open`

### Scenario: Cancel batch aborts when one target has non-terminal children
- Given ticket "test-0001" exists with status `open` and no children
- And ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq cancel test-0001 par-0001`
- Then the command exits non-zero
- And stderr contains "par-0001"
- And ticket "test-0001" has field `status` with value `open`
- And ticket "par-0001" has field `status` with value `open`

### Scenario: Cancel succeeds when all descendants are terminal
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `closed`
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
- And ticket "par-0002" exists with parent "par-0001" and status `closed`
- When the user runs `tq cancel --force par-0001`
- Then the command exits 0
- And ticket "par-0002" has field `status` with value `closed`

## Requirement: Reopen command

The system SHALL set the status to `open` for every ticket ID supplied when `tq reopen <id>...` is invoked. At least one ID SHALL be required. The system SHALL resolve and validate all supplied IDs before mutating any ticket; IF any ID is unknown, the system SHALL exit non-zero and write nothing. The system SHALL NOT write or read a `resolution` field.

### Scenario: Reopen from closed
- Given a ticket "test-0001" exists with status `closed`
- When the user runs `tq reopen test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `open`
- And ticket "test-0001" has no `resolution` field

### Scenario: Reopen from canceled
- Given a ticket "test-0001" exists with status `canceled`
- When the user runs `tq reopen test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `open`

### Scenario: Reopen multiple tickets
- Given ticket "test-0001" exists with status `closed`
- And ticket "test-0002" exists with status `canceled`
- When the user runs `tq reopen test-0001 test-0002`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `open`
- And ticket "test-0002" has field `status` with value `open`

### Scenario: Reopen with one unknown ID writes nothing
- Given a ticket "test-0001" exists with status `closed`
- When the user runs `tq reopen test-0001 nonexistent`
- Then the command exits non-zero
- And ticket "test-0001" has field `status` with value `closed`

## Requirement: Invalid operations

The system SHALL reject invalid status values and non-existent ticket IDs with non-zero exit codes. WHEN multiple IDs are supplied and any one is non-existent, the system SHALL exit non-zero and mutate no ticket.

### Scenario: Non-existent ticket
- When the user runs `tq close nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

### Scenario: Non-existent ticket among valid ones
- Given a ticket "test-0001" exists with status `open` and no children
- When the user runs `tq close test-0001 nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"
- And ticket "test-0001" has field `status` with value `open`

## Requirement: Transition output

WHEN a transition command (`start`, `close`, `cancel`, `reopen`) succeeds, the system SHALL print every affected ticket ID to stdout, one per line, in the order the writes were committed. WHEN `close --force` or `cancel --force` cascades to descendants, the system SHALL print one ID per line for every ticket whose status was changed. WHEN the transition fails for any supplied ID, the system SHALL print nothing to stdout.

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
- Given ticket "test-0001" exists with status `closed`
- When the user runs `tq reopen test-0001`
- Then the command exits 0
- And stdout contains "test-0001"

### Scenario: Multi-ID transition prints every affected ID
- Given tickets "test-0001" and "test-0002" exist with status `open` and no children
- When the user runs `tq close test-0001 test-0002`
- Then the command exits 0
- And stdout contains "test-0001"
- And stdout contains "test-0002"

### Scenario: Failed transition does not print ID
- When the user runs `tq close nonexistent`
- Then the command exits non-zero
- And stdout is empty

### Scenario: Failed batch transition prints nothing
- Given a ticket "test-0001" exists with status `open` and no children
- When the user runs `tq close test-0001 nonexistent`
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

## Requirement: Transition notes via --note

The system SHALL accept `--note TEXT` (repeatable) on `start`, `close`, `cancel`, and `reopen`. For each `--note TEXT` supplied, the system SHALL append a timestamped entry to the `## Notes` section of every ticket whose status was changed by the invocation, in the format defined by `ticket-store`, prefixing the entry with a verb tag corresponding to the transition: `[started]` for `start`, `[closed]` for `close`, `[canceled]` for `cancel`, `[reopened]` for `reopen`. All notes written in a single invocation SHALL share a single timestamp. IF no `--note` is supplied, the system SHALL NOT write to the Notes section. IF the transition fails (any supplied ID unknown, or a non-forced parent has non-terminal descendants), the system SHALL write no notes.

### Scenario: Close with note
- Given a ticket "t-001" exists with status `open` and no children
- When the user runs `tq close t-001 --note "duplicate of t-999"`
- Then the command exits 0
- And ticket "t-001" has field `status` with value `closed`
- And the `## Notes` section of "t-001" contains an entry of the form `[closed]: duplicate of t-999` with a timestamp

### Scenario: Cancel with note
- Given a ticket "t-001" exists with status `open` and no children
- When the user runs `tq cancel t-001 --note "wontfix"`
- Then ticket "t-001" has field `status` with value `canceled`
- And the `## Notes` section of "t-001" contains an entry of the form `[canceled]: wontfix`

### Scenario: Start with note
- Given a ticket "t-001" exists with status `open`
- When the user runs `tq start t-001 --note "kicking off the spike"`
- Then ticket "t-001" has field `status` with value `in_progress`
- And the `## Notes` section of "t-001" contains an entry of the form `[started]: kicking off the spike`

### Scenario: Reopen with note
- Given a ticket "t-001" exists with status `closed`
- When the user runs `tq reopen t-001 --note "regression seen in v0.3"`
- Then ticket "t-001" has field `status` with value `open`
- And the `## Notes` section of "t-001" contains an entry of the form `[reopened]: regression seen in v0.3`

### Scenario: Transition without --note writes nothing to Notes
- Given a ticket "t-001" exists with status `open` and no `## Notes` section
- When the user runs `tq close t-001`
- Then ticket "t-001" has field `status` with value `closed`
- And ticket "t-001" still has no `## Notes` section

### Scenario: Multiple notes share one timestamp
- Given a ticket "t-001" exists with status `open` and no children
- When the user runs `tq close t-001 --note "first reason" --note "second reason"`
- Then both entries appear in the `## Notes` section in order
- And both entries carry the same timestamp
- And both entries are prefixed with `[closed]:`

### Scenario: Multi-ID transition writes notes on every affected ticket
- Given tickets "t-001" and "t-002" exist with status `open` and no children
- When the user runs `tq close t-001 t-002 --note "Q2 cleanup"`
- Then both tickets have field `status` with value `closed`
- And the `## Notes` section of "t-001" contains `[closed]: Q2 cleanup`
- And the `## Notes` section of "t-002" contains `[closed]: Q2 cleanup`

### Scenario: Force-close cascade propagates note to descendants
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- And ticket "par-0003" exists with parent "par-0002" and status `in_progress`
- When the user runs `tq close -f par-0001 --note "rolling up Q2"`
- Then all three tickets have field `status` with value `closed`
- And the `## Notes` section of each of "par-0001", "par-0002", "par-0003" contains `[closed]: rolling up Q2`

### Scenario: Force-close cascade without --note writes nothing
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close -f par-0001`
- Then both tickets have field `status` with value `closed`
- And neither ticket has a `## Notes` section

### Scenario: Force-cascade does not write notes on already-terminal descendants
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `canceled` and no `## Notes` section
- When the user runs `tq close -f par-0001 --note "rollup"`
- Then ticket "par-0001" has field `status` with value `closed`
- And the `## Notes` section of "par-0001" contains `[closed]: rollup`
- And ticket "par-0002" still has status `canceled`
- And ticket "par-0002" still has no `## Notes` section

### Scenario: Failed transition writes no notes
- Given a ticket "t-001" exists with status `open` and no children
- When the user runs `tq close t-001 nonexistent --note "should not land"`
- Then the command exits non-zero
- And ticket "t-001" has field `status` with value `open`
- And ticket "t-001" has no `## Notes` section

### Scenario: Rejected force-less cascade writes no notes
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close par-0001 --note "should not land"`
- Then the command exits non-zero
- And ticket "par-0001" has field `status` with value `open`
- And ticket "par-0001" has no `## Notes` section

## Requirement: Reject idempotent transitions

The system SHALL reject any `start`, `close`, `cancel`, or `reopen` invocation in which any explicitly-named target ticket's current status already equals the requested target status. The check SHALL run after ID resolution and before the non-terminal-descendant check, so a single already-at-target ticket aborts the whole batch atomically: no ticket file is modified and no notes are written. The error message SHALL identify the ticket and its current status (e.g. `<id> is already <status>`). The check applies to explicitly-named targets only; cascade descendants discovered via `--force` are governed by `close`/`cancel` cascade rules and do not trigger this rejection. `--force` does NOT bypass the check for an explicitly-named target that is already at the requested status.

### Scenario: Reopen on an already-open ticket is rejected
- Given a ticket "t-001" exists with status `open`
- When the user runs `tq reopen t-001`
- Then the command exits non-zero
- And stderr contains `t-001 is already open`
- And ticket "t-001" still has status `open`

### Scenario: Close on an already-closed ticket is rejected
- Given a ticket "t-001" exists with status `closed`
- When the user runs `tq close t-001`
- Then the command exits non-zero
- And stderr contains `t-001 is already closed`

### Scenario: Start on an already-in_progress ticket is rejected
- Given a ticket "t-001" exists with status `in_progress`
- When the user runs `tq start t-001`
- Then the command exits non-zero
- And stderr contains `t-001 is already in_progress`

### Scenario: Cancel on an already-canceled ticket is rejected
- Given a ticket "t-001" exists with status `canceled`
- When the user runs `tq cancel t-001`
- Then the command exits non-zero
- And stderr contains `t-001 is already canceled`

### Scenario: One already-at-target ticket aborts the whole batch
- Given ticket "t-001" exists with status `open` and no `## Notes` section
- And ticket "t-002" exists with status `closed`
- When the user runs `tq close t-001 t-002 --note "Q2 cleanup"`
- Then the command exits non-zero
- And stderr contains `t-002 is already closed`
- And ticket "t-001" still has status `open`
- And ticket "t-001" still has no `## Notes` section

### Scenario: Force flag does not bypass idempotent rejection for the named target
- Given ticket "par-0001" exists with status `closed`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close -f par-0001`
- Then the command exits non-zero
- And stderr contains `par-0001 is already closed`
- And ticket "par-0002" still has status `open`
