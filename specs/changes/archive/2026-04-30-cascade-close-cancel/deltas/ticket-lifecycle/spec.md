# Ticket Lifecycle

## MODIFIED Requirements

### Requirement: Close command

The system SHALL set a ticket's status to `closed` with resolution `completed` when `tq close` is invoked. The system SHALL reject closing a ticket that has open descendants unless `-f` / `--force` is supplied. WHEN `--force` is supplied, the system SHALL also close every open descendant with resolution `completed`.

#### Scenario: Close sets completed
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq close test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `closed`
- And ticket "test-0001" has field `resolution` with value `completed`

#### Scenario: Close rejects parent with open children
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001"
- When the user runs `tq close par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0002"
- And ticket "par-0001" has field `status` with value `open`

#### Scenario: Close succeeds when all children are closed
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `closed`
- When the user runs `tq close par-0001`
- Then the command exits 0

#### Scenario: Close rejects grandparent with open grandchild
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `closed`
- And ticket "par-0003" exists with parent "par-0002" and status `open`
- When the user runs `tq close par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0003"

#### Scenario: Close ticket with no children
- Given a ticket "test-0001" exists with no children
- When the user runs `tq close test-0001`
- Then the command exits 0

#### Scenario: Close notifies when closing last open child
- Given ticket "par-0001" has one open child "par-0002"
- When the user runs `tq close par-0002`
- Then the command exits 0
- And stdout contains the ticket ID "par-0002"
- And stdout contains a notification that "par-0001" has no remaining open children

#### Scenario: Force-close cascades to open descendants
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- And ticket "par-0003" exists with parent "par-0002" and status `in_progress`
- When the user runs `tq close -f par-0001`
- Then the command exits 0
- And ticket "par-0001" has field `status` with value `closed` and resolution `completed`
- And ticket "par-0002" has field `status` with value `closed` and resolution `completed`
- And ticket "par-0003" has field `status` with value `closed` and resolution `completed`

#### Scenario: Force-close leaves already-closed descendants untouched
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `closed` and resolution `canceled`
- When the user runs `tq close --force par-0001`
- Then the command exits 0
- And ticket "par-0002" has field `resolution` with value `canceled`

### Requirement: Transition output

WHEN a transition command (`start`, `close`, `cancel`, `reopen`) succeeds, the system SHALL print the affected ticket ID to stdout. WHEN `close --force` or `cancel --force` cascades to descendants, the system SHALL print one ID per line for every ticket whose status was changed, in the order the writes were committed.

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

#### Scenario: Failed transition does not print ID
- When the user runs `tq close nonexistent`
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

### Requirement: Cancel command

The system SHALL set a ticket's status to `closed` with resolution `canceled` when `tq cancel` is invoked. The system SHALL reject cancelling a ticket that has open descendants unless `-f` / `--force` is supplied. WHEN `--force` is supplied, the system SHALL also cancel every open descendant with resolution `canceled`.

#### Scenario: Cancel sets canceled
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq cancel test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `closed`
- And ticket "test-0001" has field `resolution` with value `canceled`

#### Scenario: Cancel rejects parent with open children
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq cancel par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0002"
- And ticket "par-0001" has field `status` with value `open`

#### Scenario: Cancel succeeds when all descendants are closed
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `closed`
- When the user runs `tq cancel par-0001`
- Then the command exits 0
- And ticket "par-0001" has field `resolution` with value `canceled`

#### Scenario: Force-cancel cascades to open descendants
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- And ticket "par-0003" exists with parent "par-0002" and status `in_progress`
- When the user runs `tq cancel -f par-0001`
- Then the command exits 0
- And ticket "par-0001" has field `status` with value `closed` and resolution `canceled`
- And ticket "par-0002" has field `status` with value `closed` and resolution `canceled`
- And ticket "par-0003" has field `status` with value `closed` and resolution `canceled`

#### Scenario: Force-cancel leaves already-closed descendants untouched
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `closed` and resolution `completed`
- When the user runs `tq cancel --force par-0001`
- Then the command exits 0
- And ticket "par-0002" has field `resolution` with value `completed`
