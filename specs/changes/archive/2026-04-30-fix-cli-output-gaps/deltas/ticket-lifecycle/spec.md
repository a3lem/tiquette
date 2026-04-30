# Ticket Lifecycle

## ADDED Requirements

### Requirement: Transition output

WHEN a transition command (`start`, `close`, `cancel`, `reopen`) succeeds, the system SHALL
print the affected ticket ID to stdout.

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
