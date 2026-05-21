# Ticket Lifecycle

## MODIFIED Requirements

### Requirement: Start command

The system SHALL set the status to `in_progress` for every ticket ID supplied when `tq start <id>...` is invoked. At least one ID SHALL be required. The system SHALL resolve and validate all supplied IDs before mutating any ticket; IF any ID is unknown, the system SHALL exit non-zero and write nothing.

#### Scenario: Start sets in_progress
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq start test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `in_progress`

#### Scenario: Start multiple tickets
- Given tickets "test-0001" and "test-0002" exist with status `open`
- When the user runs `tq start test-0001 test-0002`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `in_progress`
- And ticket "test-0002" has field `status` with value `in_progress`

#### Scenario: Start with one unknown ID writes nothing
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq start test-0001 nonexistent`
- Then the command exits non-zero
- And ticket "test-0001" has field `status` with value `open`

### Requirement: Close command

The system SHALL set the status to `closed` for every ticket ID supplied when `tq close <id>...` is invoked. At least one ID SHALL be required. The system SHALL resolve and validate all supplied IDs before mutating any ticket; IF any ID is unknown, the system SHALL exit non-zero and write nothing. The system SHALL NOT write a `resolution` field. For each supplied ticket independently, the system SHALL reject closing it when it has descendants whose status is not a terminal state (`closed` or `canceled`) unless `-f` / `--force` is supplied; IF any supplied ticket is rejected, the system SHALL exit non-zero and write nothing. WHEN `--force` is supplied, the system SHALL set every non-terminal descendant of every supplied ticket to `closed`.

#### Scenario: Close sets closed
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq close test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `closed`
- And ticket "test-0001" has no `resolution` field

#### Scenario: Close multiple tickets
- Given tickets "test-0001" and "test-0002" exist with status `open` and no children
- When the user runs `tq close test-0001 test-0002`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `closed`
- And ticket "test-0002" has field `status` with value `closed`

#### Scenario: Close with one unknown ID writes nothing
- Given a ticket "test-0001" exists with status `open` and no children
- When the user runs `tq close test-0001 nonexistent`
- Then the command exits non-zero
- And ticket "test-0001" has field `status` with value `open`

#### Scenario: Close rejects parent with non-terminal children
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0002"
- And ticket "par-0001" has field `status` with value `open`

#### Scenario: Close batch aborts when one target has non-terminal children
- Given ticket "test-0001" exists with status `open` and no children
- And ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close test-0001 par-0001`
- Then the command exits non-zero
- And stderr contains "par-0001"
- And ticket "test-0001" has field `status` with value `open`
- And ticket "par-0001" has field `status` with value `open`

#### Scenario: Close succeeds when all children are terminal
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `closed`
- When the user runs `tq close par-0001`
- Then the command exits 0

#### Scenario: Close rejects grandparent with non-terminal grandchild
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `canceled`
- And ticket "par-0003" exists with parent "par-0002" and status `open`
- When the user runs `tq close par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0003"

#### Scenario: Close ticket with no children
- Given a ticket "test-0001" exists with no children
- When the user runs `tq close test-0001`
- Then the command exits 0

#### Scenario: Close notifies when closing last non-terminal child
- Given ticket "par-0001" has one open child "par-0002"
- When the user runs `tq close par-0002`
- Then the command exits 0
- And stdout contains the ticket ID "par-0002"
- And stdout contains a notification that "par-0001" has no remaining open children

#### Scenario: Force-close cascades to non-terminal descendants
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- And ticket "par-0003" exists with parent "par-0002" and status `in_progress`
- When the user runs `tq close -f par-0001`
- Then the command exits 0
- And ticket "par-0001" has field `status` with value `closed`
- And ticket "par-0002" has field `status` with value `closed`
- And ticket "par-0003" has field `status` with value `closed`

#### Scenario: Force-close leaves already-terminal descendants untouched
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `canceled`
- When the user runs `tq close --force par-0001`
- Then the command exits 0
- And ticket "par-0002" has field `status` with value `canceled`

### Requirement: Cancel command

The system SHALL set the status to `canceled` for every ticket ID supplied when `tq cancel <id>...` is invoked. At least one ID SHALL be required. The system SHALL resolve and validate all supplied IDs before mutating any ticket; IF any ID is unknown, the system SHALL exit non-zero and write nothing. The system SHALL NOT write a `resolution` field. For each supplied ticket independently, the system SHALL reject cancelling it when it has descendants whose status is not a terminal state (`closed` or `canceled`) unless `-f` / `--force` is supplied; IF any supplied ticket is rejected, the system SHALL exit non-zero and write nothing. WHEN `--force` is supplied, the system SHALL set every non-terminal descendant of every supplied ticket to `canceled`.

#### Scenario: Cancel sets canceled
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq cancel test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `canceled`
- And ticket "test-0001" has no `resolution` field

#### Scenario: Cancel multiple tickets
- Given tickets "test-0001" and "test-0002" exist with status `open` and no children
- When the user runs `tq cancel test-0001 test-0002`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `canceled`
- And ticket "test-0002" has field `status` with value `canceled`

#### Scenario: Cancel with one unknown ID writes nothing
- Given a ticket "test-0001" exists with status `open` and no children
- When the user runs `tq cancel test-0001 nonexistent`
- Then the command exits non-zero
- And ticket "test-0001" has field `status` with value `open`

#### Scenario: Cancel rejects parent with non-terminal children
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq cancel par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0002"
- And ticket "par-0001" has field `status` with value `open`

#### Scenario: Cancel batch aborts when one target has non-terminal children
- Given ticket "test-0001" exists with status `open` and no children
- And ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq cancel test-0001 par-0001`
- Then the command exits non-zero
- And stderr contains "par-0001"
- And ticket "test-0001" has field `status` with value `open`
- And ticket "par-0001" has field `status` with value `open`

#### Scenario: Cancel succeeds when all descendants are terminal
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `closed`
- When the user runs `tq cancel par-0001`
- Then the command exits 0
- And ticket "par-0001" has field `status` with value `canceled`

#### Scenario: Force-cancel cascades to non-terminal descendants
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- And ticket "par-0003" exists with parent "par-0002" and status `in_progress`
- When the user runs `tq cancel -f par-0001`
- Then the command exits 0
- And ticket "par-0001" has field `status` with value `canceled`
- And ticket "par-0002" has field `status` with value `canceled`
- And ticket "par-0003" has field `status` with value `canceled`

#### Scenario: Force-cancel leaves already-terminal descendants untouched
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `closed`
- When the user runs `tq cancel --force par-0001`
- Then the command exits 0
- And ticket "par-0002" has field `status` with value `closed`

### Requirement: Reopen command

The system SHALL set the status to `open` for every ticket ID supplied when `tq reopen <id>...` is invoked. At least one ID SHALL be required. The system SHALL resolve and validate all supplied IDs before mutating any ticket; IF any ID is unknown, the system SHALL exit non-zero and write nothing. The system SHALL NOT write or read a `resolution` field.

#### Scenario: Reopen from closed
- Given a ticket "test-0001" exists with status `closed`
- When the user runs `tq reopen test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `open`
- And ticket "test-0001" has no `resolution` field

#### Scenario: Reopen from canceled
- Given a ticket "test-0001" exists with status `canceled`
- When the user runs `tq reopen test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `open`

#### Scenario: Reopen multiple tickets
- Given ticket "test-0001" exists with status `closed`
- And ticket "test-0002" exists with status `canceled`
- When the user runs `tq reopen test-0001 test-0002`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `open`
- And ticket "test-0002" has field `status` with value `open`

#### Scenario: Reopen with one unknown ID writes nothing
- Given a ticket "test-0001" exists with status `closed`
- When the user runs `tq reopen test-0001 nonexistent`
- Then the command exits non-zero
- And ticket "test-0001" has field `status` with value `closed`

### Requirement: Invalid operations

The system SHALL reject invalid status values and non-existent ticket IDs with non-zero exit codes. WHEN multiple IDs are supplied and any one is non-existent, the system SHALL exit non-zero and mutate no ticket.

#### Scenario: Non-existent ticket
- When the user runs `tq close nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

#### Scenario: Non-existent ticket among valid ones
- Given a ticket "test-0001" exists with status `open` and no children
- When the user runs `tq close test-0001 nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"
- And ticket "test-0001" has field `status` with value `open`

### Requirement: Transition output

WHEN a transition command (`start`, `close`, `cancel`, `reopen`) succeeds, the system SHALL print every affected ticket ID to stdout, one per line, in the order the writes were committed. WHEN `close --force` or `cancel --force` cascades to descendants, the system SHALL print one ID per line for every ticket whose status was changed. WHEN the transition fails for any supplied ID, the system SHALL print nothing to stdout.

#### Scenario: Start prints ticket ID
- Given ticket "test-0001" exists with status `open`
- When the user runs `tq start test-0001`
- Then the command exits 0
- And stdout contains "test-0001"

#### Scenario: Close prints ticket ID
- Given ticket "test-0001" exists with status `open`
- When the user runs `tq close test-0001`
- Then the command exits 0
- And stdout contains "test-0001"

#### Scenario: Cancel prints ticket ID
- Given ticket "test-0001" exists with status `open`
- When the user runs `tq cancel test-0001`
- Then the command exits 0
- And stdout contains "test-0001"

#### Scenario: Reopen prints ticket ID
- Given ticket "test-0001" exists with status `closed`
- When the user runs `tq reopen test-0001`
- Then the command exits 0
- And stdout contains "test-0001"

#### Scenario: Multi-ID transition prints every affected ID
- Given tickets "test-0001" and "test-0002" exist with status `open` and no children
- When the user runs `tq close test-0001 test-0002`
- Then the command exits 0
- And stdout contains "test-0001"
- And stdout contains "test-0002"

#### Scenario: Failed transition does not print ID
- When the user runs `tq close nonexistent`
- Then the command exits non-zero
- And stdout is empty

#### Scenario: Failed batch transition prints nothing
- Given a ticket "test-0001" exists with status `open` and no children
- When the user runs `tq close test-0001 nonexistent`
- Then the command exits non-zero
- And stdout is empty

#### Scenario: Force-close prints all affected IDs
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close -f par-0001`
- Then the command exits 0
- And stdout contains "par-0001"
- And stdout contains "par-0002"

#### Scenario: Force-cancel prints all affected IDs
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq cancel -f par-0001`
- Then the command exits 0
- And stdout contains "par-0001"
- And stdout contains "par-0002"
