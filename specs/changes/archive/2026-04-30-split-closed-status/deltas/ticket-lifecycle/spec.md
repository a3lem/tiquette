# Ticket Lifecycle

## MODIFIED Requirements

### Requirement: Close command

The system SHALL set a ticket's status to `completed` when `tq close` is invoked. The system SHALL NOT write a `resolution` field. The system SHALL reject closing a ticket that has descendants whose status is not a terminal state (`completed` or `canceled`) unless `-f` / `--force` is supplied. WHEN `--force` is supplied, the system SHALL set every non-terminal descendant's status to `completed`.

#### Scenario: Close sets completed
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq close test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `completed`
- And ticket "test-0001" has no `resolution` field

#### Scenario: Close rejects parent with non-terminal children
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0002"
- And ticket "par-0001" has field `status` with value `open`

#### Scenario: Close succeeds when all children are terminal
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `completed`
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
- And ticket "par-0001" has field `status` with value `completed`
- And ticket "par-0002" has field `status` with value `completed`
- And ticket "par-0003" has field `status` with value `completed`

#### Scenario: Force-close leaves already-terminal descendants untouched
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `canceled`
- When the user runs `tq close --force par-0001`
- Then the command exits 0
- And ticket "par-0002" has field `status` with value `canceled`

### Requirement: Cancel command

The system SHALL set a ticket's status to `canceled` when `tq cancel` is invoked. The system SHALL NOT write a `resolution` field. The system SHALL reject cancelling a ticket that has descendants whose status is not a terminal state (`completed` or `canceled`) unless `-f` / `--force` is supplied. WHEN `--force` is supplied, the system SHALL set every non-terminal descendant's status to `canceled`.

#### Scenario: Cancel sets canceled
- Given a ticket "test-0001" exists with status `open`
- When the user runs `tq cancel test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `canceled`
- And ticket "test-0001" has no `resolution` field

#### Scenario: Cancel rejects parent with non-terminal children
- Given ticket "par-0001" exists
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq cancel par-0001`
- Then the command exits non-zero
- And stderr contains "has open descendants"
- And stderr contains "par-0002"
- And ticket "par-0001" has field `status` with value `open`

#### Scenario: Cancel succeeds when all descendants are terminal
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `completed`
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
- And ticket "par-0002" exists with parent "par-0001" and status `completed`
- When the user runs `tq cancel --force par-0001`
- Then the command exits 0
- And ticket "par-0002" has field `status` with value `completed`

### Requirement: Reopen command

The system SHALL set a ticket's status to `open` when `tq reopen` is invoked. The system SHALL NOT write or read a `resolution` field.

#### Scenario: Reopen from completed
- Given a ticket "test-0001" exists with status `completed`
- When the user runs `tq reopen test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `open`
- And ticket "test-0001" has no `resolution` field

#### Scenario: Reopen from canceled
- Given a ticket "test-0001" exists with status `canceled`
- When the user runs `tq reopen test-0001`
- Then the command exits 0
- And ticket "test-0001" has field `status` with value `open`
